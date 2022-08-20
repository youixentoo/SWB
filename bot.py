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
from discord.ext import commands
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

class ShowCodeButtonView(discord.ui.View): # Create a class called ShowCodeButtonView that subclasses discord.ui.View
    def __init__(self, *, code, **kwargs):
        super().__init__(**kwargs)
        self.code = code

    @discord.ui.button(label="Show code", style=discord.ButtonStyle.primary) # Create a button with a label with color Blurple
    async def button_callback(self, button, interaction):
        # print(dir(interaction))
        print(f"Button pressed by: {interaction.user}")
        await interaction.response.send_message(content=self.code, ephemeral=True) # Send a message when the button is clicked


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    
@bot.command()
async def lobby(ctx, lobby_code, *args):
    match_id = "insert unique id here" 
    origin = ctx.message
    embed = discord.Embed(
        title=f"{' '.join(args)}",
        description=f"Match id: {match_id}",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    )
    # print(origin)
    await origin.delete() # Deletes the command message
    await ctx.send(view=ShowCodeButtonView(code=lobby_code), embed=embed)
    
 
    
 
# Tests    
 
@bot.slash_command(guild_ids=guildIDS)
async def ephem(ctx):

    await ctx.send_response(content="Code", ephemeral=True)    

@bot.slash_command(guild_ids=guildIDS)
async def hello(ctx):
    await ctx.respond("Hello!")
    
@bot.slash_command(guild_ids=guildIDS)
async def embed(ctx):
    embed = discord.Embed(
        title="Embed Title",
        description="Embed desc.",
        color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
    ) 
    await ctx.respond("Hello! Here's a cool embed.", embed=embed) # Send the embed with some text
 
# End of tests   


bot.run(token)


# https://support.discord.com/hc/en-us/articles/1500000580222