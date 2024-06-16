import os
import sys

import warnings
warnings.filterwarnings("ignore")

sys.path.append(os.getcwd())
import utils

conf = utils.get_config()

DBHOST = conf["MySQL"]["server"]
DBUSER = conf["MySQL"]["dbuser"]
DBNAME = conf["MySQL"]["dbname"]
DBCHARSET = conf["MySQL"]["dbcharset"]

def try_drop(cursor, table_name):
    SQL_DROP = f"DROP TABLE IF EXISTS {table_name}"
    print(SQL_DROP)
    cursor.execute(SQL_DROP)

print(f"Configuring Tables for database configuration: \n \tServer: {DBHOST} \n \tDB-User: {DBUSER} \n \tDB-Name: {DBNAME}")

response = utils.query_yes_no("Continue?")

if response:
    ## Tab Config and Make Connection to Database ##

    CHAR_TYPE_SHORT = "VARCHAR(16) COLLATE utf8_general_ci"
    CHAR_TYPE_MEDIUM = "VARCHAR(64) COLLATE utf8_general_ci"
    CHAR_TYPE_LONG = "VARCHAR(768) COLLATE utf8_general_ci"

    print("Connecting to database...",end=" ")
    connection = utils.db_connection(DBHOST, DBUSER, DBNAME, DBCHARSET)
    cursor = connection.cursor()
    print("connected.")

    #### Table Create Sections ####
    
    print("Creating words table:")
    try:
        try_drop(cursor, "words")
        SQL_CREATE = f"CREATE TABLE words (hashid {CHAR_TYPE_SHORT} UNIQUE, word {CHAR_TYPE_MEDIUM} UNIQUE)"
        print(SQL_CREATE)
        cursor.execute(SQL_CREATE)
    except Exception as e:
        print(f"\n**ERROR ** {e}")
    

    print("Creating sentences table:")

    try:
        try_drop(cursor, "sentences")
        SQL_CREATE = f"CREATE TABLE sentences (hashid {CHAR_TYPE_SHORT} UNIQUE, sentence {CHAR_TYPE_LONG}, used INT DEFAULT 0 NOT NULL)"
        print(SQL_CREATE)
        cursor.execute(SQL_CREATE)
    except Exception as e:
        print(f"\n**ERROR ** {e}")
    print("Creating associations table:")

    try:
        try_drop(cursor, "associations")
        SQL_CREATE = f"CREATE TABLE associations (word_id {CHAR_TYPE_SHORT} NOT NULL, sentence_id {CHAR_TYPE_SHORT} NOT NULL, weight REAL NOT NULL)"
        print(SQL_CREATE)
        cursor.execute(SQL_CREATE)
    except Exception as e:
        print(f"\n**ERROR ** {e}")

    print("Creating results table:")
    try:
        try_drop(cursor, "results")
        SQL_CREATE = f"CREATE TABLE results (connection_id INTEGER, sentence_id {CHAR_TYPE_SHORT}, sentence {CHAR_TYPE_LONG}, weight REAL)"
        print(SQL_CREATE)
        cursor.execute(SQL_CREATE)
    except Exception as e:
        print(f"\n**ERROR ** {e}")
    print("\ndone.")
else:
    exit(0)

    