import sys
import configparser
import os
import pathlib

from setup_and_test import pwdutil #as pwdutil  #local util for database password
import pymysql


class ConfigFileAccessError(Exception):
    pass

def fileexists(CONFIGFILE):
    """
    Checks if the configuration file exists.
    """
    return (os.path.isfile(CONFIGFILE))

def get_config():
    """
    Retrieves configuration settings from the specified INI file.
    """

    CONFIGFILE = pathlib.Path(pathlib.Path.cwd(),"./config/config.ini")

    Config = configparser.ConfigParser()

    parsed_config = {}       # Dictionary of "section" keys.  Each value is a sub-dict of key-vals 

    if fileexists(CONFIGFILE):
        
        Config.read(CONFIGFILE)

        for section in Config.sections():

            section_data = {}
            options = Config.options(section)

            for option in options:
                section_data[option] = Config.get(section,option)
            
            parsed_config[section] = section_data
    else:
        raise ConfigFileAccessError(CONFIGFILE)
    
    return parsed_config


def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via raw_input() and return their answer.
    The "answer" return value is True for'"yes' or False for 'no'.

    """
    
    
    valid = {"yes":True,"ye":True,"y":True, "no":False, "n": False}
    
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"Invalid default answer: {default}")
    
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()

        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
            
def db_connection(host, user, dbname, charset = "utf8mb4"):
    """
    Establishes a connection to a MySQL Database Server
    """
    key = pwdutil.get_key()
    encoded = pwdutil.get_pwd()
    password = pwdutil.decode(key,encoded)

    connection  = pymysql.connect(
        host = host,
        user = user,
        password = password,
        db = dbname,
        charset = charset,
        cursorclass = pymysql.cursors.DictCursor
        )

    return connection


def db_connectionID(cursor):
    """
    Retrieves the current connection ID for the provided database cursor.
    """

    cursor.execute("SELECT connection_id()",(None))
    value = cursor.fetchone()["connection_id()"]
    return (value)