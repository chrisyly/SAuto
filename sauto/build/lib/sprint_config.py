#!/usr/bin/python3

## \file sprint_config.py
# \brief Modules as well as CLI tools for sprint pre-configure devices
#
# This modules contains the library for remote controling the JFW, MXA,
# RF Matrix, LSU and SQL databse
# It is also a stand alone command line tool
# The librarys has to work with a proper configuration file in order to
# have the ip and port for the remote devices
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import json
import argparse
import jenkins
import utility
import jfw
import mxa
import rf_matrix
import lsu
import sql
import sys
import signal
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
	global sqlite_file
	config = utility.loadConfig(confPath)
	if 'error' not in config:
		if 'SQLITE' in config: sqlite_file = config['SQLITE']['Master']
		if 'VENDORS' in config: return config['VENDORS']
		else: utility.warn('No vendors configuration found in [' + confPath + ']', False)
	return None



## \brief Load the device configuration from the given SQLite file path
#
# If the SQLite file path is not give, default SQLite data path will be load
# if the data (ip and port) in the database is not set, the program will use
# the default value instead
# NOTE: This function can be called explictly to load configuration
#
# \param vendor_name the name for vendor devices in SQLite database
# \param vendor_tag the tag name for vendor devices in SQLite database
# \param vendor_id the id for vendor devices in SQLite database
# \param db_path the path of the SQLite database file
##
def loadSQLite(vendor_name = None, vendor_tag = None, vendor_id = None, db_path = None, daemon = False):
	global sqlite_file
	if db_path: sql.setDBPath(db_path, daemon)
	else: sql.setDBPath(sqlite_file, daemon)
	if vendor_id: return sql.getSQLite('SELECT DISTINCT vendor.*, pre_config_vendor.rf_matrix_output_port, pre_config_vendor.mxa_id, pre_config_vendor.lsu_id, pre_config_vendor.aggr_id, rf_matrix_db.jfw_id, rf_matrix_db.jfw_port, rf_matrix_db.CELLID FROM vendor , pre_config_vendor, rf_matrix_db INNER JOIN vendor pre_config_vendor ON pre_config_vendor.vendor_id = vendor.id AND rf_matrix_db.port = pre_config_vendor.rf_matrix_output_port AND rf_matrix_db.rf_matrix_id = vendor.rf_matrix_id AND pre_config_vendor.vendor_id = ' + str(vendor_id))
	elif vendor_name: return sql.getSQLite('SELECT DISTINCT vendor.*, pre_config_vendor.rf_matrix_output_port, pre_config_vendor.mxa_id, pre_config_vendor.lsu_id, pre_config_vendor.aggr_id, rf_matrix_db.jfw_id, rf_matrix_db.jfw_port, rf_matrix_db.CELLID FROM vendor , pre_config_vendor, rf_matrix_db INNER JOIN vendor pre_config_vendor ON pre_config_vendor.vendor_id = vendor.id AND rf_matrix_db.port = pre_config_vendor.rf_matrix_output_port AND rf_matrix_db.rf_matrix_id = vendor.rf_matrix_id AND vendor.name = "' + str(vendor_name) + '"')
	elif vendor_tag: return sql.getSQLite('SELECT DISTINCT vendor.*, pre_config_vendor.rf_matrix_output_port, pre_config_vendor.mxa_id, pre_config_vendor.lsu_id, pre_config_vendor.aggr_id, rf_matrix_db.jfw_id, rf_matrix_db.jfw_port, rf_matrix_db.CELLID FROM vendor , pre_config_vendor, rf_matrix_db INNER JOIN vendor pre_config_vendor ON pre_config_vendor.vendor_id = vendor.id AND rf_matrix_db.port = pre_config_vendor.rf_matrix_output_port AND rf_matrix_db.rf_matrix_id = vendor.rf_matrix_id AND pre_config_vendor.tag LIKE "%' + str(vendor_tag) + '%"')
	else: return sql.getSQLite('SELECT DISTINCT vendor.*, pre_config_vendor.rf_matrix_output_port, pre_config_vendor.mxa_id, pre_config_vendor.lsu_id, pre_config_vendor.aggr_id, rf_matrix_db.jfw_id, rf_matrix_db.jfw_port, rf_matrix_db.CELLID FROM vendor , pre_config_vendor, rf_matrix_db INNER JOIN vendor pre_config_vendor ON pre_config_vendor.vendor_id = vendor.id AND rf_matrix_db.port = pre_config_vendor.rf_matrix_output_port AND rf_matrix_db.rf_matrix_id = vendor.rf_matrix_id')



## \brief configure the vendor connection and LSU cell using database records
#
# Given a json object of vendors loading from SQLite databse
# Configure the vendors connection and LSU cells by the json information
# All involved devices will be marked in_use = 1 and prevent from use
# mxa will be released to in_use = 0 once the configuration is done
#
# \param json The json object loaded from SQLite databse containing vendors information
# \param use_rest A flag for configuring LSU cell using REST API or document copy
# \param daemon Print out info message if set False, default is False
# \return in_use_vendor a list of id (integers) of SQLite vendors, used for recording vendor usage
##
def vendorConfig(json, use_rest = True, daemon = False):
	if not daemon: utility.info("################## " + Fore.YELLOW + "Vendor Configuration" + Style.RESET_ALL + " ################")
	in_use_vendors = []
	in_use_cells = {}
	balance_check = {}
	for vendor in json:
		if 'name' in vendor: utility.NOTICE(result = 'Start config [' +  vendor['name'] + ']')
		## atten adjust value
		atten = 3
		try:
			## If the vendor is not loaded from sql
			## TODO regular the web user input with the database
			if 'name' not in vendor and 'freq' not in vendor:
				cell_id = ''.join(filter(lambda char: char.isdigit(), vendor))
				if str(json[vendor]).isdigit(): vendor = loadSQLite(vendor_id = int(json[vendor]))[0]
				else: vendor = loadSQLite(vendor_name = json[vendor])[0]
				vendor['cell_id'] = int(cell_id)

			## Load the RF Matrix, JFW, and MXA information based on vendor configuration
			loadVendorConfig(vendor)
			## Read the LSU in use cells
			lsu_busy_vendors = lsu.getBusyCells()
			in_use_cells[str(vendor['lsu_id'])] = lsu_busy_vendors['tdd'].append(lsu_busy_vendors['fdd'])
			## Wait for devices ready
			waitBusy(vendor, 10, daemon) ## NOTE change this timeout time for waiting for device ready
			## setBusy('vendor', 'id=' + str(vendor['id'])) ## NOTE No longer need to check vendor availability
			if 'id' in vendor: in_use_vendors.append(vendor['id'])
			## Config MXA
			configMXA(vendor)
			## Reading MXA result and adjust JFW
			mxaResult = examMXAadjustJFW(vendor, atten)
			## Release the MXA and vendor for next test
			setBusy('mxa', 'id=' + str(mxa.ID), 0)
			## set the adjustAtten for each vendor
			vendor['adjustAtten'] = mxaResult['adjustAtten']
			## Balance check the radio power if have the same name
			balance_check = __radioBalanceCheck(vendor, balance_check = balance_check, daemon = daemon)

		except Exception as e:
			utility.error(str(e))
			setBusy('mxa', 'id=' + str(mxa.ID), 0)
			return {}

	# Configure cells
	__cellConfig(json, use_rest = use_rest, daemon = daemon)
	# Check cells are syhnc
	__cellSignalCheck(json, daemon = daemon)
	utility.SUMMARY()
	return {'in_use_vendors': in_use_vendors, 'in_use_cells': in_use_cells}



## \brief Configure the LSU cell
#
# Private function, invoke by vendorConfig function
# Given a json object of vendors loaded from SQLite database
# Configure the LSU cells based on the vendor information in json
#
# \param json The json object loaded from SQLite database containing vendors' information
# \param use_rest Bool value for calling lsu.cellConfig if use rest API or not
# \param daemon Print out the info message if set False, default is False
# \return True if configuration success, else raise exception
##
def __cellConfig(json, use_rest = True, daemon = False):
	for vendor in json:
		loadVendorConfig(vendor)
		## Config SDR
		## Deprecated, nolonger using cell configuration table ##################################################################
		if "cell_id" in vendor and vendor['cell_id']: lsu.cellConfig(vendor['lsu_id'], cid = vendor['cell_id'], rest = use_rest)
		#########################################################################################################################

		else:
			vendor['cell_id'] = vendor['CELLID']
			if "PORTMASK" not in vendor:
				if (int(vendor['CELLID']) % 2): vendor['PORTMASK'] = 3
				else: vendor['PORTMASK'] = 12
			if not lsu.cellConfig(vendor['lsu_id'], cell_conf = vendor, rest = use_rest): raise Exception("[LSU] Cell [" + str(vendor['CELLID']) + "] Configuration Failed!")

		## switch rf matrix port
		if 'adjustAtten' in vendor:
			if 'QRB' not in rf_matrix.NAME: rf_matrix.connectRFMatrix('\x30', str(vendor['rf_matrix_input_port']), str(vendor['rf_matrix_output_port']), daemon = daemon, atten = vendor['adjustAtten'])
			else: rf_matrix.connectRFMatrix(['SA' + rf_matrix.getQRBPort(vendor['rf_matrix_input_port']) + 'B' + rf_matrix.getQRBPort(vendor['rf_matrix_output_port']) + rf_matrix.roundQRBAttenuation(vendor['adjustAtten'])], daemon = daemon)
	return True



## \brief Check the LSU cell decode signal
#
# Private function, invoke by vendorConfig function
# Given a json object of vendors loaded from SQLite database
# Check if the vendors are being decoded on LSU cell
# Adjust the attenuation if signal is not close to the optimal rsrp level
# Raise the exception if LSU cell is not be able to decode the signal
#
# \param json The json object loaded from SQLite database containing vendors' information
# \param daemon Print out the info message if set False, default is False
##
def __cellSignalCheck(json, daemon = False):
	for vendor in json:
		loadVendorConfig(vendor)
		## Check LSU RSRP and adjust attenuation
		rsrp_retry_count = 10
		while rsrp_retry_count > 0:
			cell_rsrp = lsu.getCellRSRP()
			if str(vendor['cell_id']) in cell_rsrp:
				if not daemon: utility.info('a0Rsrp:' + str(cell_rsrp[str(vendor['cell_id'])]['a0Rsrp']) + ' a1Rsrp:' + str(cell_rsrp[str(vendor['cell_id'])]['a1Rsrp']))
				delta = 50 + (float(cell_rsrp[str(vendor['cell_id'])]['a0Rsrp']) + float(cell_rsrp[str(vendor['cell_id'])]['a1Rsrp'])) / 2.0
				if not daemon: utility.info("adj: " + str(vendor['adjustAtten']) + "    delta: " + str(delta))
				if abs(delta) > 3.0:
					adjAtten = vendor['adjustAtten'] + delta if (vendor['adjustAtten'] + delta) > 0 else 0
					if 'QRB' not in rf_matrix.NAME: jfw.connectJFW('SAR' + str(vendor['jfw_port']) + ' ' + str(int(adjAtten)), 2, daemon)
					else: rf_matrix.connectRFMatrix(['SA' + rf_matrix.getQRBPort(vendor['rf_matrix_input_port']) + 'B' + rf_matrix.getQRBPort(vendor['rf_matrix_output_port']) + rf_matrix.roundQRBAttenuation(adjAtten)], daemon = daemon)
				rsrp_retry_count = 0;
			else:
				if rsrp_retry_count == 1:
					setBusy('mxa', 'id=' + str(mxa.ID), 0)
					utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] LSU signal decode')
					raise Exception('LSU not be able to decode cell [' + str(vendor['cell_id']) + ']')
				utility.sleep(60, True)
				rsrp_retry_count -= 1

		if 'name' in vendor: utility.info('### Vendor ' + vendor['name'] + ' Pre-Configuration Finished ###')
		else: utility.info('### Vendor Pre-Configuration Finished ###')
		utility.PASS(result = 'Vendor ID [' + str(vendor['id']) + '] Pre-configuration')



## \brief check if the radio is balanced
#
# After analysis the vendor using MXA, check if the radio is balanced on both cable
# A balance_check dictionary is recording all tested radio
#
# \param vendor The vendor object loaded from SQLite and examed by MXA
# \param balance_check Dictionary object recording all tested vendors, default is empty
# \param daemon Print out the info message is set False, default is False
# \return balance_check Return the updated balance_check dictionary
##
def __radioBalanceCheck(vendor, balance_check = {}, daemon = False):
	if 'name' in vendor:
		if vendor['name'] in balance_check:
			if abs(vendor['adjustAtten'] - balance_check[vendor['name']]) > 3:
				utility.error('Radio balancing check failed!\nThe vendor ' + vendor['name'] + ' has [' + str(abs(vendor['adjustAtten'] - balance_check[vendor['name']])) + '] db difference!', False)
				setBusy('mxa', 'id=' + str(mxa.ID), 0)
				utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] Balance Check')
				raise Exception('Radio balancing check failure!')
			else:
				utility.PASS(result = 'Vendor ID [' + str(vendor['id']) + '] Balance Check')
				utility.info('Radio balancing check passed...')
		else:
			balance_check[vendor['name']] = vendor['adjustAtten']
		return balance_check



## \brief exam MXA and adjust JFW to match the RS Power
#
# exam the current MXA EVM result to get the RS Power, based on delta value between
# expected RS Poswer and EVM examed RS Power to adjust JFW
#
# \param vendor the current examing vendor loaded from SQLIte vendor table
# \param atten the attenuation from cabling to be added to system
# \param daemon Print out info message if set False, default is False
# \param noexception If set False, return the result with 'Fail' key and reason, no exception thrown
# \return result The MXA analysis result
##
def examMXAadjustJFW(vendor, atten = 3, daemon = False, noexception = False):
	if DAEMON: noexception = True
	## set safty atten on jfw
	if 'atten' not in vendor: vendor['atten'] = 15
	## TODO TODO TODO reset MXA connection
	if 'QRB' not in rf_matrix.NAME:
		## Set safe attenuation on JFW
		jfw.connectJFW('SAR' + str(mxa.JFW_PORT) + ' ' + str(vendor['atten']))

		## switch RBM Rf Matrix port
		rf_matrix.connectRFMatrix('\x30', str(vendor['rf_matrix_input_port']), str(mxa.MXA_PORT), atten = vendor['atten'])

		## Disconnect QRB
		## TODO TODO TODO when sharing database, MXA port on RF Matrix is different on QRB and RBM
		## 1. change database -> add QRB_mxa_port and RBM_mxa_port
		## 2. load all MXA data from database with the same name
		## NOTE will need to add a MXA handler to reset all MXA port instead of on a single QRB or RBM
		rf_matrix.resetQRBAtten(portB = 32, daemon = daemon) ## NOTE FIX the contant portB here
	else:
		## Disconnect RBM
		jfw.connectJFW('SAR' + str(mxa.JFW_PORT) + ' 127')

		## Reset QRB
		rf_matrix.resetQRBAtten(portB = mxa.MXA_PORT, daemon = daemon)

		## switch QRB RF Matrix port and set safe attenuation
		rf_matrix.connectRFMatrix(['SA' + rf_matrix.getQRBPort(vendor['rf_matrix_input_port']) + 'B' + rf_matrix.getQRBPort(mxa.MXA_PORT) + "015.0"], daemon = daemon)

	## read mxa result
	result = mxa.getEVMResult(3, daemon)
	if result:
		if result['EVM_AVG'] > 5000.0:
			utility.error("NO SYNC FOUND! Bad EVM read: [" + str(result['EVM_AVG']) + "]", False)
			result['type'] = 'Unknown'
			setBusy('mxa', 'id=' + str(mxa.ID), 0)
			if not noexception:
				utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] NO SYNC')
				raise Exception('NO SYNC FOUND')
			else:
				result['Fail'] = 'NO SYNC FOUND'
				utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] NO SYNC')
				result['adjustAtten'] = 0
				return result
		## Find primary and secondary
		## Check if PCI is correct
		if result['PCI'] < 0 or result['EVM_AVG'] > 300:
			if mxa.getSyncType() == 'RS':
				utility.pp(mxa.getMXAResult())
				result['type'] = 'Unknown'
				setBusy('mxa', 'id=' + str(mxa.ID), 0)
				if not noexception:
					utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] NO SYNC')
					raise Exception("NO SYNC FOUND")
				else:
					result['Fail'] = 'NO SYNC FOUND'
					utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] NO SYNC')
					result['adjustAtten'] = 0
					return result
			else:
				utility.warn('Not be able to decode signal. Testing if signal is a secondary port', False)
			## set the MXA mode to secondary port
			mxa.setSyncType('RS')
			mxa.setCID(vendor['pci'])
			mxa.setNumOfCRSPorts(2)
			mxa.setRefCRSPort(1)
			result = examMXAadjustJFW(vendor, atten = atten, daemon = daemon, noexception = noexception)
			if result['type'] == 'Primary': result['type'] = 'Secondary'
			return result
		## Adjust atten value
		if result['EVM_AVG'] > 0:
			if (result['PCI'] != vendor['pci']):
				utility.warn('PCI read [' + str(result['PCI']) + '] is different from database record [' + str(vendor['pci']) + ']\nEvm raead: ' + str(result['EVM_AVG']) + '\nUpdate Database with new PCI [' + str(result['PCI']) + ']', False)
				sql.updateSQLite('vendor', 'pci', result['PCI'], query = 'name="' + str(vendor['name']) + '"')
				result['Fail'] = 'PCI Changed! Read [' + str(result['PCI']) + '] record [' + str(vendor['pci']) + ']'
			result['type'] = 'Primary'
			delta = float(float(vendor['exp_atten']) - atten) + result['RSPW_AVG']
			if not daemon: utility.info('\nExpected dB power: -' + str(vendor['exp_atten']) + '\nActual dB power: ' + str(result['RSPW_AVG']) + '\nDelta Attenuator dB (cable): -' + str(atten) + '\nDifference: ' + str(delta))
			## adjust JFW to reduce delta value
			if abs(delta) > 1:
				if -5 <= (float(vendor['atten']) + delta) <= 0:
					utility.warn("Slightly exceeding attenuation minimum value!\nExceed attenuation value: " + str(int(float(vendor['atten']) + delta)) + "\nSet attenuation to [0]", False)
					vendor['atten'] = 0
				elif (float(vendor['atten']) + delta) < -5:
					utility.error("Exceeding attenuation minimum value!\nExceed attenuation value: " + str(int(float(vendor['atten']) + delta)) + "\nSet Attenuation to 0", False)
					utility.info("Release the MXA...", False)
					setBusy('mxa', 'id=' + str(mxa.ID), 0)
					vendor['atten'] = 0
					result['adjustAtten'] = float(vendor['atten'])
					utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] Exceed minimum Atten')
					result['Fail'] = 'Exceed Minimum Attenuation [' + str(int(float(vendor['atten']) + delta)) + '] dbm'
					return result
					'''
					if not noexception:
						utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] Exceed minimum Atten')
						raise Exception('Exceed Minimum Attenuation [' + str(int(float(vendor['atten']) + delta)) + '] dbm')
					else:
						utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] Exceed minimum Atten')
						result['Fail'] = 'Exceed Minimum Attenuation [' + str(int(float(vendor['atten']) + delta)) + '] dbm'
						return result
					'''
				else:
					vendor['atten'] = float(vendor['atten']) + delta
				## Removed due to DB change - if 'id' in vendor: sql.updateSQLite('vendor', 'atten', int(ajatten), 'id=' + str(vendor['id']), None, daemon)
				if 'jfw_port' in vendor and vendor['jfw_port']: jfw.connectJFW('SAR' + str(vendor['jfw_port']) + ' ' + str(vendor['atten']), 2, daemon)
				result['adjustAtten'] = float(vendor['atten'])
				return result
			else:
				if 'jfw_port' in vendor and vendor['jfw_port']: jfw.connectJFW('SAR' + str(vendor['jfw_port']) + ' ' + str(vendor['atten']), 2, daemon)
				result['adjustAtten'] = float(vendor['atten'])
				return result
		else:
			utility.error("MXA result read failure! Exam MXA failed!", False)
			if 'jfw_port' in vendor and vendor['jfw_port']: jfw.connectJFW('SAR' + str(vendor['jfw_port']) + ' ' + str(127))
			setBusy('mxa', 'id=' + str(mxa.ID), 0)
			if not noexception:
				utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] MXA NO SYNC')
				raise Exception('MXA failed to read any result')
			else:
				utility.FAIL(result = 'Vendor ID [' + str(vendor['id']) + '] MXA NO SYNC')
				result['Fail'] = 'MXA failed to read any result'
				return result



## \brief configure the MXA to match and decode the eNB resouce
#
# Configura the MXA based on the vendor load from SQLite table 'vendor'
# Config the Mode
# Config the Center Frequency
# Config the Cell ID
# Config the Attenuator Range
# Config the Sync Type
#
# \param vendor Load from SQLite 'vendor' table
# \param daemon Print out info message if set False, dafault value is false
##
def configMXA(vendor, daemon = False):
	mode = {'FDD': 'LTE', 'fdd': 'LTE', 'Fdd': 'LTE',
			'TDD': 'LTETDD', 'tdd': 'LTETDD', 'Tdd': 'LTETDD'}
	## config mxa
	if not daemon: utility.info("##################### " + Fore.YELLOW + "MXA Control" + Style.RESET_ALL + " ######################")
	## mxa.setMode(mode[vendor['tech']])
	if mode[vendor['tech']] == 'LTE': mxa.recall(3) ## mxa.setMode(mode[vendor['tech']])
	else: mxa.recall(1)
	mxa.setFrequency(vendor['freq'])
	mxa.setRang(0)
	mxa.setSyncType('PSS')
	## if not vendor['pci']: mxa.setCID('AUTO') ## Updated always using AUTO the first time running exam
	## else: mxa.setCID(vendor['pci'])
	mxa.setCID('AUTO')
	utility.PASS(result = 'MXA [' + str(mxa.ID) + '] Configuration')



## \brief load the vendor configuration for JFW, RF Matrix, and MXA
#
# Load the vendor information form SQLite 'vendor' table and
# based on vendor id load the JFW, RF Matrix, and MXA information
#
# \param vendor load from SQLite 'vendor' table
##
def loadVendorConfig(vendor):
	## Load the SQLite databse
	global sqlite_file
	if 'lsu_id' in vendor and vendor['lsu_id']: lsu.loadSQLite(str(vendor['lsu_id']), sqlite_file)
	if 'jfw_id' in vendor and vendor['jfw_id']: jfw.loadSQLite(str(vendor['jfw_id']), sqlite_file)
	if 'rf_matrix_id' in vendor and vendor['rf_matrix_id']: rf_matrix.loadSQLite(str(vendor['rf_matrix_id']), sqlite_file)
	if 'mxa_id' in vendor and vendor['mxa_id']: mxa.loadSQLite(str(vendor['mxa_id']), sqlite_file)



## \brief Checking the SQLite status of MXA and eNB resource. Waiting for resource to be freed for use
#
# Load the vendor information from SQLite 'vendor' table
# Based on the vendor info, check the eNB and MXA if are not in use
# Wait for 1 minute (default) otherwise timeout and raise an exception
# The waiting is mainly for waiting MXA to be freed
#
# \param vendor load from SQLite 'vendor' table
# \param counter each counter will check both vendor(eNB) resource and MXA availiabilty and wait for 5 seconds if in use
# \daemon print info message if set False, default value is False
##
def waitBusy(vendor, counter = 30, daemon = False):
	## wait for mxa and eNB to be available
	while (True):
		if 'id' in vendor:
			busyVendors = lsu.getBusyVendors(lsu.getBusyCells())
			if 0 == checkBusy(sql.getSQLite('SELECT * FROM mxa WHERE id=' + str(vendor['mxa_id']))[0], daemon) + checkBusy(sql.getSQLite('SELECT * FROM vendor WHERE id=' + str(vendor['id']))[0], daemon) and vendor['id'] not in busyVendors:
				## Set both MXA and eNB resource busy, block from other users
				setBusy('mxa', 'id=' + str(mxa.ID))
				utility.PASS(result = 'Resource dependency check')
				break
		else:
			if 0 == checkBusy(sql.getSQLite('SELECT * FROM mxa WHERE id=' + str(vendor['mxa_id']))[0], daemon):
				## Set both MXA and eNB resource busy, block from other users
				setBusy('mxa', 'id=' + str(mxa.ID))
				utility.PASS(result = 'Resource dependency check')
				break
		utility.sleep(60, True)
		counter -= 1
		if counter == 0:
			utility.FAIL(result = 'Resource dependency check')
			raise Exception('Execution Timeout [' + str(counter * 60) + '] seconds! Resource not available!')



## \brief Check if the in_use column is set in SQLite
#
# The device parameter is mainly for:
# vendor table
# mxa table
#
# \param device the json object loaded from SQLite table
# \deamon print info message if set False, default value is False
# \return device['in_use'] which is 0 (not use) or 1 (in use)
##
def checkBusy(device, daemon = False):
	if int(device['in_use']):
		if not daemon: utility.warn('Device [' + str(device['name']) + '] in use', False)
		## Do something else if in use
	return int(device['in_use'])



## \brief Trigger the Jenkins job with the given name
#
# login into the Jenkins <localhost> server with <username> and <password>
# trigger the Jenkins job <name>
#
# \param name The string name of the Jenkins job to be triggered
# \param localhost The ip address and port number of the Jenkins server, example: "http://localhost:8080"
# \param username The username for login into jenkins
# \param password The password for login into jenkins
##
def triggerJenkins(name = '_PE_LTE_test', localhost = 'http://localhost:8080', username = 'sprint', password = 'sprint@123', daemon = False):
	if not daemon: utility.info("################### " + Fore.YELLOW + "Jenkins Control" + Style.RESET_ALL + " ####################")
	server = jenkins.Jenkins(localhost, username, password)
	if not daemon: utility.info('Trigger Jenkins job: [' + name + ']')
	server.build_job(name)



## \brief Create a new Jenkins job with given xml configuration
#
# login into <localhost> with <username> and <password>
# create a new Jenkins job with name <job_name>
#
# \param job_name The string name of the new Jenkins job
# \param xml_confg The string of a Jenkins XML configuration file content
# \param localhost The ip address and port number of the Jenkins server, example: "http://localhost:8080"
# \param username The username for login into jenkins
# \param password The password for login into jenkins
##
def createJenkinsJob(job_name = '_PE_test', xml_config = '', localhost = "http://localhost:8080", username = "sprint", password = "sprint@123", daemon = False):
	if not daemon: utility.info("################### " + Fore.YELLOW + "Jenkins Control" + Style.RESET_ALL + " ####################")
	server = jenkins.Jenkins(localhost, username, password)
	server.create_job(job_name, xml_config)



## \brief set the in_use value in the SQLite table
#
# Set the in_use value with given value
# This function is mainly for setting
#     vendor
#     mxa
# tables to mark in use (1) or not use (0)
# Using parameter query to filter the rows
#
# \param table the table name in the SQLite database
# \param query the query to filter the rows, for example 'id=1', set None to set all rows NOTE with caution
# \param in_use the value for in_use column, default is 1 (in use), set 0 (not use)
# \db_path default value is None to use the configured db path, can set a path to apply changes to a certain SQLite db
##
def setBusy(table, query, in_use = 1, db_path = None):
	sql.updateSQLite(table, 'in_use', in_use, query, db_path, True)



## \brief system signal handler
#
# Capture the user keyboard interrupt signal (Ctrl + C)
# reset the current mxa (set in_use to 0) and then exit the program
##
def signal_handler(sig, frame):
	utility.info('Captured keyboard interrupt.\nSafe exiting the process:')
	utility.info('Reset MXA...')
	setBusy('mxa', 'id=' + str(mxa.ID), 0)
	exit(1)



## TODO TODO TODO
#
# Report generator, build the report based on the vendor_config test step results
#
def report_generator():
	return



## \brief Main function for provide the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./jfw.py -h or --help for instructions
##
def main():
	global sqlite_file, DAEMON
	signal.signal(signal.SIGINT, signal_handler) ## register the signal handler
	parser = argparse.ArgumentParser(description='Tools for sprint test pre-configuration')
	parser.add_argument('-s', '--sql', metavar='File_Path', help='Load the SQLite database path instead of configuration json file')
	parser.add_argument('-i', '--id', metavar='Vendor_ID#', type=int, help='The id number of the Vendors in SQLite database')
	parser.add_argument('-n', '--name', metavar='Vendor_Name', help='The name of the vendor device in SQLite database')
	parser.add_argument('-t', '--tag', metavar='Vendor_Tag', help='The tag of the vendor device in SQLite database')
	parser.add_argument('-j', '--jenkins', metavar='Job_Name', help='The Jenkins tool option, the input Jenkins job will be triggerred')
	parser.add_argument('-D', '--daemon', dest='DAEMON', action='store_true', help='Execute all commands without throwing any exceptions')
	args = parser.parse_args()
	if len(sys.argv) < 2: parser.print_help()
	if args.sql and args.sql is not 'None' or 'none' or 'default' or 'Default' or 'null': sqlite_file = args.sql
	if args.DAEMON: DAEMON = True
	if args.id: vendorConfig(loadSQLite(vendor_id = args.id, db_path = sqlite_file))
	elif args.name: vendorConfig(loadSQLite(vendor_name = args.name, db_path = sqlite_file))
	elif args.tag: vendorConfig(loadSQLite(vendor_tag = args.tag, db_path = sqlite_file))
	else: vendorConfig(loadSQLite(db_path = sqlite_file))
	## TODO Add an entry for reading Jenkins input
	# utility.regexParser(args.name, '.*({.*}).*', True)
	if args.jenkins: triggerJenkins(name = args.jenkins)



## \brief Global Configuration for vendor configuration
#
# \param sqlite_file the SQLite database path using globally
##
########################### Global Configuration ########################
DAEMON = False                                          # Default Value #
sqlite_file = 'simple.sqlite'                           # Default Value #
#########################################################################


## \brief Load the default configuration from SAuto framework
try:
	with open('/var/www/html/sauto/rootpath.conf', 'r') as conf_file:
		path = conf_file.read()
		if path: loadConfig(path + '/this_device_conf.json')
		else: loadConfig()
except Exception as e:
	utility.error(str(e), True)


## \brief give the entry for main when execute from command line
if __name__ == "__main__":
	main()
