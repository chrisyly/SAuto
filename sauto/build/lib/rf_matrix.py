#!/usr/bin/python3

## \file rf_matrix.py
# \brief Modules as well as CLI tools for remote RF Matrix control
#
# This modules contains the library for remote controling the RF Matrix
# and it is also a stand alone command line tool
# The library has to work with a proper configuration file in order to
# have the ip and port for the remote devices
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import json
import socket
import argparse
import utility
import sql
import sys
from colorama import Fore
from colorama import Style

## \brief This CONST_PORT is a byte value map for input string
########################## Constant #############################
CONST_PORT={"A":'\x0A', "a":'\x0A', "0A":'\x0A', "0a":'\x0A',   #
        "x0A":'\x0A', "x0a":'\x0A', "B":'\x0B', "b":'\x0B',     #
        "0B":'\x0B', "0b":'\x0B', "x0B":b'\x0B', "x0b":'\x0B',  #
        "1":'\x01', "2":'\x02', "3":'\x03', "4":'\x04',         #
        "5":'\x05', "6":'\x06', "7":'\x07', "8":'\x08',         #
        "9":'\x09', "10":'\x10', "11":'\x11', "12":'\x12',      #
        "13":'\x13', "14":'\x14', "15":'\x15', "16":'\x16',     #
        "17":'\x17', "18":'\x18', "19":'\x19', "20":'\x20',     #
        "21":'\x21', "22":'\x22', "23":'\x23', "24":'\x24',     #
        "25":'\x25', "26":'\x26', "27":'\x27', "28":'\x28',     #
        "29":'\x29', "30":'\x30', "31":'\x31', "32":'\x32'      #
        }                                                       #
#################################################################



## \brief Load the device configuration from the given config file path
#
# If the the config file path is not given, the program will tend to
# use the default path.   The config file is a json file, loadConfig is
# looking for the key 'RF_Matrix' and get TCP IP address as well as the
# Port for the remote RF_Matrix. If key is not found, a default value
# will be loaded
# NOTE: This function can be call explictly to load user configurations
#
# \param confPath a string value contain the path to the json file
##
def loadConfig(confPath = 'this_device_conf.json'):
    global ID, NAME, TCP_IP, TCP_PORT, BUFFER_SIZE, STATUS
    config = utility.loadConfig(confPath)
    if 'error' not in config:
        if 'ID' in config['RF_Matrix']: ID = config['RF_Matrix']['ID']
        if 'NAME' in config['RF_Matrix']: NAME = config['RF_Matrix']['NAME']
        if 'TCP_IP' in config['RF_Matrix']: TCP_IP = config['RF_Matrix']['TCP_IP']
        if 'TCP_PORT' in config['RF_Matrix']: TCP_PORT = config['RF_Matrix']['TCP_PORT']
        if 'BUFFER_SIZE' in config['RF_Matrix']: BUFFER_SIZE = config['RF_Matrix']['BUFFER_SIZE']
        if 'STATUS' in config['RF_Matrix']: STATUS = config['RF_Matrix']['STATUS']



## \brief Load the device configuration from the given SQLite file path
#
# If the SQLite file path is not give, default SQLite data path will be load
# if the data (ip and port) in the database is not set, the program will use
# the default value instead
# NOTE: This function can be called explictly to load configuration
#
# \param rid the id for a perticular RF Matrix device in SQLite database
# \param db_path the path of the SQLite database file
##
def loadSQLite(rid, db_path = None):
    global ID, NAME, TCP_IP, TCP_PORT, BUFFER_SIZE, STATUS
    config = sql.getSQLite('SELECT * FROM rf_matrix WHERE id=' + str(rid), db_path)
    if config:
        if config[0]['id'] is not None: ID = config[0]['id']
        if config[0]['name'] is not None: NAME = config[0]['name']
        if config[0]['ip'] is not None: TCP_IP = config[0]['ip']
        if config[0]['port'] is not None: TCP_PORT = config[0]['port']
        if config[0]['status'] is not None: STATUS = config[0]['status']



## \brief Connect to remote RF Matrix box and execute a command
#
# Remotely connecting to a RF Matrix using a TCP socket connection.
# The IP address and Port was loaded by loadConfig/loadSQLite function
# The remote command takes bytes values to execute different commands.
# A byte value map CONST_PORT is used for building the commands.
# byte start with '\x68' - check which port is current connecting to
# byte start with '\x31' - check if the port is functioning
# byte start with '\x30' - change the connection of the port
#
# \param command a bytes value as a head for certain commandsglobal TCP_IP, TCP_PORT
# \param portA the source port for operating the command
# \param portB the destination port for operating the command
# \param daemon define if the program will print the reuslt or not, default is False
# \return result the return value checked from command executed remotely
# NOTE: When looking at the code...hmmm definately ugly and can be simplify a lot
##
def connectRFMatrix(command, portA, portB, daemon = False):
    if not daemon: utility.info("################### " + Fore.YELLOW + "RF Matrix Control" + Style.RESET_ALL + " ##################")
    MESSAGE = (command + "\x50\x00"+CONST_PORT[portA]+CONST_PORT[portB]+"\x00\x00\x00").encode('utf-8')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if not daemon: utility.info('Send command: [' + str(MESSAGE) + '] to the RF-Matrix at [' + str(TCP_IP) + ':' + str(TCP_PORT) + ']')
        s.connect((TCP_IP, int(TCP_PORT)))
    except OSError:
        utility.error('Connection to ' + str(TCP_IP) + ':' + str(TCP_PORT) + ' Failed!')
        exit(1);
    s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    result = True
    if command == '\x30' and chr(data[7]) == '\x03':
        if not daemon: utility.info("Result: Connect Port A" + portA + " to Port B" + portB + Fore.GREEN + ' Success' + Style.RESET_ALL)
    elif command == '\x31' and chr(data[6]) == '\x06':
        if not daemon: utility.info("Result: Port " + portA + portB + Fore.GREEN + ' functioning' + Style.RESET_ALL)
    elif command == '\x68' and chr(data[7]) == '\x03':
        if not daemon: utility.info ("Result: " + 'Port A' + portB + ' is connecting to Port B' + hex(data[4])[2:4])
    else:
        if not daemon: utility.error('Command: ' + str(MESSAGE) + Fore.RED + ' Fail' + Style.RESET_ALL)
        result = False
    s.close()
    return result



## \brief Main function for provide the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./rf_matrix.py -h or --help for instructions
##
def main():
    parser = argparse.ArgumentParser(description='Tools for controlling RF-Matrix box')
    parser.add_argument('-c', '--connect', nargs=2, metavar=('PortANum', 'PortBNum'), help='Connect port A to port B\n Example: --connect 1 2    Connect Port A01 to Port B02')
    parser.add_argument('-H', '--health', nargs=2, metavar=('Port', 'PortNum'), help='Check port if it is functioning\n Example: --health A 20    Check Port A20 if it is functioning')
    parser.add_argument('-C', '--check', nargs=2, metavar=('Port', 'PortNum'), help='Check what port of the given port is connecting to\n Example: --check A 20    Check Port A20 which Port B is connecting to')
    parser.add_argument('-s', '--sql', metavar='SQLite File Path', help='Load the SQLite database path instead of configuration json file. Using parameter None or null to use default database')
    parser.add_argument('-i', '--id', metavar='RF Matrix ID#', type=int, help='The id number of the RF Matrix device in SQLite database, default is 1')
    args = parser.parse_args()
    rid = 1
    if len(sys.argv) < 2: parser.print_help()
    if args.id: rid = args.id
    if args.sql:
        if args.sql is 'None' or 'none' or 'default' or 'Default' or 'null':
            loadSQLite(rid)
        else:
            loadSQLite(rid, args.sql)
    if args.check: connectRFMatrix('\x68', args.check[0], args.check[1])
    elif args.health: connectRFMatrix('\x31', args.health[0], args.health[1])
    elif args.connect: connectRFMatrix('\x30', args.connect[0], args.connect[1])



## \brief Shared variables
#
# \param TCP_IP the ip address of the remote device
# \param TCP_PORT the port of the remote device
# \param BUFFER_SIZE a default buffer size when read result from remote device
# \function loadConfig() load the default configuration when loading this module
##
###################### Load Config File #########################
ID = 2                                          # Default Value #
NAME = 'RFM2'                                   # Default Value #
TCP_IP = '10.155.220.77'                        # Default Value #
TCP_PORT = 9100                                 # Default Value #
BUFFER_SIZE = 1024                              # Default Value #
STATUS = 0                                      # Default Value #
#################################################################


## \brief Load the default configuration from SAuto framework
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
