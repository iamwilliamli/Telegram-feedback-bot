import os
from datetime import datetime, date
from functools import wraps
from config import USER_JSON, ADMIN_LIST
import json

def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func
    
    return decorator

def load_admin():
    admin_dir = ADMIN_LIST
    with open(admin_dir) as f:
        content = f.readlines()
    admin_list = [x.strip() for x in content] 
    return admin_list

def getusername(update, context, reply=False):
    user = update.message.from_user
    if reply == False:
        username = user['username']
        if username == None:
            if user['last_name'] == None:
                username = user['first_name']
            else:
                username = user['first_name']+' '+ user['last_name']
        else:
            username = "@"+username
    else:
        username = user['first_name']
    return username

def write_json(data, filename=USER_JSON): 
    with open(filename,'w') as f: 
        json.dump(data, f, indent=4) 

def userinfo2json(update, context):
    username = str(getusername(update, context, reply=True))
    chat_id = int(update.effective_message.chat_id)
    f = open(USER_JSON)
    data = json.load(f)
    if username not in data.keys():
        data[username] = chat_id
        write_json(data)
    f.close()
def get_chat_id(username):
    f = open(USER_JSON)
    data = json.load(f)
    chat_id = int(data[username])
    return chat_id