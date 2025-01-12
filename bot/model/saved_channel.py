import json
import logging

class SavedChannel():
    def __init__(self, args: list) -> None:
        if not args:
            self = None
            return
        self.db_id = int(args[0])
        self.channel_id = int(args[1])
        self.save_name = args[2]
        self.saved_server_id = int(args[3])
        self.channel_name = args[4]
        self.type = args[5]
        self.position = int(args[6])
        self.parent = int(args[7])
        logging.info(f'8th arg: {args[8]}')
        logging.info(f'type: {type(args[8])}')
        new_string = str(args[8]).replace("'", '"').replace('False', '"False"').replace('True', '"True"')
        logging.info(f'8th arg: "{new_string}"')
        permissions_json = json.loads(new_string)
        for key, value in permissions_json.items():
                if value == 'False':
                    permissions_json[key] = False
                elif value == 'True':
                    permissions_json[key] = True
                else:
                    permissions_json[key] = None
        logging.info(f'Permissions: "{permissions_json}"')
        self.permissions = permissions_json
    
    def __str__(self) -> str:
        return f'Database ID: {self.db_id} ' \
               f'Channel ID: {self.channel_id} ' \
               f'Save Name: {self.save_name} ' \
               f'Saved Server ID: {self.saved_server_id} ' \
               f'Channel Name: {self.channel_name} ' \
               f'Type: {self.type} ' \
               f'Position: {self.position} ' \
               f'Parent: {self.parent} ' \
               f'Permissions: {self.permissions}'
               
    
if __name__ == '__main__':
    asdf = json.loads('{"mention_everyone": "False"}')
    for key, value in asdf.items():
        if value == 'False':
            asdf[key] = False
        elif value == 'True':
            asdf[key] = True
        else:
            asdf[key] = None
    print(asdf)