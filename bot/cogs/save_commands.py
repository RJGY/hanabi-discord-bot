import discord
from discord.ext import commands, tasks
import datetime as dt
import os
from dotenv import load_dotenv
import logging
import sqlite3
from typing import Optional
import requests
from ..model import Database

load_dotenv()
        
number = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
permanent = ["p", "perm", "permanent"]
year = ["y", "yr", "year", "years"]
month = ["m", "mon", "month", "months"]
week = ["w", "week", "weeks"]
day = ["d", "day", "days"]
hour = ["h", "hr", "hour", "hours"]
minutes = ["min", "minute", "minutes"]

class SaveCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel = int(os.environ.get('WELCOME_CHANNEL'))
        self.general_logs = int(os.environ.get('GENERAL_LOGS'))
        self.staff_logs = int(os.environ.get('STAFF_LOGS'))
        self.guild_id = int(os.environ.get('GUILD_ID'))
        self.admin_role_id = int(os.environ.get('ADMIN_ROLE_ID'))
        self.mod_role_id = int(os.environ.get('MOD_ROLE_ID'))
        self.db = Database()
        
    """Listeners"""
    def cog_unload(self):
        pass
        
    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("Loaded mod commands.")
        
    """Helper Functions"""
    
    def get_duration(self, duration):
        if not duration or duration in permanent:
            return None
        durations = year + month + week + day + hour + permanent
        if duration in durations:
            units = 1
        else:
            units = int(duration[0])
            duration = duration[1:]
        if not duration or not duration in durations:
            """Return nothing. Invalid duration."""
            return
        if duration in year:
            return dt.datetime.now().astimezone() + dt.timedelta(days=365*units)
        elif duration in month:
            return dt.datetime.now().astimezone() + dt.timedelta(days=30*units)
        elif duration in week:
            return dt.datetime.now().astimezone() + dt.timedelta(days=7*units)
        elif duration in day:
            return dt.datetime.now().astimezone() + dt.timedelta(days=1*units)
        elif duration in hour:
            return dt.datetime.now().astimezone() + dt.timedelta(hours=1*units)
        elif duration in minutes:
            return dt.datetime.now().astimezone() + dt.timedelta(minutes=1*units)
        
    """Tasks"""
    
        
    """Listeners"""
                
            
    """Commands"""
    @commands.command(name="reset")
    async def reset_command(self, ctx: commands.Context, channel: str, silent: Optional[str]=None):
        """ this is incorrect but leave for now """
        pass
        # if silent == "-s":
        #     silent = True
            
        # if "<#" in channel:
        #     channel = int(channel[2:-1])
        # target_channel = ctx.guild.get_channel(channel)
        
        # if not target_channel:
        #     return
        
        # overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        # overwrite.send_messages = True
        # await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        # deleted = await target_channel.purge(limit=None)
        
        # # delete db record here
        # locked_channel = LockedChannel(self.db.check_locked_channel_exists(target_channel.id))
        # if locked_channel:
        #     self.db.delete_locked_channel(locked_channel.id)
            
        # if silent:
        #     return
        
        # embed = discord.Embed(
        #     title="Successfully Reset Channel",
        #     colour=discord.Colour.blue(),
        #     timestamp=dt.datetime.now()
        # )
        
        # embed.set_thumbnail(url=ctx.author.display_avatar)
        # embed.set_author(name="Hanabi Bot")
        # embed.add_field(name=f'Reset channel #{target_channel.name}', value=f'', inline=False)
        # embed.add_field(name=f'Removed items from channel: #{target_channel.name}', value=f'Total - {len(deleted)}', inline=False)
        # embed.set_footer(text=f'{ctx.author}')
        # await ctx.send(embed=embed)
            
    
async def setup(bot: commands.Bot):
    await bot.add_cog(SaveCommands(bot))
    

if __name__ == "__main__":
    pass