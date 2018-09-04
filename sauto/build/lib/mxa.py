#!/usr/bin/python3

## \file mxa.py
# \brief Modules as well as CLI tools for remote MXA box control
#
# This modules contains the library for remote controling the MXA box
# and it is also a stand alone command line tool
# The library has to work with a proper configuration file in order to
# have the ip and port for the remote devices
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import json
from telnetlib import Telnet
from time import sleep
import socket
import argparse
import utility
import sql
import sys
from colorama import Fore, Style

## \brief Load the device configuration from the given config file path
#
# If the the config file path is not given, the program will tend to
# use the default path.   The config file is a json file, loadConfig is
# looking for the key 'MXA' and get TCP IP address as well as the
# Port for the remote MXA box. If key is not found, a default value
# will be loaded
# NOTE: This function can be called explictly to load user configurations
#
# \param confPath a string value contain the path to the json file
##
def loadConfig(confPath = 'this_device_conf.json'):
    global ID, NAME, TCP_IP, TELNET_PORT, LOCATION, JFW_PORT, MXA_PORT, STATUS
    config = utility.loadConfig(confPath)
    if 'error' not in config:
        if 'ID' in config['MXA']: ID = config['MXA']['ID']
        if 'NAME' in config['MXA']: NAME = config['MXA']['NAME']
        if 'TCP_IP' in config['MXA']: TCP_IP = config['MXA']['TCP_IP']
        if 'TELNET_PORT' in config['MXA']: TELNET_PORT = config['MXA']['TELNET_PORT']
        if 'SOCKET_PORT' in config['MXA']: SOCKET_PORT = config['MXA']['SOCKET_PORT']
        if 'LOCATION' in config['MXA']: LOCATION = config[0]['location']
        if 'JFW_PORT' in config['MXA']: JFW_PORT = config[0]['jfw_port']
        if 'MXA_PORT' in config['MXA']: MXA_PORT = config[0]['mxa_port']
        if 'STATUS' in config['MXA']: STATUS = config[0]['status']



## \brief Load the device configuration from the given SQLite file path
#
# If the SQLite file path is not give, default SQLite data path will be load
# if the data (ip and port) in the database is not set, the program will use
# the default value instead
# NOTE: This function can be called explictly to load configuration
#
# \param mid the id for a perticular MXA device in SQLite database
# \param db_path the path of the SQLite database file
##
def loadSQLite(mxa_id, db_path = None):
    global ID, NAME, TCP_IP, TELNET_PORT, LOCATION, JFW_PORT, MXA_PORT, STATUS
    config = sql.getSQLite('SELECT * FROM mxa WHERE id=' + str(mxa_id), db_path)
    if config:
        if config[0]['id'] is not None: ID = config[0]['id']
        if config[0]['ip'] is not None: TCP_IP = config[0]['ip']
        if config[0]['port'] is not None: TELNET_PORT = config[0]['port']
        if config[0]['name'] is not None: NAME = config[0]['name']
        if config[0]['location'] is not None: LOCATION = config[0]['location']
        if config[0]['jfw_port'] is not None: JFW_PORT = config[0]['jfw_port']
        if config[0]['mxa_port'] is not None: MXA_PORT = config[0]['mxa_port']
        if config[0]['status'] is not None: STATUS = config[0]['status']



## \brief Connect to remote MXA box and execute a command
#
# Remotely connecting to a MXA box using a Telnet connection.
# The IP address and Port was loaded by loadConfig/loadSQLite function
#
# \param command either using the CLI with -e option or input as a parameter
# \param delayTime a delay time waiting response from telnet connection, default is 5
# \param daemon define if the program will print the reuslt or not, default is False
# \return result the return value from command executed remotely
##
## NOTE: MXA may have experiencing heavy traffic and may need to increse the delay time
## NOTE: read_until() seems not working properly to track the return
def connectMXA(command, delayTime = 5, daemon = False):
    if not daemon: utility.info("##################### " + Fore.YELLOW + "MXA Control" + Style.RESET_ALL + " ######################")
    try:
        if not daemon: utility.info('Send command: [' + command + '] to the MXA box at [' + str(TCP_IP) + ':' + str(TELNET_PORT) + ']')
        tn = Telnet(TCP_IP, int(TELNET_PORT))
        tn.read_until(b'SCPI>')
        tn.write((command + '\r\n').encode('ascii'))
        sleep(delayTime)
        result = utility.regexParser(tn.read_very_eager().decode('ascii'), ' (.*)\r\nSCPI.*', daemon)
        if not daemon: utility.info('Response:\n' + result)
    except OSError:
        utility.error('Connection to ' + str(TCP_IP) + ':' + str(TELNET_PORT) + ' Failed!')
        exit(1)
    tn.close()
    return result



#TODO: check mxa is not overflow
#TODO: Using command STAT:QUES set to check the status registers
#NOTE: There are a lot of condition to check and report
#NOTE: MXA_Manual page 78
def healthCheck():
    result = connectMXA('*IDN', 2, True) ## Send IDN and/or other command to get status
    ## TODO: Read the values of status registers
    ## TODO: parse the result to get health check report



## \brief Sending 'READ:EVM?' command to remote MXA reading the current EVM result
#
# Remotely connecting to MXA box and send 'READ:EVM?' command to readding
# the EVM results with the current settings on the MXA box
# A counter parameter is to provided to calculate an average result within multiple
# data read
#
# \param counter an iteration counter to read and calculate average result of EVM and RS Pow default is 10
# \daemon define if the program will print the result of not, default is False
# \return a dictionary of EVM_AVG and RSPW_AVG values, value is None if not readable
def getEVMResult(counter = 10, daemon = False):
    if not daemon: utility.info("############# " + Fore.YELLOW + "Start collecting data from MXA" + Style.RESET_ALL + " #############")
    evmAvg = 0.0
    rspwAvg = 0.0
    for i in range(counter):
        utility.info("[Iteration " + str(i+1) + "]")
        result = connectMXA('read:evm?', 5, True)
        if not result:
            utility.error('Failed to read remote MXA at [' + TCP_IP + ']', False)
            return None
        result = result.split(',')
        evmAvg += float(result[9])
        rspwAvg += float(result[10])
        if not daemon:
            utility.info("RS EVM: " + str(float(result[9])) + " %rms")
            utility.info("RS Tx. Power(Avg): " + str(float(result[10])) + " dBm")
    evmAvg /= counter
    rspwAvg /= counter
    return {'EVM_AVG':evmAvg, 'RSPW_AVG':rspwAvg}



## \brief get the current Cell ID of the remote MXA
#
# Connect to the remote MXA and get the current Cell ID
# To change the remote MXA configuration, using command loadConfig/loadSQLite
##
def getCID():
    return int(connectMXA('EVM:DLINk:SYNC:CID?', 5, True))



## \brief set the Cell ID of the remote MXA
#
# Connect to the remote MXA and try to set the Cell ID
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \param cid cell id to be set on remote MXA
# \param daemon print out info message if set False, default is False
##
def setCID(cid, daemon = False):
    if not daemon: utility.info('[MXA] Setting Cell ID to [' + str(cid) + ']')
    connectMXA('EVM:DLINk:SYNC:CID ' + str(cid), 5, True)



## \brief get the current center frequency setting of the remote MXA
#
# Connect to the remote MXA and get the current center frequency
# To change the remote MXA configuration, using command loadConfig/loadSQLite
##
def getFrequency():
    return float(connectMXA('FREQ:CENT?', 5, True))



## \brief set the center frequency of the remote MXA
#
# Connect to the remote MXA and try to set the center frequency
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \param freq center frequency to be set on remote MXA
# \param unit the unit for center frequency {'MHz', 'GHz', 'KHz'}
# \param daemon print out info message if set False, default is False
##
def setFrequency(freq, unit = 'MHz', daemon = False):
    if not daemon: utility.info('[MXA] Setting Center Frequency to [' + str(freq) + ' ' + unit + ']')
    connectMXA('FREQ:CENT ' + str(freq) + ' ' + unit, 5, True)



## \brief get the current attenuate range of the remote MXA
#
# Connect to the remote MXA and get the current attenuate rage
# To change the remote MXA configuration, using command loadConfig/loadSQLite
##
def getRang():
    return float(connectMXA('POW:RANG?', 5, True))



## \brief set the attenuate range of the remote MXA
#
# Connect to the remote MXA and try to set the attenuate range
# To change the remote MXA configuration, using command loadConfig/loadSQLite
# NOTE: this is mainly the atten protection for MXA not overflow
#
# \param rang attenuate range to be set on remote MXA
# \param daemon print out info message if set False, default is False
##
def setRang(rang, daemon = False):
    if not daemon: utility.info('[MXA] Setting Attenuator Range to [' + str(rang) + ']')
    connectMXA('POW:RANG ' + str(rang), 5, True)



## \brief get the current physical attenuate setting of the remote MXA
#
# Connect to the remote MXA and get the current physical attenuate setting
# To change the remote MXA configuration, using command loadConfig/loadSQLite
##
def getAtten():
    return float(connectMXA('POW:ATT?', 5, True))



## \brief set the Cell ID of the remote MXA
#
# Connect to the remote MXA and try to set the Cell ID
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \param cid cell id to be set on remote MXA
# \param daemon print out info message if set False, default is False
##
def setAtten(atten, daemon = False):
    if not daemon: utility.info('[MXA] Setting Physical Attenuator to [' + str(atten) + ']')
    connectMXA('POW:ATT ' + str(atten), 5, True)



## \brief set the decode Sync Type of the remote MXA
#
# Connect to the remote MXA and try to set the Sync Type
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \param type type of the Sync, PSS or RS
# \param daemon print out info message if set False, default is False
##
def setSyncType(sType, daemon = False):
    if not daemon: utility.info('[MXA] Setting decode Sync Type to [' + str(sType) + ']')
    connectMXA('EVM:DLINk:SYNC:TYPE ' + str(sType), 5, True)



## \brief recall a pre-registered states on MXA and switch all configurations
#
# Connect to the remote MXA and send recall command to switch to a pre-configured
# states
# To change the which remote MXA to use, using command loadConfig/loadSQLite
#
# \param reg register number of pre-configured status
# \param daemon print out info message if set False, default is False
##
def recall(reg, daemon = False):
    if not daemon: utility.info('[MXA] Recall Registered status [' + str(reg) + ']')
    connectMXA('*RCL ' + str(reg), 5, True)



## \brief set the MXA mode
#
# Connect to the remote MXA and set the MXA mode
# To change which remote MXA to use, using command loadConfig/loadSQLite
# LTE mode:
#   LTE - LTE FDD mode
#   LTETDD - LTE TFF mode
#
# \param mode for LTE using value "LTE" or "LTETDD"
# \param daemon print out info message if set False, default is False
##
def setMode(mode, daemon = False):
    if not daemon: utility.info('[MXA] Setting MXA mode to [' + str(mode) + ']')
    connectMXA('INST:SEL ' + str(mode), 5, True)



## \brief Main function for providing the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./mxa.py -h or --help for instructions
##
def main():
    parser = argparse.ArgumentParser(description='Tools for controlling JFW box')
    parser.add_argument('-d', '--delay', nargs='?', const=5, metavar='Seconds', type=int, help='Set the system delay time waiting for JFW box responding, default 5 seconds')
    parser.add_argument('-e', '--execute', metavar='Command', nargs='+', help='Execute the remote command on JFW box')
    parser.add_argument('-s', '--sql', metavar='File Path', help='Load the SQLite database path instead of configuration json file. Using parameter None or null to use the default database')
    parser.add_argument('-i', '--id', metavar='MXA ID#', type=int, help='The id number of the MXA device in SQLite database, default is 1')
    args = parser.parse_args()
    delayTime = 5
    mid = 1
    if len(sys.argv) < 2: parser.print_help()
    if args.delay: delayTime = args.delay
    if args.id: mid = args.id
    if args.sql:
        if args.sql is 'None' or 'none' or 'default' or 'Default' or 'null':
            loadSQLite(mid)
        else:
            loadSQLite(mid, args.sql)
    if args.execute: connectMXA(' '.join(args.execute), delayTime)



## \brief Shared variables
#
# \param TCP_IP the ip address of the remote device
# \param TELNET_PORT the telnet port of the remote device
# \param SOCKET_PORT the TCP socket port of the remote device
# \function loadConfig() load the default configuration from json when loading this module
##
###################### Load Config File #########################
ID = 1                                          # Default Value #
NAME = 'MXA'                                    # Default Value #
TCP_IP = '10.155.226.218'                       # Default Value #
TELNET_PORT = 5023                              # Default Value #
LOCATION = ''                                   # Default Value #
JFW_PORT = 24                                   # Default Value #
MXA_PORT = 1                                    # Default Value #
STATUS = 0                                      # Default Value #
SOCKET_PORT = 5025                              # Default Value #
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
