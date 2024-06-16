import sys
import os

sys.path.append(os.getcwd())

import utils

conf = utils.get_config()
DBHOST = conf["MySQL"]["server"]
DBUSER = conf["MySQL"]["dbuser"]
DBNAME = conf["MySQL"]["dbname"]
DBCHARSET = conf["MySQL"]["dbcharset"]

if __name__ == "__main__":
    
    connection = utils.db_connection(DBHOST,DBUSER, DBNAME, DBCHARSET)

    tests = {"create_test_tab": ("CREATE TABLE bot_test_tab (col1 VARCHAR(10), col2 INTEGER)", (None,)),
             "insert_test_tab": ("INSERT INTO bot_test_tab VALUES (%s, %s)",("a",1)),
             "select_test_tab": ("SELECT col1 FROM bot_test_tab WHERE col2 = (%s)",(1,)),
             "update_test_tab": ("UPDATE bot_test_tab SET col2 = (%s) WHERE col1 = (%s)",(2,"a")),
             "drop_test_tab": ("DROP TABLE IF EXISTS bot_test_tab", (None,))
             }
    test_squence = ("drop_test_tab","create_test_tab","insert_test_tab","select_test_tab",
                    "update_test_tab","select_test_tab","drop_test_tab")

    for key in test_squence:
        print("execute", key, "Args:",tests[key][1],end=" ")
        SQL_QUERY = tests[key][0]
        ARGS = tests[key][1]
        cursor = connection.cursor()
        try:
            ret = cursor.execute(SQL_QUERY, ARGS)
            print("Response:",ret)
        except Exception as e:
            print(f"Error in test: {e}")
print("Run successful")