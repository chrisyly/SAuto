#!/usr/bin/python3

## \file utility.py
# \brief Utility tools for automation
#
# Utility modules contains the library for utility tools for automations
# List of basic tools:
# Print Methods
# REST requests API
# Regular Expression
#
# \author Liyu Ying
# \email liyu.ling@sprint.com
##

from __future__ import print_function
import subprocess
import json
import traceback
import requests
import re
import time
import datetime
import os
import pprint
import sys
import ast
from inspect import getframeinfo,stack
from colorama import Fore,Style,init
init()

###################### Golbal Pass/Fail Counter #########################
passCounter = 0											# Default Value #
failCounter = 0											# Default Value #
summary = []											# Default Value #
#########################################################################

## \brief Print method with colored tag and timestamp for automation
#
# The print methods are used for replacing the python print
# All print methods will print out a colored tag and timestamp when called
# All print methods has an optional argument "track"
#
# \param message the string will be print out to stdout
# \param track a boolean to define weather printing out traceback information, set True to print
##
###################################### Print Methods ########################################
def info(message, track = False):                                                           #
	print (Fore.GREEN + '[INFO]' + Style.RESET_ALL +                                        #
			datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ') + #
			message)                                                                        #
	sys.stdout.flush()                                                                      #
	if track:                                                                               #
		traceback.print_stack()                                                             #
																							#
def debug(message, track = True):                                                           #
	caller = getframeinfo(stack()[1][0])													#
	print (Fore.BLUE + '[DEBUG]' + Style.RESET_ALL +                                        #
			datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ') + #
			caller.filename + ':' + str(caller.lineno) + ' - ' +							#
			message)                                                                        #
	sys.stdout.flush()                                                                      #
	if track:                                                                               #
		traceback.print_stack()                                                             #
																							#
def warn(message, track = True):                                                            #
	caller = getframeinfo(stack()[1][0])													#
	print (Fore.YELLOW + '[WARN]' + Style.RESET_ALL +                                       #
			datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ') + #
			caller.filename + ':' + str(caller.lineno) + ' - ' +							#
			message)                                                                        #
	sys.stdout.flush()                                                                      #
	if track:                                                                               #
		traceback.print_exc()                                                               #
																							#
def notify(message):                                                                        #
	print ("###############" + Fore.YELLOW + message + Style.RESET_ALL + "################")#
																							#
def error(message, track = True):                                                           #
	caller = getframeinfo(stack()[1][0])													#
	print (Fore.RED + '[ERROR]' + Style.RESET_ALL  +                                        #
			datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ') + #
			caller.filename + ':' + str(caller.lineno) + ' - ' +							#
			message)                                                                        #
	sys.stdout.flush()                                                                      #
	if track:                                                                               #
		traceback.print_stack()                                                             #
																							#
def pp(message, track = False):                                                             #
	pprint.pprint(message)                                                                  #
	sys.stdout.flush()                                                                      #
	if track:                                                                               #
		traceback.print_stack()                                                             #
																							#
def getDate():                                                                              #
	return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')                #
																							#
def getTime():                                                                              #
	return datetime.datetime.fromtimestamp(time.time()).strftime('%Hh%Mm%Ss')               #
#############################################################################################



###################################### Pass/Fail Methods ####################################
def PASS(message = None, result = None, track = False):										#
	global passCounter, summary																#
	caller = getframeinfo(stack()[1][0])													#
	passCounter += 1																		#
	current = datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ')	#
	if message:																				#
		print (Fore.GREEN + '[PASS]' + Style.RESET_ALL + current +							#
			caller.filename + ':' + str(caller.lineno) + ' - ' +							#
			Fore.GREEN + message + Style.RESET_ALL)											#
	sys.stdout.flush()																		#
	if result:																				#
		summary.append({'time' : current, 'step' : result, 'result' : 'pass',				#
			'caller' : caller.filename + ':' + str(caller.lineno)})							#
	if track:																				#
		traceback.print_stack()																#
																							#
def FAIL(message = None, result = None , track = False):									#
	global failCounter, summary																#
	caller = getframeinfo(stack()[1][0])													#
	failCounter += 1																		#
	current = datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ')	#
	if message:																				#
		print (Fore.RED + '[FAIL]' + Style.RESET_ALL + current + 							#
			caller.filename + ':' + str(caller.lineno) + ' - ' +							#
			Fore.RED + message + Style.RESET_ALL)											#
	if result:																				#
		summary.append({'time' : current, 'step' : result, 'result' : 'fail',				#
			'caller' : caller.filename + ':' + str(caller.lineno)})							#
	sys.stdout.flush()																		#
	if track:																				#
		traceback.print_stack()																#
																							#
def NOTICE(message = None, result = None , track = False):									#
	global summary																			#
	caller = getframeinfo(stack()[1][0])													#
	current = datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ')	#
	if message:																				#
		print ('[NOTE]' + current +															#
			caller.filename + ':' + str(caller.lineno) + ' - ' + message)					#
	if result:																				#
		summary.append({'time' : current, 'step' : result, 'result' : 'note',				#
			'caller' : caller.filename + ':' + str(caller.lineno)})							#
	sys.stdout.flush()																		#
	if track:																				#
		traceback.print_stack()																#
																							#
def SUMMARY():																				#
	global summary, passCounter, failCounter												#
	totalCounter = passCounter + failCounter												#
	print ('Total Counter: ' + str(totalCounter))											#
	print ('Pass: ' + str(passCounter))														#
	print ('Fail: ' + str(failCounter))														#
	for record in summary:																	#
		print(record['time'] + '[' + record['result'] + ']' + record['step'] +				#
			' - ' + record['caller'])														#
																							#
def FAILSUMMARY():																			#
	global summary, passCounter, failCounter												#
	totalCounter = passCounter + failCounter												#
	print ('Total Counter: ' + str(totalCounter))											#
	print ('Pass: ' + str(passCounter))														#
	print ('Fail: ' + str(failCounter))														#
	for record in summary:																	#
		if 'fail' == record['result']:														#
			print(record['time'] + '[' + record['result'] + ']' + record['step'] +			#
				' - ' + record['caller'])													#
																							#
#############################################################################################



## TODO: resource monitor
##      Jenkins resourcelock
##      Controller tracking resource usage
##      Controller need to provide a scheduling helper for users

## TODO: Valid Input



## \brief a warper function for ast.literal_eval
#
# Parsing the dictionary like string (or json string) to a dictionary without JSON package
# Safely evaluate an expression node or a string containing a python expression
#
# \param string The input string
# \return the dictionary object
##
def strToDict(string):
    return ast.literal_eval(string)



## \brief System Call to execute any commands under Unix system
#
# Execute the given command in the kernel system
#
# \param command string of the command
# \param message if daemon is set False, print out this message in info
# \param daemon print out info message if set False, default is False
# \return system call return code
##
def systemcall(command, message = '', daemon = False):
    if not daemon: info('Executing system call: [' + command + '] ' + message)
    return os.system(command)



## \brief sleep method for system to waiting for <seconds>
#
# waiting for given <seconds>
#
# \param seconds waiting time for sleep()
# \param daemon print out info message if set False, default is False
##
def sleep(seconds, daemon = False):
    if not daemon: info('Sleeping ' + str(seconds) + ' seconds')
    time.sleep(seconds)



## \brief REST Requests methods are used to send different REST requests using requests package
#
# REST Requests methods are used for sending different REST requests
# A list of requests:
# GET - getRequest
# POST - postRequest
# DELETE - deleteRequest
#
# \param url the url address with query to the REST service
# \param daemon weather to print out info message, default is False
# \return json format REST response
# NOTE: for airmosaic, using pylsuweb module instead
##
###################### REST Requests ########################
def getRequest(url, daemon = False):                        #
    if not daemon: info("Sending GET request to: " + url)   #
    if not url.startswith('http'):                          #
        return (requests.get('http://' + url)).json()       #
    else:                                                   #
        return (requests.get(url)).json()                   #
                                                            #
def postRequest(url, daemon = False):                       #
    if not daemon: info("Sending POST request to: " + url)  #
    if not url.startswith('http'):                          #
        return (requests.get('http://' + url)).json()       #
    else:                                                   #
        return (requests.post(url)).json()                  #
                                                            #
def deleteRequest(url, daemon = False):                     #
    if not daemon: info("Sending DELETE request to: " + url)#
    if not url.startswith('http'):                          #
        return (requests.get('http://' + url)).json()       #
    else:                                                   #
        return (requests.delete(url)).json()                #
#############################################################



## \brief Regular Expression methods for string parsing
#
# regexParser - return the first match group of the string
# regex - return all matches as a list
#
# \param messge the input original message
# \param regex the rule for regex parser
##
####################################### Regex ###########################################################
def regexParser(message, regex, daemon = False):                                                        #
    match = re.match(regex, message, re.S)                                                              #
    try:                                                                                                #
        return match.group(1)                                                                           #
    except Exception as e:                                                                              #
        if not daemon: warn('No result found from [' + message + '] return message!', track = False)    #
        return ''                                                                                       #
                                                                                                        #
def regex(message, regex):                                                                              #
    match = re.match(regex, message, re.S)                                                              #
    if match:                                                                                           #
        return match.groups()                                                                           #
    else:                                                                                               #
        return ''                                                                                       #
#########################################################################################################



## \brief Generate a CSV report based on the given json and title
#
# Generate a CSV file with the given title list, load the content of the json input and fill the column
# If the json does not have the title, write '' (empty string)
# If the CSV file already exist, append the json content to the end.
# If title does not match, throw exception
#
# \param json The json object contains the row contents
# \param titles A string list of title
# \param path The path to the log file
# \param daemon Print out the info message if set False, default value is False
##
def reportGenerator(json = None, titles = None, path = None, daemon = False):
	notify("Generate Report from JSON")
	pp(json)
	if not json:
		FAIL('Can not load json object [' + str(json) + ']', track = not daemon)
		raise Exception('JSON decode error')
	if not path:
		FAIL('Can not load file writing path [' + str(path) + ']', track = not daemon)
		raise Exception('File path invalid error')
	if os.path.isfile(path):
		with open(path, 'a+') as csvFile:
			## Python bug, with flag 'a+' the file position position is not pointing to the beginning, hence read will give empty manually setting the position to the file beginning
			csvFile.seek(0)
			csvTitle = [csv_title.strip() for csv_title in csvFile.readline().split(',')]
			for title in titles:
				if title not in csvTitle:
					FAIL('CSV file title not match! [' + title + '] is missing!')
					raise Exception('CSV writing failure, title [' + title + '] mismatch')
			try:
				for row in json:
					content = ''
					if isinstance(json[row], list):
						for title in csvTitle:
							if (title not in json[row][0]):
								if title != csvTitle[0]: content += ','
							else:
								if title != csvTitle[0]: content += (',' + str(json[row][0][str(title)]))
								else: content += str(json[row][0][str(title)])
					else:
						for title in csvTitle:
							if (title not in json[row]):
								if title != csvTitle[0]: content += ','
							else:
								if title != csvTitle[0]: content += (',' + str(json[row][str(title)]))
								else: content += str(json[row][str(title)])
					csvFile.write(content + '\n')
			except Exception as e:
				error(str(e))
	else:
		with open(path, 'w') as csvFile:
			csvTitle = ''
			for title in titles:
				if title != titles[-1]: csvTitle += (title + ',')
				else: csvTitle += title
			csvFile.write(csvTitle + '\n')
			try:
				for row in json:
					content = ''
					if isinstance(json[row], list):
						for title in titles:
							if (title not in json[row][0]):
								if title != titles[0]: content += ','
							else:
								if title != titles[0]: content += (',' + str(json[row][0][str(title)]))
								else: content += str(json[row][0][str(title)])
					else:
						for title in titles:
							if (title not in json[row]):
								if title != titles[0]: content += ','
							else:
								if title != titles[0]: content += (',' + str(json[row][str(title)]))
								else: content += str(json[row][str(title)])
					csvFile.write(content + '\n')
			except Exception as e:
				error(str(e))

	return



## \brief Generate a Jenkins plot CSV report based on the given json and title
#
# Generate a CSV file with the given title list, load the content of the json input and fill the column
# If the json does not have the title, write '' (empty string)
# If the CSV file already exist, append the json content to the end.
# If title does not match, throw exception
#
# \param json The json object contains the row contents
# \param titles A string list of title
# \param path The path to the log file
# \param daemon Print out the info message if set False, default value is False
##
def reportGeneratorJenkins(json = None, titles = None, path = None, daemon = False):
	notify("Generate Jenkins plot CSV file from JSON")
	pp(json)
	if not json:
		FAIL('Can not load json object [' + str(json) + ']', track = not daemon)
		raise Exception('JSON decode error')
	if not path:
		FAIL('Can not load file writing path [' + str(path) + ']', track = not daemon)
		raise Exception('File path invalid error')
	if os.path.isfile(path):
		with open(path, 'a+') as csvFile:
			## Python bug, with flag 'a+' the file position position is not pointing to the beginning, hence read will give empty manually setting the position to the file beginning
			csvFile.seek(0)
			csvTitle = [csv_title.strip() for csv_title in csvFile.readline().split(',')]
			csvTitle.pop(0)
			for title in titles:
				if title not in csvTitle:
					FAIL('CSV file title not match! [' + title + '] is missing!')
					raise Exception('CSV writing failure, title [' + title + '] mismatch')
			rowDict = {}
			try:
				for vendor_id in json:
					row = ''
					if isinstance(json[vendor_id], list):
						rowDict[json[vendor_id][0]['name'] + '-' + str(json[vendor_id][0]['rf_matrix_port'])] = str(json[vendor_id][0]['RSPW_AVG'])
					else:
						rowDict[json[vendor_id]['name'] + '-' + str(json[vendor_id]['rf_matrix_port'])] = str(json[vendor_id]['RSPW_AVG'])
				for title in csvTitle:
					if (title not in titles) or (title not in rowDict):
						if title != titles[-1]: row += ','
					else:
						if title != titles[-1]: row += rowDict[title] + ','
						else: row += rowDict[title]
				csvFile.write(getDate() + ',' + row + '\n')
			except Exception as e:
				error(str(e))
	else:
		with open(path, 'w') as csvFile:
			csvTitle = 'Date,'
			rowDict = {}
			for title in titles:
				if title != titles[-1]: csvTitle += (title + ',')
				else: csvTitle += title
			csvFile.write(csvTitle + '\n')
			try:
				row = ''
				for vendor_id in json:
					if isinstance(json[vendor_id], list):
						rowDict[json[vendor_id][0]['name'] + '-' + str(json[vendor_id][0]['rf_matrix_port'])] = str(json[vendor_id][0]['RSPW_AVG'])
					else:
						rowDict[json[vendor_id]['name'] + '-' + str(json[vendor_id]['rf_matrix_port'])] = str(json[vendor_id]['RSPW_AVG'])
				for title in titles:
					if title not in rowDict:
						if title != titles[-1]: row += ','
					else:
						if title != titles[-1]: row += rowDict[title] + ','
						else: row += rowDict[title]
				csvFile.write(getDate() + ',' + row + '\n')
			except Exception as e:
				error(str(e))
	return



## \brief write the json/dictionary object input to a given file path
#
# load the inputJSON object, and write it to a file with the given path.
# If the inputJSON is None, throw excepiton and increment the failure counter
# If the path is None, throw exception and increment the failure counter
# Create the path folder if is not been created
#   Log will be saved under the log path and put in a folder with the current date
#   Log file will be name with the created [time + name] format
#
# \param inputJSON input either json object or dictionary or json like string
# \param path The Path to the log file, a folder will be created with the current date if not created
# \param name The name of the log file, a prefix of the time being created will be added to the log file name
# \param daemon Print out the message if set False, default is False
##
def writeJSON(inputJSON = None, path = None, name = None, daemon = False):
	if not inputJSON:
		error('Can not load json object [' + str(json) + ']')
		raise Exception('JSON decode error')
	if not path:
		error('Can not load write file path [' + str(path) + ']')
		raise Exception('File path invalid error')
	else:
		date = getDate()
		systemcall('mkdir -p ' + str(path) + '/' + str(date), daemon = daemon)
		with open(str(path) + '/' + str(date) + '/' + str(name), 'w') as logfile:
			try:
				logfile.write(json.dumps(inputJSON))
			except Exception as e:
				error(str(e))
		return



## \brief open the json file and try to return the json read
#
# \param confPath the path of the input file
# \return json object, if any exception raised, return a json with 'error' key
##
def loadConfig(confPath):
    try:
        with open(confPath, 'r') as json_config:
            return json.load(json_config)
    except Exception as e:
        warn("Configuration load failure!\nPath looking for: " + confPath, False)
        return {"error" : confPath + ' ' + str(e)}
