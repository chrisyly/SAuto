#!/usr/bin/python3

## \file jfw.py
# \brief Modules as well as CLI tools for remote JFW box control
#
# This modules contains the library for remote controling the JFW box
# and it is also a stand alone command line tool
# The library has to work with a proper configuration file in order to
# have the ip and port for the remote devices
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import json
from telnetlib import Telnet
import argparse
import utility
import sql
import sys
from os import path
from colorama import Fore,Style

## \brief Load the device configuration from the given config file path
#
# If the the config file path is not given, the program will tend to
# use the default path.   The config file is a json file, loadConfig is
# looking for the key 'JFW' and get TCP IP address as well as the
# Port for the remote JFW box. If key is not found, a default value
# will be loaded
# NOTE: This function can be called explictly to load user configurations
#
# \param confPath a string value contain the path to the json file
##
def loadConfig(confPath = 'this_device_conf.json'):
	global ID, NAME, TCP_IP, TCP_PORT, LOCATION, STATUS
	config = utility.loadConfig(confPath)
	if 'error' not in config:
		if 'ID' in config['JFW']: ID = config['JFW']['ID']
		if 'NAME' in config['JFW']: NAME = config['JFW']['NAME']
		if 'TCP_IP' in config['JFW']: TCP_IP = config['JFW']['TCP_IP']
		if 'TCP_PORT' in config['JFW']: TCP_PORT = config['JFW']['TCP_PORT']
		if 'LOCATION' in config['JFW']: LOCATION = config['JFW']['LOCATION']
		if 'STATUS' in config['JFW']: STATUS = config['JFW']['STATUS']


## \brief Load the device configuration from the given SQLite file path
#
# If the SQLite file path is not give, default SQLite data path will be load
# if the data (ip and port) in the database is not set, the program will use
# the default value instead
# NOTE: This function can be called explictly to load configuration
#
# \param jid the id for a perticular JFW device in SQLite database
# \param db_path the path of the SQLite database file
##
def loadSQLite(jid, db_path = None):
	global ID, NAME, TCP_IP, TCP_PORT, LOCATION, STATUS
	config = sql.getSQLite('SELECT * FROM ' + JFW_TABLE_NAME + ' WHERE id=' + str(jid), db_path)
	if config:
		if config[0]['id'] is not None: ID = config[0]['id']
		if config[0]['name'] is not None: NAME = config[0]['name']
		if config[0]['ip'] is not None: TCP_IP = config[0]['ip']
		if config[0]['port'] is not None: TCP_PORT = config[0]['port']
		if config[0]['location'] is not None: LOCATION = config[0]['location']
		if config[0]['status'] is not None: STATUS = config[0]['status']



## \brief Connect to remote JFW box and execute a command
#
# Remotely connecting to a JFW box using a Telnet connection.
# The IP address and Port was loaded by loadConfig/loadSQLite function
#
# \param command either using the CLI with -e option or input as a parameter
# \param delayTime a delay time waiting response from telnet connection, default is 2
# \param daemon define if the program will print the reuslt or not, default is False
# \return result the return value from command executed remotely
##
## NOTE: due to legacy firmware version, set the Atten with command: SAR<port> <value>
def connectJFW(command, delayTime = 2, daemon = False):
	if not daemon: utility.info("###################### " + Fore.YELLOW + 'JFW Control' + Style.RESET_ALL + " #####################")
	MESSAGE = (command + '\r\n').encode('ascii')
	try:
		if not daemon: utility.info('Send command: [' + command + '] to the JFW box at [' + str(TCP_IP) + ':' + str(TCP_PORT) + ']')
		tn = Telnet(TCP_IP, int(TCP_PORT))
		tn.write(MESSAGE)
		utility.sleep(delayTime, daemon = True)
		result = tn.read_very_eager().decode('ascii')
		if not daemon: utility.info('Response:\n' + result)
		tn.close()
	except Exception as e:
		utility.error(str(e) + ' - Connection to ' + str(TCP_IP) + ':' + str(TCP_PORT) + ' Failed!')
		result = str(e) + ' - JFW does not allow multiple login on the same device!'
	return result



## \brief Health Check function for checking Attenuator Port(s) status
#
# Remotely execute a read status command to a JFW box
# By default it is checking all attenuates, by explictly sending command to perform
# a single check on a certain port
#
# \param command default is RAA READ ALL ATTENUATES
# \param daemon default is False will print out the read results
# \return result if anything goes wrong with the port, return False
##
def healthCheck(command = 'RAA', daemon = False):
	if not daemon: utility.info("################ " + Fore.YELLOW + 'JFW Health Check' + Style.RESET_ALL + " ###############")
	data = connectJFW(command, 2, True)
	result = {}
	for line in data.split('\n'):
		keys = utility.regex(line, 'Atten\s*#*(\d+)\s*=*\s*(\d+)..')
		if keys:
			if not daemon: utility.info("Attenuator #" + keys[0] + " - " + keys[1] + "dB")
			result[keys[0]] = keys[1]
	return result



## \brief Main function for provide the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./jfw.py -h or --help for instructions
##
def main():
	global JFW_TABLE_NAME
	parser = argparse.ArgumentParser(description='Tools for controlling JFW box')
	parser.add_argument('--REBOOT', dest='REBOOT', action='store_true', help='Reboot the JFW system, has a 20 seconds delay after reboot')
	parser.add_argument('-d', '--delay', nargs='?', const=2, metavar='Seconds', type=int, help='Set the system delay time waiting for JFW box responding, default 2 seconds')
	parser.add_argument('-e', '--execute', metavar='Command', nargs='+', help='Execute the remote command on JFW box')
	parser.add_argument('-H', '--health', dest='HEALTH', action='store_true', help='Health check all attenuates status')
	parser.add_argument('-s', '--sql', metavar='SQLite_File_Path', help='Load the SQLite database path instead of configuration json file. Using parameter None or null to use default database')
	parser.add_argument('-n', '--name', metavar='SQLite_Table_Name', help='Define the name of the table to be load when loading the SQLite')
	parser.add_argument('-i', '--id', metavar='JFW_ID#', type=int, help='The id number of the JFW device in SQLite database, default is 1')
	args = parser.parse_args()
	delayTime = 2
	jid = 1
	if len(sys.argv) < 2: parser.print_help()
	if args.delay: delayTime = args.delay
	if args.id: jid = args.id
	if args.name: JFW_TABLE_NAME = args.name
	if args.sql:
		if args.sql is 'None' or 'none' or 'default' or 'Default' or 'null':
			loadSQLite(jid)
		else:
			loadSQLite(jid, args.sql)
	if args.REBOOT:
		connectJFW('REBOOT', delayTime)
		utility.sleep(20, daemon = True)
	if args.HEALTH: healthCheck()
	if args.execute: connectJFW(' '.join(args.execute), delayTime)



## \brief Shared variables
#
# \param TCP_IP the ip address of the remote device
# \param TCP_PORT the port of the remote device
# \function loadConfig() load the default configuration when loading this module
##
###################### Load Config File #########################
ID = 1                                          # Default Value #
NAME = 'JFW1'                                   # Default Value #
TCP_IP = '10.155.227.81'                        # Default Value #
TCP_PORT = 3001                                 # Default Value #
LOCATION = ''                                   # Default Value #
STATUS = 0                                      # Default Value #
JFW_TABLE_NAME = "jfw"                          # Default Value #
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
