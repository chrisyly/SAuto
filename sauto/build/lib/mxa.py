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
import socket
import argparse
import utility
import sql
import sys
import jfw
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
	config = sql.getSQLite('SELECT * FROM ' + MXA_TABLE_NAME + ' WHERE id=' + str(mxa_id), db_path)
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
		##tn.write(('\r\n').encode('ascii'))
		tn.read_until(b'SCPI>')
		tn.write((command + '\r\n').encode('ascii'))
		utility.sleep(delayTime, True)
		result = (utility.regexParser(tn.read_very_eager().decode('ascii'), ' (.*)\r\nSCPI.*', daemon)).replace('SCPI> ', '').replace(command, '').replace('\r\n', '')
		if result:
			if not daemon: utility.info('Response:\n' + result)
		else:
			result = ''
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



## \brief Reset the attenuation on MXA
#
# Load MXA list from SQLite database baed on name, reset attenuations
#
# \param name The string name of the MXA
# \param daemon Print out info message if set False, default is False
##
def resetMXA(name, db_path = None, daemon = False):
	if name: mxaList = sql.getSQLite('SELECT * FROM rf_matrix_db WHERE output_device = "' + name + '"', db_path = db_path)
	else: raise Exception ('resetMXA failed, input argument [name] is not valid')
	for mxa in mxaList:
		if mxa['jfw_id'] and mxa['jfw_port']:
			jfw.loadSQLite(str(mxa['jfw_id']), db_path = db_path)
			jfw.connectJFW('SAR' + str(mxa['jfw_port']) + ' 127')
		else:
			rf_matrix_box = sql.getSQLite('SELECT * FROM rf_matrix WHERE id=' + str(mxa['rf_matrix_id']), db_path = db_path)[0]
			rf_matrix.loadSQLite(str(rf_matrix_box['id']), db_path = db_path)
			if 'QRB' in rf_matrix_box['name']: rf_matrix.resetQRBAtten(portB = mxa['port'], daemon = daemon)
			elif 'RFM' in rf_matrix_box['name']: jfw.connectJFW('SAR' + str(JFW_PORT) + ' 127')
	return mxaList




## \brief Reading the current MXA LTE report from remote MXA
#
# Remotely connecting to MXA and send 'CALC:EVM:DATA4:TABL:NAM?' and 'CALC:EVM:DATA4:TABL:STR?' command
# retrun the key-value pair based on NAM and STR result
#
# \param daemon Print out info message if set False, default is False
# \return result A dictionary of key-value pairs
##
def getMXAResult(daemon = False):
	if not daemon: utility.info("############# " + Fore.YELLOW + "Reading MXA Report" + Style.RESET_ALL + " #############")
	name = (connectMXA('CALC:EVM:DATA4:TABL:NAM?', daemon = True).replace('"', '')).split(',')
	value = (connectMXA('CALC:EVM:DATA4:TABL:STR?', daemon = True).replace('"', '')).split(',')
	result = {}
	for i in range(0, len(name)):
		result[name[i]] = value[i]
	return result



## \brief Sending 'READ:EVM?' command to remote MXA reading the current EVM result
#
# Remotely connecting to MXA box and send 'CALC:EVM:DATA4:TABL:STR?' command to read
# the EVM results with the current settings on the MXA box
# A counter parameter is to provided to calculate an average result within multiple
# data read
#
# \param counter an iteration counter to read and calculate average result of EVM and RS Pow default is 10
# \daemon define if the program will print the result of not, default is False
# \return a dictionary of EVM_AVG and RSPW_AVG values, value is None if not readable
##
def getEVMResult(counter = 10, daemon = False):
	if not daemon: utility.info("############# " + Fore.YELLOW + "Reading MXA EVM Results" + Style.RESET_ALL + " #############")
	evmList = []
	rspwList = []
	pciList = []
	evmAvg = 0.0
	rspwAvg = 0.0
	pci = -1
	for i in range(counter):
		utility.info("[Iteration " + str(i+1) + "]")
		mxaRead = getMXAResult(daemon = True)
		evmRead = str(mxaRead['RSEVM']) ## str(connectMXA('CALC:EVM:DATA4:TABL:STR? "RSEVM"', 5, True))
		## utility.debug("Test evm: " + evmRead, False)
		evmRead = float(''.join(j for j in evmRead if j.isdigit() or j == '.' or j == '-'))
		if not evmRead:
			utility.error('Failed to read remote MXA at [' + TCP_IP + ']', False)
			break
		evmList.append(evmRead)
		evmAvg += evmRead
		if str(mxaRead['RSRP']) == '---': rspwRead = str(mxaRead['RSTP'])
		else: rspwRead = str(mxaRead['RSRP']) ## str(connectMXA('CALC:EVM:DATA4:TABL:STR? "RSRP"', 5, True))
		## utility.debug("Test rstp: " + rspwRead, False)
		rspwRead = float(''.join(j for j in rspwRead if j.isdigit() or j == '.' or j == '-'))
		if not rspwRead:
			utility.error('Failed to read remote MXA at [' + TCP_IP + ']', False)
			break
		rspwList.append(rspwRead)
		rspwAvg += rspwRead
		pciRead = int(''.join(i for i in str(mxaRead['CellId']) if i.isdigit()))
		pciList.append(pciRead)
		if pci == -1:
			pci = pciRead
		else:
			if pci != pciRead:
				pci = -2
				utility.warn('MXA not getting consistent PCI value, read [' + str(pciRead) + ']', False)

		if not daemon:
			utility.info("PCI: " + str(pci))
			utility.info("RS EVM: " + str(evmRead) + " %rms")
			utility.info("RS Rx. Power(Avg): " + str(rspwRead) + " dBm")
	evmAvg /= counter
	rspwAvg /= counter
	return {'EVM_LIST': evmList, 'RSPW_LIST': rspwList, 'PCI_LIST': pciList, 'EVM_AVG': evmAvg, 'RSPW_AVG': rspwAvg, 'PCI': pci}



## \brief get the current Cell ID of the remote MXA
#
# Connect to the remote MXA and get the current Cell ID
# To change the remote MXA configuration, using command loadConfig/loadSQLite
##
def getCID():
	return int(''.join(i for i in str(connectMXA('CALC:EVM:DATA4:TABL:STR? "CellId"', 5, True)) if i.isdigit()))



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
	if str(cid).isdigit():
		connectMXA('EVM:DLINk:SYNC:CID:AUTO OFF', 5, True)
		connectMXA('EVM:DLINk:SYNC:CID ' + str(cid), 5, True)
	else: connectMXA('EVM:DLINk:SYNC:CID:AUTO ON', 5, True)



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



## \brief get the decode Sync Type of the remote MXA
#
# Connect to the remote MXA and try to get the Sync Type
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \return str(connectMXA('EVM:DLINk:SYNC:TYPE?')) value should either be "RS" or "PSS"
def getSyncType():
	return str(connectMXA('EVM:DLINk:SYNC:TYPE?', 5, True))




## \brief get the current Number of C-RS Ports setting of the remote MXA
#
# Connect to the remote MXA and get the current Numbere of C-RS Ports setting
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \return an integer of number of ports
##
def getNumOfCRSPorts():
	return int(str(connectMXA('EVM:DLINk:SYNC:ANTenna:NUMBer?', 5, True))[3])



## \brief set the Number of C-RS Ports of the remote MXA
#
# Connect to the remote MXA and set the Number of C-RS Ports
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \param ant The antenna number to be set for C-RS Ports, start with 'ANT'. Example: ANT1|ANT2|ANT4
# \param daemon Print out the info message if set False, default is False
##
def setNumOfCRSPorts(ant, daemon = False):
	if not daemon: utility.info('[MXA] Setting Number of C-RS Ports to [' + str(ant) + ']')
	if str(ant).isdigit(): ant = 'ANT' + str(ant)
	connectMXA('EVM:DLINk:SYNC:ANTenna:NUMBer ' + str(ant), 5, True)



## \brief get the current Reference C-RS Port of the remote MXA
#
# Connect to the remote MXA and get the current reference C-RS Port setting
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \return an integer of port number
##
def getRefCRSPort():
	return int(str(connectMXA('EVM:DLINk:SYNC:ANTenna:PORT?', 5, True))[1])



## \brief set the current Reference C-RS Port of the remote MXA
#
# Connect to the remote MXA and set the Reference C-RS Port setting
# To change the remote MXA configuration, using command loadConfig/loadSQLite
#
# \param port The port numbers to be set for Reference C-RS port, start with 'P'. Example: P0|P1|p2|p3 (max one of four ports can be selected)
# \param daemon Print out the info message if set False, default is False
##
def setRefCRSPort(port, daemon = False):
	if str(port).isdigit(): port = 'P' + str(port)
	if not daemon: utility.info('[MXA] Setting the Reference C-RS Port [' + str(port) + '] to use')
	if 'AUTO' in str(port) or 'Auto' in str(port) or 'auto' in str(port): connectMXA('EVM:DLINk:SYNC:ANTenna:PORT:AUTO ON', 5, True)
	else:
		connectMXA('EVM:DLIN:SYNC:ANT:PORT:AUTO OFF', 5, True)
		connectMXA('EVM:DLIN:SYNC:ANT:PORT ' + str(port), 5, True)



## \brief convert EARFCN to frequency
#
# convert the input earfcn value to frequency (MHz)
#
# \param earfcn EARFCN value
# \param daemon print the info message if set False, default value is False
# \return frequency (MHz)
##
## TODO TODO TODO return frequency, technology, and BW
def earfcnToFrequency(earfcn, daemon = False):
	offset = 0
	frequencyLow = 0
	############################### FDD ###############################
	if 0 <= earfcn <= 599: offset = 0; frequencyLow = 2110;                 ## 2100
	elif 18000 <= earfcn <= 18599: offset = 18000; frequencyLow = 1920;
	elif 600 <= earfcn <= 1199: offset = 600; frequencyLow = 1930;          ## 1900 PCS
	elif 18600 <= earfcn <= 19199: offset = 18600; frequencyLow = 1850;
	elif 1200 <= earfcn <= 1949: offset = 1200; frequencyLow = 1805;        ## 1800+
	elif 19200 <= earfcn <= 19949: offset = 19200; frequencyLow = 1710;
	elif 1950 <= earfcn <= 2399: offset = 1950; frequencyLow = 2110;        ## AWS-1
	elif 19950 <= earfcn <= 20399: offset = 19950; frequencyLow = 1710;
	elif 2400 <= earfcn <= 2649: offset = 2400; frequencyLow = 869;         ## 850
	elif 20400 <= earfcn <= 20649: offset = 20400; frequencyLow = 824;
	elif 2650 <= earfcn <= 2749: offset = 2650; frequencyLow = 875;         ## UMTS only
	elif 20650 <= earfcn <= 20749: offset = 20650; frequencyLow = 830;
	elif 2750 <= earfcn <= 3449: offset = 2750; frequencyLow = 2620;        ## 2600
	elif 20750 <= earfcn <= 21449: offset = 20750; frequencyLow = 2500;
	elif 3450 <= earfcn <= 3799: offset = 3450; frequencyLow = 925;         ## 900 GSM
	elif 21450 <= earfcn <= 21799: offset = 21450; frequencyLow = 880;
	elif 3800 <= earfcn <= 4149: offset = 3800; frequencyLow = 1844.9;      ## 1800
	elif 21800 <= earfcn <= 22149: offset = 21800; frequencyLow = 1749.9;
	elif 4150 <= earfcn <= 4749: offset = 4150; frequencyLow = 2110;        ## AWS-1+
	elif 22150 <= earfcn <= 22749: offset = 22150; frequencyLow = 1710;
	elif 4750 <= earfcn <= 4949: offset = 4750; frequencyLow = 1475.9;      ## 1500 Lower
	elif 22750 <= earfcn <= 22999: offset = 22750; frequencyLow = 1427.9;
	elif 5010 <= earfcn <= 5179: offset = 5010; frequencyLow = 729;         ## 700 a
	elif 23010 <= earfcn <= 23179: offset = 23010; frequencyLow = 699;
	elif 5180 <= earfcn <= 5279: offset = 5180; frequencyLow = 746;         ## 700 c
	elif 23180 <= earfcn <= 23279: offset = 23180; frequencyLow = 777;
	elif 5280 <= earfcn <= 5379: offset = 5280; frequencyLow = 758;         ## 700 PS
	elif 23280 <= earfcn <= 23379: offset = 23280; frequencyLow = 788;
	## Downlink
	elif 5730 <= earfcn <= 5849: offset = 5730; frequencyLow = 734;         ## 700 b
	elif 23730 <= earfcn <= 23849: offset = 23730; frequencyLow = 704;
	elif 5850 <= earfcn <= 5999: offset = 5850; frequencyLow = 860;         ## 800 Lower
	elif 23850 <= earfcn <= 23999: offset = 23850; frequencyLow = 815;
	elif 6000 <= earfcn <= 6149: offset = 6000; frequencyLow = 875;         ## 800 Upper
	elif 24000 <= earfcn <= 24149: offset = 24000; frequencyLow = 830;
	elif 6150 <= earfcn <= 6449: offset = 6150; frequencyLow = 791;         ## 800 DD
	elif 24150 <= earfcn <= 24449: offset = 24150; frequencyLow = 832;
	elif 6450 <= earfcn <= 6599: offset = 6450; frequencyLow = 1495.9;      ## 1500 Upper
	elif 24450 <= earfcn <= 24599: offset = 24450; frequencyLow = 1447.9;
	elif 6600 <= earfcn <= 7399: offset = 6600; frequencyLow = 3510;        ## 3500
	elif 24600 <= earfcn <= 25399: offset = 24600; frequencyLow = 3410;
	elif 7500 <= earfcn <= 7699: offset = 7500; frequencyLow = 2180;        ## 2000 S-band
	elif 25500 <= earfcn <= 25699: offset = 25500; frequencyLow = 2000;
	elif 7700 <= earfcn <= 8039: offset = 7700; frequencyLow = 1525;        ## 1600 L-band
	elif 25700 <= earfcn <= 26039: offset = 25700; frequencyLow = 1626.5;
	elif 8040 <= earfcn <= 8689: offset = 8040; frequencyLow = 1930;        ## 1900+
	elif 26040 <= earfcn <= 26689: offset = 26040; frequencyLow = 1850;
	elif 8690 <= earfcn <= 9039: offset = 8690; frequencyLow = 859;         ## 850+
	elif 26690 <= earfcn <= 27039: offset = 26690; frequencyLow = 814;
	elif 9040 <= earfcn <= 9209: offset = 9040; frequencyLow = 852;         ## 800 SMR
	elif 27040 <= earfcn <= 27209: offset = 27040; frequencyLow = 807;
	elif 9210 <= earfcn <= 9659: offset = 9210; frequencyLow = 758;         ## 700 APT
	elif 27210 <= earfcn <= 27659: offset = 27210; frequencyLow = 703;
	elif 9660 <= earfcn <= 9769: offset = 9960; frequencyLow = 717;         ## 700 d
	## Downlink only
	elif 9770 <= earfcn <= 9869: offset = 9770; frequencyLow = 2350;        ## 2300 WCS
	elif 27660 <= earfcn <= 27759: offset = 27660; frequencyLow = 2305;
	elif 9870 <= earfcn <= 9919: offset = 9870; frequencyLow = 462.5;       ## 450
	elif 27760 <= earfcn <= 27809: offset = 27760; frequencyLow = 452.5;
	elif 9920 <= earfcn <= 10359: offset = 9920; frequencyLow = 1452;       ## 1500 L-band
	## Downlink only

	############################### TDD ###############################
	elif 36000 <= earfcn <= 36199: offset = 36000; frequencyLow = 1900;     ## TD 1900
	elif 36200 <= earfcn <= 36349: offset = 36200; frequencyLow = 2010;     ## TD 2000
	elif 36350 <= earfcn <= 36949: offset = 36350; frequencyLow = 1850;     ## TD PCS Lower
	elif 36950 <= earfcn <= 37549: offset = 36950; frequencyLow = 1930;     ## TD PCS Upper
	elif 37550 <= earfcn <= 37749: offset = 37550; frequencyLow = 1910;     ## TD PCS Center gap
	elif 37750 <= earfcn <= 38249: offset = 37750; frequencyLow = 2570;     ## TD 2600
	elif 38250 <= earfcn <= 38649: offset = 38250; frequencyLow = 1880;     ## TD 1900+
	elif 38650 <= earfcn <= 39649: offset = 38650; frequencyLow = 2300;     ## TD 2300
	elif 39650 <= earfcn <= 41589: offset = 39650; frequencyLow = 2496;     ## TD 2500
	elif 41590 <= earfcn <= 43589: offset = 41590; frequencyLow = 3400;     ## TD 3500
	elif 43590 <= earfcn <= 45589: offset = 43590; frequencyLow = 3600;     ## TD 3700
	elif 45590 <= earfcn <= 46589: offset = 45590; frequencyLow = 703;      ## TD 700
	elif 46590 <= earfcn <= 46789: offset = 46590; frequencyLow = 1447;     ## TD 1500
	elif 46790 <= earfcn <= 54539: offset = 46790; frequencyLow = 4150;     ## TD Unlicensed
	elif 54540 <= earfcn <= 55239: offset = 54540; frequencyLow = 5855;     ## TD V2X
	elif 55240 <= earfcn <= 56739: offset = 55240; frequencyLow = 3550;     ## TD 3600
	elif 56740 <= earfcn <= 58239: offset = 56740; frequencyLow = 3550;     ## TD 3600r
	elif 58240 <= earfcn <= 59089: offset = 58240; frequencyLow = 1432;     ## TD 1500+
	elif 59090 <= earfcn <= 59139: offset = 59090; frequencyLow = 1427;     ## TD 1500-
	elif 59140 <= earfcn <= 60139: offset = 59140; frequencyLow = 3300;     ## TD 3300

	frequency = frequencyLow + 0.1 * (earfcn - offset)
	if not daemon: utility.info("EARFCN [" + str(earfcn) + "] has frequency: " + str(frequency))
	return frequency



## TODO TODO
def frequencyToEarfcn():
	return 1


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



## TODO TODO TODO
def getDependentMXA():
	return sql.getSQLite('SELECT * FROM rf_matrix_db where output_device="' + NAME + '"')




## \brief Main function for providing the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./mxa.py -h or --help for instructions
##
def main():
	global MXA_TABLE_NAME
	parser = argparse.ArgumentParser(description='Tools for controlling JFW box')
	parser.add_argument('-d', '--delay', nargs='?', const=5, metavar='Seconds', type=int, help='Set the system delay time waiting for JFW box responding, default 5 seconds')
	parser.add_argument('-e', '--execute', metavar='Command', nargs='+', help='Execute the remote command on JFW box')
	parser.add_argument('-s', '--sql', metavar='SQLite File Path', help='Load the SQLite database path instead of configuration json file. Using parameter None or null to use the default database')
	parser.add_argument('-n', '--name', metavar='SQLite Table Name', help='Define the name of the table to be used when loading the SQLite')
	parser.add_argument('-i', '--id', metavar='MXA ID#', type=int, help='The id number of the MXA device in SQLite database, default is 1')
	args = parser.parse_args()
	delayTime = 5
	mid = ID
	if len(sys.argv) < 2: parser.print_help()
	if args.delay: delayTime = args.delay
	if args.id: mid = args.id
	if args.name: MXA_TABLE_NAME = args.name
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
NAME = 'MXASpecAn'                              # Default Value #
TCP_IP = '10.155.226.218'                       # Default Value #
TELNET_PORT = 5023                              # Default Value #
LOCATION = ''                                   # Default Value #
JFW_PORT = 24                                   # Default Value #
MXA_PORT = 1                                    # Default Value #
STATUS = 0                                      # Default Value #
SOCKET_PORT = 5025                              # Default Value #
MXA_TABLE_NAME = 'mxa'                          # Default Value #
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
