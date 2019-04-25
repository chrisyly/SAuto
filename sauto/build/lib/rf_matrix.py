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
import pexpect
from colorama import Fore
from colorama import Style

############################### Constant ################################
## \brief This CONST_PORT is a byte value map for input string			#
CONST_PORT={"A":'\x0A', "a":'\x0A', "0A":'\x0A', "0a":'\x0A',			#
		"x0A":'\x0A', "x0a":'\x0A', "B":'\x0B', "b":'\x0B',				#
		"0B":'\x0B', "0b":'\x0B', "x0B":'\x0B', "x0b":'\x0B',			#
		"1":'\x01', "2":'\x02', "3":'\x03', "4":'\x04',					#
		"5":'\x05', "6":'\x06', "7":'\x07', "8":'\x08',					#
		"9":'\x09', "10":'\x10', "11":'\x11', "12":'\x12',				#
		"13":'\x13', "14":'\x14', "15":'\x15', "16":'\x16',				#
		"17":'\x17', "18":'\x18', "19":'\x19', "20":'\x20',				#
		"21":'\x21', "22":'\x22', "23":'\x23', "24":'\x24',				#
		"25":'\x25', "26":'\x26', "27":'\x27', "28":'\x28',				#
		"29":'\x29', "30":'\x30', "31":'\x31', "32":'\x32'				#
		}																#
																		#
## \brief string integer to HEX string table							#
HEX_STRING_TABLE={"0":"0", "1":"1", "2":"2", "3":"3", "4":"4",			#
		"5":"5", "6":"6", "7":"7", "8":"8", "9":"9", "10":"A",			#
		"11":"B", "12":"C", "13":"D", "14":"E", "15":"F"				#
		}																#
																		#
## \brief Attenuation string to byte value table						#
ATTEN_TABLE={															#
		"0":"\x00", "1":"\x01", "2":"\x02", "3":"\x03", "4":"\x04",		#
		"5":"\x05", "6":"\x06", "7":"\x07", "8":"\x08", "9":"\x09",		#
		"10":"\x0A", "11":"\x0B", "12":"\x0C", "13":"\x0D", "14":"\x0E",#
		"15":"\x0F", "16":"\x10", "17":"\x11", "18":"\x12", "19":"\x13",#
		"20":"\x14", "21":"\x15", "22":"\x16", "23":"\x17", "24":"\x18",#
		"25":"\x19", "26":"\x1A", "27":"\x1B", "28":"\x1C", "29":"\x1D",#
		"30":"\x1E", "31":"\x1F", "32":"\x20", "33":"\x21", "34":"\x22",#
		"35":"\x23", "36":"\x24", "37":"\x25", "38":"\x26", "39":"\x27",#
		"40":"\x28", "41":"\x29", "42":"\x2A", "43":"\x2B", "44":"\x2C",#
		"45":"\x2D", "46":"\x2E", "47":"\x2F", "48":"\x30", "49":"\x31",#
		"50":"\x32", "51":"\x33", "52":"\x34", "53":"\x35", "54":"\x36",#
		"55":"\x37", "56":"\x38", "57":"\x39", "58":"\x3A", "59":"\x3B",#
		"60":"\x3C", "61":"\x3D", "62":"\x3E", "63":"\x3F"				#
		}																#
																		#
## \brief QRB address string to byte value table						#
QRB_ADDRESS_TABLE={"00":'\x00',"01":'\x01',"02":'\x02',"03":'\x03',		#
		"04":'\x04',"05":'\x05',"06":'\x06',"07":'\x07',"08":'\x08',	#
		"09":'\x09',"0A":'\x0A',"0B":'\x0B',"0C":'\x0C',"0D":'\x0D',	#
		"0E":'\x0E',"0F":'\x0F',"10":'\x10',"11":'\x11',"12":'\x12',	#
		"13":'\x13',"14":'\x14',"15":'\x15',"16":'\x16',"17":'\x17',	#
		"18":'\x18',"19":'\x19',"1A":'\x1A',"1B":'\x1B',"1C":'\x1C',	#
		"1D":'\x1D',"1E":'\x1E',"1F":'\x1F',"20":'\x20',"21":'\x21',	#
		"22":'\x22',"23":'\x23',"24":'\x24',"25":'\x25',"26":'\x26',	#
		"27":'\x27',"28":'\x28',"29":'\x29',"2A":'\x2A',"2B":'\x2B',	#
		"2C":'\x2C',"2D":'\x2D',"2E":'\x2E',"2F":'\x2F',"30":'\x30',	#
		"31":'\x31',"32":'\x32',"33":'\x33',"34":'\x34',"35":'\x35',	#
		"36":'\x36',"37":'\x37',"38":'\x38',"39":'\x39',"3A":'\x3A',	#
		"3B":'\x3B',"3C":'\x3C',"3D":'\x3D',"3E":'\x3E',"3F":'\x3F',	#
		"40":'\x40',"41":'\x41',"42":'\x42',"43":'\x43',"44":'\x44',	#
		"45":'\x45',"46":'\x46',"47":'\x47',"48":'\x48',"49":'\x49',	#
		"4A":'\x4A',"4B":'\x4B',"4C":'\x4C',"4D":'\x4D',"4E":'\x4E',	#
		"4F":'\x4F',"50":'\x50',"51":'\x51',"52":'\x52',"53":'\x53',	#
		"54":'\x54',"55":'\x55',"56":'\x56',"57":'\x57',"58":'\x58',	#
		"59":'\x59',"5A":'\x5A',"5B":'\x5B',"5C":'\x5C',"5D":'\x5D',	#
		"5E":'\x5E',"5F":'\x5F',"60":'\x60',"61":'\x61',"62":'\x62',	#
		"63":'\x63',"64":'\x64',"65":'\x65',"66":'\x66',"67":'\x67',	#
		"68":'\x68',"69":'\x69',"6A":'\x6A',"6B":'\x6B',"6C":'\x6C',	#
		"6D":'\x6D',"6E":'\x6E',"6F":'\x6F',"70":'\x70',"71":'\x71',	#
		"72":'\x72',"73":'\x73',"74":'\x74',"75":'\x75',"76":'\x76',	#
		"77":'\x77',"78":'\x78',"79":'\x79',"7A":'\x7A',"7B":'\x7B',	#
		"7C":'\x7C',"7D":'\x7D',"7E":'\x7E',"7F":'\x7F',"80":'\x80',	#
		"81":'\x81',"82":'\x82',"83":'\x83',"84":'\x84',"85":'\x85',	#
		"86":'\x86',"87":'\x87',"88":'\x88',"89":'\x89',"8A":'\x8A',	#
		"8B":'\x8B',"8C":'\x8C',"8D":'\x8D',"8E":'\x8E',"8F":'\x8F',	#
		"90":'\x90',"91":'\x91',"92":'\x92',"93":'\x93',"94":'\x94',	#
		"95":'\x95',"96":'\x96',"97":'\x97',"98":'\x98',"99":'\x99',	#
		"9A":'\x9A',"9B":'\x9B',"9C":'\x9C',"9D":'\x9D',"9E":'\x9E',	#
		"9F":'\x9F',"A0":'\xA0',"A1":'\xA1',"A2":'\xA2',"A3":'\xA3',	#
		"A4":'\xA4',"A5":'\xA5',"A6":'\xA6',"A7":'\xA7',"A8":'\xA8',	#
		"A9":'\xA9',"AA":'\xAA',"AB":'\xAB',"AC":'\xAC',"AD":'\xAD',	#
		"AE":'\xAE',"AF":'\xAF',"B0":'\xB0',"B1":'\xB1',"B2":'\xB2',	#
		"B3":'\xB3',"B4":'\xB4',"B5":'\xB5',"B6":'\xB6',"B7":'\xB7',	#
		"B8":'\xB8',"B9":'\xB9',"BA":'\xBA',"BB":'\xBB',"BC":'\xBC',	#
		"BD":'\xBD',"BE":'\xBE',"BF":'\xBF',"C0":'\xC0',"C1":'\xC1',	#
		"C2":'\xC2',"C3":'\xC3',"C4":'\xC4',"C5":'\xC5',"C6":'\xC6',	#
		"C7":'\xC7',"C8":'\xC8',"C9":'\xC9',"CA":'\xCA',"CB":'\xCB',	#
		"CC":'\xCC',"CD":'\xCD',"CE":'\xCE',"CF":'\xCF',"D0":'\xD0',	#
		"D1":'\xD1',"D2":'\xD2',"D3":'\xD3',"D4":'\xD4',"D5":'\xD5',	#
		"D6":'\xD6',"D7":'\xD7',"D8":'\xD8',"D9":'\xD9',"DA":'\xDA',	#
		"DB":'\xDB',"DC":'\xDC',"DD":'\xDD',"DE":'\xDE',"DF":'\xDF',	#
		"E0":'\xE0',"E1":'\xE1',"E2":'\xE2',"E3":'\xE3',"E4":'\xE4',	#
		"E5":'\xE5',"E6":'\xE6',"E7":'\xE7',"E8":'\xE8',"E9":'\xE9',	#
		"EA":'\xEA',"EB":'\xEB',"EC":'\xEC',"ED":'\xED',"EE":'\xEE',	#
		"EF":'\xEF',"F0":'\xF0',"F1":'\xF1',"F2":'\xF2',"F3":'\xF3',	#
		"F4":'\xF4',"F5":'\xF5',"F6":'\xF6',"F7":'\xF7',"F8":'\xF8',	#
		"F9":'\xF9',"FA":'\xFA',"FB":'\xFB',"FC":'\xFC',"FD":'\xFD',	#
		"FE":'\xFE',"FF":'\xFF'											#
		}																#
																		#
## \breif QRB string to port value map									#
PORT_MAP = {"1":"001", "2":"002", "3":"003", "4":"004",					#
		"5":"005", "6":"006", "7":"007", "8":"008",						#
		"9":"009", "10":"010", "11":"011", "12":"012",					#
		"13":"013", "14":"014", "15":"015", "16":"016",					#
		"17":"017", "18":"018", "19":"019", "20":"020",					#
		"21":"021", "22":"022", "23":"023", "24":"024",					#
		"25":"025", "26":"026", "27":"027", "28":"028",					#
		"29":"029", "30":"030", "31":"031", "32":"032"					#
		}																#
#########################################################################



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
# \return config JSON object of rf_matrix loaded from file
##
def loadConfig(confPath = 'this_device.conf.json'):
	global ID, NAME, TCP_IP, TCP_PORT, BUFFER_SIZE, STATUS
	config = utility.loadConfig(confPath)
	if 'error' not in config:
		if 'ID' in config['RF_Matrix']: ID = config['RF_Matrix']['ID']
		if 'NAME' in config['RF_Matrix']: NAME = config['RF_Matrix']['NAME']
		if 'TCP_IP' in config['RF_Matrix']: TCP_IP = config['RF_Matrix']['TCP_IP']
		if 'TCP_PORT' in config['RF_Matrix']: TCP_PORT = config['RF_Matrix']['TCP_PORT']
		if 'BUFFER_SIZE' in config['RF_Matrix']: BUFFER_SIZE = config['RF_Matrix']['BUFFER_SIZE']
		if 'STATUS' in config['RF_Matrix']: STATUS = config['RF_Matrix']['STATUS']
		return config['RF_Matrix']
	return config



## \brief Load the device configuration from the given SQLite file path
#
# If the SQLite file path is not give, default SQLite data path will be load
# if the data (ip and port) in the database is not set, the program will use
# the default value instead
# NOTE: This function can be called explictly to load configuration
#
# [Updated 1/16/2019] Added a golbal variable "RF_MATRIX_TABLE_NAME" to have the table name
# "RF_MATRIX_TABLE_NAME" is replacing the hard coded table name
#
# \param rid the id for a perticular RF Matrix device in SQLite database
# \param table_name the sqlite table name for rf_matrix
# \param db_path the path of the SQLite database file
# \return config JSON object of RF Matrix loaded from database
##
def loadSQLite(rid, table_name = None, db_path = None):
	global ID, NAME, TCP_IP, TCP_PORT, BUFFER_SIZE, STATUS
	if table_name: config = sql.getSQLite('SELECT * FROM ' + str(table_name) + ' WHERE id=' str(rid), db_path)
	else: config = sql.getSQLite('SELECT * FROM ' + RF_MATRIX_TABLE_NAME + ' WHERE id=' + str(rid), db_path)
	if config:
		if config[0]['id'] is not None: ID = config[0]['id']
		if config[0]['name'] is not None: NAME = config[0]['name']
		if config[0]['ip'] is not None: TCP_IP = config[0]['ip']
		if config[0]['port'] is not None: TCP_PORT = config[0]['port']
		if config[0]['status'] is not None: STATUS = config[0]['status']
		return config[0]
	return {"error": "Loading table [" + RF_MATRIX_TABLE_NAME + "] with ID [" + str(rid) + "] Failed"}



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
# [Updated 2/4/2019] Ehternet command deprecated
# [Updated 1/15/2019] Added the QRB implementation
# byte start with '\x30' - change the connection of the port with an attenuation
# byte start with '\x31' - preset the connection of the port with an attenuation
# byte start with '\x32' - set all preset connection with command [\x31]
#
# \param command a bytes value as a head for certain commandsglobal TCP_IP, TCP_PORT
# \param portA the source port for operating the command
# \param portB the destination port for operating the command
# \param daemon define if the program will print the reuslt or not, default is False
# \param atten A default attenuation set for QRB box, default is 15
# \return result the return value checked from command executed remotely
##
def connectRFMatrix(command, portA = "", portB = "", daemon = False, atten = 15):
	global ID, NAME, TCP_IP, TCP_PORT, BUFFER_SIZE, STATUS
	if not daemon: utility.info("################### " + Fore.YELLOW + "RF Matrix Control" + Style.RESET_ALL + " ##################")
	result = True

	if 'QRB' in NAME:
		result = connectSSH(command, host = TCP_IP, username = "prime", password = "prime123", daemon = daemon)
		''' Deprecated QRB RF_Matrix Ethernet command
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect((TCP_IP, int(TCP_PORT)))
		except OSError:
			utility.error('Connection to ' + str(TCP_IP) + ':' + str(TCP_PORT) + ' Failed!')
			exit(1);

		if command == '\x30': MESSAGE = (command + "\x40" + getQRBAddress(int(portA), int(portB), daemon) + getPortAddress(int(portA), daemon) + getPortAddress(int(portB), daemon) + rf_matrix.getAttenAddress(int(atten)) + "\x00\x00").encode('utf-8')
		if command == '\x31': MESSAGE = (command + "\x40" + getQRBAddress(int(portA), int(portB), daemon) + getPortAddress(int(portA), daemon) + getPortAddress(int(portB), daemon) + rf_matrix.getAttenAddress(int(atten)) + "\x00\x00").encode('utf-8')
		if command == '\x32': MESSAGE = (command + "\x00\x00\x00\x00\x00\x00\x00").encode('utf-8')
		if not daemon: utility.info('Send command: [' + str(MESSAGE) + '] to the RF-Matrix at [' + str(TCP_IP) + ':' + str(TCP_PORT) + ']')
		s.send(MESSAGE)
		data = s.recv(BUFFER_SIZE)
		if command == '\x30' and chr(data[7]) == '\xaa':
			if not daemon: utility.info("Result: Connect Port A" + portA + " to Port B" + portB + "with attenuation [" + str(atten) + "]" + Fore.GREEN + " Success" + Style.RESET_ALL)
		elif command == '\x31' and chr(data[7]) == '\xaa':
			if not daemon: utility.info("Result: Preset Port A" + portA + " to Port B" + portB + "with attenuation [" + str(atten) + "]" + Fore.GREEN + " Success" + Style.RESET_ALL)
		elif command == '\x32' and chr(data[7]) == '\xaa':
			if not daemon: utility.info ("Result: Load all preset routing " + Fore.GREEN + " Success" + Style.RESET_ALL)
		else:
			if not daemon: utility.error('Command: ' + str(MESSAGE) + Fore.RED + ' Fail' + Style.RESET_ALL)
			result = False
		'''
	else:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect((TCP_IP, int(TCP_PORT)))
		except OSError:
			utility.error('Connection to ' + str(TCP_IP) + ':' + str(TCP_PORT) + ' Failed!')
			exit(1);

		MESSAGE = (command + "\x50\x00"+CONST_PORT[portA]+CONST_PORT[portB]+"\x00\x00\x00").encode('utf-8')
		if not daemon: utility.info('Send command: [' + str(MESSAGE) + '] to the RF-Matrix at [' + str(TCP_IP) + ':' + str(TCP_PORT) + ']')
		s.send(MESSAGE)
		data = s.recv(BUFFER_SIZE)
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



## \brief Connect to remote QRB server using interact ssh
#
# Using pexpect package to start an expect like ssh connection with remote QRB server
# Logging into QRB and enter qrb_command_mode
# Execute each command in commands list and then exit QRB CLI
#
# \param commands A list of the string command to be executed on qrb_command_mode
# \param host String of the IP address of the remote QRB server, default is 10.155.208.121
# \param username String of the SSH login username of the remote QRB server, default is prime
# \param password String of the SSH login password of the remote QRB server, default is prime123
# \param daemon Boolean. Print out the info message if set False, default is False
# \return True if execution all pass, otherwise False
##
def connectSSH(commands, host = "10.155.208.121", username = "prime", password = "prime123", daemon = False):
	result = True
	if not daemon: utility.info("...SSH Connect to " + host)
	sshClient = pexpect.spawn('ssh -o StrictHostKeyChecking=no ' + username + '@' + host)
	sshClient.expect("Password: ", timeout = 20)
	sshClient.sendline(password)
	sshClient.expect(username + ":.*")
	sshClient.sendline("qrb_command_mode")
	sshClient.expect("#")
	if not daemon:
		if "Entered Into QRB Command Mode" in sshClient.before.decode('utf-8'):
			utility.info("Entered Into QRB Command Mode")
	for command in commands:
		sshClient.sendline(command)
		sshClient.expect("#")
		if not daemon:
			if "S\r" in sshClient.before.decode('utf-8'):
				utility.info('Command [' + command + '] execution successful on host [' + host + ']')
			else:
				utility.warn('Command [' + command + '] execution FAIL on host [' + host + ']', track = False)
				result = False
	sshClient.sendline("exit")
	utility.sleep(1, daemon = True)
	sshClient.sendline("exit")
	return result



## \brief Calculate the QRB address low byte based on Matrix input/output port
#
# The calculation use the QRB_ADDRESS_TABLE to translate the the value into byte
#
# \param portA The input port of the RF Matrix
# \param portB The output port of the RF Matrix
# \param daemon Print out the info if set False, Default value is False
# \return the byte value of the QRB low byte
##
def getQRBAddress(portA, portB, daemon = False):
	## TODO valid input port - if (not portA) and (not portB): utility.error('Invalid input port!')
	MSB = (int(portA) - 1) // 32
	LSB = (int(portB) - 1) // 32
	return QRB_ADDRESS_TABLE[HEX_STRING_TABLE[str(MSB)] + HEX_STRING_TABLE[str(LSB)]]
	## return hex(((portA - 1) // 32) * 16 + ((portB - 1) // 32))



## \brief Reset the QRB RF-Matrix port connection based on the port input
#
# Disconnect the port connection on QRB RF-Matrix based on following condition:
# 1. if portA and portB are given, disconnect PortA and PortB
# 2. if only portA is given, disconnect ALL connection from given portA to all port B
# 3. if only portB is given, disconnect ALL connection from all port A to given portB
#
# \param portA integer or string value in [1,32]. The input port of QRB RF-Matrix
# \param portB integer or string value in [1,32]. The output port of QRB RF-Matrix
# \username The username to login into remote QRB server, default is prime
# \password The password to login into remote QRB server, default is prime123
# \daemon Print out the info message if set False, default is False
##
def resetQRBAtten(portA = None, portB = None, username = "prime", password = "prime123", daemon = False):
	command = []
	## TODO valid the input arguments
	if portA and portB: command.append('SA' + getQRBPort(portA) + 'B' + getQRBPort(portB) + '999.9')
	elif portA and (not portB):
		for i in range (1,33):
			command.append('SA' + getQRBPort(portA) + 'B' + getQRBPort(i) + '999.9')
	elif (not portA) and portB:
		for i in range (1,33):
			command.append('SA' + getQRBPort(i) + 'B' + getQRBPort(portB) + '999.9')
	connectSSH(command, username = username, password = password, daemon = daemon)



## \brief Get the QRB port value for command
#
# Using the map PORT_MAP to return the string value of the QRB port
#
# \param port The string or int input port number [1,32]
# \param daemon Print the info message if set False, default is False
# \return PORT_MAP[port] string value of the port, example 23 -> "023"
##
def getQRBPort(port, daemon = False):
	return PORT_MAP[str(port)]



## \breif Build QRB CLI attenuation string value
#
# If number is in [0, 60.0] return the number with 1 decimal and extra 0s at the beginning
# If number is negetive or greater then 60, return "999.9" which disconnect the port
#
# \param number The input number of the attenuation
# \return String value of the attenuation
##
def roundQRBAttenuation(number):
	number += 0.0000001
	if 0.0 <= number < 10: return ('00' + str(round(number,1)))
	elif 10.0 <= number <= 60.0: return ('0' + str(round(number,1)))
	else: return "999.9"



## \brief get the QRB Port address byte value
#
# Using the CONST_PORT table to get the port address
# The Port address is the remaining value of port / 32
# See getQRBAddress for more information to get the low byte value
#
# \param port The QRB input port
# \daemon Print out the info message if set False, Default value is False
# \return the byte value of port address
##
def getPortAddress(port, daemon = False):
	return CONST_PORT[str(int(port) % 32)]



## \brief get the Attenuation Address byte value
#
# Using the ATTEN_TABLE to get the attentuation address
#
# \param atten The attenuation to be set on the port
# \param daemon Print out the info message if set False, Default value is False
# \return the byte value of the attenuation
##
def getAttenAddress(atten, daemon = False):
	return ATTEN_TABLE[str(atten)]



## \brief RF Matrix Device Management Class defination
#
# Version: 1.0.0
# RFMatrix class is a collection of RF Matrix device control methods
# RF Matrix device require Ethernet connection to execute remote commands
##
class RFMatrix:
	MY_ID = 2
	MY_NAME = 'RFM2'
	MY_TCP_IP = '10.155.220.77'
	MY_TCP_PORT = 9100
	MY_BUFFER_SIZE = 1024
	MY_STATUS = 0
	MY_RF_MATRIX_TABLE_NAME = 'rf_matrix'
	MY_DAEMON = False

	## \brief MXA constructor
	def __init__(self, config = None, defaultConfigFile = 'this_device_conf.json', daemon = False):
		self.MY_DAEMON = daemon
		self.__loadConfig(json = config, confPath = self.__getConfigFile(confFile = defaultConfigFile))
		pass
		## --- End of Constructor --- ##



	## \brief Private method loadConfig, loading the configuration from json file
	#
	# If json is not given, load  the configuration from configuration file
	#
	# \param json json/dictionary object with RF Matrix information
	# \param confPath the string path to the json configuration file
	# \return True if no error found, else False
	##
	def __loadConfig(self, json = None, confPath = 'this_device_conf.json'):
		if not json:
			config = utility.loadConfig(confPath = confPath)
			if 'error' in config: return False
			else: config = config['RF_Matrix']
		else: config = json
		if 'error' in config: return False
		if 'ID' in config: self.MY_ID = config['ID']
		elif 'id' in config: self.MY_ID = config['id']
		if 'NAME' in config: self.MY_NAME = config['NAME']
		elif 'name' in config: self.MY_NAME = config['name']
		if 'TCP_IP' in config: self.MY_TCP_IP = config['TCP_IP']
		elif 'ip' in config: self.MY_TCP_IP = config['ip']
		if 'TCP_PORT' in config: self.MY_TCP_PORT = config['TCP_PORT']
		elif 'port' in config: self.MY_TCP_PORT = config['port']
		if 'BUFFER_SIZE' in config: self.MY_BUFFER_SIZE = config['BUFFER_SIZE']
		elif 'buffer_size' in config: self.MY_BUFFER_SIZE = config['buffer_size']
		if 'RF_MATRIX_TABLE_NAME' in config: self.MY_RF_MATRIX_TABLE_NAME = config['RF_MATRIX_TABLE_NAME']
		elif 'rf_matrix_table_name' in config: self.MY_RF_MATRIX_TABLE_NAME = config['rf_matrix_table_name']
		if 'STATUS' in config: self.MY_STATUS = config['STATUS']
		elif 'status' in config: self.MY_STATUS = config['status']
		return True



	## \brief Loading RF Matrix configuration from SQLite database
	#
	# \param rid the id number of the RF Matrix recorded in SQLite database
	# \param table_name the sqlite table name for the RF Matrix
	# \param db_path the string path of the SQLite database file
	# \return True if no error found, else False
	##
	def loadSQLite(self, rid, table_name = None, db_path = None):
		try:
			if table_name: config = sql.getSQLite('SELECT * FROM ' + str(table_name) + ' WHERE id=' + str(rid), db_path)[0]
			else: config = sql.getSQLite('SELECT * FROM ' + self.MY_RF_MATRIX_TABLE_NAME + ' WHERE id=' + str(rid), db_path)[0]
		except Exception as e:
			utility.warn("RF Matirx loadSQLite failed: " + str(e), track = False)
			config = {"error" : str(e)}
		return self.__loadConfig(json = config)



	## \brief Get the configuration file path from rootpath.conf file (created after installation)
	#
	# getConfigFile will always look into the "config_files" folder to look for configuration files
	#
	# \param confFile The string name of the configuration file, default is "this_device_conf.json"
	# \return None if file not found, else the path of the file
	##
	def __getConfigFile(self, confFile = "this_device_conf.json"):
		try:
			with open('/var/www/html/sauto/rootpath.conf', 'r') as conf_file:
				path = conf_file.read()
				if path: return path + '/config_files/' + confFile
				else: return 'this_device_conf.json'
		except Exception as e:
			utility.error(str(e), False)
			return None


	## TODO TODO TODO add execute/reset/etc...


## \brief Main function for provide the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./rf_matrix.py -h or --help for instructions
##
def main():
	global RF_MATRIX_TABLE_NAME
	parser = argparse.ArgumentParser(description='Tools for controlling RF-Matrix box')
	parser.add_argument('-c', '--connect', nargs=2, metavar=('PortANum', 'PortBNum'), help='Connect port A to port B\n Example: --connect 1 2    Connect Port A01 to Port B02')
	parser.add_argument('-H', '--health', nargs=2, metavar=('Port', 'PortNum'), help='Check port if it is functioning\n Example: --health A 20    Check Port A20 if it is functioning')
	parser.add_argument('-C', '--check', nargs=2, metavar=('Port', 'PortNum'), help='Check what port of the given port is connecting to\n Example: --check A 20    Check Port A20 which Port B is connecting to')
	parser.add_argument('-s', '--sql', metavar='SQLite_File_Path', help='Load the SQLite database path instead of configuration json file. Using parameter None or null to use default database')
	parser.add_argument('-n', '--name', metavar='SQLite_Table_Name', help='Define the name of the table to be used when loading the SQLite')
	parser.add_argument('-i', '--id', metavar='RF_Matrix_ID#', type=int, help='The id number of the RF Matrix device in SQLite database, default is 1')
	args = parser.parse_args()
	rid = 1
	if len(sys.argv) < 2: parser.print_help()
	if args.id: rid = args.id
	if args.name: RF_MATRIX_TABLE_NAME = args.name
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
ID = 2											# Default Value #
NAME = 'RFM2'									# Default Value #
TCP_IP = '10.155.220.77'						# Default Value #
TCP_PORT = 9100									# Default Value #
BUFFER_SIZE = 1024								# Default Value #
STATUS = 0										# Default Value #
RF_MATRIX_TABLE_NAME = "rf_matrix"				# Default Value #
#################################################################


## \brief Load the default configuration from SAuto framework
try:
	with open('/var/www/html/sauto/rootpath.conf', 'r') as conf_file:
		path = conf_file.read()
		if path: loadConfig(path + '/config_files/this_device_conf.json')
		else: loadConfig()
except Exception as e:
	utility.error(str(e), False)
	exit(1)


## \brief give the entry for main when execute from command line
if __name__ == "__main__":
	main()
