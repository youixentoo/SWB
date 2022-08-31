# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 14:21:28 2022

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
        
conn.execute('''CREATE TABLE LOBBY
             (ID INTEGER PRIMARY KEY AUTOINCREMENT,
              CODE TEXT NOT NULL,
              HOST TEXT NOT NULL,
              DATE INTEGER NOT NULL,
              UUID TEXT NOT NULL);''')
        
conn.execute('''CREATE TABLE PARTICIPANTS
             (ID INTEGER,
              PLAYER TEXT NOT NULL,
              FOREIGN KEY(ID) REFERENCES LOBBY(ID),
              UNIQUE(ID, PLAYER));''')

"""
import sqlite3
import time
import datetime
import dateparser

def main():
    conn = sqlite3.connect('db/storage.db')
    cur = conn.cursor()
    print("Opened database successfully");
    
    # show_code_command(cur, conn)
    select_command(conn, cur)
    
    cur.close()
    conn.close()
    
def select_command(conn, cur):
    # "select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id and l.code = 'DGEHDS' group by l.id"
    #  group by l.id
    argument = "20h"
    lobby_code = "GTHDMA"
    mult_codes = ('4d7d6085-49af-43ad-8ea7-2ae20e3b6e9a', '43c34947-bf6c-49ec-804f-8e998d09d549')
    
    print(mult_codes)
    print(type(mult_codes))
    
    if(argument[-1] == "m"):
        datestr = f"{argument[:-1]} min ago"
    elif(argument[-1] == "h"):
        datestr = f"{argument[:-1]} hours ago"
    elif(argument[-1] == "d"):
        datestr = f"{argument[:-1]} days ago"
    else:
        datestr = argument
        
    dt = dateparser.parse(datestr, settings={'DATE_ORDER': 'MDY'})
    unix_start = int(dt.timestamp())
    unix_end = int(time.time())
        
    
    # data = cur.execute(f"select l.code, group_concat(p.player, ', '), group_concat(p.playerid, ', ') from lobby l left join participants p on l.id = p.id where l.date > {unix_start} and l.date < {unix_end} group by l.id")
    # data = cur.execute(f"select l.code, group_concat(p.player || '; ' || p.playerid, ', ') from lobby l left join participants p on l.id = p.id where l.code = '{lobby_code}'")
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.uuid in {mult_codes} group by l.id")
    print(list(data))
    
        

def lobby_creation_command(cur, conn):
    match_id = "GTHTDE"
    host = "youixentoo#6937"
    unix_time = 1661431650
    unique_id = "c3ee1b7c-6496-4286-b8db-caaa03ce903c"
    
    player_show = "youixentoo#6937"
    
    cur.execute(f"INSERT INTO LOBBY (CODE, HOST, DATE, UUID) VALUES('{match_id}', '{host}', {unix_time}, '{unique_id}')")
    part_key = cur.lastrowid
    cur.execute(f"INSERT INTO PARTICIPANTS (ID, PLAYER) VALUES({part_key}, '{player_show}')")
    
    conn.commit()
    
def show_code_command(cur, conn, primary_key=1):
    player_show = "other#0001"
    player_id = 48606
    
    with conn:
        command = f"INSERT INTO PARTICIPANTS (ID, PLAYER, PLAYERID) VALUES({primary_key}, '{player_show}', '{player_id}')"
        conn.execute(command)
        # print(conn.lastrowid)
    
    print(command)
    cur.execute(command)

    conn.commit()


if __name__ == "__main__":
    main()