class SavedServer():
    def __init__(self, args: list) -> None:
        self.db_id = int(args[0])
        self.server_id = int(args[1])
        self.save_name = args[2]
        
    
    def __str__(self) -> str:
        return f'ID: {self.db_id}, Server ID: {self.server_id}, Save Name: {self.save_name}'