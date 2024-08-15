import datetime as dt

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
    
    