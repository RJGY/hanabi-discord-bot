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
        self.database.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER DEFAULT NULL, invite_code TEXT DEFAULT NULL, ban_count INTEGER DEFAULT 0 NOT NULL, kick_count INTEGER DEFAULT 0 NOT NULL, timeout_count INTEGER DEFAULT 0 NOT NULL, has_been_banned INTEGER DEFAULT 0 NOT NULL, role INTEGER DEFAULT 0 NOT NULL, message_count INTEGER DEFAULT 0 NOT NULL );')
        self.database.execute('CREATE TABLE IF NOT EXISTS temp_roles (id INTEGER PRIMARY KEY AUTOINCREMENT, role_id INTEGER DEFAULT NULL, user_id INTEGER NOT NULL, expiry_time TEXT DEFAULT NULL, reason TEXT DEFAULT NULL, created_by INTEGER DEFAULT NULL);')
        self.database.execute('CREATE TABLE IF NOT EXISTS locked_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id INTEGER DEFAULT NULL, expiry_time TEXT DEFAULT NULL, reason TEXT DEFAULT NULL, created_by INTEGER DEFAULT NULL)')
        self.database.execute('CREATE TABLE IF NOT EXISTS saved_servers (id INTEGER PRIMARY KEY AUTOINCREMENT, server_id INTEGER DEFAULT NULL, save_name TEXT DEFAULT NULL)')
        self.database.execute('CREATE TABLE IF NOT EXISTS saved_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id INTEGER DEFAULT NULL, save_name TEXT DEFAULT NULL, saved_server_id INTEGER DEFAULT NULL, channel_name TEXT DEFAULT NULL, type INTEGER DEFAULT NULL, position INTEGER DEFAULT NULL, parent INTEGER DEFAULT NULL, permissions TEXT DEFAULT NULL)')
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
        
        self.database.execute('CREATE TABLE IF NOT EXISTS schema_log (has_init_users INTEGER DEFAULT 0, in_maintenance_mode INTEGER DEFAULT 0);')
        cursor = self.database.cursor()
        cursor.execute("SELECT COUNT(*) FROM schema_log")
        row_count = cursor.fetchone()[0]

        # If the table is empty, insert default values
        if row_count == 0:
            cursor.execute("INSERT INTO schema_log DEFAULT VALUES")
        self.database.commit()
        
    """Create object on table"""
        
    def new_user(self, user_id: int, invite_code: str, role: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if self.get_user(user_id):
            return
        self.database.execute(f'INSERT INTO users (user_id, invite_code, role) VALUES (?, ?, ? );', (user_id, invite_code, role))
        self.database.commit()
        return self.get_user(user_id)
        
    def new_temp_role(self, user_id: int, role_id: int, expiry_time: str, reason: str, created_by: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'INSERT INTO temp_roles (role_id, user_id, expiry_time, reason, created_by) VALUES (?, ?, ?, ?, ?);', (role_id, user_id, expiry_time, reason, created_by))
        self.database.commit()
        return self.get_role(role_id, user_id)
        
    def new_locked_channel(self, channel_id: int, expiry_time: str, reason: str, created_by: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'INSERT INTO locked_channels (channel_id, expiry_time, reason, created_by) VALUES (?, ?, ?, ?);', (channel_id, expiry_time, reason, created_by))
        self.database.commit()
        return self.get_locked_channel(channel_id)
        
    def new_saved_server(self, server_id: int, save_name: str):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'INSERT INTO saved_servers (server_id, save_name) VALUES (?, ?);', (server_id, save_name))
        self.database.commit()
        return self.get_saved_server(server_id, save_name)
        
    def new_saved_channel(self, channel_id: int, save_name: str, saved_server_id: int, channel_name: str, type: int, position: int, parent: int, permissions: str):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'INSERT INTO saved_channels (channel_id, save_name, saved_server_id, channel_name, type, position, parent, permissions) VALUES (?, ?, ?, ?, ?, ?, ?, ?);', (channel_id, save_name, saved_server_id, channel_name, type, position, parent, permissions))
        self.database.commit()
        return self.get_saved_channel(channel_id, save_name)
        
    """Check object exists"""
        
    def get_user(self, user_id: int) -> Optional[list]:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM users WHERE user_id = {user_id}')
        return cursor.fetchone()
    
    def get_locked_channel(self, channel_id: int) -> Optional[list]:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM locked_channels WHERE channel_id = {channel_id}')
        return cursor.fetchone()
    
    def get_role(self, role_id: int, user_id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM temp_roles WHERE role_id = {role_id} and user_id = {user_id}')
        return cursor.fetchone()
    
    def get_saved_server(self, server_id: int, save_name: str) -> Optional[list]:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM saved_servers WHERE server_id = {server_id} and save_name = "{save_name}"')
        return cursor.fetchone()
    
    def get_saved_channel(self, channel_id: int, save_name: str) -> Optional[list]:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM saved_channels WHERE channel_id = {channel_id} and save_name = "{save_name}"')
        return cursor.fetchone()
    
    def check_has_init_user_table(self) -> bool:
        """Only needed to run once when bot is first started and there are already users in the server."""
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute("SELECT has_init_users FROM schema_log")
        return bool(cursor.fetchone()[0])
    
    def check_maintenance_mode(self) -> bool:
        if not self.database:
            self.database = sqlite3.connect('dataase/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute("SELECT in_maintenance_mode FROM schema_log")
        return bool(cursor.fetchone()[0])
    
    """Update objects"""
        
    def add_message_count(self, user_id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.get_user(user_id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT message_count FROM users WHERE user_id = {user_id}')
        message_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET message_count = {message_count} WHERE user_id = {user_id};')
        self.database.commit()
    
    def add_timeout_count(self, user_id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.get_user(user_id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT timeout_count FROM users WHERE user_id = {user_id};')
        timeout_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET timeout_count = {timeout_count} WHERE user_id = {user_id};')
        self.database.commit()
        
    def add_ban_count(self, user_id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.get_user(user_id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT ban_count FROM users WHERE user_id = {user_id}')
        ban_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET ban_count = {ban_count} WHERE user_id = {user_id};')
        self.database.commit()
        
    def add_kick_count(self, user_id: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.get_user(user_id):
            return
        cursor = self.database.cursor()
        cursor.execute(f'SELECT kick_count FROM users WHERE user_id = {user_id}')
        kick_count = int(cursor.fetchone()[0]) + 1
        self.database.execute(f'UPDATE users SET kick_count = {kick_count} WHERE user_id = {user_id};')
        self.database.commit()
        
    def set_user_id(self, user_id: int, role: int):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        if not self.get_user(user_id):
            return
        self.database.execute(f'UPDATE users SET role = {role} WHERE user_id = {user_id};')
        self.database.commit()
        
    def clear_user_punishment_history(self, user_id):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'UPDATE users SET kick_count = 0, timeout_count = 0, ban_count = 0 WHERE user_id = {user_id};')
        self.database.commit()
        
    def has_init_all_users(self):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'UPDATE schema_log SET has_init_users = 1;')
        self.database.commit()
        
    def set_maintenance_mode(self, mode: bool):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'UPDATE schema_log SET in_maintenance_mode = {int(mode)};')
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
        
    def delete_saved_server(self, id):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'DELETE FROM saved_servers WHERE id = {id};')
        self.database.commit()
        
    def delete_saved_channel(self, id):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'DELETE FROM saved_channels WHERE id = {id};')
        self.database.commit()
        
    def delete_all_locked_channels(self):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'DELETE FROM locked_channels;')
        self.database.commit()
        
    def delete_all_saved_channels_with_name(self, name):
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        self.database.execute(f'DELETE FROM saved_channels WHERE save_name = "{name}";')
        self.database.execute(f'DELETE FROM saved_servers WHERE save_name = "{name}";')
        self.database.commit()
    
    """Get all from table"""    
    
    def get_all_roles(self) -> list:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM temp_roles')
        return cursor.fetchall()
    
    def get_all_locked_channels(self) -> list:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM locked_channels')
        return cursor.fetchall()
    
    def get_all_servers(self) -> list:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM saved_servers')
        return cursor.fetchall()
    
    def get_all_channels(self) -> list:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM saved_channels')
        return cursor.fetchall()
    
    def get_all_channels_from_server_and_name(self, saved_server_id: int, save_name: str) -> list:
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM saved_channels WHERE saved_server_id = {saved_server_id} and save_name = "{save_name}"')
        return cursor.fetchall()
    
    def get_channels_from_id(self, channel_id: int) -> list:
        """Returns all saved channels with a given channel_id."""
        if not self.database:
            self.database = sqlite3.connect('database/hanabi_bot.db')
        cursor = self.database.cursor()
        cursor.execute(f'SELECT * FROM saved_channels WHERE channel_id = {channel_id}')
        return cursor.fetchall()
    