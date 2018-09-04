#!/usr/bin/python3

## \file sql.py
# \brief Modules as well as CLI tools for sqlite database control
#
# This modules contains the library for sqlite database control
# and it is also a stand alone command line tool
# The library has to work with a proper configuration file in order to
# have the sqlite file path
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import utility
import sqlite3
import json
import argparse
from colorama import Fore,Style

## \brief Load the device configuration from the given config file path
#
# If the the config file path is not given, the program will tend to
# use the default path.   The config file is a json file, loadConfig is
# looking for the key 'SQLITE' and get 'Master' value which is the sqlite file path
# If key is not found, a default value will be loaded
# NOTE: This function can be called explictly to load user configurations
#
# \param confPath a string value contain the path to the json file
##
def loadConfig(confPath = 'this_device_conf.json'):
    global sqlite_file
    config = utility.loadConfig(confPath)
    if 'error' not in config:
        if 'Master' in config['SQLITE']: sqlite_file = config['SQLITE']['Master']



## \brief initialize a connection to the sqlite database
#
# __init is Calling internally to initilize a connection object to the sqlite
# database.    If the database path is None, it will use the default path
#
# \param da_path string path to  the sqlite database file
# \param daemon print out the info message if set False, the default is False
# \return calling connectSQLite function and return the connction object
##
def __init(db_path = None, daemon = False):
    if db_path is None:
        return connectSQLite(sqlite_file, daemon)
    return connectSQLite(db_path, daemon)



## \brief execute the sqlite database file to create and retrn the connection object
#
# Connect the SQLite databse with given database path (db_path), and return the connection
# object.    if the db_path is None, using the default path value (sqlite_file)
# NOTE: sqlite_file is can be explictly loaded by loadConfig function or changed using
# setDBPath
#
# \param db_path string value contains the path of the SQLite database
# \param daemon print out the info message if set False, the default is False
# \return conn the connection object from sqlite3 module
##
def connectSQLite(db_path, daemon = False):
    if db_path is None: db_path = sqlite_file
    try:
        if not daemon: utility.info("Connecting to DB: " + db_path)
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error:
        utility.error("Connection to " + db_path + " failed")
        exit(1)



## \brief set the global variable sqlite_file value
#
# Set the default global variable sqlite_file with the given database path value (db_path)
#
# \param db_path a string value contains the path to the SQLite database
# \param daemon print out the info message if set False, the default is False
##
def setDBPath(db_path, daemon = False):
    global sqlite_file
    if db_path:
        if not daemon: utility.info('Setting SQLite database path to [' + db_path + ']')
        sqlite_file = db_path



## \brief Execute the database query and return the result in JSON
#
# Execute the given SQLite query and return the result in JSON format
# If the connection is not provided, load the default database by calling __init()
#
# \param command the SQLite query string to be executed
# \param conn the connection object from sqlite3 module which connecting to a database
# \param daemon print out the info message if set False, the default is False
# \return calling buildJson to return the JSON result
##
def executeSQLite(command, conn = None, daemon = False):
    if not daemon: utility.info("############### " + Fore.YELLOW + "Connecting and Executing SQLite Query" + Style.RESET_ALL+ " ###############")
    if conn is None: conn = __init(None, daemon)
    try:
        c = conn.cursor()
        if not daemon: utility.info("Executing query: " + command)
        result = c.execute(command).fetchall()
        if not daemon:
            for row in result:
                i = 0
                utility.info("======= Entry " + str(i+1) + " =======")
                for name in names:
                    utility.info(name + ': ' + str(row[i]))
                    i += 1

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        utility.error(str(e) + "\n    Query " + command + " executeion failed")
        exit(1)
    if not result:
        return None
    else:
        names = list(map(lambda x:x[0], c.description))
        return buildJson(names, result)



## \brief Build and return the JSON object with given keys and values
#
# Read the SQLite query result from executeSQLite command, read the result
# build the json object based on column name and rows
#
# \param name The name list of each column
# \param results each result is a row in the SQLite query response
# \return the JSON object of the SQLite query result
##
def buildJson(names, results):
    result = []
    for row in results:
        dic = {}
        column = 0
        for name in names:
            dic[name] = row[column]
            column += 1
        result.append(dic)
    return json.loads(json.dumps(result))



## \brief A warper function for executeSQLite, allow to use a different database
#
# A warper function for executeSQLite, mainly for running SELET command in SQLite
# Allow to use a user defined database instead of global default
#
# \param command The command will be execute as SQLite query. Example: SELETE * FROM vendor
# \param db_path The database path for SQLite
# \return JSON result from execute SQLite query command
##
def getSQLite(command, db_path = None, daemon = True):
    return executeSQLite(command, __init(db_path, daemon), daemon)
           


## \brief Execute the UPDATE query to modify a SQLite table
#
# A warper function for Execute UPDATE query in the SQLite database
# Update the table in the give database path with the key and value
# Using the query argument to add extra filter
#
# Example: updataSQLite('vendor', id, 2, id=1) == UPDATE vendor SET id=2 WHERE id=1;
#
# \param table The table in the given SQLite database
# \param key The key in the given SQLite database
# \param value The change value to set for the key
# \param query (Optional) a filter to select which row(s)
# \param db_path (Optional) the SQLite database path
# \param daemon print out the info message if set False, the default is False
##
def updateSQLite(table, key, value, query=None, db_path=None, daemon = False):
    if query is not None:
        command = 'UPDATE ' + table + ' SET ' + key + '=' + str(value) + ' WHERE ' + query
    else:
        command = 'UPDATE ' + table + ' SET ' + key + '=' + str(value)
    executeSQLite(command, __init(db_path, daemon), daemon)



## \brief Execute the INSERT query to add a row in SQLite database
#
# A warper function for execute INSERT query in the SQLite databse
# insert a row into the give table with given query
#
# \param table The table in the given database
# \param query The "key=value" list for set column values
# \param conn (optional) the SQLite connection object
# \param daemon print out the info message if set False, the default is False
# TODO for further usage, modify this function
##
def insertSQLite(table, query, conn = None, daemon = False):
    command = 'INSERT INTO ' + table + ' VALUES (' + query + ')'
    executeSQLite(command, conn, daemon)



## \brief Main function for provide the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./sql.py -h or --help for instructions
##
def main():
    global sqlite_file
    parser = argparse.ArgumentParser(description='SQLite CLI tools')
    parser.add_argument('-e', '--execute', metavar='Command', nargs='+', help='Execute the SQLite query command')
    parser.add_argument('-s', '--sql', metavar='SQLite Path', help='Define to use the given SQLite DB Path')
    if len(sys.argv) < 2: parser.print_help()
    args = parser.parse_args()
    if args.sql: sqlite_file = args.sql
    if args.execute: executeSQLite(' '.join(args.execute))



## \brief Global shared variables
#
# \param sqlite_file the default SQLite database file path
##
########################### Load Config File ############################
sqlite_file = 'default.sqlite'                          # Default Value #
#########################################################################


## \brief Load the default configuration from SAuto Framework
try:
    with open('/var/www/html/sauto/rootpath.conf', 'r') as conf_file:
        path = conf_file.read()
        if path: loadConfig(path + '/this_device_conf.json')
        else: loadConfig()
except Exception as e:
    utility.error(str(e), False)
    exit(1)


## \brief give the entry for main when execute from command line
if __name__ == "__main__":
    main()
