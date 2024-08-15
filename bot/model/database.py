import os
import sqlite3
from typing import Optional

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