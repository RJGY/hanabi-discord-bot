from bot import HanabiBot
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

def main():
    bot = HanabiBot()
    bot.run()

if __name__ == "__main__":
    main()