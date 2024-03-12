import discord
from discord.ext import commands, tasks
import datetime as dt
import os
from dotenv import load_dotenv

load_dotenv()

class SystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel = int(os.environ.get('WELCOME_CHANNEL'))
        self.general_logs = int(os.environ.get('GENERAL_LOGS'))
        self.staff_logs = int(os.environ.get('STAFF_LOGS'))
        
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick != after.nick:
            embed = discord.Embed(
                title="Nickname Change",
                colour=discord.Colour.light_grey(),
                timestamp=dt.datetime.now()
                
            )
            embed.set_thumbnail(url=after.display_avatar)
            embed.set_author(name="Hanabi Bot")
            if not after.nick:
                embed.add_field(name=f'{before.nick} reset their nickname to {after.name}', value='', inline=False)
            elif not before.nick:
                embed.add_field(name=f'{before.name} added their nickname to {after.nick}', value='', inline=False)
            else:
                embed.add_field(name=f'{before.nick} changed their nickname to {after.nick}', value='', inline=False)
            await after.guild.get_channel(self.general_logs).send(embed=embed)
        if before.display_avatar != after.display_avatar:
            embed = discord.Embed(
                title="Avatar Change",
                colour=discord.Colour.light_grey(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=after.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{before.name} changed their avatar.', value='', inline=False)
            await after.guild.get_channel(self.general_logs).send(embed=embed)
            
    

async def setup(bot):
    await bot.add_cog(SystemCommands(bot))
    

if __name__ == "__main__":
    pass