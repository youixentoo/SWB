# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 11:02:45 2022

@author: youixentoo
"""
import nest_asyncio
nest_asyncio.apply()

import os
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

class ShowCodeButtonView(discord.ui.View): # Create a class called ShowCodeButtonView that subclasses discord.ui.View
    def __init__(self, *, code, unique_id, **kwargs):
        super().__init__(**kwargs, timeout=300) # I think it's in seconds
        self.code = code
        self.unique_id = unique_id
        
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="Time limit reached, joining match disabled", view=self)

    @discord.ui.button(label="Show code", style=discord.ButtonStyle.primary) # Create a button with a label with color Blurple
    async def button_callback(self, button, interaction):
        # print(dir(interaction))
        print(f"Button pressed by: {interaction.user}")
        tempSaveData(self.code, interaction.user)
        await interaction.response.send_message(content=self.code.upper(), ephemeral=True) # Send a message when the button is clicked
        
        
     
        
# class SetEncoder(json.JSONEncoder):
#     def default(self, obj):
#        if isinstance(obj, set):
#           return list(obj)
#        return json.JSONEncoder.default(self, obj)

"""
What to store in database:
    - 'Primary key'
    - Lobby code
    - Host
    - List of players
    - Date created match
    - UUID

"""


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    
@bot.command()
async def lobby(ctx, lobby_code, *args):
    origin = ctx.message
    host = f"{origin.author.name}#{origin.author.discriminator}"
    unique_id = uuid4()
    embed = discord.Embed(
        title=f"{' '.join(args)}",
        description=f"Match hosted by: {host}\nID: {unique_id}",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )
    # print(origin)
    await origin.delete() # Deletes the command message
    await ctx.send(view=ShowCodeButtonView(code=lobby_code, unique_id=unique_id), embed=embed)
    
    
@bot.command()
async def getData(ctx, lobby_code):
    match_data = tempShowData(lobby_code)
    await ctx.send(match_data)
    
    
    
def tempLoadStorage():
    with open("storage.json") as json_file:
        return json.load(json_file)

def tempSaveStorage(tempData):
    with open("storage.json", "w") as json_file:
        return json.dump(tempData, json_file)
    
    
def tempSaveData(match_id, player):
    tempData = tempLoadStorage()
    player_string = f"{player.name}#{player.discriminator}"
    
    if(tempData.get(match_id)):
        tempPlayerData = tempData[match_id]
        if not(player_string in tempPlayerData):
            print("player already in list")
            tempPlayerData.append(player_string)
        tempData[match_id] = tempPlayerData
    else:
        tempData[match_id] = [player_string]
    
    print("TempData:",tempData)
        
    tempSaveStorage(tempData)
    
    
def tempShowData(match_id):
    tempData = tempLoadStorage()
    player_data = tempData.get(match_id)
    if(player_data):
        return "\n".join(player_data)
    else:
        return "None"
    
    
 
    
 
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