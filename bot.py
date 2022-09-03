# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 11:02:45 2022

@author: youixentoo

List of things to do in order
TODO: Feedback
TODO: Duplicate lobby codes

TODO: Set up permissions orso --> you can do this in server settings

"""
import nest_asyncio
nest_asyncio.apply()

import os
import time
import datetime
import dateparser
import sqlite3
import logging
import discord
from uuid import uuid4
from discord.ext import commands
from discord.commands import option
from dotenv import load_dotenv

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

token = os.getenv("TOKEN")
guildIDS = [1009793614337024000]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect('db/storage.db')


class ShowCodeButtonView(discord.ui.View): # Create a class called ShowCodeButtonView that subclasses discord.ui.View
    """
    Class that subclasses discord.ui.View
    
    Adds 2 buttons. One shows the lobby code, to only the user that pressed the button.
    The other button closes the match (removes all buttons), only the person who hosts can do this.
    The match gets closes automatically after 300 seconds (5 min)
    """
    def __init__(self, *, code, db_primary_key, host, **kwargs):
        super().__init__(**kwargs, timeout=300) # I think it's in seconds
        self.code = code
        self.db_primary_key = db_primary_key
        self.host = host
        self.disabled = False

    async def on_timeout(self):
        if not(self.disabled):
            self.clear_items() 
        return

        # await self.message.edit(view=self) # content="Time limit reached, joining match disabled",

    @discord.ui.button(label="Show code", style=discord.ButtonStyle.primary) # Create a button with a label with color Blurple
    async def button_callback(self, button, interaction):
        show_code_db(self.db_primary_key, interaction.user)
        await interaction.response.send_message(content=self.code.upper(), ephemeral=True) # Send a message when the button is clicked

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red) # Create a button with a label with color Red
    async def second_button_callback(self, button, interaction):
        if(str(interaction.user) == str(self.host)):
            self.clear_items()
            self.disabled = True
            await interaction.response.edit_message(content="Match closed", view=self)
        else:
            await interaction.response.send_message(content="You're not the host of this match and therefore don't have permission to close it", ephemeral=True) # Send a message when the button is clicked



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# User command

@bot.slash_command(guild_ids=guildIDS, description="Create a lobby for other players to join")
@option(
        "code",
        description="6 letter match code",
        required=True
        )
@option(
        "description",
        description="Type of match, for example: 'NM pods'",
        required=True
        )
async def lobby(ctx: discord.ApplicationContext, code: str, description: str):
    """
    Command for creation of lobbies. Stores every lobby in a sqlite database.

    Parameters
    ----------
    code : str
        The lobby code.
    description : str
        Description of the match; game mode, map, etc.

    Returns
    -------
    Embed with the name of the host and UUID of the match. Underneath it shows 2 buttons, one to show the lobby code, 
    the other is used to close the match by the person who hosted.

    """
    if(len(code) != 6 or not code.isalpha()):
        await ctx.respond(content=f"Invalid lobby code: {code}", ephemeral=True)
        return
    
    message_unix_time = int(time.time())
    unique_id = uuid4()
    embed = discord.Embed(
        title=description,
        description=f"Match hosted by: {ctx.user}\nID: {unique_id}",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )
    db_primary_key = lobby_creation_db(code.upper(), ctx.user, ctx.user.id, message_unix_time, unique_id)
    await ctx.delete()
    await ctx.respond(view=ShowCodeButtonView(code=code, db_primary_key=db_primary_key, host=ctx.user), embed=embed)


# @bot.command(aliases=['lbb', 'looby'])
# async def lobby(ctx: discord.ApplicationContext, lobby_code=None, *args):
#     if not(lobby_code):
#         await ctx.reply(content="Example usage: !lobby ABCDEF NM pods")
#         return

#     message_unix_time = int(time.time())
#     origin = ctx.message

#     if(len(lobby_code) != 6):
#         await ctx.reply(content="Invalid lobby code")
#         return
#     else:
#         await origin.delete() # Deletes the command message

#     host = f"{origin.author.name}#{origin.author.discriminator}"
#     unique_id = uuid4()
#     embed = discord.Embed(
#         title=f"{' '.join(args)}",
#         description=f"Match hosted by: {host}\nID: {unique_id}",
#         color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
#     )
#     db_primary_key = lobby_creation_db(lobby_code.upper(), host, origin.author.id, message_unix_time, unique_id)
#     await ctx.send(view=ShowCodeButtonView(code=lobby_code, db_primary_key=db_primary_key, host=host), embed=embed)


# Moderation commands

# /getlobby
@bot.slash_command(guild_ids=guildIDS, description="Retrieve data from a lobby using either the lobby code or the lobby id")
@option(
        "code",
        description="Lobby code or lobby id",
        required=True
        )
@option(
        "include_pid",
        description="Include player id (True/False)",
        required=False,
        default=False)
async def getlobby(ctx: discord.ApplicationContext, code: str, include_pid:bool=False):
    """
    Staff command to search the database for single lobby codes. 
    To be used with either the 6 letter codes or the 36 character UUID.
    Optionally, you can include a bool to add the user id of the players to the output.

    Parameters
    ----------
    code : str
        The lobby code to search.
    include_pid : bool, optional
        True or False to add the user's id to the output. The default is False.

    Returns
    -------
    The data from the match.

    """
    # Check for length of the code to determine the type of code to search the database for.
    if(len(code) == 6):
        match_data = get_lobby_code_db(code, include_pid)
    elif(len(code) == 36):
        match_data = get_uuid_code_db(code, include_pid)
    else:
        match_data = "None"

    await ctx.respond(match_data)


# /getlobbys
@bot.slash_command(guild_ids=guildIDS, description="Retrieve data from multiple lobbies at once. Only ever search 1 type of code at once.")
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
    Data from the matches

    """
    t_codes = tuple(codes.split(" ")) 
    sum_l = sum(map(lambda c: len(c), codes.split(" ")))

    if(sum_l / len(t_codes) == 6):
        match_data = get_lobby_codes_db(t_codes)
    elif(sum_l / len(t_codes) == 36):
        match_data = get_uuid_codes_db(t_codes)
    else:
        match_data = "Invalid search"

    await ctx.respond(match_data)


# /getperiod
@bot.slash_command(guild_ids=guildIDS, description="Retrieve lobbies from a specified time period. Retrieves from now until specified without a2. (DMY)")
@option(
        "a1",
        description="First date, also supports 20m, 3h, or 5d",
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
    Date from the matches.

    """
    if(a2):
        match_data = get_unix_double(a1, a2)
    else:
        match_data = get_unix_single(a1)

    await ctx.respond(match_data)


# From here on it's database related functions

"""
Called when a person creates a lobby.
Creates a new entry in the database, lobby table, and adds the host to the participants table aswell.
"""
def lobby_creation_db(lobby_code, host, host_id, unix_time, unique_id):
    cur = conn.cursor()

    with conn:
        cur.execute(f"INSERT INTO LOBBY (CODE, HOST, DATE, UUID) VALUES('{lobby_code}', '{host}', {unix_time}, '{unique_id}')")
        primary_key = cur.lastrowid
        cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER, PLAYERID) VALUES({primary_key}, '{host}', '{host_id}')")

    cur.close()

    return primary_key


"""
Called when the 'Show code' button is pressed.
Adds the person who clicked the button to the database.
"""
def show_code_db(primary_key, player_show):
    cur = conn.cursor()

    with conn:
        try:
            cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER, PLAYERID) VALUES({primary_key}, '{player_show}', '{player_show.id}')")
        except sqlite3.IntegrityError as sql_IE:
            pass

    cur.close()
    
"""
Formats the output data

TODO: implement
""" 
def format_output(sql_data):
    data = list(sql_data)
    print(data)
    
    return data


"""
Retrieve data from 1 lobby based on a lobby code
"""
def get_lobby_code_db(lobby_code, include_pid):
    cur = conn.cursor()
    if include_pid:
        data = cur.execute(f"select l.code, group_concat(p.player || '; ' || p.playerid, ', ') from lobby l left join participants p on l.id = p.id where l.code = '{lobby_code}'")
    else:
        data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.code = '{lobby_code}'")
    formatted = format_output(data)
    cur.close()
    return formatted


"""
Retrieve data based on multiple lobby codes
"""
def get_lobby_codes_db(lobby_codes):
    cur = conn.cursor()
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.code in {lobby_codes} group by l.id")
    formatted = format_output(data)
    cur.close()
    return formatted


"""
Retrieve data from 1 lobby based on a UUID
"""
def get_uuid_code_db(uuid_code, include_pid):
    cur = conn.cursor()
    if include_pid:
        data = cur.execute(f"select l.uuid, group_concat(p.player || '; ' || p.playerid, ', ') from lobby l left join participants p on l.id = p.id where l.uuid = '{uuid_code}'")
    else:
        data = cur.execute(f"select l.uuid, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.uuid = '{uuid_code}'")
    formatted = format_output(data)
    cur.close()
    return formatted


"""
Retrieve data based on multiple UUIDs
"""
def get_uuid_codes_db(uuid_codes):
    cur = conn.cursor()
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.uuid in {uuid_codes} group by l.id")
    formatted = format_output(data)
    cur.close()
    return formatted


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

    dt = dateparser.parse(datestr, settings={'DATE_ORDER': 'MDY'})
    unix_start = int(dt.timestamp())
    unix_end = int(time.time())
    return get_period_db(unix_start, unix_end)


"""
Handles double date selection
"""
def get_unix_double(arg1, arg2):
    dt1 = dateparser.parse(arg1, settings={'DATE_ORDER': 'MDY'})
    dt2 = dateparser.parse(arg2, settings={'DATE_ORDER': 'MDY'})

    unix_start = int(dt1.timestamp())
    unix_end = int(dt2.timestamp())
    return get_period_db(unix_start, unix_end)


"""
Date selection database query
"""
def get_period_db(unix_start, unix_end):
    cur = conn.cursor()
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.date > {unix_start} and l.date < {unix_end} group by l.id")
    formatted = format_output(data)
    cur.close()
    return formatted


bot.run(token)


# https://support.discord.com/hc/en-us/articles/1500000580222
