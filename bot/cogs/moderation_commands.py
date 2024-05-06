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

permanent = ["p", "perm", "permanent"]
year = ["y", "yr", "year"]
month = ["m", "month"]
week = ["w", "week"]
day = ["d", "day"]
hour = ["h", "hr", "hour"]

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

class Database():
    def __init__(self):
        os.makedirs('database', exist_ok=True)
        self.database = sqlite3.connect('database/hanabi_bot.db')
        
    def init_tables(self):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY NOT NULL, invite_code TEXT DEFAULT NULL, ban_count INTEGER DEFAULT 0 NOT NULL, kick_count INTEGER DEFAULT 0 NOT NULL, timeout_count INTEGER DEFAULT 0 NOT NULL, has_been_banned INTEGER DEFAULT 0 NOT NULL, role INTEGER DEFAULT 0 NOT NULL, message_count INTEGER DEFAULT 0 NOT NULL );')
        self.database.execute('CREATE TABLE IF NOT EXISTS temp_roles (id INTEGER PRIMARY KEY AUTOINCREMENT, role_id INTEGER DEFAULT NULL, user_id INTEGER NOT NULL, expiry_time TEXT DEFAULT NULL, reason TEXT DEFAULT NULL, created_by INTEGER DEFAULT NULL);')
        self.database.execute('CREATE TABLE IF NOT EXISTS locked_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id INTEGER DEFAULT NULL, expiry_time TEXT DEFAULT NULL, reason TEXT DEFAULT NULL, created_by INTEGER DEFAULT NULL)')
        self.database.commit()
        
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
        
    def new_lock_channel(self, channel_id: int, expiry_time: str, reason: str, created_by: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'INSERT INTO locked_channels (channel_id, expiry_time, reason, created_by) VALUES (?, ?, ?, ?);', (channel_id, expiry_time, reason, created_by))
        self.database.commit()
    
    def init_user_variables(self, id: int, role: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.check_user_exists(id):
            return
        self.database.execute(f'UPDATE users SET role = {role} WHERE id = {id};')
        self.database.commit()
        
    def init_schema_log(self):
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
        
    def check_user_exists(self, id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM users WHERE id = {id}')
        return cursor.fetchone()
    
    def check_has_init_user_table(self):
        """Only needed to run once when bot is first started and there are already users in the server."""
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute("SELECT has_init_users FROM schema_log")
        return bool(cursor.fetchone()[0])
    
    def has_init_all_users(self):
        if not self.database:
            self.database = sqlite3.conntect('database/hanabi_bot.db')
        self.database.execute(f'UPDATE schema_log SET has_init_users = 1;')
        self.database.commit()
        
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
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.db.init_tables()
        self.db.init_schema_log()
        await self.init_users()
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        logging.info("Loaded mod commands.")
        
    def find_invite_by_code(self, invite_list: list[discord.Invite], code: str) -> discord.Invite:
        for inv in invite_list:
            if inv.code == code:
                return inv
    
    def get_duration(self, duration):
        if duration in year:
            return dt.datetime.now().astimezone() + dt.timedelta(days=365)
        elif duration in month:
            return dt.datetime.now().astimezone() + dt.timedelta(days=30)
        elif duration in week:
            return dt.datetime.now().astimezone() + dt.timedelta(days=7)
        elif duration in day:
            return dt.datetime.now().astimezone() + dt.timedelta(days=1)
        elif duration in hour:
            return dt.datetime.now().astimezone() + dt.timedelta(hours=1)
        return dt.datetime(2100, 1,1).astimezone()
            
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
            self.db.init_user_variables(member.id, role)
            
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
            
    @commands.command(name="timeout")
    async def timeout_command(self, ctx: commands.Context, person: str, duration: Optional[str]=None, reason: Optional[str]=None):
        """Times out a user."""
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
            if (date - today).days > 27:
                date = dt.datetime.now().astimezone() + dt.timedelta(days=28)
            await member.edit(timed_out_until=date, reason=reason)
            await ctx.invoke(self.on_command_success)
            self.db.add_timeout_count(member.id)
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
            await ctx.invoke(self.on_command_fail)
        
    @commands.command(name="untimeout")
    async def untimeout_command(self, ctx: commands.Context, person: str, reason: Optional[str]=None):
        """Removes timeout from a user."""
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
            await ctx.invoke(self.on_command_fail)
            
    @commands.command(name="kick")
    async def kick_command(self, ctx: commands.Context, person: str, reason: Optional[str]=None):
        """Kicks a user from guild."""
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
            await ctx.invoke(self.on_command_fail)
            
    @commands.command(name="ban")
    async def ban_command(self, ctx: commands.Context, person: str, reason: Optional[str]=None):
        """Bans a user from guild."""
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
            await ctx.invoke(self.on_command_fail)
            
    @commands.command(name="unban")
    async def unban_command(self, ctx: commands.Context, person: str, reason: Optional[str]=None):
        """Unbans a user from guild."""
        if not person:
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        target_role = User(self.db.check_user_exists(member.id)).role
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role > target_role and user_role > 0:
            await member.unban(reason=reason)
            await ctx.invoke(self.on_command_success)
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
    async def history_command(self, ctx: commands.Context, person: str, channel: Optional[str]):
        """Gets chat history of a user."""
        if not person:
            return
        
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role < 2:
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
        embed.add_field(name=f'{member.display_name} Chat History:', value=f'{channel_name}', inline=False)
        embed.add_field(name=f'Pastebin Link:', value=f'{last_paste}', inline=False)
        embed.set_footer(text=f'{ctx.author}')
        await ctx.reply(embed=embed)
        
    @commands.command(name="addrole")
    async def addrole_command(self, ctx: commands.Context, person: str, role: str, duration: Optional[str]=None, reason: Optional[str]=None):
        if not person:
            return
        
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role < 2:
            await ctx.invoke(self.on_command_fail)
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        if not member:
            return
        
        if "<@" in role:
            role = ctx.guild.get_role(int(role[2:-1]))
        else:
            role = ctx.guild.get_role(role)
            
        date = self.get_duration(duration)
        
            
            
    
    @commands.command(name="removerole")
    async def removerole_command(self, ctx: commands.Context, person: str, role: str, duration: Optional[str]=None, reason: Optional[str]=None):
        if not person:
            return
        
        user_role = User(self.db.check_user_exists(ctx.author.id)).role
        if user_role < 2:
            await ctx.invoke(self.on_command_fail)
            return
        
        if "<@" in person:
            member = ctx.guild.get_member(int(person[2:-1]))
        else:
            member = ctx.guild.get_member(person)
            
        if not member:
            return
    
    
    
    
async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCommands(bot))
    
    
def test_db():
    db = Database()
    db.init_tables()
    db.new_user(124, "invite", 0)
    db.init_user_variables(124, 1)
    db.init_schema_log()
    print(db.check_has_init_user_table())
    db.add_message_count(124)
    db.has_init_all_users()
    print(db.check_has_init_user_table())
    db.new_temp_role(124, -1, str(dt.datetime.now().astimezone()), "balls", -1)
    
    
def test_pastebin_api():
    paste = Pastebin()
    paste.create_new_paste("new paste1", "new content very cool1")
    print(paste.get_last_paste_url())
    

if __name__ == "__main__":
    test_db()