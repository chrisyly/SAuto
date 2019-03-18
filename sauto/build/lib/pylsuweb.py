#*******************************************************************************
#File:
#  $Id: pylsu.py 1091 2017-07-28 14:05:22Z michele $
#  $Revision: 1091 $
#  $Date: 2017-07-28 16:05:22 +0200 (Fri, 28 Jul 2017) $
#  $Author: michele $
#
#  (c) 2017 Prisma-Telecom Testing srl
#  The Source Code contained herein is Prisma-Telecom Testing srl
#  confidential material.
#
#Purpose:
#
#Operation:
#
#Notes/Issues: Aligned to version 1.2.7
#*******************************************************************************/

import json
#import requests
from ftplib import FTP
import telnetlib
import time
import os
import subprocess
import signal
import sys
import tempfile
import tarfile
import shutil
import platform
import traceback
import utility
from datetime import datetime
from pyutils import ssh_wrapper as pe_ssh
from pyutils import pe_log, b, void
#from pyutils import get3GPPReleaseFromSid
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, Request
    from urllib.error import URLError
    from http.client import BadStatusLine
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, Request, URLError, HTTPError
    from httplib import BadStatusLine

##################################
#        API for eLSU O&M        #
##################################

# Internal parameters initialization
user = 'user'
password = 'user'
rootuser = 'root'
rootpassword = 'root'
prompt = ['[a-zA-Z//]+[@\$]', "\n\$\s"]
headers = {'Content-Type': 'application/json'}
##################################
#          API functions        #
##################################

def system_login(lsu_ip, method="POST", cookie="", username="user", password="user"):
    """Login into LSU web interface, returns cookie for next commands
    Returns error in case lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param method: POST|GET, POST execute login, GET gets status
    :param cookie: cookie if known
    :param username: custom username
    :param password: custom password
    :return: cookie or status
    |
    :example: system_login( "192.168.1.2"  )
    :sample output: TWISTED_SESSION=d993e44b2a00ec7058b35be7782d5bc1; Path=/
    """
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    cmd='system/login'
    payload = {}
    payload['username'] = user
    payload['password'] = password
    data = json.dumps(payload).encode('utf-8')
    req = Request("http://%s/%s" %(lsu_ip, cmd),data=data,headers=headers)
    if method == "GET":
        req.get_method = lambda: 'GET'
        req.add_header('cookie', cookie)
    try:
        open2=urlopen(req,timeout=10)
        login_output=json.loads(open2.read().decode('utf-8'))
        cookie = open2.headers.get('Set-Cookie')
    except Exception as pe_err:
        pe_log(False, [], "*WARN* LSU problem in login:"+str(pe_err))
    if method == "GET":
        return login_output 
    else:
        return cookie

def system_logout(lsu_ip, cookie="", username="user", password="user"):
    """Logout from LSU web interface, returns cookie for next commands
    Returns error in case lsu is not reachable or nothin

    :param lsu_ip: LSU IP address
    :param cookie: cookie if known
    :param username: custom username
    :param password: custom password
    :return: cookie or status
    |
    :example: system_logout( "192.168.1.2" , cookie="TWISTED_SESSION=d993e44b2a00ec7058b35be7782d5bc1; Path=/" )
    :sample output: ""
    """
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    cmd='system/logout'
    payload = {}
    payload['username'] = user
    payload['password'] = password
    data = json.dumps(payload).encode('utf-8')
    req = Request("http://%s/%s" %(lsu_ip, cmd),data=data,headers=headers)
    req.add_header('cookie', cookie)
    login_output="logged out"
    try:
        open2=urlopen(req,timeout=10)
        login_output=(open2.read().decode('utf-8'))
    except Exception as pe_err:
        pe_log(False, [], "*WARN* LSU problem in login:"+str(pe_err))
    return login_output

def system_interfaceVersion(lsu_ip, username="user", password="user"):
    """Get version of LSU WEB REST Interface
    Returns error in case lsu is not reachable.

    :param lsu_ip: LSU IP address
    :return: cookie or status
    |
    :example: system_interfaceVersion( "192.168.1.2"  )
    :sample output: {'result': 'success', 'error': '', 'output': {'version': '1.2.4'}, 'version': '1.2.4'}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    version="NA"
    cmd = 'system/interfaceVersion/'
    cookie = system_login (lsu_ip, username=username, password=password)
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    req.add_header('cookie', cookie)
    try:
        lsu_ret = urlopen(req,timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
        version = lsu_ret_dict["version"]
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict, 'version':version}

def system_status(lsu_ip):
    """Get status of LSU web interface, 

    :return: status
    |
    :example: system_login( "192.168.1.2"  )
    :sample output: {'result': 'success', 'error': '', 'output': {'result': 'RUNNING'}, 'status': 'RUNNING'}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    status = "Not RUNNING"
    cmd = 'system/status/'
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req,timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
        status = lsu_ret_dict["result"]
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict, 'status':status }


def system_hostInfo(lsu_ip, username="user", password="user"):
    """Login into LSU web interface, returns cookie for next commands
    Returns error in case lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param method: POST|GET, POST execute login, GET gets status
    :param cookie: cookie if known
    :param username: custom username
    :param password: custom password
    :return: cookie or status
    |
    :example: system_login( "192.168.1.2"  )
    :sample output: TWISTED_SESSION=d993e44b2a00ec7058b35be7782d5bc1; Path=/
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'system/hostInfo/'
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def system_lsuInfoXml(lsu_ip, username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'system/lsuInfoXml/'
    cookie = system_login (lsu_ip, username=username, password=password)
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    req.add_header('cookie', cookie)
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def system_lsuCfg(lsu_ip, username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'system/lsuCfg/'
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def archive_files(lsu_ip, method="GET", command="", filename="test", cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'archive/files'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    
    if method != "GET":
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
    if method == "DELETE" and filename != "":
        cmd += '?filename='+str(filename)+".tar.gz"
        print (cmd)
    elif method == "POST":
        payload['filename'] = filename
        if command == "":
            cmd = 'archive/default'
            payload['filename'] += ".tar.gz"
        elif command == "restore":
            cmd = 'archive/restore'
        elif command == "save":
            cmd = 'archive/save'
    print (cookie)
    print (cmd)
    try:
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


#   _____           _                    __  __                                   
#  |  __ \         | |                  |  \/  |                                  
#  | |__) |_ _  ___| | ____ _  __ _  ___| \  / | __ _ _ __   __ _  __ _  ___ _ __ 
#  |  ___/ _` |/ __| |/ / _` |/ _` |/ _ \ |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
#  | |  | (_| | (__|   < (_| | (_| |  __/ |  | | (_| | | | | (_| | (_| |  __/ |   
#  |_|   \__,_|\___|_|\_\__,_|\__, |\___|_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|   
#                              __/ |                               __/ |          
#                             |___/                               |___/  

def packageManager_systemOperation(lsu_ip, command="REBOOT", cookie=""):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    commands = [ "SHUTDOWN", "REBOOT"]
    result = "failed"
    error = ""
    cmd = 'archive/files'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    payload['name'] = command
    if command not in commands:
        return {'result':result,'error':command + " not Allowed",'output':""}
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def packageManager_softwareOperations(lsu_ip, command="CLEAN", cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    commands = [ "START", "STOP", "CLEAN"]
    result = "failed"
    error = ""
    cmd = 'packageManager/softwareOperations'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    payload['type'] = command
    if command not in commands:
        return {'result':result,'error':command + " not Allowed",'output':""}
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        if command == "START":
            res = packageManager_softwareOperations(lsu_ip, command="STOP", cookie=cookie, username="user", password="user")
            print (res)
        data = json.dumps(payload).encode('utf-8')
        print (cookie)
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        lsu_ret = urlopen(req, timeout=120)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def packageManager_cleanPPU (lsu_ip, ppu="0-1", cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/cleanPPU'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    payload['cleanPPuData'] = ppu
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        data = json.dumps(payload).encode('utf-8')        
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        #add cookie for next ops
        lsu_ret_dict['cookie'] = cookie
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}



def packageManager_freeDiskSpace(lsu_ip, cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/freeDiskSpace'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    try:

        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        req.get_method = lambda: "GET"
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def packageManager_installationHistory(lsu_ip, cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/installationHistory'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    try:

        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        req.get_method = lambda: "GET"
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def packageManager_installedPackages(lsu_ip, cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/installedPackages'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    try:

        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        req.get_method = lambda: "GET"
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def packageManager_package(lsu_ip, method="GET", filename="", cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/package'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    lsu_ret_dict = {}
    payload = {}
    
    if method != "GET":
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
    if method == "DELETE" and filename != "":
        cmd += '?filename='+str(filename)
        print (cmd)
    elif method == "POST":
        payload['filename'] = filename
    print (cookie)
    print (cmd)
    try:
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def packageManager_packageBubble(lsu_ip, method="GET", filename="", cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/packageBubble'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    lsu_ret_dict = {}
    payload = {}
    
    if method != "GET":
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
    if method == "DELETE" and filename != "":
        cmd += '?filename='+str(filename)
        print (cmd)
    elif method == "POST":
        payload['filename'] = filename
    print (cookie)
    print (cmd)
    try:
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def packageManager_report(lsu_ip, cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/report'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    try:

        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        req.get_method = lambda: "GET"
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        lsu_ret_dict['cookie'] = cookie
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def packageManager_jobResult(lsu_ip, job_id, cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/jobResult?jobId='+str(job_id)
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        req.get_method = lambda: "GET"
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def packageManager_jobMonitor(lsu_ip, job_id, stdin="", cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/jobMonitor'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    #if job_id.isdigit() is not True:
    #    return {'result':result,'error':"jobId is not a number",'output':job_id}
    payload['jobId'] = job_id
    payload['stdIn'] = stdin
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        print (cookie)
        req.add_header('cookie', cookie)
        req.get_method = lambda: "POST"
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def packageManager_reportFiles(lsu_ip, method="GET", filename="", cookie="", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'packageManager/reportFiles'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}
    if method == "DELETE":
        cmd += "?filename=" + filename
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data, headers=headers)
        req.add_header('cookie', cookie)
        req.get_method = lambda: method
        lsu_ret = urlopen(req, timeout=60)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        #lsu_ret_dict['cookie'] = cookie
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        print(traceback.format_exc())
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}



def rat_status(lsu_ip, rat="LTE", username="user", password="user"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    if rat == "LTE":
        rat = "lte"
    elif rat == "UMTS":
        rat = "umts"
    elif rat == "GSM":
        rat = "gsm"
    elif rat == "5Gv":
        rat = "fivegv"
    elif rat == "5Gnr":
        rat = "fivegnr"
    else:
        return {'result':result,'error':"Unknown rat:"+str(rat),'output':lsu_ret_dict}
    cmd = rat+'/status'
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

#################################
#  _____  _____ _   _ _____     #
# | ____|/ ____| \ | |  __ \    #
# | |__ | |  __|  \| | |__) |   #
# |___ \| | |_ | . ` |  _  /    #
#  ___) | |__| | |\  | | \ \    #
# |____/ \_____|_| \_|_|  \_    #
#                               #
#################################

def fivegnr_beamCounters(lsu_ip, cellNumber="1", sdr="0", ppu="0-1", instance="0"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/beamCounters?cellNumber='+str(cellNumber)+'&sdr='+sdr+'ppu='+ppu+'instance='+instance
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def fivegnr_beamsCounters(lsu_ip, cellNumber="1"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/beamsCounters?cellNumber='+str(cellNumber)
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}



def fivegnr_sdrBase(lsu_ip):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/sdrBase' 
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def fivegnr_baseBandPPUs(lsu_ip):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/baseBandPPUs'
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def fivegnr_lsuInfoXmlPpus(lsu_ip):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'ivegnr/lsuInfoXmlPpus'
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def fivegnr_beam(lsu_ip, method="POST",cookie="",  **kwargs):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/beam'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}

    if 'cellNumber' in kwargs:
        cellNumber = kwargs['cellNumber']
        payload['cellNumber'] = kwargs['cellNumber']
    else:
        return {'result':result,'error':"Missing cellNumber in parameters",'output':kwargs}
    if 'sdr' in kwargs:
        sdr = kwargs['sdr']
        payload['sdr'] = kwargs['sdr']
    else:
        return {'result':result,'error':"Missing sdr in parameters",'output':kwargs}
    if 'ppu' in kwargs:
        ppu = kwargs['ppu']
        payload['ppu'] = kwargs['ppu']
    else:
        return {'result':result,'error':"Missing ppu in parameters",'output':kwargs}
    if 'instance' in kwargs:
        instance = kwargs['instance']
        payload['instance'] = kwargs['instance']
    else:
        return {'result':result,'error':"Missing instance in parameters",'output':kwargs}
	
    if 'ssbScOffset' in kwargs:
        payload['ssbScOffset'] = kwargs['ssbScOffset']
    else:
        payload['ssbScOffset'] = 0
    if 'dlFreqRf' in kwargs:
        payload['dlFreqRf'] = kwargs['dlFreqRf']
    else:
        payload['dlFreqRf'] = 0
    if 'ulFreqRf' in kwargs:
        payload['ulFreqRf'] = kwargs['ulFreqRf']
    else:
        payload['ulFreqRf'] = 0
    if 'ulGain1' in kwargs:
        payload['ulGain1'] = kwargs['ulGain1']
    else:
        payload['ulGain1'] = 0
    if 'dlGain1' in kwargs:
        payload['dlGain1'] = kwargs['dlGain1']
    else:
        payload['dlGain1'] = 0
    if 'ulGain0' in kwargs:
        payload['ulGain0'] = kwargs['ulGain0']
    else:
        payload['ulGain0'] = 0
    if 'dlGain0' in kwargs:
        payload['dlGain0'] = kwargs['dlGain0']
    else:
        payload['dlGain0'] = 0
    if method == "DELETE":
        cmd = cmd + "?cellNumber="+str(cellNumber)+"&sdr="+sdr+"&ppu="+ppu+"&instance="+instance
    
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        data = json.dumps(payload).encode('utf-8')
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def fivegnr_cell(lsu_ip, method="POST",cookie="",  **kwargs):
    """Create od delete a cell for 5GNR.
    Returns error in case of error or {
    result:	boolean
    creationFileContent:	string
    }

    :param lsu_ip: LSU IP address
    :param method: POST/GET
    :param cookie: cookie for cell operation, otherwise login is done
    :param kwargs: parameters for creating cell
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: fivegnr_cell( "192.168.1.2" , method="DELETE" , {"cellNumber":"1"} )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/cell'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}

    if 'cellNumber' in kwargs:
        cellNumber = kwargs['cellNumber']
        payload['cellNumber'] = kwargs['cellNumber']
    else:
        return {'result':result,'error':"Missing cellNumber in parameters",'output':kwargs}
    if 'sdr' in kwargs:
        sdr = kwargs['sdr']
        payload['sdr'] = kwargs['sdr']
    else:
        return {'result':result,'error':"Missing sdr in parameters",'output':kwargs}
    if 'ppu' in kwargs:
        ppu = kwargs['ppu']
        payload['ppu'] = kwargs['ppu']
    else:
        return {'result':result,'error':"Missing ppu in parameters",'output':kwargs}
    if 'instance' in kwargs:
        instance = kwargs['instance']
        payload['instance'] = kwargs['instance']
    else:
        return {'result':result,'error':"Missing instance in parameters",'output':kwargs}
	
    if 'ssbScOffset' in kwargs:
        payload['ssbScOffset'] = kwargs['ssbScOffset']
    else:
        payload['ssbScOffset'] = 0
    if 'dlFreqRf' in kwargs:
        payload['dlFreqRf'] = kwargs['dlFreqRf']
    else:
        payload['dlFreqRf'] = 0
    if 'ulFreqRf' in kwargs:
        payload['ulFreqRf'] = kwargs['ulFreqRf']
    else:
        payload['ulFreqRf'] = 0
    if 'ulGain1' in kwargs:
        payload['ulGain1'] = kwargs['ulGain1']
    else:
        payload['ulGain1'] = 0
    if 'dlGain1' in kwargs:
        payload['dlGain1'] = kwargs['dlGain1']
    else:
        payload['dlGain1'] = 0
    if 'ulGain0' in kwargs:
        payload['ulGain0'] = kwargs['ulGain0']
    else:
        payload['ulGain0'] = 0
    if 'dlGain0' in kwargs:
        payload['dlGain0'] = kwargs['dlGain0']
    else:
        payload['dlGain0'] = 0
    for a in range(1,16):
        if "gp"+str(a) in kwargs:
            payload["gp"+str(a)] = kwargs["gp"+str(a)]
        else:
            payload["gp"+str(a)] = 0
    if method == "DELETE":
        cmd = cmd + "?cellNumber="+str(cellNumber)+"&sdr="+sdr+"&ppu="+ppu+"&instance="+instance
    
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        data = json.dumps(payload).encode('utf-8')
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}



#   _____  _____ _________      __
#  | ____|/ ____|__   __\ \    / /
#  | |__ | |  __   | |   \ \  / / 
#  |___ \| | |_ |  | |    \ \/ /  
#   ___) | |__| |  | |     \  /   
#  |____/ \_____|  |_|      \/   

def fivegv_pathCounters(lsu_ip, cellNumber="1", sdr="0", ppu="0-1", instance="0"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param rat: radio access technology (UMTS||LTE||GSM)
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: checkCellStatus( "192.168.1.2" , "LTE" , "1" )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/beamCounters?cellNumber='+str(cellNumber)+'&sdr='+sdr+'ppu='+ppu+'instance='+instance
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def fivegv_path(lsu_ip, method="POST",cookie="",  **kwargs):
    """Create or delete a cell for 5GTV.
    Returns error in case of error or {
    result:	boolean
    creationFileContent:	string
    }

    :param lsu_ip: LSU IP address
    :param method: POST/GET
    :param cookie: cookie for cell operation, otherwise login is done
    :param kwargs: parameters for creating cell
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: fivegnr_cell( "192.168.1.2" , method="DELETE" , {"cellNumber":"1"} )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'fivegnr/cell'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}

    if 'cellNumber' in kwargs:
        cellNumber = kwargs['cellNumber']
        payload['cellNumber'] = kwargs['cellNumber']
    else:
        return {'result':result,'error':"Missing cellNumber in parameters",'output':kwargs}
    if 'sdr' in kwargs:
        sdr = kwargs['sdr']
        payload['sdr'] = kwargs['sdr']
    else:
        return {'result':result,'error':"Missing sdr in parameters",'output':kwargs}
    if 'ppu' in kwargs:
        ppu = kwargs['ppu']
        payload['ppu'] = kwargs['ppu']
    else:
        return {'result':result,'error':"Missing ppu in parameters",'output':kwargs}
    if 'instance' in kwargs:
        instance = kwargs['instance']
        payload['instance'] = kwargs['instance']
    else:
        return {'result':result,'error':"Missing instance in parameters",'output':kwargs}
	
    if 'ssbScOffset' in kwargs:
        payload['ssbScOffset'] = kwargs['ssbScOffset']
    else:
        payload['ssbScOffset'] = 0
    if 'dlFreqRf' in kwargs:
        payload['dlFreqRf'] = kwargs['dlFreqRf']
    else:
        payload['dlFreqRf'] = 0
    if 'ulFreqRf' in kwargs:
        payload['ulFreqRf'] = kwargs['ulFreqRf']
    else:
        payload['ulFreqRf'] = 0
    if 'ulGain1' in kwargs:
        payload['ulGain1'] = kwargs['ulGain1']
    else:
        payload['ulGain1'] = 0
    if 'dlGain1' in kwargs:
        payload['dlGain1'] = kwargs['dlGain1']
    else:
        payload['dlGain1'] = 0
    if 'ulGain0' in kwargs:
        payload['ulGain0'] = kwargs['ulGain0']
    else:
        payload['ulGain0'] = 0
    if 'dlGain0' in kwargs:
        payload['dlGain0'] = kwargs['dlGain0']
    else:
        payload['dlGain0'] = 0
    for a in range(1,16):
        if "gp"+str(a) in kwargs:
            payload["gp"+str(a)] = kwargs["gp"+str(a)]
        else:
            payload["gp"+str(a)] = 0
    if method == "DELETE":
        cmd = cmd + "?cellNumber="+str(cellNumber)+"&sdr="+sdr+"&ppu="+ppu+"&instance="+instance
    
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        data = json.dumps(payload).encode('utf-8')
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

#   _   _______ ______ 
#  | | |__   __|  ____|
#  | |    | |  | |__   
#  | |    | |  |  __|  
#  | |____| |  | |____ 
#  |______|_|  |______|

def lte_cellCounters(lsu_ip, cellNumber="1", type="FDD", ppu="0-1"):
    """Check for the given cell counetrs
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param type: TDD|FDD
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: lte_cellCounters("172.17.11.181", cellNumber="1", type="FDD", ppu="0-1")
    :sample output: {'result': 'success', 'error': '', 'output': {'schedulerInfo': {'dlprb3040': 
                    {'perc': '0.00', 'value': '0'}, 'dlprb7080': {'perc': '0.00', 'value': '0'}, 
                    'dlprb5060': {'perc': '0.00', 'value': '0'}, 'dlprb8090': {'perc': '0.00', 'value': '0'}, 
                    'ulprb010': {'perc': '0.00', 'value': '0'}, 'pdcchdci2a': {'perc': '0.00', 'value': '0'}, 
                    'ulprb8090': {'perc': '0.00', 'value': '0'}, 'ulprb1020': {'perc': '0.00', 'value': '0'}, 
                    'ulprb4050': {'perc': '0.00', 'value': '0'}, 'dlprb010': {'perc': '0.80', 'value': '5627639'},
                    'dlprb2030': {'perc': '0.20', 'value': '1364274'}, 'ulprb2030': {'perc': '0.00', 'value': '0'},
                    'ulprb7080': {'perc': '0.00', 'value': '0'}, 'puschmcs': [{'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}], 'dlprb1020': {'perc': '0.00', 'value': '0'}, 'dlprb4050': 
                    {'perc': '0.00', 'value': '0'}, 'pdcchdci1a': {'perc': '1.00', 'value': '6821377'}, 'pdcchdci2': 
                    {'perc': '0.00', 'value': '0'}, 'pdcchdci1': {'perc': '0.00', 'value': '0'}, 'pdcchdci0': {
                    'perc': '0.00', 'value': '0'}, 'ulprb5060': {'perc': '0.00', 'value': '0'}, 'ulprb3040':
                        {'perc': '0.00', 'value': '0'}, 'ulprb90100': {'perc': '0.00', 'value': '0'}, 'dlprb90100': {
                    'perc': '0.00', 'value': '0'}, 'pdschmcs': [{'perc': '0.02', 'value': '170536'}, {'perc': '0.00', 
                    'value': '5'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 
                    'value': '0'}, {'perc': '0.78', 'value': '5457098'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.20', 'value': '1364274'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, {'perc': '0.00', 'value': '0'}, 
                    {'perc': '0.00', 'value': '0'}], 'dlprb6070': {'perc': '0.00', 'value': '0'}, 'ulprb6070': 
                    {'perc': '0.00', 'value': '0'}}, 'powerInfo': {'values': [{'pathloss': {'max': 'UNAVAILABLE', 
                    'avg': 'UNAVAILABLE', 'min': 'UNAVAILABLE'}, 'rsrp': {'max': '0.00', 'avg': '-58.50', 'min': '-58.75'},
                    'snr': {'max': '28.87', 'avg': '27.88', 'min': '0.00'}}, {'pathloss': {'max': 'UNAVAILABLE', 'avg': 
                    'UNAVAILABLE', 'min': 'UNAVAILABLE'}, 'rsrp': {'max': '0.00', 'avg': '-59.25', 'min': '-59.25'}, 
                    'snr': {'max': '32.57', 'avg': '30.80', 'min': '0.00'}}, {'pathloss': {'max': '', 'avg': '', 'min': ''},
                    'rsrp': {'max': '', 'avg': '', 'min': ''}, 'snr': {'max': '', 'avg': '', 'min': ''}}, {'pathloss': 
                    {'max': '', 'avg': '', 'min': ''}, 'rsrp': {'max': '', 'avg': '', 'min': ''}, 'snr': {'max': '', 'avg': '', 'min': ''}}]}, 
                    'commonParameters': {'mezz1SerialNumber': '', 'ulRfGain': -20.0, 'residualFrequencyError': 0, 
                    'bcchDecodingAntanna0': 'Success', 'bcchDecodingAntanna1': 'Success', 'subframe': 5, 'alarm': 0, 
                    'bound': 0, 'sfn': 247, 'mezz0SerialNumber': '', 'numberOfFrequencyCorrections': 1, 'dlRfGain2': 
                    '', 'dlRfGain3': '', 'dlRfGain0': 19, 'dlRfGain1': 20, 'initialFrequencyError': 1, 'cellId': 202},
                     'throughtputParameters': {'numberOfTransmittedBytes': 0, 'nacksRatioL': 0.0, 'bler': 0.0, 'bitrateUL': 0,
                      'numberOfNacks': 0, 'numberOfCrcErrors': 0, 'bitrateDL': 1, 'numberOfReveivedBytes': 169681676}, 
                      'systemParameters': {'maxBoosterTemp': 39, 'antennasParameters': [{'antennaId': '00', 'type': '', 
                      'version': '', 'calibrationDate': ''}, {'antennaId': '01', 'type': '', 'version': '', 'calibrationDate': ''},
                       {'antennaId': '02', 'type': '', 'version': '', 'calibrationDate': ''}, {'antennaId': '03', 'type': '', 'version': '',
                        'calibrationDate': ''}], 'minBoosterTemp': 37, 'currentBaseTemp': 35, 'minBaseTemp': 32, 'maxBaseTemp': 35, 
                        'currentBoosterTemp': 39}}}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'lte/cellCounters?cellNumber='+str(cellNumber)+'&type='+type+'&ppu='+ppu
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def lte_cellConfiguration(lsu_ip, cellNumber="1", ppu="0-1"):
    """Check for the given cell synchronization status.
    Returns error in case cell does not exists or lsu is not reachable.

    :param lsu_ip: LSU IP address
    :param type: TDD|FDD
    :param cell: cell id of the cell to be checked
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: lte_cellConfiguration("172.17.11.181")
    :sample output: {'result': 'success', 'error': '', 'output': {'nbiotUlEarFcn': 4294967295, 'ulearfcn': 20050, 'localCellId1': False, 'splitMode': 'RF', 'aggrId': 0, 'dlearfcn': 2050, 'epdcch': 0, 'downlinkHarq': False, 'localCellId0': True, 'fadingSim': '', 'ulTest': '', 'pracCfg': 1, 'gp4': 0, 'intfTypeSdr00': 'COMBINE_RX_TX', 'exCyclePrefix': False, 'ta': 0, 'sdr': 0, 'pdcchType': 15, 'laa': 0, 'interferenceId': 0, 'nbiotDlEarFcn': 4294967295, 'ulRfGain': '', 'nbiot': 0, 'dlAttenuation': 0, 'verbosity': 4294967295, 'nbiotPrbUp': 65535, 'dlBw': '20Mhz', 'sibwin': 0, 'debug': 0, 'dlRfGain0': '', 'dlRfGain1': '', 'nbiotPrbDn': 65535, 'gp1': 0, 'gp2': 0, 'gp3': 0}}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'lte/cellConfiguration?cellNumber='+str(cellNumber)+'&ppu='+ppu
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def lte_cell(lsu_ip, method="POST",cookie="", username="user", password="user",  **kwargs):
    """Create or delete a cell for LTE.

    :param lsu_ip: LSU IP address
    :param method: POST/GET
    :param cookie: cookie for cell operation, otherwise login is done
    :param kwargs: parameters for creating cell
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: fivegnr_cell( "192.168.1.2" , method="DELETE" , {"cellNumber":"1"} )
    :sample output: {'status': 'LOADING', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'NOT SYNCHRONIZED', 'status_info': '', 'result': 'success', 'error': ''}
    :sample output: {'status': 'SYNCHRONIZED', 'status_info': u'6', 'result': 'success', 'error': ''}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'lte/radioCell'
    headers = {'Content-Type': 'application/json', "Accept": "application/json"}
    payload = {}

    if 'cellNumber' in kwargs:
        cellNumber = kwargs['cellNumber']
        payload['cellNumber'] = kwargs['cellNumber']
    else:
        return {'result':result,'error':"Missing cellNumber in parameters",'output':kwargs}
    if method == "POST":
        if 'type' in kwargs and (kwargs['type'] == "TDD" or kwargs['type'] == "FDD"):
            payload['type'] = kwargs['type']
        else:
            return {'result':result,'error':"Missing or wrong type in parameters",'output':kwargs}
        if 'ppu' in kwargs:
            ppu = kwargs['ppu']
            payload['ppu'] = kwargs['ppu']
        else:
            return {'result':result,'error':"Missing ppu in parameters",'output':kwargs}
        #TODO
        #{'nbiotUlEarFcn': 4294967295, 'ulearfcn': 20050, 'localCellId1': False, 'splitMode': 'RF', 'aggrId': 0, 'dlearfcn': 2050, 'epdcch': 0, 'downlinkHarq': False, 'localCellId0': True, 'fadingSim': '', 'ulTest': '', 'pracCfg': 1, 'gp4': 0, 'intfTypeSdr00': 'COMBINE_RX_TX', 'exCyclePrefix': False, 'ta': 0, 'sdr': 0, 'pdcchType': 15, 'laa': 0, 'interferenceId': 0, 'nbiotDlEarFcn': 4294967295, 'ulRfGain': '', 'nbiot': 0, 'dlAttenuation': 0, 'verbosity': 4110417920, 'nbiotPrbUp': 65535, 'dlBw': '20Mhz', 'sibwin': 0, 'debug': 0, 'dlRfGain0': '', 'dlRfGain1': '', 'nbiotPrbDn': 65535, 'gp1': 0, 'gp2': 0, 'gp3': 0}}
        payload['genericProperties']={} 
        if 'ulearfcn' in kwargs:
            payload['genericProperties']['ulearfcn'] = kwargs['ulearfcn']
        else:
            return {'result':result,'error':"Missing ulearfcn in parameters",'output':kwargs}
        if 'dlearfcn' in kwargs:
            payload['genericProperties']['dlearfcn'] = kwargs['dlearfcn']
        else:
            return {'result':result,'error':"Missing dlearfcn in parameters",'output':kwargs}
        for a in kwargs:
            payload['genericProperties'][a]=kwargs[a]
        for a in range(1,4):
            if "gp"+str(a) in kwargs:
                payload['genericProperties']["gp"+str(a)] = kwargs["gp"+str(a)]
            else:
                payload['genericProperties']["gp"+str(a)] = 0
    if method == "DELETE":
        cmd = cmd + "?cellNumber="+str(cellNumber)
    #print (payload)
    try:
        if cookie == "":
            cookie = system_login(lsu_ip, username=username, password=password)
            cookie = utility.regexParser(cookie,'(.*);.*')
        data = json.dumps(payload).encode('utf-8')
        req = Request("http://%s/%s" %(lsu_ip, cmd), data=data)
        req.get_method = lambda: method
        req.add_header('cookie', cookie)
        req.add_header('Content-Type', "application/json")
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        result = "success"
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

'''
  _    _ __  __ _______ _____
 | |  | |  \/  |__   __/ ____|
 | |  | | \  / |  | | | (___  
 | |  | | |\/| |  | |  \___ \ 
 | |__| | |  | |  | |  ____) |
  \____/|_|  |_|  |_| |_____/  '''
#MISSING

'''  
   _____  _____ __  __ 
  / ____|/ ____|  \/  |
 | |  __| (___ | \  / |
 | | |_ |\___ \| |\/| |
 | |__| |____) | |  | |
  \_____|_____/|_|  |_|'''
#TODO


'''
  _______ _____ _______ __  __ 
 |__   __/ ____|__   __|  \/  |
    | | | (___    | |  | \  / |
    | |  \___ \   | |  | |\/| |
    | |  ____) |  | |  | |  | |
    |_| |_____/   |_|  |_|  |_|
                               
                              '''

def tstm_isPortBusy(lsu_ip, port="7100"):
    """Check if tstm is running atets on a given port.

    :param lsu_ip: LSU IP address
    :param port: tstm simulation port
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: tstm_isPortBusy("172.17.11.181",port="7100")
    :sample output: {'result': '', 'error': '[Errno 261] Connection refused', 'output': {'result': '', 'success': False, 'error': '[Errno 261] Connection refused'}}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'tstm/isPortBusy?port='+port
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = lsu_ret_dict["result"]
        error = lsu_ret_dict["error"]
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}

def tstm_isTstmRunning(lsu_ip, port="7100", rat="LTE", release="Mar18"):
    """Check if tstm is running atets on a given port.

    :param lsu_ip: LSU IP address
    :param port: tstm simulation port
    :param rat: tstm rat (LTE, GSM, UMTS, 5Gv, 5GNR)
    :param release: tstm release (Mar18)
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: tstm_isTstmRunning("172.17.11.181",port="7100",rat="LTE",release="Mar18")
    :sample output: {'result': '', 'error': '[Errno 261] Connection refused', 'output': {'result': '', 'success': False, 'error': '[Errno 261] Connection refused'}}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'tstm/isTstmRunning?port='+port+'&technology='+rat+"&release="+release
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = lsu_ret_dict["result"]
        error = lsu_ret_dict["error"]
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}


def tstm_runningSimulations(lsu_ip, port="7100"):
    """Check if tstm is running atets on a given port.

    :param lsu_ip: LSU IP address
    :param port: tstm simulation port
    :return: {'result':'success|failed','error':'','status':status,'status_info':status_info}
    |
    :example: tstm_runningSimulations("172.17.11.181",port="7100")
    :sample output: {'result': '', 'error': '[Errno 261] Connection refused', 'output': {'result': '', 'success': False, 'error': '[Errno 261] Connection refused'}}
    """
    lsu_ret_dict = {}
    result = "failed"
    error = ""
    cmd = 'tstm/runningSimulations?port='+port
    req = Request("http://%s/%s" %(lsu_ip, cmd))
    try:
        lsu_ret = urlopen(req, timeout=10)
        lsu_ret_dict = json.loads(lsu_ret.read().decode('utf-8'))
        #pe_log(False, [], "*DEBUG* "+str(lsu_ret))
        result = lsu_ret_dict["result"]
        error = lsu_ret_dict["error"]
    except Exception as pe_err:
        pe_log(False, [], "*WARN* "+str(pe_err))
        error = str(pe_err)
    return {'result':result,'error':error,'output':lsu_ret_dict}
