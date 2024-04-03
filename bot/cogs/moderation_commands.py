import discord
from discord.ext import commands, tasks
import datetime as dt
import os
from dotenv import load_dotenv
import logging
import sqlite3

load_dotenv()



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
        
    def init_user_table(self):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY NOT NULL, invite_code TEXT DEFAULT NULL, ban_count INTEGER DEFAULT 0 NOT NULL, kick_count INTEGER DEFAULT 0 NOT NULL, timeout_count INTEGER DEFAULT 0 NOT NULL, has_been_banned INTEGER DEFAULT 0 NOT NULL, role INTEGER DEFAULT 0 NOT NULL, message_count INTEGER DEFAULT 0 NOT NULL );')
        self.database.commit()
        
    def new_user(self, id: int, invite_code: str, role: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if self.check_user_exists(id):
            return
        self.database.execute(f'INSERT INTO users (id, invite_code, role) VALUES (?, ?, ? );', (id, invite_code, role))
        self.database.commit()
    
    def init_user_variables(self, id: int, role: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.check_user_exists(id):
            return
        self.database.execute(f'UPDATE users SET role = {role} WHERE id = {id};')
        
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
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute("SELECT has_init_users FROM schema_log")
        return bool(cursor.fetchone()[0])
        
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
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.db.init_user_table()
        self.db.init_schema_log()
        await self.init_users()
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        logging.info("Loaded mod commands.")
        
    def find_invite_by_code(self, invite_list: list[discord.Invite], code: str) -> discord.Invite:
        for inv in invite_list:
            if inv.code == code:
                return inv
            
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
            
    async def on_command(self, command: commands.Context):
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
        
    @commands.command(name="info")
    async def info_command(self, ctx: commands.Context, person: str):
        """Retrieves the discord info from a user."""
        if not person:
            return
        await ctx.invoke(self.on_command)
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
        
    
async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCommands(bot))
    

if __name__ == "__main__":
    db = Database()
    db.init_user_table()
    db.new_user(124, "invite", 0)
    db.init_user_variables(124, 1)
    db.init_schema_log()
    db.check_has_init_user_table()
    db.add_message_count(124)
    