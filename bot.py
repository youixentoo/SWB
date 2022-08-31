# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 11:02:45 2022

@author: youixentoo
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

import json

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
    def __init__(self, *, code, db_primary_key, **kwargs):
        super().__init__(**kwargs, timeout=300) # I think it's in seconds
        self.code = code
        self.db_primary_key = db_primary_key

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="Time limit reached, joining match disabled", view=self)

    @discord.ui.button(label="Show code", style=discord.ButtonStyle.primary) # Create a button with a label with color Blurple
    async def button_callback(self, button, interaction):
        # print(dir(interaction.user))
        # print(f"Button pressed by: {interaction.user}")
        show_code_db(self.db_primary_key, interaction.user)
        # tempSaveData(self.code, interaction.user)
        await interaction.response.send_message(content=self.code.upper(), ephemeral=True) # Send a message when the button is clicked




# class SetEncoder(json.JSONEncoder):
#     def default(self, obj):
#        if isinstance(obj, set):
#           return list(obj)
#        return json.JSONEncoder.default(self, obj)

"""
What to store in database:
    - 'Primary key'
    - Lobby code (TGHTYF) - str
    - Host (youixentoo#6937) - str
    - List of players - 1-to-many # https://www.reddit.com/r/learnpython/comments/93cief/how_to_store_a_list_in_one_sqlite3_column/
        -- Point to primary key
    - Date created match - int --> unix time, using unixepoch() method
    - UUID - str

    Table 1: Lobby
        Table 2: Participants


TODO: Set up permissions orso
TODO: Option for output to be formatted or as export or something

"""


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
    message_unix_time = int(time.time())
    origin = ctx.message
    unique_id = uuid4()
    embed = discord.Embed(
        title=description,
        description=f"Match hosted by: {ctx.user}\nID: {unique_id}",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )   
    db_primary_key = lobby_creation_db(code.upper(), ctx.user, ctx.user.id, message_unix_time, unique_id)
    await ctx.delete() # Deletes the command message
    await ctx.respond(view=ShowCodeButtonView(code=code, db_primary_key=db_primary_key), embed=embed)
    

@bot.command() #aliases=['lb', 'looby']
async def lb(ctx: discord.ApplicationContext, lobby_code, *args):
    message_unix_time = int(time.time())
    origin = ctx.message
    host = f"{origin.author.name}#{origin.author.discriminator}"
    unique_id = uuid4()
    embed = discord.Embed(
        title=f"{' '.join(args)}",
        description=f"Match hosted by: {host}\nID: {unique_id}",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )   
    db_primary_key = lobby_creation_db(lobby_code.upper(), host, origin.author.id, message_unix_time, unique_id)
    await origin.delete() # Deletes the command message
    await ctx.send(view=ShowCodeButtonView(code=lobby_code, db_primary_key=db_primary_key), embed=embed)


# Moderation commands


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
async def getlobby(ctx: discord.ApplicationContext, code: str, include_pid:bool):
    if(len(code) == 6):
        match_data = get_lobby_code_db(code, include_pid)
    elif(len(code) == 36):
        match_data = get_uuid_code_db(code, include_pid)
    else:
        match_data = "None"

    await ctx.respond(match_data)


@bot.slash_command(guild_ids=guildIDS, description="Retrieve data from multiple lobbies at once. Only ever search 1 type of code at once.")
@option(
        "codes",
        description="Multiple lobby codes or lobby ids, seperated with a space",
        required=True
        )
async def getlobbys(ctx: discord.ApplicationContext, codes: str):
    t_codes = tuple(codes.split(" "))
    
    if(len(t_codes[1]) == 6):
        match_data = get_lobby_codes_db(t_codes)
    elif(len(t_codes[1]) == 36):
        match_data = get_uuid_codes_db(t_codes)
    else:
        match_data = "None"
        
    await ctx.respond(match_data)


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
async def getperiod(ctx: discord.ApplicationContext, a1: str, a2=None):
    if(a2):
        match_data = get_unix_double(a1, a2)
    else:
        match_data = get_unix_single(a1)
        
    await ctx.respond(match_data)
    
    


def lobby_creation_db(lobby_code, host, host_id, unix_time, unique_id):
    cur = conn.cursor()

    with conn:
        cur.execute(f"INSERT INTO LOBBY (CODE, HOST, DATE, UUID) VALUES('{lobby_code}', '{host}', {unix_time}, '{unique_id}')")
        primary_key = cur.lastrowid
        cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER, PLAYERID) VALUES({primary_key}, '{host}', '{host_id}')")

    cur.close()

    return primary_key


def show_code_db(primary_key, player_show):
    cur = conn.cursor()

    with conn:
        try:
            cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER, PLAYERID) VALUES({primary_key}, '{player_show}', '{player_show.id}')")
        except sqlite3.IntegrityError as sql_IE:
            pass

    cur.close()


def get_lobby_code_db(lobby_code, include_pid):
    cur = conn.cursor()
    if include_pid:
        data = cur.execute(f"select l.code, group_concat(p.player || '; ' || p.playerid, ', ') from lobby l left join participants p on l.id = p.id where l.code = '{lobby_code}'")
    else:
        data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.code = '{lobby_code}'")
    match_data = list(data)
    print(list(match_data))
    cur.close()
    return match_data


def get_lobby_codes_db(lobby_codes):
    cur = conn.cursor()
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.code in {lobby_codes} group by l.id")
    match_data = list(data)
    print(list(match_data))
    cur.close()
    return match_data



def get_uuid_code_db(uuid_code, include_pid):
    cur = conn.cursor()
    if include_pid:
        data = cur.execute(f"select l.uuid, group_concat(p.player || '; ' || p.playerid, ', ') from lobby l left join participants p on l.id = p.id where l.uuid = '{uuid_code}'")
    else:
        data = cur.execute(f"select l.uuid, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.uuid = '{uuid_code}'")
    match_data = list(data)
    print(list(match_data))
    cur.close()
    return match_data


def get_uuid_codes_db(uuid_codes):
    cur = conn.cursor()
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.uuid in {uuid_codes} group by l.id")
    match_data = list(data)
    print(list(match_data))
    cur.close()
    return match_data


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
    
    
def get_unix_double(arg1, arg2):
    dt1 = dateparser.parse(arg1, settings={'DATE_ORDER': 'MDY'})
    dt2 = dateparser.parse(arg2, settings={'DATE_ORDER': 'MDY'})
    
    unix_start = int(dt1.timestamp())
    unix_end = int(dt2.timestamp())
    return get_period_db(unix_start, unix_end)


def get_period_db(unix_start, unix_end):    
    cur = conn.cursor()
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.date > {unix_start} and l.date < {unix_end} group by l.id")
    match_data = list(data)
    print(list(match_data))
    cur.close()
    return match_data


bot.run(token)


# https://support.discord.com/hc/en-us/articles/1500000580222
