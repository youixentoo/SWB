# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 11:02:45 2022

@author: youixentoo
"""
import nest_asyncio
nest_asyncio.apply()

import os
import time
import sqlite3
import logging
import discord
from uuid import uuid4
from discord.ext import commands
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
        # print(dir(interaction))
        print(f"Button pressed by: {interaction.user}")
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

"""


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    
@bot.command()
async def lobby(ctx, lobby_code, *args):
    message_unix_time = int(time.time())
    origin = ctx.message
    host = f"{origin.author.name}#{origin.author.discriminator}"
    unique_id = uuid4()
    embed = discord.Embed(
        title=f"{' '.join(args)}",
        description=f"Match hosted by: {host}\nID: {unique_id}",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )
    db_primary_key = lobby_creation_db(lobby_code.upper(), host, message_unix_time, unique_id)
    await origin.delete() # Deletes the command message
    await ctx.send(view=ShowCodeButtonView(code=lobby_code, db_primary_key=db_primary_key), embed=embed)
    
    
@bot.command()
async def getData(ctx, lobby_code):
    match_data = get_data_db()
    await ctx.send(match_data)
    
    
def lobby_creation_db(lobby_code, host, unix_time, unique_id):    
    cur = conn.cursor()
    
    with conn:
        cur.execute(f"INSERT INTO LOBBY (CODE, HOST, DATE, UUID) VALUES('{lobby_code}', '{host}', {unix_time}, '{unique_id}')")
        primary_key = cur.lastrowid
        cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER) VALUES({primary_key}, '{host}')")
        
    cur.close()
    
    return primary_key


def show_code_db(primary_key, player_show):
    cur = conn.cursor()
    
    with conn:
        cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER) VALUES({primary_key}, '{player_show}')")
        
    cur.close() 
    

def get_data_db():
    cur = conn.cursor()
    data = cur.execute("select l.code, group_concat(p.player, ', ') as players from lobby l left join participants p on l.id = p.id group by l.id")
    match_data = list(data)
    print(list(match_data))
    cur.close()
    return match_data
    
 
    
 
# Tests    

@bot.command()
async def give(ctx, *args):
    embed = discord.Embed(
        title=f"{''.join(args)}",
        description="Embed desc.",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    ) 
    await ctx.send(embed=embed) # Send the embed with some text
 
@bot.slash_command(guild_ids=guildIDS)
async def ephem(ctx):

    await ctx.send_response(content="Code", ephemeral=True)    

@bot.slash_command(guild_ids=guildIDS)
async def hello(ctx):
    await ctx.respond("Hello!")
    
@bot.slash_command(guild_ids=guildIDS)
# @option(
#         "description",
#         description="Embed description",
#         required=True
# )
async def embed(ctx, code: str):
    embed = discord.Embed(
        title=f"{code}",
        description="Embed desc.",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    ) 
    await ctx.respond(embed=embed) # Send the embed with some text
 
# End of tests   

bot.run(token)


# https://support.discord.com/hc/en-us/articles/1500000580222