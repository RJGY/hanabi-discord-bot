import discord
from discord.ext import commands, tasks
import datetime as dt
import os
from dotenv import load_dotenv
import logging
from typing import Optional
import requests
from ..model import *

load_dotenv()

number = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
permanent = ["p", "perm", "permanent"]
year = ["y", "yr", "year", "years"]
month = ["m", "mon", "month", "months"]
week = ["w", "week", "weeks"]
day = ["d", "day", "days"]
hour = ["h", "hr", "hour", "hours"]
minutes = ["min", "minute", "minutes"]
        
class Pastebin:
    '''Create a new Pastebin API wrapper instance by providing username, password, and your api dev key'''

    def __init__(self):
        self.username = os.getenv('PASTE_BIN_USERNAME')
        self.password = os.getenv('PASTE_BIN_PASSWORD')
        self.api_dev_key = os.getenv('PASTE_BIN_KEY')
        self.login_data = {'api_dev_key': self.api_dev_key,
                           'api_user_name': self.username,
                           'api_user_password': self.password}

        self.token = None
        self.login()

    '''If you want to post pastes as yourself'''

    def login(self):
        res = requests.post('https://pastebin.com/api/api_login.php', data=self.login_data)
        if res.ok:
            self.token = res.text
            return True
        return False

    '''Post a new paste'''

    def create_new_paste(self, name, content):
        payload = {
            'api_option': 'paste',
            'api_dev_key': self.api_dev_key,
            'api_user_key': self.token,
            'api_paste_name': name,
            'api_paste_expire_date': '1D',
            'api_paste_private': 1,
            'api_paste_code': content
        }
        res = requests.post('https://pastebin.com/api/api_post.php', data=payload)
        print(res.text)
        if res.ok:
            return res.text
        return False
    
    '''Get last paste'''
    
    def get_last_paste_url(self):
        payload = {
            'api_option': 'list',
            'api_dev_key': self.api_dev_key,
            'api_user_key': self.token,
            'api_results_limit': 1000
        }
        res = requests.post('https://pastebin.com/api/api_post.php', data=payload)
        if res.ok:
            return res.text.split("<paste_url>")[-1].split("</paste_url>")[0]
        return False
        

class ModerationCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel = int(os.environ.get('WELCOME_CHANNEL'))
        self.general_logs = int(os.environ.get('GENERAL_LOGS'))
        self.staff_logs = int(os.environ.get('STAFF_LOGS'))
        self.guild_id = int(os.environ.get('GUILD_ID'))
        self.admin_role_id = int(os.environ.get('ADMIN_ROLE_ID'))
        self.mod_role_id = int(os.environ.get('MOD_ROLE_ID'))
        self.invites = []
        self.db = Database()
        self.pastebin = Pastebin()
        self.index = 0
        
    """Listeners"""
    def cog_unload(self):
        self.role_task.cancel()
        self.locked_channel_task.cancel()
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.db.init_tables()
        self.db.init_schema_log()   
        await self.init_users()
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        logging.info("Loaded mod commands.")
        self.role_task.start()
        self.locked_channel_task.start()
        
    """Helper Functions"""
        
    def find_invite_by_code(self, invite_list: list[discord.Invite], code: str) -> discord.Invite:
        for inv in invite_list:
            if inv.code == code:
                return inv
    
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
            
    async def init_users(self):
        guild = self.bot.get_guild(self.guild_id)
        
        for member in guild.members:
            if not self.db.get_user(member.id):
                self.db.new_user(member.id, "N/A", 0)
            role_ids = [role.id for role in member.roles]
            role = 0
            if self.admin_role_id in role_ids:
                role = 2
            elif self.mod_role_id in role_ids:
                role = 1
            self.db.set_user_id(member.id, role)
            
        self.db.has_init_all_users()
            
    async def on_command_success(self, command: commands.Context=None, interaction: discord.Interaction=None):
        """On command function."""
        embed = discord.Embed(
            title="Command Used",
            colour=discord.Colour.green(),
            timestamp=dt.datetime.now()
        )
        if interaction:
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{interaction.user} (ID: {interaction.user.id}) ran command {interaction.command.name} in {interaction.channel}', value='', inline=False)
        else:
            embed.set_thumbnail(url=command.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{command.author} (ID: {command.author.id}) ran command {command.message.content} in {command.channel}', value='', inline=False)
        await self.bot.get_channel(self.staff_logs).send(embed=embed)
        
    async def on_command_fail(self, command: Optional[commands.Context]=None, interaction: Optional[discord.Interaction]=None):
        """On command fail function."""
        embed = discord.Embed(
            title="Command Used",
            colour=discord.Colour.green(),
            timestamp=dt.datetime.now()
        )
        if command:
            embed.set_thumbnail(url=command.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{command.author} (ID: {command.author.id}) attempted to exeucte {command.message.content} in {command.channel}', value='Failed Reason: No Permission', inline=False)
        else:
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{interaction.user} (ID: {interaction.user.id}) attempted to exeucte {interaction.message.content} in {interaction.channel}', value='Failed Reason: No Permission', inline=False)
        await self.bot.get_channel(self.staff_logs).send(embed=embed)
        
    """Tasks"""
    
    @tasks.loop(seconds=60.0)
    async def role_task(self):
        logging.debug("Scanning for temporary roles...")
        roles = self.db.get_all_roles()
        for role in roles:
            role_obj = Role(role)
            if role_obj.expiry_time < dt.datetime.now().astimezone():
                discord_role = self.bot.get_guild(self.guild_id).get_role(role_obj.role_id)
                user = self.bot.get_guild(self.guild_id).get_member(role_obj.user_id)
                if not user or not discord_role:
                    self.db.delete_role(role_obj.id)
                    continue
                await user.remove_roles(discord_role, reason="Role timed out")
                user = self.bot.get_guild(self.guild_id).get_member(role_obj.user_id)
                self.db.delete_role(role_obj.id)
                
                embed = discord.Embed(
                    title="Role Removed",
                    colour=discord.Colour.green(),
                    timestamp=dt.datetime.now()
                )
                embed.set_thumbnail(url=user.display_avatar)
                embed.set_author(name="Hanabi Bot")
                embed.add_field(name=f'{user.display_name} (ID: {user.id}) Role was removed', value='Role timed out', inline=False)
                await self.bot.get_channel(self.staff_logs).send(embed=embed)
                
                
    @tasks.loop(seconds=60.0)
    async def locked_channel_task(self):
        logging.debug("Scanning for locked channels...")
        channels = self.db.get_all_locked_channels()
        for channel in channels:
            channel_obj = LockedChannel(channel)
            if channel_obj.expiry_time < dt.datetime.now().astimezone():
                guild = self.bot.get_guild(self.guild_id)
                locked_channel = guild.get_channel(channel_obj.channel_id)
                overwrite = locked_channel.overwrites_for(guild.default_role)
                overwrite.send_messages = True
                await locked_channel.set_permissions(guild.default_role, overwrite=overwrite)
                self.db.delete_locked_channel(channel_obj.id)
                
                user = self.bot.get_guild(self.guild_id).get_member(channel_obj.created_by)
                embed = discord.Embed(
                    title="Role Removed",
                    colour=discord.Colour.green(),
                    timestamp=dt.datetime.now()
                )
                embed.set_thumbnail(url=user.display_avatar)
                embed.set_author(name="Hanabi Bot")
                embed.add_field(name=f'{user.display_name} (ID: {user.id}) Locked channel was removed', value='Locked channel timed out', inline=False)
                await self.bot.get_channel(self.staff_logs).send(embed=embed)
        
    
    @role_task.before_loop
    async def before_role_task(self):
        logging.info('Waiting for role task...')
        await self.bot.wait_until_ready()
        
    @locked_channel_task.before_loop
    async def before_channel_task(self):
        logging.info('Waiting for channel task...')
        await self.bot.wait_until_ready()
        
    """Listeners"""
                
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        invites_before_join = self.invites
        invites_after_join = await member.guild.invites()
        
        for invite in invites_before_join:
            if invite.uses < self.find_invite_by_code(invites_after_join, invite.code).uses:
                invite_code = invite.code
        
        self.db.new_user(member.id, invite_code, 0)
        
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):   
        if self.db.get_user(message.author.id):
            self.db.add_message_count(message.author.id)
            
    """Commands"""
    @discord.app_commands.command(name="test", description="Test command.")
    async def test_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Test command.")
        
    @discord.app_commands.command(name="info", description="Retrieves the discord info from a user.")
    @discord.app_commands.describe(member="The user to retrieve info from.")
    async def info_command(self, interaction: discord.Interaction, member: discord.Member):
        """Retrieves the discord info from a user."""
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        if not self.db.get_user(member.id):
            self.db.new_user(member.id, "N/A", 0)
    
        await self.on_command_success(interaction=interaction)
        
        db_data = self.db.get_user(member.id)
        user = User(db_data)
        embed = discord.Embed(
            title="Info",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'User Name:', value=f'{member.name}', inline=True)
        embed.add_field(name=f'Server Join Date', value=f'{member.joined_at.date()}', inline=True)
        embed.add_field(name='User ID:', value=f'{member.id}', inline=True)
        invite_code = user.invite_code if user.invite_code else "N/A"
        embed.add_field(name='Invited Link: ', value=f'{invite_code}', inline=True)
        embed.add_field(name='Account Creation Date:', value=f'{member.created_at.date()}', inline=True)
        embed.add_field(name='Total Messages:', value=f'{user.message_count}')
        roles = [role.name for role in member.roles if role.name != '@everyone']
        embed.add_field(name='User Roles', value=f'{", ".join(roles)}', inline=True)
        embed.add_field(name='Bans: ', value=f'{user.ban_count}', inline=True)
        embed.add_field(name='Kicks: ', value=f'{user.kick_count}', inline=True)
        embed.add_field(name='Timeouts: ', value=f'{user.timeout_count}', inline=True)
        embed.add_field(name='Has Been Previously Banned: ', value=f'{bool(user.has_been_banned)}', inline=True)
        embed.set_footer(text=f'{interaction.user.display_name}')
        await interaction.response.send_message(embed=embed)
            
    @discord.app_commands.command(name="timeout", description="Times out a user.")
    @discord.app_commands.describe(member="The user to time out.")
    @discord.app_commands.describe(silent="Silences the timeout message.")
    @discord.app_commands.describe(duration="The duration of the timeout.")
    @discord.app_commands.describe(reason="The reason for the timeout.")
    async def timeout_command(self, interaction: discord.Interaction, member: discord.Member, silent: Optional[bool]=None, duration: Optional[str]=None, reason: Optional[str]=None):
        """Times out a user."""
        if not silent:
            silent = False
            
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        target_role = User(self.db.get_user(member.id)).role
        user_role = User(self.db.get_user(interaction.user.id)).role
        if user_role > target_role and user_role > 0:
            date = self.get_duration(duration)
            today = dt.datetime.now().astimezone()
            if not date or (date - today).days > 28:
                date = dt.datetime.now().astimezone() + dt.timedelta(days=28)
            await member.edit(timed_out_until=date, reason=reason)
            await self.on_command_success(interaction=interaction)
            self.db.add_timeout_count(member.id)
            if silent:
                return
            embed = discord.Embed(
                title="Timed User Out",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{member.display_name} was successfully timed out by {interaction.user.display_name}', value='', inline=False)
            embed.add_field(name=f'Timed out until: {date}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{interaction.user.display_name}')
            await interaction.response.send_message(embed=embed)
        else:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to execute timeout command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user.display_name}')
            await interaction.response.send_message(embed=embed)
            await self.on_command_fail(interaction)
        
    @discord.app_commands.command(name="untimeout", description="Removes timeout from a user.")
    @discord.app_commands.describe(member="The user to remove the timeout from.")
    @discord.app_commands.describe(silent="Silences the timeout message.")
    @discord.app_commands.describe(reason="The reason for the untimeout.")
    async def untimeout_command(self, interaction: discord.Interaction, member: discord.Member, silent: Optional[bool]=None, reason: Optional[str]=None):
        """Removes timeout from a user."""
        if not silent:
            silent = False
        
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
            
        target_role = User(self.db.get_user(member.id)).role
        user_role = User(self.db.get_user(interaction.user.id)).role
        is_timed_out = member.is_timed_out()
        if user_role > target_role and is_timed_out and user_role > 0:
            await member.timeout(None, reason=reason)
            await self.on_command_success(interaction=interaction)
            if silent:
                return
            embed = discord.Embed(
                title="Time Out Removed",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{member.display_name} was untimed out by {interaction.user.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
        else:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to execute untimeout command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            await self.on_command_fail(interaction=interaction)
            
    @discord.app_commands.command(name="kick", description="Kicks a user from guild.")
    @discord.app_commands.describe(member="The user to kick.")
    @discord.app_commands.describe(silent="Silences the kick message.")
    @discord.app_commands.describe(reason="The reason for the kick.")
    async def kick_command(self, interaction: discord.Interaction, member: discord.Member, silent: Optional[bool]=None, reason: Optional[str]=None):
        """Kicks a user from guild."""
        if not silent :
            silent = False
        
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
            
        target_role = User(self.db.get_user(member.id)).role
        user_role = User(self.db.get_user(interaction.user.id)).role
        if user_role > target_role and user_role > 0:
            await member.kick(reason=reason)
            await self.on_command_success(interaction=interaction)
            self.db.add_kick_count(member.id)
            if silent:
                return
            embed = discord.Embed(
                title="Kicked User",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{member.display_name} was kicked by {interaction.user.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
        else:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to execute kick command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            await self.on_command_fail(interaction=interaction)
            
    @discord.app_commands.command(name="ban", description="Bans a user from guild.")
    @discord.app_commands.describe(member="The user to ban.")
    @discord.app_commands.describe(silent="Silences the ban message.")
    @discord.app_commands.describe(reason="The reason for the ban.")
    async def ban_command(self, interaction: discord.Interaction, member: discord.Member, silent: Optional[bool]=None, reason: Optional[str]=None):
        """Bans a user from guild."""
        if not silent:
            silent = False
            
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        if "<@" in member:
            member = interaction.guild.get_member(int(member[2:-1]))
        else:
            member = interaction.guild.get_member(member)
            
        target_role = User(self.db.get_user(member.id)).role
        user_role = User(self.db.get_user(interaction.user.id)).role
        if user_role > target_role and user_role > 0:
            await member.ban(reason=reason)
            await self.on_command_success(interaction=interaction)
            self.db.add_ban_count(member.id)
            if silent:
                return
            embed = discord.Embed(
                title="Banned User",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{member.display_name} was banned by {interaction.user.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
        else:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to execute ban command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            await self.on_command_fail(interaction=interaction)
            
    @discord.app_commands.command(name="unban", description="Unbans a user from guild.")
    @discord.app_commands.describe(member="The user to unban.")
    @discord.app_commands.describe(silent="Silences the unban message.")
    @discord.app_commands.describe(reason="The reason for the unban.")
    async def unban_command(self, interaction: discord.Interaction, member: discord.Member, silent: Optional[bool]=None, reason: Optional[str]=None):
        """Unbans a user from guild."""
        if not silent:
            silent = False
            
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
            
        user_role = User(self.db.get_user(interaction.user.id)).role
        if user_role > 0:
            await member.unban(reason=reason)
            await self.on_command_success(interaction=interaction)
            if silent:
                return
            embed = discord.Embed(
                title="Unbanned User",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{member.display_name} was unbanned by {interaction.user.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
        else:
            await self.on_command_fail(interaction=interaction)
            
    @discord.app_commands.command(name="history", description="Gets chat history of a user.")
    @discord.app_commands.describe(member="The user to retrieve chat history from.")
    @discord.app_commands.describe(channel="The channel to retrieve chat history from.")
    async def history_command(self, interaction: discord.Interaction, member: discord.Member, channel: Optional[discord.TextChannel]=None):
        """Gets chat history of a user."""
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        user_role = User(self.db.get_user(interaction.user.id)).role
        if user_role < 2:
            embed = discord.Embed(
                title="Failed to execute history command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            await self.on_command_fail(interaction=interaction)
            return
        
        target_channel = None
        channel_name = None
        
        if not channel:
            channel_name = interaction.channel.name
            target_channel = interaction.channel
        else:
            channel_name = channel.name
            target_channel = channel
            
        if not target_channel:
            return
        
        
        messages = [message async for message in target_channel.history(limit=None, oldest_first=True) if message.author.id == member.id]
        
        if len(messages) < 1:
            embed = discord.Embed(
                title="Failed to execute history command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No messages sent.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            return
        
        self.on_command_success(interaction=interaction)
        
        message_str = ""
        for message in messages: 
            message_str += f'{message.created_at} {message.author.display_name} {message.content} \n'
            
        current_time = dt.datetime.now().astimezone()
        
        self.pastebin.create_new_paste(f'{member.display_name} messages in {channel_name} as of {current_time}', message_str)
        last_paste = self.pastebin.get_last_paste_url()
        
        embed = discord.Embed(
            title="User Chat History",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'{member.display_name} Chat  :', value=f'{channel_name}', inline=False)
        embed.add_field(name=f'Pastebin Link:', value=f'{last_paste}', inline=False)
        embed.set_footer(text=f'{interaction.user}')
        await interaction.response.send_message(embed=embed)
        
    @discord.app_commands.command(name="addrole", description="Adds a role to a user.")
    @discord.app_commands.describe(member="The user to add the role to.")
    @discord.app_commands.describe(role="The role to add.")
    @discord.app_commands.describe(silent="Silences the add role message.")
    @discord.app_commands.describe(duration="The duration of the role.")
    @discord.app_commands.describe(reason="The reason for the role.")
    async def addrole_command(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role, silent: Optional[bool]=None, duration: Optional[str]=None, reason: Optional[str]=None):
        """Adds a role to a user."""
        if not silent:
            silent = False

        if not member:
            embed = discord.Embed(
                title="Failed to execute addrole command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: Incorrect arguements.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            return
        
        user_role = User(self.db.get_user(interaction.user.id)).role
        
        # Only admins can use this command
        if user_role < 2:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to execute add role command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            await self.on_command_fail(interaction=interaction)
            return
            
        if not role:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'No role provided.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        if role.id == self.admin_role_id:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Unable to give admin role.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        if not reason:
            reason = f'Added by {interaction.user}'
        
        await interaction.user.add_roles(role, reason=reason)
        expiry_date = self.get_duration(duration)
        
        if expiry_date:
            self.db.new_temp_role(member.id, role.id, expiry_date, reason, interaction.user.id)
            
        if silent: 
            return
        
        embed = discord.Embed(
            title="Successfully Updated User's Roles",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'Role Added:', value=f'{role.name}', inline=False)
        if not expiry_date:
            embed.add_field(name=f'Duration:', value=f'N/A', inline=False)
        else:
            embed.add_field(name=f'Duration:', value=f'{expiry_date}', inline=False)
        embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
        embed.set_footer(text=f'{interaction.user}')
        await interaction.response.send_message(embed=embed)
            
    
    @discord.app_commands.command(name="removerole", description="Removes a role from a user.")
    @discord.app_commands.describe(member="The user to remove the role from.")
    @discord.app_commands.describe(role="The role to remove.")
    @discord.app_commands.describe(silent="Silences the remove role message.")
    @discord.app_commands.describe(reason="The reason for the role.")
    async def removerole_command(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role, silent: Optional[bool]=None, reason: Optional[str]=None):
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        user_role = User(self.db.get_user(interaction.user.id)).role
        if user_role < 2:
            if silent: 
                return
            embed = discord.Embed(
                title="Failed to execute remove role command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            await self.on_command_fail(interaction=interaction)
            return
            
        if not role:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'No role provided.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        if role.id == self.admin_role_id:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Unable to remove admin role.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        if not reason:
            reason = f'Removed by {interaction.user}'
            
        await interaction.user.remove_roles(role, reason=reason)
        
        if silent: 
            return
        
        embed = discord.Embed(
            title="Successfully Updated User's Roles",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'Role Removed:', value=f'{role.name}', inline=False)
        embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
        embed.set_footer(text=f'{interaction.user}')
        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="clear", description="Clears all punishment history of a user.")
    @discord.app_commands.describe(member="The user to clear the punishment history of.")
    @discord.app_commands.describe(silent="Silences the clear message.")
    async def clear_command(self, interaction: discord.Interaction, member: discord.Member, silent: Optional[bool]=None):
        if not silent:
            silent = False
            
        if not member:
            embed = discord.Embed(
                title="Error",
                colour=discord.Colour.red(),    
                timestamp=dt.datetime.now()
            )
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Member was not found.', value='')
            interaction.response.send_message(embed=embed)
            return
        
        self.db.clear_user_punishment_history(member.id)
        
        if silent: 
            return
        
        embed = discord.Embed(
            title="Successfully Cleared User's Punishment History",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'Punishment history removed from: {member.display_name}', value=f'', inline=False)
        embed.set_footer(text=f'{interaction.user}')
        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="purge", description="Purges a channel of messages.")
    @discord.app_commands.describe(multi="The channel/person to purge.")
    @discord.app_commands.describe(silent="Silences the purge message.")
    async def purge_command(self, interaction: discord.Interaction, multi: str, silent: Optional[bool]=None):
        if not silent:
            silent = False
        
        if "<#" in multi:
            channel = int(multi[2:-1])
            target_channel = interaction.guild.get_channel(channel)
            
            if not target_channel:
                embed = discord.Embed(
                    title="Error",
                    colour=discord.Colour.red(),    
                    timestamp=dt.datetime.now()
                )
                embed.set_author(name="Hanabi Bot")
                embed.add_field(name=f'Channel was not found.', value='')
                interaction.response.send_message(embed=embed)
                return
            
            deleted = await target_channel.purge(limit=None)
            
            if silent:
                return
            
            embed = discord.Embed(
                title="Successfully Purged Channel",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Removed items from channel: #{target_channel.name}', value=f'Total - {len(deleted)}', inline=False)
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            
        else:
            if "<@" in multi:
                member = interaction.guild.get_member(int(multi[2:-1]))
            else:
                member = interaction.guild.get_member(multi)
            if not member:
                embed = discord.Embed(
                    title="Error",
                    colour=discord.Colour.red(),    
                    timestamp=dt.datetime.now()
                )
                embed.set_author(name="Hanabi Bot")
                embed.add_field(name=f'Member was not found.', value='')
                interaction.response.send_message(embed=embed)
                return
            channels = [discord_channel for discord_channel in interaction.guild.channels if str(discord_channel.type) == 'text']
            deleted_messages = dict()
            total_messages = 0
            for discord_channel in channels:
                deleted = await discord_channel.purge(limit=None, check=lambda message: message.author == member)
                deleted_messages[discord_channel.name] = len(deleted)
                total_messages += len(deleted)
            
            if silent:
                return
            
            embed = discord.Embed(
                title="Successfully Purged Channel",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            if len(deleted_messages) < 9:
                for key, value in deleted_messages.items():
                    embed.add_field(name=f'#{key} - {value} messages', value=f'')
            embed.add_field(name=f'Total - {total_messages} messages', value=f'')
            embed.set_footer(text=f'{interaction.user}')
            await interaction.response.send_message(embed=embed)
            
    
    @discord.app_commands.command(name="lock", description="Locks a channel.")
    @discord.app_commands.describe(channel="The channel to lock.")
    @discord.app_commands.describe(silent="Silences the lock message.")
    @discord.app_commands.describe(duration="The duration of the lock.")
    @discord.app_commands.describe(reason="The reason for the lock.")
    async def lock_command(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel]=None, silent: Optional[bool]=None, duration: Optional[str]=None, reason: Optional[str]=None):
        if not silent:
            silent = False
            
        target_channel = channel or interaction.channel
        overwrite = target_channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await target_channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        expiry_date = self.get_duration(duration)
        
        if expiry_date:
            self.db.new_locked_channel(target_channel.id, expiry_date, reason, interaction.user.id)
        
        if silent:
            return
        
        embed = discord.Embed(
            title="Successfully Locked Channel",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=interaction.user.display_avatar)
        embed.set_author(name="Hanabi Bot") 
        embed.add_field(name=f'#{target_channel.name} has been locked.', value=f'')
        embed.set_footer(text=f'{interaction.user}')
        await target_channel.send(embed=embed)
    
    @discord.app_commands.command(name="unlock", description="Unlocks a locked channel.")
    @discord.app_commands.describe(channel="The channel to unlock.")
    @discord.app_commands.describe(silent="Silences the unlock message.")
    async def unlock_command(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel]=None, silent: Optional[bool]=None):
        if not silent:
            silent = False
        
        target_channel = channel or interaction.channel
        overwrite = target_channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await target_channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        locked_channel = LockedChannel(self.db.get_locked_channel(target_channel.id))
        if locked_channel and len(locked_channel.__dict__) > 0:
            self.db.delete_locked_channel(locked_channel.id)
        
        if silent:
            return
        
        embed = discord.Embed(
            title="Successfully Unlocked Channel",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=interaction.user.display_avatar)
        embed.set_author(name="Hanabi Bot") 
        embed.add_field(name=f'#{target_channel.name} has been unlocked.', value=f'')
        embed.set_footer(text=f'{interaction.user}')
        await target_channel.send(embed=embed)
    
async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCommands(bot))
    
    
def test_database():
    database = Database()
    database.init_tables()
    
    user_id = 124
    invite_code = "invite"
    role_id = 0
    database.new_user(user_id, invite_code, role_id)
    database.set_user_id(user_id, 1)
    
    database.init_schema_log()
    database.add_message_count(user_id)
    database.clear_user_punishment_history(user_id)
    
    temp_role_id = 1226467615229345825
    expiry_time = str(dt.datetime.now().astimezone())
    reason = "balls"
    created_by = 150124453815255040
    database.new_temp_role(user_id, temp_role_id, expiry_time, reason, created_by)
    
    
def test_pastebin_api():
    pastebin = Pastebin()
    pastebin.create_new_paste("new_paste", "new_content")
    last_paste_url = pastebin.get_last_paste_url()
    print(last_paste_url)
    

if __name__ == "__main__":
    test_database()