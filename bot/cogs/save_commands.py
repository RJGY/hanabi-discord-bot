import discord
from discord.ext import commands, tasks
import datetime as dt
import os
from dotenv import load_dotenv
import logging
import sqlite3
from typing import Optional
import requests

load_dotenv()

number = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
permanent = ["p", "perm", "permanent"]
year = ["y", "yr", "year", "years"]
month = ["m", "mon", "month", "months"]
week = ["w", "week", "weeks"]
day = ["d", "day", "days"]
hour = ["h", "hr", "hour", "hours"]
minutes = ["min", "minute", "minutes"]

class User():
    def __init__(self, args):
        if len(args) != 8:
            return
        self.id = args[0]
        self.invite_code = args[1]
        self.ban_count = args[2]
        self.kick_count = args[3]
        self.timeout_count = args[4]
        self.has_been_banned = args[5]
        self.role = args[6]
        self.message_count = args[7]
    
    def __str__(self) -> str:
        return f'ID: {self.id}, Invite Code: {self.invite_code}, Ban Count: {self.ban_count}, Kick Count: {self.kick_count}, Timeout Count: {self.timeout_count}, Has Been Banned Before: {self.has_been_banned}, ' + \
                    f'Role: {self.role}, Message Count: {self.message_count}'
                    
class Role():
    def __init__(self, args):
        if len(args) != 6:
            return
        self.id = args[0]
        self.role_id = args[1]
        self.user_id = args[2]
        self.expiry_time = dt.datetime.strptime(args[3], f'%Y-%m-%d %H:%M:%S.%f%z')
        self.reason = args[4]
        self.created_by = args[5]
        
    def __str__(self) -> str:
        return f'ID: {self.id}, Role ID: {self.role_id}, User ID: {self.user_id}, Expiry Time: {self.expiry_time}, Reason: {self.reason}, Created By: {self.created_by}'
    
class LockedChannel():
    def __init__(self, args) -> None:
        if len(args) != 5:
            return
        self.id = args[0]
        self.channel_id = args[1]
        self.expiry_time = dt.datetime.strptime(args[2], f'%Y-%m-%d %H:%M:%S.%f%z')
        self.reason = args[3]
        self.created_by = args[4]
    
    def __str__(self) -> str:
        return f'ID: {self.id}, Channel ID: {self.channel_id}, Expiry Time: {self.expiry_time}, Reason: {self.reason}, Created By: {self.created_by}'


class Database():
    def __init__(self):
        os.makedirs('database', exist_ok=True)
        self.database = sqlite3.connect('database/hanabi_bot.db')
        
    """Init Tables"""    
    
    def init_tables(self):
        """
        Initializes the database tables for users, temp roles, and locked channels if they do not already exist.
        """
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY NOT NULL, invite_code TEXT DEFAULT NULL, ban_count INTEGER DEFAULT 0 NOT NULL, kick_count INTEGER DEFAULT 0 NOT NULL, timeout_count INTEGER DEFAULT 0 NOT NULL, has_been_banned INTEGER DEFAULT 0 NOT NULL, role INTEGER DEFAULT 0 NOT NULL, message_count INTEGER DEFAULT 0 NOT NULL );')
        self.database.execute('CREATE TABLE IF NOT EXISTS temp_roles (id INTEGER PRIMARY KEY AUTOINCREMENT, role_id INTEGER DEFAULT NULL, user_id INTEGER NOT NULL, expiry_time TEXT DEFAULT NULL, reason TEXT DEFAULT NULL, created_by INTEGER DEFAULT NULL);')
        self.database.execute('CREATE TABLE IF NOT EXISTS locked_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id INTEGER DEFAULT NULL, expiry_time TEXT DEFAULT NULL, reason TEXT DEFAULT NULL, created_by INTEGER DEFAULT NULL)')
        self.database.commit()
        
    def init_schema_log(self):
        """
        Initializes the schema log table in the database if it doesn't exist.
        
        This function checks if the database connection is established and creates it if not.
        It then creates the schema log table with a single column 'has_init_users' of type INTEGER
        with a default value of 0.
        
        If the table is empty, it inserts a default row with all values set to 0.
        
        This function does not take any parameters and does not return anything.
        """
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        
        self.database.execute('CREATE TABLE IF NOT EXISTS schema_log (has_init_users INTEGER DEFAULT 0);')
        cursor = self.database.cursor()
        cursor.execute("SELECT COUNT(*) FROM schema_log")
        row_count = cursor.fetchone()[0]

        # If the table is empty, insert default values
        if row_count == 0:
            cursor.execute("INSERT INTO schema_log DEFAULT VALUES")
        self.database.commit()
        
    """Create object on table"""
        
    def new_user(self, id: int, invite_code: str, role: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if self.check_user_exists(id):
            return
        self.database.execute(f'INSERT INTO users (id, invite_code, role) VALUES (?, ?, ? );', (id, invite_code, role))
        self.database.commit()
        
    def new_temp_role(self, user_id: int, role_id: int, expiry_time: str, reason: str, created_by: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'INSERT INTO temp_roles (role_id, user_id, expiry_time, reason, created_by) VALUES (?, ?, ?, ?, ?);', (role_id, user_id, expiry_time, reason, created_by))
        self.database.commit()
        
    def new_locked_channel(self, channel_id: int, expiry_time: str, reason: str, created_by: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'INSERT INTO locked_channels (channel_id, expiry_time, reason, created_by) VALUES (?, ?, ?, ?);', (channel_id, expiry_time, reason, created_by))
        self.database.commit()
        
    """Check object exists"""
        
    def check_user_exists(self, id: int) -> Optional[list]:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM users WHERE id = {id}')
        return cursor.fetchone()
    
    def check_locked_channel_exists(self, channel_id: int) -> Optional[list]:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM locked_channels WHERE channel_id = {channel_id}')
        return cursor.fetchone()
    
    def check_role_exists(self, role_id: int, user_id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM temp_roles WHERE role_id = {role_id} and user_id = {user_id}')
        return cursor.fetchone()
    
    def check_has_init_user_table(self) -> bool:
        """Only needed to run once when bot is first started and there are already users in the server."""
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute("SELECT has_init_users FROM schema_log")
        return bool(cursor.fetchone()[0])
    
    def has_init_all_users(self):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'UPDATE schema_log SET has_init_users = 1;')
        self.database.commit()
        
        
    """Add to object"""
        
    def add_message_count(self, id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.check_user_exists(id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT message_count FROM users WHERE id = {id}')
        message_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET message_count = {message_count} WHERE id = {id};')
        self.database.commit()
    
    def add_timeout_count(self, id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.check_user_exists(id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT timeout_count FROM users WHERE id = {id}')
        timeout_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET timeout_count = {timeout_count} WHERE id = {id};')
        self.database.commit()
        
    def add_ban_count(self, id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.check_user_exists(id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT ban_count FROM users WHERE id = {id}')
        ban_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET ban_count = {ban_count} WHERE id = {id};')
        self.database.commit()
        
    def add_kick_count(self, id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.check_user_exists(id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT kick_count FROM users WHERE id = {id}')
        kick_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET kick_count = {kick_count} WHERE id = {id};')
        self.database.commit()
        
    def set_user_id(self, id: int, role: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.check_user_exists(id):
            return
        self.database.execute(f'UPDATE users SET role = {role} WHERE id = {id};')
        self.database.commit()
        
    """Delete object from table"""
        
    def delete_role(self, id):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'DELETE FROM temp_roles WHERE id = {id};')
        self.database.commit()
        
    def delete_locked_channel(self, id):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'DELETE FROM locked_channels WHERE id = {id};')
        self.database.commit()
    
    """Get all from table"""    
    
    def get_all_roles(self) -> list:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM temp_roles')
        return cursor.fetchall()
    
    def get_all_channels(self) -> list:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM locked_channels')
        return cursor.fetchall()
        
    def clear_user_punishment_history(self, id):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'UPDATE users SET kick_count = 0, timeout_count = 0, ban_count = 0 WHERE id = {id};')
        self.database.commit()
        
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
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.db.init_tables()
        self.db.init_schema_log()   
        await self.init_users()
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        logging.info("Loaded mod commands.")
        self.role_task.start()
        self.channel_task.start()
        
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
            if not self.db.check_user_exists(member.id):
                self.db.new_user(member.id, "N/A", 0)
            role_ids = [role.id for role in member.roles]
            role = 0
            if self.admin_role_id in role_ids:
                role = 2
            elif self.mod_role_id in role_ids:
                role = 1
            self.db.set_user_id(member.id, role)
            
        self.db.has_init_all_users()
            
    async def on_command_success(self, command: commands.Context):
        """On command function."""
        embed = discord.Embed(
            title="Command Used",
            colour=discord.Colour.green(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=command.author.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'{command.author} (ID: {command.author.id}) ran command {command.message.content} in {command.channel}', value='', inline=False)
        await self.bot.get_channel(self.staff_logs).send(embed=embed)
        
    async def on_command_fail(self, command: commands.Context):
        """On command fail function."""
        embed = discord.Embed(
            title="Command Used",
            colour=discord.Colour.green(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=command.author.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'{command.author} (ID: {command.author.id}) attempted to exeucte {command.message.content} in {command.channel}', value='Failed Reason: No Permission', inline=False)
        await self.bot.get_channel(self.staff_logs).send(embed=embed)
        
    """Tasks"""
    
    @tasks.loop(seconds=60.0)
    async def role_task(self):
        logging.debug("Scanning for roles...")
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
    async def channel_task(self):
        logging.debug("Scanning for channels...")
        channels = self.db.get_all_channels()
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
        logging.info('Waiting...')
        await self.bot.wait_until_ready()
        
    @channel_task.before_loop
    async def before_channel_task(self):
        logging.info('Waiting...')
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
        if self.db.check_user_exists(message.author.id):
            self.db.add_message_count(message.author.id)
            
    """Commands"""
        
    @commands.command(name="info")
    async def info_command(self, ctx: commands.Context, person: str):
        """Retrieves the discord info from a user."""
        if not person:
            return
        await ctx.invoke(self.on_command_success)
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
        
        if not self.db.check_user_exists(member.id):
            self.db.new_user(member.id, "N/A", 0)
        
        db_data = self.db.check_user_exists(member.id)
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
        embed.add_field(name='Invited Link: ', value=f'{user.invite_code}', inline=True)
        embed.add_field(name='Account Creation Date:', value=f'{member.created_at.date()}', inline=True)
        embed.add_field(name='Total Messages:', value=f'{user.message_count}')
        roles = [role.name for role in member.roles if role.name != '@everyone']
        embed.add_field(name='User Roles', value=f'{", ".join(roles)}', inline=True)
        embed.add_field(name='Bans: ', value=f'{user.ban_count}', inline=True)
        embed.add_field(name='Kicks: ', value=f'{user.kick_count}', inline=True)
        embed.add_field(name='Timeouts: ', value=f'{user.timeout_count}', inline=True)
        embed.add_field(name='Has Been Previously Banned: ', value=f'{bool(user.has_been_banned)}', inline=True)
        embed.set_footer(text=f'{ctx.author}')
        await ctx.reply(embed=embed)
            
    @commands.command(name="timeout")
    async def timeout_command(self, ctx: commands.Context, person: str, silent: Optional[str]=None, duration: Optional[str]=None, reason: Optional[str]=None):
        """Times out a user."""
        if silent and silent != "-s":
            reason = duration
            duration = silent
            silent = False
        elif silent == "-s":
            silent = True
            
        if not person:
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
        
        target_role = User(self.db.check_user_exists(member.id)).role
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role > target_role and user_role > 0:
            date = self.get_duration(duration)
            today = dt.datetime.now().astimezone()
            if not date or (date - today).days > 28:
                date = dt.datetime.now().astimezone() + dt.timedelta(days=28)
            await member.edit(timed_out_until=date, reason=reason)
            await ctx.invoke(self.on_command_success)
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
            embed.add_field(name=f'{member.display_name} was successfully timed out by {ctx.author.display_name}', value='', inline=False)
            embed.add_field(name=f'Timed out until: {date}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
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
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            await ctx.invoke(self.on_command_fail)
        
    @commands.command(name="untimeout")
    async def untimeout_command(self, ctx: commands.Context, person: str, silent: Optional[str]=None, reason: Optional[str]=None):
        """Removes timeout from a user."""
        if silent and silent != "-s":
            reason = silent
            silent = False
        elif silent == "-s":
            silent = True
        
        if not person:
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        target_role = User(self.db.check_user_exists(member.id)).role
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        is_timed_out = member.is_timed_out()
        if user_role > target_role and is_timed_out and user_role > 0:
            await member.timeout(None, reason=reason)
            await ctx.invoke(self.on_command_success)
            if silent:
                return
            embed = discord.Embed(
                title="Time Out Removed",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{member.display_name} was untimed out by {ctx.author.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
        else:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to execute untimeout command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            await ctx.invoke(self.on_command_fail)
            
    @commands.command(name="kick")
    async def kick_command(self, ctx: commands.Context, person: str, silent: Optional[str]=None, reason: Optional[str]=None):
        """Kicks a user from guild."""
        if silent and silent != "-s":
            reason = silent
            silent = False
        elif silent == "-s":
            silent = True
        
        if not person:
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        target_role = User(self.db.check_user_exists(member.id)).role
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role > target_role and user_role > 0:
            await member.kick(reason=reason)
            await ctx.invoke(self.on_command_success)
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
            embed.add_field(name=f'{member.display_name} was kicked by {ctx.author.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
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
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            await ctx.invoke(self.on_command_fail)
            
    @commands.command(name="ban")
    async def ban_command(self, ctx: commands.Context, person: str, silent: Optional[str]=None, reason: Optional[str]=None):
        """Bans a user from guild."""
        if silent and silent != "-s":
            reason = silent
            silent = False
        elif silent == "-s":
            silent = True
            
        if not person:
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        target_role = User(self.db.check_user_exists(member.id)).role
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role > target_role and user_role > 0:
            await member.ban(reason=reason)
            await ctx.invoke(self.on_command_success)
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
            embed.add_field(name=f'{member.display_name} was banned by {ctx.author.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
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
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            await ctx.invoke(self.on_command_fail)
            
    @commands.command(name="unban")
    async def unban_command(self, ctx: commands.Context, person: str, silent: Optional[str]=None, reason: Optional[str]=None):
        """Unbans a user from guild."""
        if silent and silent != "-s":
            reason = silent
            silent = False
        elif silent == "-s":
            silent = True
            
        if not person:
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role > 0:
            await member.unban(reason=reason)
            await ctx.invoke(self.on_command_success)
            if silent:
                return
            embed = discord.Embed(
                title="Unbanned User",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{member.display_name} was unbanned by {ctx.author.display_name}', value='', inline=False)
            embed.add_field(name=f'Reason: {reason}', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
        else:
            await ctx.invoke(self.on_command_fail)
            
    @commands.command(name="history")
    async def history_command(self, ctx: commands.Context, person: str, silent: Optional[str]=None, channel: Optional[str]=None):
        """Gets chat history of a user."""
        if silent and silent != "-s":
            channel = silent
            silent = False
        elif silent == "-s":
            silent = True
            
        if not person:
            return
        
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role < 2:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to execute history command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            await ctx.invoke(self.on_command_fail)
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        if not member:
            return
        
        target_channel = None
        channel_name = ""
        
        if not channel:
            channel_name = ctx.channel.name
            target_channel = ctx.channel
        else:
            if "<#" in channel:
                channel = int(channel[2:-1])
            channel_name = ctx.guild.get_channel(channel).name
            target_channel = ctx.guild.get_channel(channel)
            
        if not target_channel:
            return
        
        
        messages = [message async for message in target_channel.history(limit=None, oldest_first=True) if message.author.id == member.id]
        
        if len(messages) < 1:
            return
        
        await ctx.invoke(self.on_command_success)
        
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
        embed.set_footer(text=f'{ctx.author}')
        await ctx.reply(embed=embed)
        
    @commands.command(name="addrole")
    async def addrole_command(self, ctx: commands.Context, person: str, role: str, silent: Optional[str]=None, duration: Optional[str]=None, reason: Optional[str]=None):
        """Adds a role to a user."""
        if silent and silent != "-s":
            reason = duration
            duration = silent
            silent = False
        elif silent == "-s":
            silent = True
        
        if not person:
            return
        
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        
        # Only admins can use this command
        if user_role < 2:
            if silent:
                return
            embed = discord.Embed(
                title="Failed to add role command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            await ctx.invoke(self.on_command_fail)
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        if not member:
            return
        
        if "<@" in role:
            member_role = ctx.guild.get_role(int(role[2:-1]))
        else:
            member_role = ctx.guild.get_role(role)
            
        if not member_role:
            return
        
        if member_role.id == self.admin_role_id:
            return
        
        member.add_roles(member_role, reason=reason)
        expiry_date = self.get_duration(duration)
        
        if expiry_date:
            self.db.new_temp_role(member.id, member_role.id, expiry_date, reason, ctx.author.id)
            
        if silent: 
            return
        
        embed = discord.Embed(
            title="Successfully Updated User's Roles",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'Role Added:', value=f'{member_role.name}', inline=False)
        if not expiry_date:
            embed.add_field(name=f'Duration:', value=f'N/A', inline=False)
        else:
            embed.add_field(name=f'Duration:', value=f'{expiry_date}', inline=False)
        embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
        embed.set_footer(text=f'{ctx.author}')
        await ctx.reply(embed=embed)
            
    
    @commands.command(name="removerole")
    async def removerole_command(self, ctx: commands.Context, person: str, role: str, silent: Optional[str]=None, reason: Optional[str]=None):
        if silent and silent != "-s":
            reason = silent
            silent = False
        elif silent == "-s":
            silent = True
            
        if not person:
            return
        
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role < 2:
            if silent: 
                return
            embed = discord.Embed(
                title="Failed to remove role command.",
                colour=discord.Colour.dark_blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Reason: No permission.', value='', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.reply(embed=embed)
            await ctx.invoke(self.on_command_fail)
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        if not member:
            return
        
        if "<@" in role:
            member_role = ctx.guild.get_role(int(role[2:-1]))
        else:
            member_role = ctx.guild.get_role(role)
            
        if not member_role:
            return
        
        if member_role.id == self.admin_role_id:
            return
        
        member.remove_roles(member_role, reason=reason)
        
        if silent: 
            return
        
        embed = discord.Embed(
            title="Successfully Updated User's Roles",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'Role Removed:', value=f'{member_role.name}', inline=False)
        embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
        embed.set_footer(text=f'{ctx.author}')
        await ctx.reply(embed=embed)
    
    @commands.command(name="clear")
    async def clear_command(self, ctx: commands.Context, person: str, silent: Optional[str]=None):
        if silent == "-s":
            silent = True
        
        if not person:
            return
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        if not member:
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
        embed.set_footer(text=f'{ctx.author}')
        await ctx.reply(embed=embed)
    
    @commands.command(name="purge")
    async def purge_command(self, ctx: commands.Context, multi: str, silent: Optional[str]=None):
        if silent == "-s":
            silent = True
        
        if "<#" in multi:
            channel = int(multi[2:-1])
            target_channel = ctx.guild.get_channel(channel)
            
            if not target_channel:
                return
            deleted = await target_channel.purge(limit=None)
            
            if silent:
                return
            
            embed = discord.Embed(
                title="Successfully Purged Channel",
                colour=discord.Colour.blue(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'Removed items from channel: #{target_channel.name}', value=f'Total - {len(deleted)}', inline=False)
            embed.set_footer(text=f'{ctx.author}')
            await ctx.send(embed=embed)
            
        else:
            if "<@" in multi:
                member = ctx.guild.get_member(int(multi[2:-1]))
            else:
                member = ctx.guild.get_member(multi)
            if not member:
                return
            channels = [discord_channel for discord_channel in ctx.guild.channels if str(discord_channel.type) == 'text']
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
            embed.set_footer(text=f'{ctx.author}')
            await ctx.send(embed=embed)
                
    @commands.command(name="reset")
    async def reset_command(self, ctx: commands.Context, channel: str, silent: Optional[str]=None):
        """ this is incorrect but leave for now """
        if silent == "-s":
            silent = True
            
        if "<#" in channel:
            channel = int(channel[2:-1])
        target_channel = ctx.guild.get_channel(channel)
        
        if not target_channel:
            return
        
        overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        deleted = await target_channel.purge(limit=None)
        
        # delete db record here
        locked_channel = LockedChannel(self.db.check_locked_channel_exists(target_channel.id))
        if locked_channel:
            self.db.delete_locked_channel(locked_channel.id)
            
        if silent:
            return
        
        embed = discord.Embed(
            title="Successfully Reset Channel",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'Reset channel #{target_channel.name}', value=f'', inline=False)
        embed.add_field(name=f'Removed items from channel: #{target_channel.name}', value=f'Total - {len(deleted)}', inline=False)
        embed.set_footer(text=f'{ctx.author}')
        await ctx.send(embed=embed)
            
    
    @commands.command(name="lock")
    async def lock_command(self, ctx: commands.Context, channel: str, silent: Optional[str]=None, duration: Optional[str]=None, reason: Optional[str]=None):
        if silent and silent != "-s":
            reason = duration
            duration = silent
            silent = False
        elif silent == "-s":
            silent = True
        
        if "<#" in channel:
            channel = int(channel[2:-1])
            
        target_channel = ctx.guild.get_channel(channel)
        target_channel = target_channel or ctx.channel
        overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        expiry_date = self.get_duration(duration)
        
        if expiry_date:
            self.db.new_locked_channel(target_channel.id, expiry_date, reason, ctx.author.id)
        
        if silent:
            return
        
        embed = discord.Embed(
            title="Successfully Locked Channel",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(name="Hanabi Bot") 
        embed.add_field(name=f'#{target_channel.name} has been locked.', value=f'')
        embed.set_footer(text=f'{ctx.author}')
        await target_channel.send(embed=embed)
    
    @commands.command(name="unlock")
    async def unlock_command(self, ctx: commands.Context, channel: str, silent: Optional[str]=None):
        if silent == "-s":
            silent = True
        
        if "<#" in channel:
            channel = int(channel[2:-1])
            
        target_channel = ctx.guild.get_channel(channel)
        target_channel = target_channel or ctx.channel
        overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        locked_channel = LockedChannel(self.db.check_locked_channel_exists(target_channel.id))
        if locked_channel:
            self.db.delete_locked_channel(locked_channel.id)
        
        if silent:
            return
        
        embed = discord.Embed(
            title="Successfully Unlocked Channel",
            colour=discord.Colour.blue(),
            timestamp=dt.datetime.now()
        )
        
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(name="Hanabi Bot") 
        embed.add_field(name=f'#{target_channel.name} has been locked.', value=f'')
        embed.set_footer(text=f'{ctx.author}')
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