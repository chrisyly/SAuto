#!/usr/bin/python3

## \file lsu.py
# \brief Modules as well as CLI tools for remote lsu control
#
# This modules contains the library for remote controling the LSU by REST request
# and it is also a stand alone command line tool
# The library has to work with a proper configuration file in order to
# have the ip address for the remote devices
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import sql
import pylsuweb
import json
import utility
import argparse
import sys
from colorama import Fore
from colorama import Style


## \brief DL band convert talble
__DL_BW_CONVERTER = {'1.4': 6,
	'3': 15,
	'5': 25,
	'10': 50,
	'15': 75,
	'20': 100}


## \brief Load the device configuration from the given config file path
#
# If the the config file path is not given, the program will tend to
# use the default path.   The config file is a json file, loadConfig is
# looking for the key 'LSU' and get TCP IP address for the remote RF_Matrix.
# If key is not found, a default value will be loaded
# NOTE: This function can be call explictly to load user configurations
#
# \param confPath a string value contain the path to the json file
##
def loadConfig(confPath = 'this_device_conf.json'):
	global TCP_IP, sqlite_file
	config = utility.loadConfig(confPath)
	if 'error' not in config:
		if 'TCP_IP' in config['LSU']: TCP_IP = config['LSU']['TCP_IP']
		if 'SQLITE' in config: sqlite_file = config['SQLITE']['Master']



## \brief Load the lsu configuration from the given SQLite file path
#
# If the SQLite file path is not give, default SQLite data path will be load
# if the data (ip) in the database is not set, the program will use
# the default value instead
# NOTE: This function can be called explictly to load configuration
#
# \param lid the id for a perticular JFW device in SQLite database
# \param db_path the path of the SQLite database file
##
def loadSQLite(lid, db_path = None, daemon = False):
	global TCP_IP, sqlite_file
	if db_path:
		sql.setDBPath(db_path, daemon)
	else:
		sql.setDBPath(sqlite_file, daemon)
	config = sql.getSQLite('SELECT * FROM lsu WHERE id=' + str(lid), db_path)
	if config:
		if config[0]['ip'] is not None:
			TCP_IP = config[0]['ip']



## \brief Build the RESTful API URL
#
# Concatnate the LSU IP address with the RESTful API address path
#
# \param tail The RESTful API address path
# \return TCP_IP+tail the complete URL for the RESTful API
##
def getURL(tail='/lte/status'):
	return TCP_IP + tail



## \brief Send GET request to the remote LSU
#
# Send the GET request to the remote LSU and return the json string
#
# \param url URL of the remote LSU REST service
# \return utility.getRequest() JSON string of response of the RESET service
##
def connectLSU(url):
	if not url:
		url = getURL()
	return utility.getRequest(url)



## \brief Config the remote LSU cell configure file
#
# Create a config file based on given lsu ID and Cell ID in the SQLite database
# Move the remote LSU configure file (if exist) to tmp folder
# Scp the new config file into the cell configuration folder
#
# Dependency Cell timeout: 2 Hours
#
# \param lid LSU id for retreving LSU information from SQLite database lsu table
# \param cid Cell id for retreving CELL information from SQLite database lte_cell table
# \param cell_conf The Json configuration of the cell
# \param rest REST flag, using REST API to config cell instead of file copying
# \param daemon flag, print out info message if set False, default value is False
##
def cellConfig(lid, cid = None, cell_conf = None, rest = True, skipValidation = False, daemon = False):
	## config Cell based on which LSU (lid), using which pre_set cell configuration id (cid - this is a SQLite table id)
	if not daemon: utility.info("##################### " + Fore.YELLOW + "Config SDR Cell" + Style.RESET_ALL + " ######################")
	lsu_ip = sql.getSQLite('SELECT * FROM lsu WHERE id=' + str(lid))[0]['ip']
	lsu_cell = cell_conf
	## Deprecated - No longer using lte_cell table from SQLite database ###############
	if cid: lsu_cell = sql.getSQLite('SELECT * FROM lte_cell WHERE id=' + str(cid))[0]
	###################################################################################
	else: cid = int(lsu_cell['CELLID'])

	## Verify the cell configuration before configure the cell, skip the cell configuration if
	## 1. [skipValidation] set True
	## 2. [skipValidation] is False and cell is not configured as [lsu_cell]
	if (not skipValidation) and validCell(cell_conf = lsu_cell, daemon = True):
		if not daemon: utility.info("Cell already configured. Skip cell configuration.")
		return True

	## cell dependency check and waiting for dependent cell to finish
	lsu_busy_vendors = getBusyCells(daemon = True)
	in_use_cells = lsu_busy_vendors['tdd'].append(lsu_busy_vendors['fdd'])
	dependent_cell = -1
	if cid % 2: dependent_cell = cid + 1
	else: dependent_cell = cid - 1
	if in_use_cells and ((dependent_cell in in_use_cells) or (cid in in_use_cells)):
		## Timeout value for dependency cell
		timeout = 120
		while True:
			if not daemon:
				utility.info('Dependent Cell [' + str(dependent_cell) + '] is currently in use, check back in 60 seconds...')
				utility.sleep(60, True)
				timeout -= 1
				if timeout < 0:
					utility.warn('TIMEOUT! Dependent Cell [' + str(dependent_cell) + '] is not available!')
					raise Exception('[LSU] Cell Configuration Timeout! The dependent cell [' + str(dependent_cell) + '] is not available!')
					exit(1)
				else:
					lsu_busy_vendors = getBusyCells(daemon = True)
					in_use_cells = lsu_busy_vendors['tdd'].append(lsu_busy_vendors['fdd'])
					if dependent_cell not in in_use_cells:
						break

	## If <rest> is False (default is True), using scp to replace the cell configuration file on remote LSU
	if not rest:
		conf_path = createConfig(lsu_cell)
		cell_id = utility.regexParser(conf_path, '.*ue\.(..).*')
		utility.systemcall('sshpass -p user ssh user@' + lsu_ip + ' \'mv /res/sdr/cfg/ppu.0-' + str(int(cell_id)) + '/lte* /tmp/\'')
		utility.sleep(2, daemon)
		utility.systemcall('sshpass -p user scp /tmp/' + conf_path + ' user@' + lsu_ip + ':/tmp/')
		utility.sleep(10, daemon)
		utility.systemcall('sshpass -p user ssh user@' + lsu_ip + ' \'mv /tmp/' + conf_path + ' /res/sdr/cfg/ppu.0-' + str(int(cell_id)) + '/\'')
		utility.sleep(10, daemon)
	## If <rest> is True (default is True), using the LSU REST API to delete and create the cell configuration file on remote LSU
	else:
		conf_dict = createRestConfig(lsu_cell)
		conf_dict['dlBw'] += 'Mhz'
		if not daemon: utility.info('Deleting Cell [' + str(conf_dict['cellNumber']) + ']')
		pylsuweb.lte_cell(lsu_ip, 'DELETE', '', 'user', 'user', **conf_dict)
		utility.sleep(10, daemon)
		if not daemon: utility.info('Create Cell [' + str(conf_dict['cellNumber']) + ']')
		pylsuweb.lte_cell(lsu_ip, 'POST', '', 'user', 'user', **conf_dict)
		utility.sleep(10, daemon)

	## valid if cell configuration is successful
	if validCell(cell_conf = lsu_cell):
		if not daemon: utility.info("Cell Configuration Succeed!")
		return True
	else:
		utility.error("Cell Configuration Failed!")
		## raise Exception("[LSU] Cell [" + str(conf_dict['cellNumber']) + "] Configuration Failed!")
		return False



## \brief Check the cell configuration is matching the cell to be configured
#
# if cid is givem, load the cell configuration with the cid number
# else using the cell_conf
#
# \param cid Cell id for retreving CELL information from SQLite database lte_cell table
# \param cell_conf The Json configuration of the cell
# \param current_cell The current cell json (or dictionary) object, if not defined, load the current cell from the targeting cell id
# \param daemon Print out the info message if set False, default value is False
#
# \return True if the current cell is matching the cell_conf or cid, else False
##
def validCell(cid = None, cell_conf = None, current_cell = None, daemon = False):
	lsu_cell = cell_conf
	if cid: lsu_cell = sql.getSQLite('SELECT * FROM lte_cell WHERE id=' + str(cid))[0]
	if not current_cell: current_cell = getCellConfig(lsu_cell['CELLID'], True)
	## Check if the current cell is matching the cell configuration
	if current_cell and int(current_cell['dlearfcn']) == int(lsu_cell['DLEARFCN']) and int(current_cell['ulearfcn']) == int(lsu_cell['ULEARFCN']) and str(lsu_cell['BW']) + 'Mhz' == str(current_cell['dlBw']) and int(current_cell['aggrId']) == int(lsu_cell['aggr_id']):
		if not daemon: utility.info("Cell is configured.")
		return True
	else:
		if not daemon: utility.info("Cell is NOT configured!")
		utility.pp(lsu_cell)
		utility.pp(current_cell)
		return False



## \brief Read the lsu /lte/status response and report any busy cell
#
# Send LSU check lte status GET request and report any busy cell
#
# \param json The json response from remote LSU /lte/status GET request
# \param daemon print out info message if set False, default value is False
# \return result A dictionary of fdd and tdd busy cells
##
def getBusyCells(json = None, daemon = False):
	if not json: json = utility.getRequest(getURL('/lte/status'), True)
	if not daemon: utility.info("###################### " + Fore.YELLOW + "LSU Control" + Style.RESET_ALL + " #####################")
	if not daemon: utility.info("Updating data from remote LSU [" + TCP_IP + "]...")
	result = {'fdd':[], 'tdd':[]}
	for fdd in json['fddCellStatus']:
		if fdd['genericProperties']['bindName'] != "":
			if not daemon: utility.info('FDD Cell [' + str(fdd['genericProperties']['cellNumber']) + '] is currently running by user [' + fdd['genericProperties']['bindName'] + ']')
			result['fdd'].append(fdd['genericProperties']['cellNumber'])
	for tdd in json['tddCellStatus']:
		if tdd['genericProperties']['bindName'] != "":
			if not daemon: utility.info('TDD Cell [' + str(tdd['genericProperties']['cellNumber']) + '] is currently running by user [' + tdd['genericProperties']['bindName'] + ']')
			result['tdd'].append(tdd['genericProperties']['cellNumber'])
	if not daemon: utility.info("Finished updating remote LSU status")
	return result



## \brief Read the given json response from getBusyCells or other resources, return the current in use vendors
#
# Read the given json of busy cells, check the SQL to find the correcsponding in use vendors
#
# \param json The json response contains list of busy cells NOTE lsu id is not checked here, switch LSU by using loadSQLite method
# \param daemon Print out the info message is set False, default value is False
# \return result A list of busy vendor details
##
def getBusyVendors(json = None, daemon = False):
	busyCells = []
	result = []
	if json:
		if (('fdd' in json) or ('tdd' in json)): busyCells = json['fdd'] + json['tdd']
		else: busyCells = json
		vendors = sql.getSQLite('SELECT DISTINCT rf_matrix_db.CELLID, pre_config_vendor.mxa_id, pre_config_vendor.lsu_id, vendor.* FROM rf_matrix_db, pre_config_vendor, vendor INNER JOIN vendor rf_matrix_db ON rf_matrix_db.input_device = vendor.name AND vendor.freq IS NOT NULL AND vendor.pci IS NOT NULL AND vendor.tech IS NOT NULL')
		for vendor in vendors:
			if vendor['CELLID'] in busyCells: result.append(vendor)
		return result
	else:
		if not daemon: utility.info('No busy cells found! Vendors are not deployed on LSU!')
		return result



## \brief Read the given json response from getBusyCells or other resources, return the current NOT in use vendors
#
# Read the given json of busy cells, check the SQL to find the correcsponding NOT in use vendors
#
# \param json The json response contains list of busy cells NOTE lsu id is not checked here, set the LSU id by using loadSQLite method
# \param daemon Print out the info message is set False, default value is False
# \return result A list of free vendor details
##
def getFreeVendors(json = None, daemon = False):
	busyCells = []
	result = []
	if json:
		if (('fdd' in json) or ('tdd' in json)): busyCells = json['fdd'] + json['tdd']
		else: busyCells = json
		vendors = sql.getSQLite('SELECT DISTINCT rf_matrix_db.CELLID, pre_config_vendor.mxa_id, pre_config_vendor.lsu_id, vendor.* FROM rf_matrix_db, pre_config_vendor, vendor INNER JOIN vendor rf_matrix_db ON rf_matrix_db.input_device = vendor.name AND vendor.freq IS NOT NULL AND vendor.pci IS NOT NULL AND vendor.tech IS NOT NULL')
		for vendor in vendors:
			if vendor['CELLID'] not in busyCells:
				is_duplicate = False
				for single_result in result:
					if (single_result['id'] == vendor['id']) and (single_result['rf_matrix_input_port'] == vendor['rf_matrix_input_port']) and (single_result['freq'] == vendor['freq']):
						is_duplicate = True
						break
				if not is_duplicate: result.append(vendor)
		return result
	else:
		if not daemon: utility.info('No busy cells found! Vendors are not deployed on LSU!')
		return result



## \brief Read and return the RSRP value from LSU if signal is being synchronized
#
# if the LSU result (json) is not given, load the current in use LSU
# Read the json result from LSU, if any of RSRP value is none 0.0, return the RSRP value
#
# \param json The json return value from LSU cell status, if not given, load from the current TCP_IP
# \param daemon Print the info message if is False, default value is False
# \return result The RSRP values from current LSU
##
def getCellRSRP(json = None, daemon = False):
	if not json: json = getCellContent(daemon = True)
	result = {}
	for fdd in json['fddCellStatus']:
		a0Rsrp = 0.0
		a1Rsrp = 0.0
		if 'a0Rsrp' in fdd['genericProperties']: a0Rsrp = fdd['genericProperties']['a0Rsrp']
		if 'a1Rsrp' in fdd['genericProperties']: a1Rsrp = fdd['genericProperties']['a1Rsrp']
		if a0Rsrp != 0.0 or a1Rsrp != 0.0: result[str(fdd['genericProperties']['cellNumber'])] = {'a0Rsrp': a0Rsrp, 'a1Rsrp': a1Rsrp}
	for tdd in json['tddCellStatus']:
		a0Rsrp = 0.0
		a1Rsrp = 0.0
		if 'a0Rsrp' in tdd['genericProperties']: a0Rsrp = tdd['genericProperties']['a0Rsrp']
		if 'a1Rsrp' in tdd['genericProperties']: a1Rsrp = tdd['genericProperties']['a1Rsrp']
		if a0Rsrp != 0.0 or a1Rsrp != 0.0: result[str(tdd['genericProperties']['cellNumber'])] = {'a0Rsrp': a0Rsrp, 'a1Rsrp': a1Rsrp}
	return result



## \brief Read the all recorded lsu /lte/status response and report all current cells
#
# Load http IP address from database
# Send LSU check lte status GET request and report all current cells
#
# \param daemon Print out info message if set False, default value is False
# \return lsu_json The dictionary of all current cell information from all LSU
##
def getAllCellContent(daemon = False):
	lsu_json = sql.getSQLite('SELECT * FROM lsu')
	for lsu in lsu_json:
		lsu['info'] = utility.getRequest(('http://' + lsu['ip'] + '/lte/status'), True)
	if not daemon:
		utility.info("Loading cell information from LSU [" + lsu['ip'] + "]")
		utility.pp(lsu_json)
	return lsu_json



## \brief Read the current lsu /lte/status response and report all current ells
#
# Using the current TCP_IP address
# Send LSU check lte status GET request and report all current cells
#
# \param daemon Print out the info message if set False, default value is False
# \return lsu The dictionary of all current cell information
##
def getCellContent(daemon = False):
	lsu = utility.getRequest(getURL('/lte/status'), True)
	if not daemon:
		utility.info("Loading cell information from LSU [" + TCP_IP + "]")
		utility.pp(lsu)
	return lsu



## \brief Read the lsu /lte/cellConfiguration response and report the cell configuration
#
# Send GET request to LSU reading one cell configuration
#
# \param cell_id the integer value of cell ID on the LSU, for example 1,2,3...12
# \param daemon print out the info message if set False, default value is false
##
def getCellConfig(cell_id, daemon = False):
	json = utility.getRequest(getURL('/lte/cellConfiguration?ppu=0-' + str(cell_id) + '&cellNumber=' + str(cell_id)))
	if not daemon: utility.pp(json)
	return json


## \brief Create the LSU cell configuration file
#
# Read the SQLite lte_cell table and generate a LSU cell configuration file
# The configuration file is generate under the /tmp folder with the cell name
#
# \param json The JSON object read from SQLite table lte_cell
# \param daemon Print info message if set False, default is False
# \return conf_file_name the name of the created configuration file
# NOTE: perfer NOT use this to create config file
## Create configuration
def createConfig(json = None, daemon = False):
	conf_file_name = ''
	if json:
		if int(json['CELLID']) < 10: conf_file_name = 'lte' + json['tech'] + '.ue.0' + str(int(json['CELLID'])) + '.01'
		else: conf_file_name = 'lte' + json['tech'] + '.ue.' + str(json['CELLID']) + '.01'
	with open('/tmp/' + conf_file_name, 'w') as config_file: ## Change file name
		if json:
			config_file.write('#\n')
			config_file.write('# OBJECT: LTE CELL ' + str(int(json['CELLID'])) + ' on PPU 0-' + str(int(json['CELLID'])) + '\n')
			config_file.write('#\n\n')
			config_file.write('DL_BW                        = ' + str(__DL_BW_CONVERTER[str(json['BW'])]) + '\n')
			config_file.write('DL_ATTENUATION               = ' + str(0) + '\n')
			config_file.write('ULEARFCN                     = ' + str(json['ULEARFCN']) + '\n')
			config_file.write('DLEARFCN                     = ' + str(json['DLEARFCN']) + '\n')
			config_file.write('UL_TEST                      = ' + str('NO_TEST') + '\n')
			config_file.write('SIBWIN                       = ' + str(0) + '\n')
			config_file.write('TA                           = ' + str(0) + '\n')
			config_file.write('AGGR_ID                      = ' + str(json['aggr_id']) + '\n')
			config_file.write('INTERFERENCE_ID              = ' + str(0) + '\n')
			config_file.write('EPDCCH                       = ' + str(0) + '\n')
			config_file.write('NBIOT                        = ' + str(0) + '\n')
			config_file.write('LOCAL_CELLID                 = ' + str((int(json['CELLID']) - 1) % 2) + '\n')
			config_file.write('PORTMASK                     = ' + str(int(json['PORTMASK'])) + '\n')
			config_file.write('SDR                          = ' + str(int((int(json['CELLID']) - 1) / 2)) + '\n')
			config_file.write('SPLIT_MODE                   = ' + str(0) + '\n')
			config_file.write('DL_RF_GAIN_0                 = ' + str('AUTO') + '\n')
			config_file.write('DL_RF_GAIN_1                 = ' + str('AUTO') + '\n')
			config_file.write('INTFTYPE_SDR00               = ' + str('COMBINE_RX_TX') + '\n')
			config_file.write('FADING_SIM                   = ' + str() + '\n')
			config_file.write('EX_CYCLE_PREFIX              = ' + str(0) + '\n')
			config_file.write('PRACH_CFG                    = ' + str(1) + '\n')
			config_file.write('DOWNLINK_HARQ                = ' + str(0) + '\n')
			config_file.write('VERBOSITY                    = ' + str(0) + '\n')
			config_file.write('DEBUG                        = ' + str(0) + '\n')
			config_file.write('PDCCH_TYPE                   = ' + str(15) + '\n')
			config_file.write('GP_1                         = ' + str(0) + '\n')
			config_file.write('GP_2                         = ' + str(0) + '\n')
			config_file.write('GP_3                         = ' + str(0) + '\n')
			config_file.write('GP_4                         = ' + str(0) + '\n')
			config_file.write('UL_RF_GAIN                   = ' + str('AUTO') + '\n')
			config_file.write('NBIOT_PRBON                  = ' + str(65535) + '\n')
			config_file.write('NBIOT_PRBUP                  = ' + str(65535) + '\n')
		else:
			utility.error('Loading configuration failed!')
			config_file.close()
			raise Exception("[LSU] Creating Cell Configuration file from JSON Failed!")
			exit(1)
		config_file.close()
		if not daemon: utility.info('SDR configuration file generation finished!')
	return conf_file_name



## \brief Create the LSU cell REST API configuration
#
# Read the SQLite lte_cell table and generate a LSU cell configuration for REST API
#
# \param json The JSON object read from SQLite table lte_cell
# \param daemon Print info message if set False, default is False
# \return conf_dict a dictionary for REST API 
## Create configuration
def createRestConfig(json = None, daemon = False):
	conf_dict = {}
	if json:
		conf_dict['type'] = str(json['tech']).upper()
		conf_dict['ppu'] = '0-' + str(json['CELLID'])
		conf_dict['cellNumber'] = int(json['CELLID'])
		conf_dict['dlBw'] = str(json['BW'])
		conf_dict['dlAttenuation'] = 0
		conf_dict['ulearfcn'] = int(json['ULEARFCN'])
		conf_dict['dlearfcn'] = int(json['DLEARFCN'])
		conf_dict['ta'] = 0
		conf_dict['aggrId'] = int(json['aggr_id'])
		conf_dict['interferenceId'] = 0
		conf_dict['epdcch'] = 0
		conf_dict['nbiot'] = 0
		conf_dict['localCellId0'] = True if ((int(json['CELLID']) - 1) % 2 == 0) else False
		conf_dict['localCellId1'] = True if ((int(json['CELLID']) - 1) % 2 == 1) else False
		conf_dict['sdr'] = int((int(json['CELLID']) - 1) / 2)
		conf_dict['splitMode'] = 'RF'
		conf_dict['intfTypeSdr00'] = str('COMBINE_RX_TX')
		conf_dict['fadingSim'] = ''
		conf_dict['exCyclePrefix'] = 0
		conf_dict['prachCfg'] = 1
		conf_dict['downlinkHarq'] = 0
		conf_dict['verbosity'] = 4110417920
		conf_dict['debug'] = 0
		conf_dict['pdcchType'] = 15
		conf_dict['gp1'] = 0
		conf_dict['gp2'] = 0
		conf_dict['gp3'] = 0
		conf_dict['gp4'] = 0
		conf_dict['nbiotPrbdn'] = 65535
		conf_dict['nbiotPrbup'] = 65535
		conf_dict['nbiotUlEarFcn'] = 4294967295
		conf_dict['nbiotDlEarFcn'] = 4294967295
		conf_dict['laa'] = 0
	else:
		utility.error('Loading configuration failed!')
		raise Exception("[LSU] Creating Cell Rest Configuration from JSON Failed!")
		exit(1)
	if not daemon: utility.info('SDR REST configuration generation finished!')
	return conf_dict



## \brief Main function for provide the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:
# ./lsu.py -h or --help for instructions
##
def main():
	global TCP_IP
	parser = argparse.ArgumentParser(description='Tools for monitoring LSU box')
	parser.add_argument('-a', '--address', metavar=('IP_ADDRESS'), help='Set the ip address of remote LSU\n Example: ./lsu.py --address 10.155.208.101')
	parser.add_argument('-b', '--busy', action='store_true', help='Connect to remote LSU and get the current in use cells\n Example: ./lsu.py --address 10.155.208.101 -b    Read the remote LTE in use cell from 10.155.208.101')
	parser.add_argument('-H', '--health', metavar=('Cell_ID'), help='Connect to remote LSU and check the cell status\n Example: ./lsu.py --address 10.155.208.101 -H    Read the remote LTE cell status info from 10.155.208.101')
	parser.add_argument('-g', '--generate', metavar=('Cell_ID'), help='Connect to remote LSU and generate a cell config file based on the <Cell_ID>\n Example: ./lsu.py --generate 1    generate a cell config file for the remote LTE cell')
	parser.add_argument('-i', '--id', metavar=('LSU_ID'), help='Set the remote LSU SQLite id\n Example: .lsu.py --id 1    Set and load the SQLite LSU id=1, default value is 1')
	parser.add_argument('-d', '--daemon', dest='daemon', action='store_true', help='Run the lsu tool as daemon\n Example: ./lsu.py -d --address http://10.155.208.101/lte/status    Read the remote LTE cell info from 10.155.208.101')
	args = parser.parse_args()
	daemon = False
	lid = 1
	if len(sys.argv) < 2: parser.print_help()
	if args.daemon: daemon = args.daemon
	if args.address: TCP_IP = args.address
	if args.id: lid = args.id
	if args.busy: getBusyCells()
	if args.health: getCellConfig(args.health, daemon = daemon)
	if args.generate: cellConfig(lid, cid = args.generate, rest = False, daemon = daemon)



## \brief Shared variables
#
# \param TCP_IP the ip address of the remote device
# \function loadConfig() load the default configuration when loading this module
##
######################### Load Config File ##########################
TCP_IP = 'http://10.155.208.101'                    # Default Value #
sqlite_file = 'simple.sqlite'    # Default Value #
#####################################################################


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
