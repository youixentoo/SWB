# -*- coding: utf-8 -*-
from dotenv import load_dotenv
from os import getenv
from mysql.connector import connect

load_dotenv()
_connection = None

def get_db_connection():
    global _connection
    if not _connection:
        db_config={"user":getenv("DB_user"), 
            "password":getenv("DB_pass"),
            "host":'sql.ferox.host',
            "database":'s30605_lobby_data'}
        _connection = connect(**db_config)
    elif not _connection.is_connected():
        _connection.reconnect()
    return _connection