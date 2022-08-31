# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 13:38:00 2022

@author: youixentoo

What to store in database:
    - 'Primary key'
    - Lobby code (TGHTYF) - str
    - Host (youixentoo#6937) - str
    - Date created match - int --> unix time, using unixepoch() method
    - UUID - str
    - List of players - 1-to-many # https://www.reddit.com/r/learnpython/comments/93cief/how_to_store_a_list_in_one_sqlite3_column/
        -- Point to primary key
    
    Table 1: Lobby
        Table 2: Participants
        
PRAGMA foreign_keys = ON;

"""


import sqlite3

conn = sqlite3.connect('db/storage.db')
cur = conn.cursor()
print("Opened database successfully");

cur.execute("PRAGMA foreign_keys = ON")

cur.execute('''CREATE TABLE LOBBY
              (ID INTEGER PRIMARY KEY AUTOINCREMENT,
              CODE TEXT NOT NULL,
              HOST TEXT NOT NULL,
              DATE INTEGER NOT NULL,
              UUID TEXT NOT NULL);''')
        
cur.execute('''CREATE TABLE PARTICIPANTS
             (ID INTEGER,
              PLAYER TEXT NOT NULL,
              PLAYERID TEXT NOT NULL,
              FOREIGN KEY(ID) REFERENCES LOBBY(ID),
              UNIQUE(ID, PLAYERID));''')
         
conn.commit()
         
print("Table created successfully");

conn.close()