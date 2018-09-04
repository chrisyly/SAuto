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
# \email lying0401@gmail.com
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
from colorama import Fore,Style,init
init()

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
    if track:                                                                               #
        traceback.print_stack()                                                             #
                                                                                            #
def debug(message, track = True):                                                           #
    print (Fore.BLUE + '[DEBUG]' + Style.RESET_ALL +                                        #
            datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ') + #
            message)                                                                        #
    if track:                                                                               #
        traceback.print_stack()                                                             #
                                                                                            #
def warn(message, track = True):                                                            #
    print (Fore.YELLOW + '[WARN]' + Style.RESET_ALL +                                       #
            datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ') + #
            message)                                                                        #
    if track:                                                                               #
        traceback.print_exc()                                                               #
                                                                                            #
def error(message, track = True):                                                           #
    print (Fore.RED + '[ERROR]' + Style.RESET_ALL  +                                        #
            datetime.datetime.fromtimestamp(time.time()).strftime('[%m-%d-%Y %H:%M:%S] ') + #
            message)                                                                        #
    if track:                                                                               #
        traceback.print_stack()                                                             #
                                                                                            #
def pp(message, track = False):                                                             #
    pprint.pprint(message)                                                                  #
    if track:                                                                               #
        traceback.print_stack()                                                             #
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
##
###################### REST Requests ########################
def getRequest(url, daemon = False):                        #
    if not daemon: info("Sending GET request to: " + url)   #
    return (requests.get(url)).json()                       #
                                                            #
def postRequest(url, daemon = False):                       #
    if not daemon: info("Sending POST request to: " + url)  #
    return (requests.post(url)).json()                      #
                                                            #
def deleteRequest(url, daemon = False):                     #
    if not daemon: info("Sending DELETE request to: " + url)#
    return (requests.delete(url)).json()                    #
#############################################################



## \brief Regular Expression methods for string parsing
#
# regexParser - return the first match group of the string
# regex - return all matches as a list
#
# \param messge the input original message
# \param regex the rule for regex parser
##
####################################### Regex ###########################################
def regexParser(message, regex, daemon = False):                                        #
    match = re.match(regex, message, re.S)                                              #
    try:                                                                                #
        return match.group(1)                                                           #
    except Exception as e:                                                              #
        if not daemon: warn('No result found from [' + message + '] return message!')   #
        return ''                                                                       #
                                                                                        #
def regex(message, regex):                                                              #
    match = re.match(regex, message, re.S)                                              #
    if match:                                                                           #
        return match.groups()                                                           #
    else:                                                                               #
        return ''                                                                       #
#########################################################################################



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
        return {"error" : confPath + ' ' + e}
