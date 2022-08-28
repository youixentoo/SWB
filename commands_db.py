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
    
    # show_code_command(1, cur, conn)
    select_command(conn, cur)
    
    cur.close()
    conn.close()
    
def select_command(conn, cur):
    # "select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id and l.code = 'DGEHDS' group by l.id"
    #  group by l.id
    argument = "28 8 2022"
    
    if(argument[-1] == "m"):
        datestr = f"{argument[:-1]} min ago"
    elif(argument[-1] == "h"):
        datestr = f"{argument[:-1]} hours ago"
    elif(argument[-1] == "d"):
        datestr = f"{argument[:-1]} days ago"
    else:
        datestr = argument
        
    
    
    dt = dateparser.parse(datestr, settings={'DATE_ORDER': 'MDY'})
    print(dt)    
    
    # dt = datetime.datetime(2022, 8, 27) #y, m, d
    dt2 = datetime.datetime(2022, 8, 28) #y, m, d
    unix_time = int(dt.timestamp())
    # unix_time2 = int(dt2.timestamp())
    unix_time2 = int(time.time())
    
    data = cur.execute(f"select l.code, group_concat(p.player, ', ') from lobby l left join participants p on l.id = p.id where l.date > {unix_time} and l.date < {unix_time2} group by l.id")
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
    
def show_code_command(primary_key, cur, conn):
    player_show = "other#0001"
    with conn:
        command = f"INSERT INTO PARTICIPANTS (ID, PLAYER) VALUES({primary_key}, '{player_show}')"
        conn.execute(command)
        print(conn.lastrowid)
    
    print(command)
    # cur.execute(command)

    # conn.commit()


if __name__ == "__main__":
    main()