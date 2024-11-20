class User():
    def __init__(self, args):
        if len(args) != 9:
            print('Invalid number of arguments passed to User constructor')
            return
        self.db_id = args[0]
        self.user_id = args[1]
        self.invite_code = args[2]
        self.ban_count = args[3]
        self.kick_count = args[4]
        self.timeout_count = args[5]
        self.has_been_banned = args[6]
        self.role = args[7]
        self.message_count = args[8]
    
    def __str__(self) -> str:
        return f'DB ID: {self.db_id}, User ID: {self.user_id}, Invite Code: {self.invite_code}, Ban Count: {self.ban_count}, Kick Count: {self.kick_count}, Timeout Count: {self.timeout_count}, Has Been Banned Before: {self.has_been_banned}, ' + \
                    f'Role: {self.role}, Message Count: {self.message_count}'
                    