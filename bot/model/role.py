import datetime as dt

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