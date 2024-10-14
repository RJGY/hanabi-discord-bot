import discord
from discord.enums import ChannelType
from discord.ext import commands, tasks
from discord.permissions import PermissionOverwrite
import datetime as dt
import os
from dotenv import load_dotenv
import logging
import sqlite3
from typing import Optional
import requests
from ..model import Database, SavedChannel, SavedServer, LockedChannel

load_dotenv()
        
number = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
permanent = ["p", "perm", "permanent"]
year = ["y", "yr", "year", "years"]
month = ["m", "mon", "month", "months"]
week = ["w", "week", "weeks"]
day = ["d", "day", "days"]
hour = ["h", "hr", "hour", "hours"]
minutes = ["min", "minute", "minutes"]

strucutre_channel_types = [ChannelType.text, ChannelType.voice]

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
        logging.info("Unloading save commands.")
        pass
        
    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("Loaded save commands.")
        pass
        
    """Helper Functions"""
        
    """Tasks"""
    
        
    """Listeners"""
                
            
    """Commands"""
    @commands.command(name="reset")
    async def reset_command(self, ctx: commands.Context, channel: str, name: Optional[str]=None):
        if "<#" in channel:
            channel = int(channel[2:-1])
        
        if name:
            saved_channel = SavedChannel(self.db.get_saved_channel(channel, name))
            if not saved_channel:
                embed = discord.Embed(
                title="Could not reset channel",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot") 
            embed.add_field(name=f'Channel was not found.', value=f'Could not find saved channel {channel} {name}.')
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
        else:
            saved_channels = [SavedChannel(channel) for channel in self.db.get_channels_from_id(channel)]
            if not saved_channels:
                embed = discord.Embed(
                    title="Could not reset channel",
                    colour=discord.Colour.blue(),
                    timestamp=dt.datetime.now()
                )
                
                embed.set_thumbnail(url=ctx.author.display_avatar)
                embed.set_author(name="Hanabi Bot") 
                embed.add_field(name=f'Channel was not found.', value=f'Could not find saved channel {channel}.')
                embed.set_footer(text=f'{ctx.author}')
                await ctx.reply(embed=embed)
                return
            saved_channel = max(saved_channels, key=lambda x: x.db_id)
            
        
        overwrite_json = saved_channel.permissions
        overwrite = PermissionOverwrite()
        overwrite._values = overwrite_json
        
        target_channel = ctx.guild.get_channel(saved_channel.channel_id)
        new_channel = await target_channel.clone()
        await target_channel.delete()
        await new_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await new_channel.edit(position=saved_channel.position)
        
        embed = discord.Embed(
            title="Successfully Reset Channel",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(name="Hanabi Bot") 
        embed.add_field(name=f'#{new_channel.name} has been reset to default permissions.', value=f'')
        embed.set_footer(text=f'{ctx.author}')
        await new_channel.send(embed=embed)
    
        
    @commands.command(name="save")
    async def save_command(self, ctx: commands.Context, name: str):
        if not name:
            return
        if self.db.get_saved_server(ctx.guild.id, name):
            embed = discord.Embed(
                title="Cannot Save Server",
                colour=discord.Colour.red(),
                timestamp=dt.datetime.now()
            )
            
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot") 
            embed.add_field(name=f'Server cannot be saved.', value=f'Save of {ctx.guild.name} {name} already exists.')
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            return
            
        
        channels = ctx.guild.channels
        category_channels = [channel for channel in channels if channel.type == ChannelType.category]
        structure_channels = [channel for channel in channels if channel.type in strucutre_channel_types]                
        
        saved_server = SavedServer(self.db.new_saved_server(ctx.guild.id, name))
        saved_category_channels = []
        for category_channel in category_channels:
            saved_category_channels.append(SavedChannel(self.db.new_saved_channel(category_channel.id, name, saved_server.db_id, category_channel.name, category_channel.type.value, category_channel.position, -1, str(category_channel.overwrites_for(ctx.guild.default_role)._values))))
            
        for structure_channel in structure_channels:
            parent = -1
            if structure_channel.category:
                for saved_category_channel in saved_category_channels:
                    if structure_channel.category.id == saved_category_channel.channel_id:
                        parent = saved_category_channel.db_id
            permissions = str(structure_channel.overwrites_for(ctx.guild.default_role)._values).replace("'", '"').replace('False', '"False"').replace('True', '"True"')
            self.db.new_saved_channel(structure_channel.id, name, saved_server.db_id, structure_channel.name, structure_channel.type.value, structure_channel.position, parent, permissions)
            
        embed = discord.Embed(
            title="Saved Server",
            colour=discord.Colour.red(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(name="Hanabi Bot") 
        embed.add_field(name=f'Server {ctx.guild.name} has been saved to {name}.', value=f'')
        embed.set_footer(text=f'{ctx.author}')
        await ctx.reply(embed=embed)
    
    
    @commands.command(name="restore")
    async def restore_command(self, ctx: commands.Context, name: str):
        if not name:
            return
        if not self.db.get_saved_server(ctx.guild.id, name):
            embed = discord.Embed(
                title="Cannot Restore Server",
                colour=discord.Colour.red(),
                timestamp=dt.datetime.now()
            )
            
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot") 
            embed.add_field(name=f'Server cannot be restored.', value=f'Restore of {ctx.guild.name} {name} does not exist.')
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            return
        
        saved_server = SavedServer(self.db.get_saved_server(ctx.guild.id, name))
        saved_channels = [SavedChannel(channel) for channel in self.db.get_all_channels_from_server_and_name(saved_server.db_id, name)]
        parent_channels = [channel for channel in saved_channels if channel.parent == -1]
        child_channels = [channel for channel in saved_channels if channel.parent != -1]
        new_parent_channels = []
        new_child_channels = []
        
        log_channels = [self.welcome_channel, self.general_logs, self.staff_logs]
        
        for c in ctx.guild.channels:
            if c.id not in log_channels:
                await c.delete()
        
        for parent_channel in parent_channels:
            match parent_channel.type:
                case 2:
                    target_channel = await ctx.guild.create_voice_channel(parent_channel.channel_name)
                case 4:
                    target_channel = await ctx.guild.create_category_channel(parent_channel.channel_name)
                case 0:
                    target_channel = await ctx.guild.create_text_channel(parent_channel.channel_name)
                case _:
                    target_channel = await ctx.guild.create_text_channel(parent_channel.channel_name)
            new_parent_channels.append(target_channel)
        
        for i in range(len(new_parent_channels)):
            new_parent_channel = new_parent_channels[i]
            old_parent_channel = parent_channels[i]
            
            overwrite_json = old_parent_channel.permissions
            overwrite = PermissionOverwrite()
            overwrite._values = overwrite_json
            await new_parent_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await new_parent_channel.edit(position=old_parent_channel.position)
        
        for child_channel in child_channels:
            match child_channel.type:
                case 2:
                    target_channel = await ctx.guild.create_voice_channel(child_channel.channel_name)
                case 4:
                    target_channel = await ctx.guild.create_category(child_channel.channel_name)
                case 0:
                    target_channel = await ctx.guild.create_text_channel(child_channel.channel_name)
                case _:
                    target_channel = await ctx.guild.create_text_channel(child_channel.channel_name)
            new_child_channels.append(target_channel)
            
        for i in range(len(new_child_channels)):
            new_child_channel = new_child_channels[i]
            old_child_channel = child_channels[i]
            
            overwrite_json = old_child_channel.permissions
            overwrite = PermissionOverwrite()
            overwrite._values = overwrite_json
            parent_id = old_child_channel.parent
            for i in range(len(parent_channels)):
                if parent_channels[i].db_id == parent_id:
                    category_channel = new_parent_channels[i]
                
            await new_child_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await new_child_channel.edit(category=category_channel, position=old_child_channel.position)

        self.db.delete_all_locked_channels()
        

        embed = discord.Embed(
            title="Restored Server",
            colour=discord.Colour.red(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(name="Hanabi Bot") 
        embed.add_field(name=f'Server has been restored', value=f'Server has been restored from save {name}.')
        embed.add_field(name=f'Save has been removed. Please re-save.', value=f'')
        embed.add_field(name=f'All locked channels have been removed.', value=f'Re-lock all channels as needed.')
        embed.set_footer(text=f'{ctx.author}')
        await ctx.guild.get_channel(self.staff_logs).send(embed=embed)
        return
        
    
    @commands.command(name="maintenance")
    async def maintenance_command(self, ctx: commands.Context): 
        all_channels = ctx.guild.channels
        locked_channels = [LockedChannel(channel) for channel in self.db.get_all_locked_channels()]
        locked_channel_ids = [channel.channel_id for channel in locked_channels]
        non_locked_channels = [channel for channel in all_channels if channel.id not in locked_channel_ids]
        
        maintenance_mode = self.db.check_maintenance_mode()
        
        for channel in non_locked_channels:
            overwrites = channel.overwrites_for(ctx.guild.default_role)
            overwrites._values['send_messages'] = maintenance_mode
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            
        self.db.set_maintenance_mode(not maintenance_mode)
        
        if maintenance_mode:
            embed = discord.Embed(
                title="Maintenance Mode",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Maintenance Mode has been disabled.', value=f'')
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            
        else:
            embed = discord.Embed(
                title="Maintenance Mode",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Maintenance Mode has been enabled.', value=f'')
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
        return
    
async def setup(bot: commands.Bot):
    await bot.add_cog(SaveCommands(bot))
    

if __name__ == "__main__":
    pass