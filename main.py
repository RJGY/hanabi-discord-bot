from bot import HanabiBot
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

# load_dotenv()

# bot = commands.Bot(command_prefix=os.getenv('SYMBOL'), intents=discord.Intents.all())

# @bot.event
# async def on_ready():
#     print('Bot is ready.')
#     try:
#         synced = await bot.tree.sync()
#         print (f'Synced {len(synced)} commands.')
#     except Exception as e:
#         print(e)
        
# @bot.tree.command(name='hello')
# async def hello_command(interaction: discord.Interaction):
#     await interaction.response.send_message('Hello World!')
    
# @bot.tree.command(name='test')
# async def test_command(interaction: discord.Interaction):
#     await interaction.response.send_message('Test Command')
    
# @bot.tree.command(name='say')
# @app_commands.describe(message='The message to send.')
# async def say_command(interaction: discord.Interaction, message: str):
#     await interaction.response.send_message(message)
    
# bot.run(os.getenv('DISCORD_TOKEN'))

def main():
    bot = HanabiBot()
    bot.run()

if __name__ == "__main__":
    main()