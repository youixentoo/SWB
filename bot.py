# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 11:02:45 2022

@author: youixentoo

Restrict access in server settings

TODO: Fix rate limits to be per person

"""

import nest_asyncio
nest_asyncio.apply()

import logging
import discord
from os import getenv, sep
from re import sub, UNICODE
from csv import writer
from functools import partial
from json import load
from time import time
from uuid import uuid4
from dotenv import load_dotenv
from dateparser import parse as d_parse
from discord import guild_only
from discord.ext import commands
from discord.commands import option
from mysql.connector import connect
from mysql.connector.errors import OperationalError, IntegrityError
from db import get_db_connection


"""
Load settings.json
"""
def load_settings():
    with open("settings.json") as jFile:
        return load(jFile)


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a+')
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s]:%(levelname)s:%(name)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(handler)

load_dotenv()

token = getenv("TOKEN")
settings = load_settings()
guildIDS = settings["guildIDS"]
channelIDS = settings["channelIDS"]
modRoleIDS = settings["modRoleIDS"]
generalRoleIDS = settings["generalRoleIDS"]
hackerRoleID = settings["hackerRoleID"]
bypassIDS = settings["bypassIDS"]

intents = discord.Intents.default()
intents.message_content = True

# bot = commands.Bot(command_prefix='!', intents=intents)
bot = discord.Bot(intents=intents)
### Legacy sqlite3 code ###
# conn = connect(f'db{sep}storage.db')
# conn.execute("pragma foreign_keys = 1")


# Button class
class ShowCodeButtonView(discord.ui.View): # Create a class called ShowCodeButtonView that subclasses discord.ui.View
    """
    Class that subclasses discord.ui.View

    Adds 2 buttons. One shows the lobby code, to only the user that pressed the button.
    The other button closes the match (removes all buttons), only the person who hosts can do this.
    The match gets closed automatically after 300 seconds (5 min)
    """
    def __init__(self, *, code, db_primary_key, host, hackers, **kwargs):
        super().__init__(**kwargs, timeout=300) # I think it's in seconds
        self.code = code
        self.db_primary_key = db_primary_key
        self.host = host
        self.hackers = hackers
        self.disabled = False
        self.cd = commands.CooldownMapping(commands.Cooldown(18, 2), commands.BucketType.default) # Global

    async def on_timeout(self):
        self.clear_items()
        await self.message.edit(content="Match closed", view=self)

    @discord.ui.button(label="Show code", style=discord.ButtonStyle.primary) # Create a button with a label with color Blurple
    async def button_callback(self, button, interaction):
        logger.info(f"User: {interaction.user} ({interaction.user.id}) pressed the 'Show Code' button")
        bucket = self.cd.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return await interaction.response.send_message(f"Too many requests. Try again in: {round(retry_after, 1)} seconds.", ephemeral=True)
        # == 281493155377840128
        if interaction.user.id in bypassIDS or not bool(interaction.user.get_role(hackerRoleID)): # Check if the person has hacker role # 'other' role in test server: 1027299501356093562
            show_code_db(self.db_primary_key, interaction.user.id)
            await interaction.response.send_message(content=self.code.upper(), ephemeral=True) # Send a message when the button is clicked       
        else:
            await interaction.response.send_message(content="The host of this match has prevented hackers from joining", ephemeral=True) # Send a message when the button is clicked
            
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red) # Create a button with a label with color Red
    async def second_button_callback(self, button, interaction):
        if(str(interaction.user.id) == str(self.host)):
            self.clear_items()
            self.disabled = True
            await interaction.response.edit_message(content="Match closed", view=self)
        else:
            await interaction.response.send_message(content="You're not the host of this match and therefore don't have permission to close it", ephemeral=True) # Send a message when the button is clicked


# Exception handling
# Custom class to easily display message
class ExceptionDisplayMessage(Exception):
    pass


"""
Check if the channel is correct
"""
def correct_channel():
    def predicate(ctx):
        return ctx.channel_id in channelIDS
    return commands.check(predicate)


"""
Override of commands.has_any_role()
No longer of type Callable
"""
def has_required_role(*items: int | str):
    def predicate(ctx):
        if ctx.guild is None: 
            raise commands.NoPrivateMessage()
        
        getter = partial(discord.utils.get, ctx.author.roles)  # type: ignore
        if any(
            getter(id=item) is not None
            if isinstance(item, int)
            else getter(name=item) is not None
            for item in items
        ):
            return True
        raise commands.MissingAnyRole(list(items))
    
    return commands.check(predicate)


# Global
@bot.event
async def on_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.respond("You don't have access to this command", ephemeral=True)
    else:
        await ctx.respond(error)

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    logger.warning(f"User: {ctx.user} ({ctx.user.id}) used command: /{ctx.command} and caused:\n{error}")
    if isinstance(error, commands.MissingAnyRole):
        await ctx.respond("You don't have access to this command", ephemeral=True)
    elif isinstance(error, discord.errors.ApplicationCommandInvokeError):
        if isinstance(error.original, ExceptionDisplayMessage):
            await ctx.respond(error.original, ephemeral=True)
        elif isinstance(error.original, discord.errors.HTTPException):
            if(error.original.code == 50035): # exceeding max length of title (256) or query output too long
                await ctx.respond("Make your description shorter")
            else:
                embed = discord.Embed(
                    title="An error occurred",
                    description=f"{type(error)}:\n{error}\nContact: <@281493155377840128>",
                    color=discord.Colour.red(), # Because red == error
                )
                await ctx.respond(embed=embed)
        else:
            await ctx.respond(error)
    elif isinstance(error, commands.errors.NotOwner):
        await ctx.respond("You don't have access to this command", ephemeral=True)
    elif isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.respond(error, ephemeral=True)
    elif isinstance(error, discord.errors.CheckFailure):
        await ctx.respond("You can't use this command here", ephemeral=True)
    elif isinstance(error, commands.CheckAnyFailure):
        await ctx.respond("You don't have access to this command", ephemeral=True)
    else:
        embed = discord.Embed(
            title="An error occurred",
            description=f"{type(error)}:\n{error}\nContact: <@281493155377840128>",
            color=discord.Colour.red(), # Because red == error
        )

        await ctx.respond(embed=embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_application_command(ctx: discord.ApplicationContext):
    logger.info(f"User: {ctx.user} ({ctx.user.id}) used command: /{ctx.command}")


# User command
@bot.slash_command(guild_ids=guildIDS, description="Create a lobby for other players to join")
@commands.cooldown(5, 2)
@guild_only()
@correct_channel()
@option(
        "code",
        description="6 letter match code",
        required=True
        )
@option(
        "description",
        description="Type of match, for example: 'NM pods'",
        required=False,
        default=" "
        )
@option(
        "hackers",
        description="Allow hackers to join?",
        required=False,
        default=True)
async def lobby(ctx: discord.ApplicationContext, code: str, description: str, hackers: bool):
    """
    Command for creation of lobbies. Stores every lobby in a sqlite database.
    Cooldown: rate: 1, per: 5 seconds.

    Parameters
    ----------
    code : str
        The lobby code.
    description : str
        Description of the match; game mode, map, etc.
    hackers: bool, optional
        Do you allow people with hacker role to get the code?

    Returns
    -------
    Embed with the name of the host and UUID of the match. Underneath it shows 2 buttons, one to show the lobby code,
    the other is used to close the match by the person who hosted.

    """
    sub_code = sub(r"[\W]+", "", code, flags=UNICODE) # Remove any non letters

    if(len(sub_code) != 6 or not sub_code.isalpha()): # Checks code length and if it's only letters (redundant)
        await ctx.respond(content=f"Invalid lobby code: {sub_code}", ephemeral=True)
        return

    message_unix_time = int(time())
    unique_id = uuid4()
    embed = discord.Embed(
        title=description,
        description=f"**Host:** <@{ctx.user.id}>\n**ID:** `{unique_id}`",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )
    db_primary_key = lobby_creation_db(sub_code.upper(), ctx.user.id, message_unix_time, unique_id)
    button_view = ShowCodeButtonView(code=sub_code, db_primary_key=db_primary_key, host=ctx.user.id, hackers=hackers)
    await ctx.delete()
    button_view.message = await ctx.send(view=button_view, embed=embed)


# Moderation commands

# /getlobby
@bot.slash_command(guild_ids=guildIDS, description="Retrieve data from a lobby using either the lobby code or the lobby id")
@commands.cooldown(1, 5)
@commands.check_any(has_required_role(*modRoleIDS), commands.is_owner())
@guild_only()
# @correct_channel()
@option(
        "code",
        description="Lobby code or lobby id",
        required=True
        )
@option(
        "hidden",
        description="Response hidden?",
        required=False,
        default=False)
async def getlobby(ctx: discord.ApplicationContext, code: str, hidden: bool = False):
    """
    Staff command to search the database for single lobby codes.
    To be used with either the 6 letter codes or the 36 character UUID.t.

    Parameters
    ----------
    code : str
        The lobby code to search.

    Returns
    -------
    The data from the match.

    """
    # Check for length of the code to determine the type of code to search the database for.
    if(len(code) == 6):
        match_data = get_lobby_code_db(code.upper())
    elif(len(code) == 36):
        match_data = get_uuid_code_db(code)
    else:
        await ctx.respond("Please enter a valid code", ephemeral=True)
        return

    lobby, host, date, *participants = match_data
    try:
        part_list = set(f"<@{player}>" for player in participants[0].split(","))
    except AttributeError:
        raise ExceptionDisplayMessage(f"Invalid search: {code}")

    embed = discord.Embed(
        title=f"Code: {lobby}",
        description=f"**Host:** <@{host}>\n**Participants:** {', '.join(part_list)}\n**Date:** <t:{date}>",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )

    await ctx.respond(embed=embed, ephemeral=hidden)


# /getlobbys
@bot.slash_command(guild_ids=guildIDS, description="Retrieve data from multiple lobbies at once. Only ever search 1 type of code at once.")
@commands.cooldown(1, 5)
@commands.check_any(has_required_role(*modRoleIDS), commands.is_owner())
@guild_only()
# @correct_channel()
@option(
        "codes",
        description="Multiple lobby codes or lobby ids, seperated with a space",
        required=True
        )
async def getlobbys(ctx: discord.ApplicationContext, codes: str):
    """
    Staff command to search the database for multiple lobby codes.
    To be used with either the 6 letter codes or the 36 character UUIDs.

    Parameters
    ----------
    codes : str
        Lobby codes to search.

    Returns
    -------
    Data from the matches as a .tsv file.

    """
    t_codes = tuple(codes.split(" "))
    sum_l = sum(map(lambda c: len(c), codes.split(" ")))

    try:
        if(sum_l / len(t_codes) == 6):
            get_lobby_codes_db(t_codes)
        elif(sum_l / len(t_codes) == 36):
            get_uuid_codes_db(t_codes)
        else:
            await ctx.respond("Please enter valid codes", ephemeral=True)
            return
    except OperationalError:
        raise ExceptionDisplayMessage("Select more than 1 code please")

    response = discord.File("files/lobby_data.txt")
    await ctx.respond(file=response)


# /getperiod
@bot.slash_command(guild_ids=guildIDS, description="Retrieve lobbies from a specified time period. Retrieves from now until specified without a2. (DMY)")
@commands.cooldown(1, 5)
@commands.check_any(has_required_role(*modRoleIDS), commands.is_owner())
@guild_only()
# @correct_channel()
@option(
        "a1",
        description="First date, also supports for example: 20m, 3h, or 5d",
        required=True)
@option(
        "a2",
        description="Second date",
        required=False,
        default=None)
async def getperiod(ctx: discord.ApplicationContext, a1: str, a2: str=None):
    """
    Staff command to search the database for lobby codes.
    This command is based on time/dates.

    Parameters
    ----------
    a1 : str
        The first date to search, either in dd/mm/yyyy format or relative with {num}m/h/d.
    a2 : str, optional
        If specified, searches until this date. The default is None.

    Returns
    -------
    Data from the matches as a .tsv file.

    """
    try:
        if(a2):
            get_unix_double(a1, a2)
        else:
            get_unix_single(a1)
    except AttributeError:
        raise ExceptionDisplayMessage("Invalid date selected")

    response = discord.File("files/lobby_data.txt")
    await ctx.respond(file=response)


# /stats
@bot.slash_command(guild_ids=guildIDS, description="Get stats")
@commands.cooldown(1, 5)
@guild_only()
@commands.check_any(has_required_role(*modRoleIDS), commands.is_owner())
# @correct_channel()
async def stats(ctx: discord.ApplicationContext):
    """
    Shows some stats

    Returns
    -------
    Amount of lobbies and unique players logged.

    """
    stats = count_command()
    embed = discord.Embed(
        title="Logged stats",
        description=f"Lobbies: {stats[0]}\nPlayers: {stats[1]}",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )

    await ctx.respond(embed=embed)
    
        
@bot.slash_command(guild_ids=guildIDS, description="Check permissions")      
@commands.cooldown(1, 5)
@guild_only()
@commands.check_any(has_required_role(*modRoleIDS), commands.is_owner())
@option(
        "hidden",
        description="Hidden",
        required=False,
        default=True)
async def perms(ctx: discord.ApplicationContext, hidden: bool=True):
    """
    Shows channel permissions

    Returns
    -------
    The enabled permissions for the channel the command is used in.

    """
    permissions = ctx.app_permissions
        
    embed = discord.Embed(
        title="Permissions enabled",
        description="{}".format("\n".join([permission for permission, value in permissions if value])),
        color=discord.Colour.dark_teal(), 
    )
    await ctx.respond(embed=embed, ephemeral=hidden)
    
    
# General commands
    
# /usethebot
@bot.slash_command(guild_ids=guildIDS, description="Use the bot")
@commands.cooldown(1, 20)
# @has_required_role(*modRoleIDS)
@commands.check_any(has_required_role(*generalRoleIDS), commands.is_owner())
@guild_only()
@correct_channel()
@option(
        "mention",
        description="Directed at who? userid or @",
        required=False)
async def usethebot(ctx: discord.ApplicationContext, mention: str=None):
    """
    Shows embed to use the bot

    Returns
    -------
    Embed telling you to use the bot

    """
    embed = discord.Embed(
        title="This bot exists in case you find hackers in your lobby",
        description="Use **/lobby**\nFor more info: https://discord.com/channels/1000163670808068147/1000163671923765327/1139339639023476758",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )

    if(mention):
        await ctx.respond(f"Hey <@{mention.strip('<@>')}>", embed=embed)
    else:
        await ctx.respond(embed=embed)
        

# Owner command

# /query
@bot.slash_command(guild_ids=guildIDS, description="Query database")
@commands.cooldown(1, 5)
@commands.is_owner()
@guild_only()
# @correct_channel()
@option(
        "hidden",
        description="Hidden",
        required=False,
        default=False)
async def query(ctx: discord.ApplicationContext, query: str, hidden: bool=False):
    """
    Used to query the database using the bot.
    Owner only for obvious reasons.

    Parameters
    ----------
    query : str
        The query.

    Returns
    -------
    Data.

    """
    if("drop table" in query.lower()):
        await ctx.respond("No dropping tables here", ephemeral=True)
        return

    output = exc_query(query)

    if output:
        embed = discord.Embed(
            description="{}".format("".join(make_lines(output))),
            color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
        )
        await ctx.respond(embed=embed, ephemeral=hidden)
    else:
        await ctx.respond(f"Query: {query} executed", ephemeral=hidden)

# From here on it's database related functions

"""
Called when a person creates a lobby.
Creates a new entry in the database, lobby table, and adds the host to the participants table aswell.
"""
def lobby_creation_db(lobby_code, host, unix_time, unique_id):
    conn = get_db_connection()

    with conn:
        cur = conn.cursor()
        cur.execute(f"INSERT INTO LOBBY (CODE, HOST, DATE, UUID) VALUES('{lobby_code}', '{host}', {unix_time}, '{unique_id}')")
        primary_key = cur.lastrowid
        cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER) VALUES({primary_key}, '{host}')")
        conn.commit()

    cur.close()
    return primary_key


"""
Called when the 'Show code' button is pressed.
Adds the person who clicked the button to the database.
"""
def show_code_db(primary_key, player):
    conn = get_db_connection()

    with conn:
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER) VALUES({primary_key}, '{player}')")
        except IntegrityError as sql_IE:
            pass
        conn.commit()

    cur.close()


"""
Formats the output data to tsv to be opened in excel.
In order for discord to preview it, it gets saved as .txt.
"""
def format_output(sql_data):
    with open(f"files{sep}lobby_data.txt", "w", newline="") as tsv_file:
        tsv_writer = writer(tsv_file, delimiter='\t')
        tsv_writer.writerow(("Unix", "Code", "Host", "Participants"))
        tsv_writer.writerows(to_tsv(sql_data))


"""
Generator for conversion of the data from sql to tsv.
A generator is used so the entire return of data doesn't get loaded into ram.
"""
def to_tsv(T):
    for x in T:
        u, c, h, p = x
        joined = set(p.split("\t"))
        yield (u, c, h, *joined)

"""
Retrieve data from 1 lobby based on a lobby code
"""
def get_lobby_code_db(lobby_code):
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(f"SELECT l.CODE, l.HOST, l.DATE, GROUP_CONCAT(p.PLAYER) from LOBBY l LEFT JOIN PARTICIPANTS p on l.ID = p.ID WHERE l.CODE = '{lobby_code}'")
        data = cur.fetchall()
        l_data = list(data)[0]
        cur.close()
    return l_data


"""
Retrieve data based on multiple lobby codes
"""
def get_lobby_codes_db(lobby_codes):
    upper_codes = tuple(map(str.upper, lobby_codes))
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(f"SELECT l.CODE, l.HOST, l.DATE, GROUP_CONCAT(p.PLAYER SEPARATOR '\t') from LOBBY l LEFT JOIN PARTICIPANTS p on l.ID = p.ID WHERE l.CODE in {upper_codes} GROUP BY l.CODE")
        data = cur.fetchall()
        format_output(data)
        cur.close()


"""
Retrieve data from 1 lobby based on a UUID
"""
def get_uuid_code_db(uuid_code):
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(f"SELECT l.UUID, l.HOST, l.DATE, GROUP_CONCAT(p.PLAYER) from LOBBY l LEFT JOIN PARTICIPANTS p on l.ID = p.ID WHERE l.UUID = '{uuid_code}'")
        data = cur.fetchall()
        l_data = list(data)[0]
        cur.close()
        return l_data


"""
Retrieve data based on multiple UUIDs
"""
def get_uuid_codes_db(uuid_codes):
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(f"SELECT l.DATE, l.CODE, l.HOST, GROUP_CONCAT(p.PLAYER SEPARATOR '\t') from LOBBY l LEFT JOIN PARTICIPANTS p on l.ID = p.ID WHERE l.UUID in {uuid_codes} GROUP BY l.ID")
        data = cur.fetchall()
        format_output(data)
        cur.close()


"""
Convert the {num}m/h/d commands to one dateparser actually understands
Also handles the use of single date selection
"""
def get_unix_single(argument):
    if(argument[-1] == "m"):
        datestr = f"{argument[:-1]} min ago"
    elif(argument[-1] == "h"):
        datestr = f"{argument[:-1]} hours ago"
    elif(argument[-1] == "d"):
        datestr = f"{argument[:-1]} days ago"
    else:
        datestr = argument

    dt = d_parse(datestr, settings={'DATE_ORDER': 'MDY'})
    unix_start = int(dt.timestamp())
    unix_end = int(time())
    return get_period_db(unix_start, unix_end)


"""
Handles double date selection
"""
def get_unix_double(arg1, arg2):
    dt1 = d_parse(arg1, settings={'DATE_ORDER': 'MDY'})
    dt2 = d_parse(arg2, settings={'DATE_ORDER': 'MDY'})

    unix_start = int(dt1.timestamp())
    unix_end = int(dt2.timestamp())
    return get_period_db(unix_start, unix_end)


"""
Date selection database query
"""
def get_period_db(unix_start, unix_end):
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(f"SELECT l.DATE, l.CODE, l.HOST, GROUP_CONCAT(p.player SEPARATOR '\t') from LOBBY l LEFT JOIN PARTICIPANTS p ON l.ID = p.ID WHERE l.DATE > {unix_start} and l.DATE < {unix_end} GROUP BY l.CODE")
        data = cur.fetchall()
        format_output(data)
        cur.close()


"""
Count some data
"""
def count_command():
    conn = get_db_connection()

    with conn:  
        cur = conn.cursor()
        cur.execute("SELECT COUNT(ID) from LOBBY")
        rows,*_ = cur.fetchone()
        cur.execute("SELECT PLAYER from PARTICIPANTS")
        groups = cur.fetchall()
        players = len(set(unpack_tuple(groups)))

    cur.close()
    return (rows, players)


"""
Unpacks list of single value tuples
"""
def unpack_tuple(single_tuple):
    for x in single_tuple:
        p,*_ = x
        yield p


"""
Query DB
"""
def exc_query(query):
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(query)
        output = cur.fetchall()
        cur.close()
        conn.commit()
    return output


"""
Generate embed output query
"""
def make_lines(output):
    for x in output:
        yield f"{x}\n"
        
    
    

bot.run(token)
