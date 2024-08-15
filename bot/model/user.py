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
                    