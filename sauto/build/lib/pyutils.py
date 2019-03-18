#*************************************************************************
# File:
#  $Id: pyutils.py 1106 2017-08-27 11:23:36Z michele $
#  $Revision: 1106 $
#  $Date: 2017-08-27 13:23:36 +0200 (Sun, 27 Aug 2017) $
#  $Author: michele $
#
#  (c) 2017 Prisma-Telecom Testing srl
#  The Source Code contained herein is Prisma-Telecom Testing srl
#  confidential material.
#
# Purpose:
#
# Operation:
#
# Notes/Issues:
#*******************************************************************************/
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
    from http.client import BadStatusLine
    import codecs
    def b(x):
        return codecs.latin_1_encode(x)[0]
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen
    from httplib import BadStatusLine
    def b(x):
        return x
import json
from ftplib import FTP
import telnetlib
import time
import os
import subprocess
import signal
import sys
import csv
import tempfile
import threading
import humanize
try:
    import paramiko
    paramiko_lib = True
except ImportError:
    paramiko_lib = False
    from flame5 import sshlib
import socket
import zipfile
import re
import glob
import ast
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt_lib = True
except ImportError as e:
    plt_lib = False
import types
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring
import platform
from datetime import datetime
if platform.python_implementation() == 'IronPython':
    # Create a temporary folder where downloaded files will be stored
    temp_dir = tempfile.mkdtemp()
    filename = tempfile.gettempdir() + '/' + \
        datetime.now().strftime('%Y%m%d-%H%M%S') + "-" + 'PATE_DEBUG.txt'
    tempfile = open(filename, 'w')
    print ("Debugging logs in" + str(filename))
if platform.python_implementation() == 'IronPython':
    import xml.etree.ElementTree as ET
    from elementtree import ElementTree as ETP
else:
    import xml.etree.ElementTree as ET
    import xml.etree.ElementTree as ETP
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError
from collections import namedtuple
from shutil import copyfile, copy2, rmtree, copy
import tarfile

##################################
#        API for eLSU O&M        #
##################################
json_output = False
json_buffer = []
SSH_PORT = 22


##################################
#       Internal utilities       #
##################################
class ssh_wrapper(object):
    def __init__(self,
                 host=None,
                 port=SSH_PORT,
                 username='',
                 password='',
                 timeout=10,
                 log_file=None,
                 wait_for=["user@"]):
        """Constructor.

        Named parameters:
        host      -- IP address of the SSH server.
        port      -- SSH port. Default is 22.
        username  -- User name to shell.
        password  -- Password for user.
        timeout   -- Timeout for connection.
        log_file  -- Path to file where traffic will be logged. None if no logging
         is necessary (default).
        """
        global paramiko_lib
        self.host = host
        self.port = port
        self.timeout = timeout
        self.username = username
        self.password = password
        self.log_file_name = log_file
        self.log_file = None
        self.connection = None
        self.paramiko_lib = paramiko_lib
        self.wait_for = wait_for
        if self.paramiko_lib == True:
            self.connection = paramiko.SSHClient()
            self.connection.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
        else:
            self.connection = sshlib.SSH()
        pe_log(json_output, json_buffer,  "*DEBUG* Init with host:" + str(host) + " UNAME:" + str(
            username) + " PWD:" + str(password))

    # pylint: disable=R0913
    def connect(self,
                host=None,
                port=None,
                username=None,
                password=None,
                timeout=None):
        """Opens connetion to SSH server.

        Named parameters:
        host      -- IP address of the SSH server.
        port      -- SSH port.
        username  -- User name to shell.
        password  -- Password for user.
        timeout   -- Timeout for connection.

        Returns:
        True on successful connection.
        """
        if host == None:
            host = self.host
        if username == None:
            username = self.username
        if password == None:
            password = self.password
        pe_log(json_output, json_buffer,  "*DEBUG* Connecting to:" + str(host) + " " + str(username) + " " + str(
            password))
        if self.paramiko_lib == True:
            # pe_log(json_output, json_buffer,  "Conn"
            ret = self.connection.connect(
                host, username=username, password=password, timeout= timeout)
        else:
            ret = self.connection.open(
                host, username=username, password=password, timeout=10)
        return ret

    # pylint: enable=R0913

    def close(self):
        """Closes existing connection to server.
        """
        return self.connection.close()

    def exec_command(self, buff, expect=None, timeout=None):
        """Writes text to connection.

        Named parameters:
        buff -- Text that should be written.

        Return value:
        True on successful send.
        """
        if self.paramiko_lib == True:
            print ("*DEBUG* SSH SND> "+ str(buff))
            stdin, stdout, stderr = self.connection.exec_command(
                buff, timeout=timeout)
            errr= stderr.readlines()
            if errr:
                print (errr)
            sshoutput = stdout.readlines()
            print ("*DEBUG* SSH RCV< " + str(sshoutput))
            return sshoutput
        else:
            s = self.connection.write(buff + "\n")
            s = self.connection.expect(self.wait_for)
            ret = s.split("\n")[1:-1]
            return ret

    def invoke_shell(self):
        """Writes text to connection.

        Named parameters:
        buff -- Text that should be written.

        Return value:
        True on successful send.
        """
        if self.paramiko_lib == True:
            client = self.connection.invoke_shell()

            return client
    def send(self, buff):
        """Writes text to connection.

        Named parameters:
        buff -- Text that should be written.

        Return value:
        True on successful send.
        """
        if self.paramiko_lib == True:
            client = self.connection.invoke_shell()

            return client

#Empty function for stop 
def void():
    return False
    
# For compatibility with Python 2.6
def _check_output(*popenargs, **kwargs):
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output


# Returns the list of available PE Wireshark configuration files
def _tshark_cfg_list():
    tshark_cfg_list = _check_output(
        ['pe_tshark', '-D'], stderr=subprocess.STDOUT)
    tshark_cfg_list = tshark_cfg_list.rsplit('\n')
    del tshark_cfg_list[-1]
    tshark_cfg_list = [
        x.rsplit()[1][x.rsplit()[1].find('[LSU]') + 5:]
        for x in tshark_cfg_list
    ]
    return tshark_cfg_list


# Returns the list of a specific counter values (optionally filtered with a specific counter instance) from airmosaic
# counters csv file
def _get_counter_values(counters, counterName, subscriberName=''):
    valuesList = []
    csvCont = csv.DictReader(open(counters, 'rt'), delimiter=',')
    try:
        if subscriberName == '':
            for row in csvCont:
                valuesList.append(row[counterName])
        else:
            for row in csvCont:
                if row['Instance'] == subscriberName:
                    valuesList.append(row[counterName])
    except KeyError as e:
        pe_log(json_output, json_buffer, "*WARN* " + str(e))
        pass
    #print (valuesList)
    return valuesList


def pe_log(json_output, json_buffer, output, additional=""):
    global tempfile
    time = datetime.now().strftime('%Y%m%d-%H%M%S')
    if platform.python_implementation() == 'IronPython':
        if '*DEBUG*' not in output:
            output = str(output).replace('*INFO* ', '')
            output = str(output).replace('*WARN* ', '')
            print (output)
        output.replace('*DEBUG*', '')
        tempfile.write(time + ' ' + str(output))
        tempfile.write("\n")
        tempfile.flush()
    else:
        #print (str(output))
        sys.stdout.write(str(output) + '\n')
        sys.stdout.flush()
        if json_output == True:
            if '*DEBUG*' not in output:
                str(output).replace('*INFO*', '')
                json_buffer.append(output)


def _save_counters_plot(test_home, data_to_plot, x_label):
    if plt_lib == False:
        pe_log(json_output, json_buffer,
               "*INFO* Plot function not available on this platform")
        return True
    try:
        test_name = os.path.split(test_home)[1]
        if test_name == '':
            test_name = os.path.split(test_home[:-1])[1]
        test_name = '_'.join(test_name.rsplit('_')[1:])
        counters_by_type = {'groups': [], 'subscribers': [], 'cells': []}
        for elem in data_to_plot:
            if elem['counter_type'] == 'Group':
                counters_by_type['groups'].append(elem)
            elif elem['counter_type'] == 'Subscriber':
                counters_by_type['subscribers'].append(elem)
            elif elem['counter_type'] == 'Cell':
                counters_by_type['cells'].append(elem)
        for elemkey in counters_by_type.keys():
            independent_counters = {}
            if len(counters_by_type[elemkey]) > 0:
                for elem in counters_by_type[elemkey]:
                    if not (elem['counter_name'] in
                            independent_counters.keys()):
                        independent_counters[elem['counter_name']] = [elem]
                    else:
                        independent_counters[elem['counter_name']].append(elem)
                for counter_name in independent_counters.keys():
                    fig = plt.figure()
                    #ax1 = fig.add_subplot(1, 1, 1, facecolor='white')
                    ax1 = fig.add_subplot(1, 1, 1)
                    legends_list = []
                    for elem in independent_counters[counter_name]:
                        #x = elem['timestamps']
                        x=  np.array(elem['timestamps'], dtype=float)
                        y = elem['counter_vals']
                        for i in range(len(y)):
                            if y[i] == 'null':
                                y[i] = 0
                        y =  np.array(y, dtype=float)
                        counter_category=counter_name.split("->")[-2]
                        if "RRC" in counter_category:
                            counter_category=""
                        y_label = counter_category+" " +counter_name.split("->")[-1]
                        title = counter_name
                        legends_list.append(elem['counter_instance'])

                        plt.plot(x, y)
                        #pe_log(False,[],"*INFO* "+ str(x))
                        #pe_log(False,[],"*INFO* "+ str(y))
                        #Uncomment when debugging
                        #plt.show()
                        plt.title(title)
                        plt.ylabel(y_label)
                        plt.xlabel(x_label)
                    if len(legends_list) < 32:
                        plt.legend(legends_list, fontsize='xx-small')
                    plt.savefig(
                        os.path.join(test_home, test_name + '_' + elemkey
                                     + title.replace('->', '').replace(
                                         ' ', '').replace('%', '').replace(
                                             '/', '') + '.png'))
                    plt.close(fig)
    except Exception as e:
        pe_log(json_output, json_buffer,
               "*INFO* Plot function not available on this platform:"+str(e))
    return True


# Check an IPv4 is formally correct
def _is_ip_v4(ip):
    ip_split = ip.rsplit('.')
    if len(ip_split) != 4:
        return False
    for elem in ip_split:
        try:
            ip_digit = int(elem)
        except ValueError:
            return False
        if (ip_digit < 0) or (ip_digit > 255):
            return False
    return True


def _indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def getPPUFromScenario(sid, scenario):
    """Get The PPU from a sid and scenario, useful when need to cope with LSU and PPU like getting trcinfo or removing traces only on a PPU
    Returns error in case cell does not exists or lsu is not reachable.

    :param sid: path of sid configuration file
    :param scenario: full path of scenario file
    :return: {'result':'success|failed','error':'','ppu':ppu_list}

    |

    :example: getPPUFromScenario( "test.sid","test.sce" )
    :example output: {'result': 'success', 'ppu': [u'10', u'20'], 'error': ''}
    """
    from .pylsu import getCellPPU
    ppu = []
    LSUip = getIPsFromSid(sid)[0]['value']
    pe_log(json_output, json_buffer, "*DEBUG* " + str(LSUip))
    try:
        socket.inet_aton(LSUip)
    except:
        return {
            'result': 'failed',
            'error': 'could not get a valid IP from Sid',
            'info': LSUip
        }
    cells = getCellsFromScenario(scenario)
    if cells == []:
        return {
            'result': 'failed',
            'error': 'could not get a valid cell from Scenario',
            'info': cells
        }
    pe_log(json_output, json_buffer,  "*DEBUG* " + str(cells))
    for cell in cells:
        # pe_log(json_output, json_buffer,  cell['cells']
        # Check for HO
        if "," in cell['cells']:
            # pe_log(json_output, json_buffer,  "HO in scenario"
            ho_cells = cell['cells'].split(',')
            pe_log(json_output, json_buffer,  "*DEBUG* " + str(ho_cells))
            for ho_cell in ho_cells:
                # pe_log(json_output, json_buffer,  ho_cell
                c_ppu = getCellPPU(LSUip, "LTE", ho_cell)
                if 'ppu' in c_ppu:
                    ppu.append(c_ppu['ppu'])
        else:
            c_ppu = getCellPPU(LSUip, "LTE", cell['cells'])
            if 'ppu' in c_ppu:
                ppu.append(c_ppu['ppu'])

    return {'result': 'success', 'error': '', 'ppu': ppu}


def getIPsFromSid(sid):
    """Get The tstm and LSU ip from a sid and scenario, useful when user doesn't want to cope with LSU internals.

    :param sid: path of sid configuration file
    :return: array of dictionary with name and value as key

    |

    :example: getIPsFromSid( "test.sid","test.sce" )
    :example output: [{'name': 'LSU', 'value': '172.17.10.152'}, {'name': 'TstmIp', 'value': '172.17.16.165'}]
    """

    root = ET.parse(sid)
    global_variables = root.findall('.//CommonServices')
    global_variables_list = []
    for elem in global_variables:
        global_variables_list.append({
            'name': "LSU",
            'value': elem.get('LSUHostname')
        })
    # pe_log(json_output, json_buffer,  global_variables_list
    global_variables = root.findall(
        './/db[@name="tstmDb"]/record/String[@name="TstmIp"]')
    for elem in global_variables:
        # pe_log(json_output, json_buffer,  elem.get('name')
        global_variables_list.append({
            'name': elem.get('name'),
            'value': elem.get('value')
        })
    alternative_lsu_ip = root.findall('.//SpecificServices/db[@name="AdvancedSettings"]/record[@name="Entry"]/String[@name="__alternative_lsu_ip"]')
    if len(alternative_lsu_ip)>0:
        alternative_lsu_ip=alternative_lsu_ip[0]
        if alternative_lsu_ip.get('value')=="" or alternative_lsu_ip.get('value')==global_variables_list[0]['value']:
            pe_log(json_output, json_buffer, "*DEBUG* " + "no alternative lsu ip address added")
        else:
            pe_log(json_output, json_buffer, "*DEBUG* " + "an alternative lsu ip address found")
            global_variables_list.append({'name': alternative_lsu_ip.get('name'),'value': alternative_lsu_ip.get('value')})
        pe_log(json_output, json_buffer,  "*DEBUG* " + str(global_variables_list))
    return global_variables_list

def getPCIFromSid(sid, rat, username="user", password="user"):
    """Get The tstm and LSU ip from a sid and scenario, useful when user doesn't want to cope with LSU internals.

    :param sid: path of sid configuration file
    :return: array of dictionary with name and value as key

    |

    :example: getIPsFromSid( "test.sid","test.sce" )
    :example output: [{'name': 'LSU', 'value': '172.17.10.152'}, {'name': 'TstmIp', 'value': '172.17.16.165'}]
    """
    from .pylsu import checkCellStatus
    root = ET.parse(sid)
    cellspci = {}
    lsu_ip = root.find('.//CommonServices').get('LSUHostname')
    cellspci['lsu']=lsu_ip
    print (cellspci)
    #cellspci['lsu']=lsu_ip
    
    cells = root.findall('.//SpecificServices/db[@name="CellDb"]/record')
    cellspci['pci']=[]
    for elem in cells:
        cellinuse=elem.find('.//Boolean[@name="UseCell"]').get('value')
        cell=elem.get('name')
        #pe_log(json_output, json_buffer,  str(cellinuse.get('name'))+" "+str(cellinuse.get('value')))
        if cellinuse=="true":
            pe_log(json_output, json_buffer,  str(elem.get('name'))+" "+str(elem.get('value')))
            pci=checkCellStatus(lsu_ip,rat, cell, username=username, password=password)['status_info']
            print (pci)
            cellspci['pci'].append({
                'cell': cell,
                'pci': pci,
            })
    pe_log(json_output, json_buffer,  cellspci)
    return 1
    alternative_lsu_ip = root.findall('.//SpecificServices/db[@name="AdvancedSettings"]/record[@name="Entry"]/String[@name="__alternative_lsu_ip"]')
    if len(alternative_lsu_ip)>0:
        alternative_lsu_ip=alternative_lsu_ip[0]
        if alternative_lsu_ip.get('value')=="" or alternative_lsu_ip.get('value')==global_variables_list[0]['value']:
            pe_log(json_output, json_buffer, "*DEBUG* " + "no alternative lsu ip address added")
        else:
            pe_log(json_output, json_buffer, "*DEBUG* " + "an alternative lsu ip address found")
            global_variables_list.append({'name': alternative_lsu_ip.get('name'),'value': alternative_lsu_ip.get('value')})
        pe_log(json_output, json_buffer,  "*DEBUG* " + str(global_variables_list))
    return global_variables_list

def getUsrFromSid(sid):
    """Get The tstm and LSU ip from a sid and scenario, useful when user doesn't want to cope with LSU internals.

    :param sid: path of sid configuration file
    :return: array of dictionary with name and value as key

    |

    :example: getIPsFromSid( "test.sid","test.sce" )
    :example output: [{'name': 'LSU', 'value': '172.17.10.152'}, {'name': 'TstmIp', 'value': '172.17.16.165'}]
    """
    cont = ETP.iterparse(sid, events=("start", "end"))
    mdl_name = ""
    for action, elem in iter(cont):
        if 'external' in elem.attrib:
            mdl_name = elem.attrib['external']
            break
        elem.clear
    return mdl_name



def getAmmFromSce(sce):
    """Get The tstm and LSU ip from a sid and scenario, useful when user doesn't want to cope with LSU internals.

    :param sid: path of sid configuration file
    :return: array of dictionary with name and value as key

    |

    :example: getIPsFromSid( "test.sid","test.sce" )
    :example output: [{'name': 'LSU', 'value': '172.17.10.152'}, {'name': 'TstmIp', 'value': '172.17.16.165'}]
    """
    root = ET.parse(sce)
    amm_sce = root.find('.//AmmExternalLinkedFiles')
    if amm_sce is not None:
        return True
    else:
        return False
    # pe_log(json_output, json_buffer,  global_variables_list


def getTstmPortFromSid(sid):
    """Get The tstm and LSU ip from a sid and scenario, useful when user doesn't want to cope with LSU internals.

    :param sid: path of sid configuration file
    :return: array of dictionary with name and value as key

    |

    :example: getIPsFromSid( "test.sid","test.sce" )
    :example output: [{'name': 'LSU', 'value': '172.17.10.152'}, {'name': 'TstmIp', 'value': '172.17.16.165'}]
    """
    root = ET.parse(sid)
    global_variables = root.findall(
        './/SpecificServices/db[@name="AdvancedSettings"]/record/Integer[@name="__tstmtcpport"]'
    )
    global_variables_list = []
    try:
        tstm_port = global_variables[0].get('value')
        if tstm_port == "-1":
            tstm_port = ""
    except:
        tstm_port = ""
    # pe_log(json_output, json_buffer,  global_variables_list
    return {'result': 'success', 'error': '', 'tstm_port': tstm_port}


def get3GPPReleaseFromSid(sid):
    """Get The 3GPP release from sid, useful when LTE tstm is not running and must be started.

    :param sid: path of sid configuration file
    :return: string with 3GPP release that can be joined to \"startLteFddUuTstmGUI\" 


    :example: getIPsFromSid( "test.sid" )
    :example output: "Jun16"
    """
    root = ET.parse(sid)
    gpp_release = root.findall('.//SpecificServices')  # .get("Release")
    for rel in gpp_release:
        # pe_log(json_output, json_buffer,  rel.get("Release")
        try:
            compact_rel = rel.get("Release").split(" ")
            tst_rel = compact_rel[0][:3] + compact_rel[1][-2:]
        except:
            compact_rel = rel.get("Version")
            if compact_rel == "1.1":
                tst_rel="Sep17"
                try:
                   compact_rel = rel.get("Perspective")
                   if compact_rel == "LTE_CLASSIC" :
                       tst_rel="Mar18" 
                except:
                    pass
        # pe_log(json_output, json_buffer,  tst_rel
    return tst_rel


def getRatFromSid(sid):
    """Get The 3GPP release from sid, useful when LTE tstm is not running and must be started.

    :param sid: path of sid configuration file
    :return: string with 3GPP release that can be joined to \"startLteFddUuTstmGUI\"


    :example: getRatFromSid( "test.sid" )
    :example output: "LTE"
    """
    rat = {"Lte_Tm": "LTE", "UmtsUu_Tm": "UMTS",
           "Um_Tm": "GSM", "5g_Tm": "5Gv"}
    root = ET.parse(sid)
    services = root.findall('.//SpecificServices')
    for tstm_services in services:
        try:
            selected_rat = rat[tstm_services.get("SpecificTstmName")]
            if selected_rat=="LTE" and root.getroot().attrib['AppVersion'].split()[1]=="V5G":
                selected_rat = rat["5g_Tm"]
            break
        except:
            selected_rat = "Unknown"
    return selected_rat


def getCellsFromScenario(scenario):
    """Get The cells used in a scenario, useful when user doesn't want to cope with LSU internals.

    :param scenario: path of scenario file
    :return: array of dictionary with cells and group_name as key

    |

    :example: getCellsFromScenario("test.sce" )
    :example output: [{'cells': '1', 'group_name': 'Sector1'}, {'cells': '2', 'group_name': 'Sector2'}]

    """
    root = ET.parse(scenario)
    groups_sec = root.findall('.//Group')
    groups = []
    for elem in groups_sec:
        cells = []
        group_name = elem.get('name')
        mobility_sec = root.find('.//Group[@name="' + group_name +
                                 '"]/TemplateProfileMobility')
        if mobility_sec is None:
            pe_log (json_output,json_buffer, '*WARN* getCellsFromScenario(): no cell information found in {0}'.format(scenario))
            return groups
        if ' ' in group_name:
            group_name = "'" + group_name + "'"
        if mobility_sec.get('name') == 'Mobility.MultiCellMobility':
            serving_cell = mobility_sec.get('CELL_NUM')
            if serving_cell == None:
                # This means that this is an LTE scenario
                target_cells_sec_list = mobility_sec.get(
                    'CellCompositeList').rsplit(';')[1].rsplit(':')
                for target_cell_sec in target_cells_sec_list:
                    cells.append(target_cell_sec)
            else:
                target_cells_sec_list = mobility_sec.get(
                    'TGT_MULTI_ACTIVE_SET').rsplit(';')[1:]
                cells.append(serving_cell)
                for target_cell_sec in target_cells_sec_list:
                    cells.append(target_cell_sec.rsplit(':')[0])
            groups.append({'group_name': group_name, 'cells': ','.join(cells)})
        elif mobility_sec.get('name') == 'Mobility.CellPingPong':
            serving_cell = mobility_sec.get('InitialCell')
            cells.append(serving_cell)
            cells.append(mobility_sec.get('FinalCell'))
            groups.append({'group_name': group_name, 'cells': ','.join(cells)})
        elif mobility_sec.get('name') == 'Mobility.SimpleCellTransition':
            serving_cell = mobility_sec.get('InitialCell')
            cells.append(serving_cell)
            cells.append(mobility_sec.get('FinalCell'))
            groups.append({'group_name': group_name, 'cells': ','.join(cells)})
        # AMM case
        elif mobility_sec.get(
                'name'
        ) == 'com.prisma.mobility.mobilityplugin.MapDrivenMobility':
            cell_binding_sec = root.find('.//MdmCellBinding').text
            cell_binding_xml = ET.fromstring(cell_binding_sec)
            entry_list = cell_binding_xml.findall('.//entry')
            for cell_elem in entry_list:
                tmpCellVal = cell_elem.find('.//value').text
                if tmpCellVal != 'none':
                    cells.append(tmpCellVal)
                else:
                    pe_log (json_output,json_buffer, '*WARN* getCellsFromScenario(): found unconfigured AMM cell in scenario {0} !'.format(scenario))
            groups.append({'group_name': group_name, 'cells': ','.join(cells)})
        else:
            serving_cell = mobility_sec.get('CELL_NUM')
            if serving_cell == None:
                serving_cell = mobility_sec.get('Cell')
            groups.append({'group_name': group_name, 'cells': serving_cell})
    # Enable if you need debugging
    # pe_log(json_output, json_buffer,  json.dumps(groups)
    return groups


def editSceFile(rat, sce, **kwargs):
    """
    Edit cells in the given Airmosaic sce file.
    NB: it can modify the value of the given cells_list
    :param cells_list: list of cells used in the scenario
    :param rat: radio access technology in use (GSM/UMTS/LTE)
    :param sce: path to the Airmosaic sce file to be edited
    :param kwargs: cells_list, in this format:...
    :return:
    """
    cells_list_sce = None
    if 'cells_list' in kwargs:
        cells_list_sce = kwargs['cells_list']
    pe_log(json_output, json_buffer, '*DEBUG* Cells list: %s' % cells_list_sce)

    if not os.path.exists(sce):
        pe_log(
            json_output, json_buffer,
            "*ERROR* Can't find scenario file: %s Test will be aborted!" % sce)
        sys.exit("Can't find %s" % sce)

    try:
        sce_xml = ET.parse(sce)
    except ExpatError:
        pe_log(json_output, json_buffer,
               "*WARN* Warning: could not edit scenario file")
        return -1
    root = sce_xml.getroot()
    gr = root.findall('.//Group')
    pe_log(json_output, json_buffer, '*DEBUG* editSceFile(): gr={0}'.format(str(gr)))
    if cells_list_sce is not None:
        # Handle the special case in which 'all_groups' key is passed in
        # cells_list_sce
        if 'all_groups' in cells_list_sce:
            for elem in gr:
                cells_list_sce[elem.get('name')] = cells_list_sce['all_groups']
            del cells_list_sce['all_groups']
        #pe_log(json_output, json_buffer, '*DEBUG* editSceFile(): cells_list_sce: %s' % cells_list_sce)
        for elem in cells_list_sce:
            mob_profile = root.find('.//Group[@name="%s"]/TemplateProfileMobility' % elem)
            #pe_log(json_output, json_buffer, '*DEBUG* editSceFile(): mob_profile={0}'.format(str(mob_profile)))
            if mob_profile is not None:
                # TAa nothing to do for this     
                continue
            if rat == 'UMTS':
                pe_log(json_output, json_buffer,
                       '*DEBUG* Current serving cell for group %s: %s' %
                       (elem, mob_profile.get('CELL_NUM')))
                pe_log(json_output, json_buffer,
                       '*DEBUG* Setting serving cell to %s' %
                       cells_list_sce[elem][0])
                mob_profile.set('CELL_NUM', cells_list_sce[elem][0])
            elif rat == 'LTE':
                if mob_profile:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Current serving cell for group %s: %s' %
                           (elem, mob_profile.get('Cell')))
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Setting serving cell to %s' %
                           cells_list_sce[elem][0])
                    mob_profile.set('Cell', cells_list_sce[elem][0])
                else:
                    print ('*INFO* NO mob_profile intialized')
            elif rat == '5Gv':
                pe_log(json_output, json_buffer,
                       '*DEBUG* Current serving cell for group %s: %s' %
                       (elem, mob_profile.get('Cell')))
                pe_log(json_output, json_buffer,
                       '*DEBUG* Setting serving cell to %s' %
                       cells_list_sce[elem][0])
                mob_profile.set('Cell', cells_list_sce[elem][0])
            elif rat == '5Gnr':
                pe_log(json_output, json_buffer,
                       '*DEBUG* Current serving cell for group %s: %s' %
                       (elem, mob_profile.get('Cell')))
                pe_log(json_output, json_buffer,
                       '*DEBUG* Setting serving cell to %s' %
                       cells_list_sce[elem][0])
                mob_profile.set('Cell', cells_list_sce[elem][0])
            elif rat == 'GSM':
                pe_log(json_output, json_buffer,
                       '*DEBUG* Current serving cell for group %s: %s' %
                       (elem, mob_profile.get('CELL_NUM')))
                pe_log(json_output, json_buffer,
                       '*DEBUG* Setting serving cell to %s' %
                       cells_list_sce[elem][0])
                mob_profile.set('CELL_NUM', cells_list_sce[elem][0])
            # Now set HO path, if more than one cell have been passed for this
            # group
            num_cells = len(cells_list_sce[elem])
            if num_cells > 1:
                if rat == 'UMTS':
                    try:
                        active_set = mob_profile.get(
                            'TGT_MULTI_ACTIVE_SET').rsplit(';')
                        pe_log(json_output, json_buffer,
                               "*DEBUG* Current HO Path for group %s: %s " %
                               (elem, mob_profile.get('TGT_MULTI_ACTIVE_SET')))
                    except AttributeError:
                        pe_log(
                            json_output, json_buffer,
                            "*INFO* Group %s do not contain handover procedures. Skipping activeset editing..."
                            % elem)
                        active_set = []  # This way the script can carry on
                    for i in range(len(active_set) - 1):
                        if i < (num_cells - 1):
                            active_set[i + 1] = re.sub(
                                '[0-9]*', cells_list_sce[elem][i + 1],
                                active_set[i + 1], 1)
                    comp_act_set = ';'.join(active_set)
                    pe_log(json_output, json_buffer,
                           "*DEBUG* Final HO path for group %s: %s" %
                           (elem, comp_act_set))
                    mob_profile.set('TGT_MULTI_ACTIVE_SET', comp_act_set)
                elif rat == 'LTE' or rat == '5Gv':
                    if mob_profile.get('name') == 'Mobility.MultiCellMobility':
                        try:
                            active_set = mob_profile.get(
                                'CellCompositeList').rsplit(';')
                            pe_log(
                                json_output, json_buffer,
                                "*DEBUG* Current mobility profile for group %s: Mobility.MultiCellMobility"
                                % elem)
                            pe_log(
                                json_output, json_buffer,
                                "*DEBUG* Current HO Path for group %s: %s " %
                                (elem, mob_profile.get('CellCompositeList')))
                        except AttributeError:
                            pe_log(
                                json_output, json_buffer,
                                "*INFO* Group %s do not contain handover procedures. Skipping activeset editing..."
                                % elem)
                            active_set = []  # This way the script can carry on
                        if len(active_set) > 0:
                            active_set = ','.join(
                                list(set(cells_list_sce[elem])))
                            active_set += ';'
                            active_set += ':'.join(cells_list_sce[elem])
                            pe_log(json_output, json_buffer,
                                   "*DEBUG* Final HO path for group %s: %s" %
                                   (elem, active_set))
                            mob_profile.set('CellCompositeList', active_set)
                    elif (mob_profile.get('name') == 'Mobility.CellPingPong') and (len(cells_list_sce[elem]) >= 2):
                        pe_log(
                            json_output, json_buffer,
                            "*DEBUG* Current mobility profile for group %s: Mobility.CellPingPong"
                            % elem)
                        pe_log(json_output, json_buffer,
                               "*DEBUG* Current start cell for group %s: %s" %
                               (elem, mob_profile.get('InitialCell')))
                        pe_log(json_output, json_buffer,
                               "*DEBUG* Current end cell for group %s: %s" %
                               (elem, mob_profile.get('FinalCell')))
                        mob_profile.set('InitialCell', cells_list_sce[elem][0])
                        mob_profile.set('FinalCell', cells_list_sce[elem][1])
                    elif (mob_profile.get('name') ==
                          'Mobility.SimpleCellTransition') and (
                              len(cells_list_sce[elem]) >= 2):
                        pe_log(
                            json_output, json_buffer,
                            "*DEBUG* Current mobility profile for group %s: Mobility.SimpleCellTransition"
                            % elem)
                        pe_log(json_output, json_buffer,
                               "*DEBUG* Current start cell for group %s: %s" %
                               (elem, mob_profile.get('InitialCell')))
                        pe_log(json_output, json_buffer,
                               "*DEBUG* Current end cell for group %s: %s" %
                               (elem, mob_profile.get('FinalCell')))
                        mob_profile.set('InitialCell', cells_list_sce[elem][0])
                        mob_profile.set('FinalCell', cells_list_sce[elem][1])
                    else:
                        active_set = []  # This way the script can carry on
    # Write output scenario file
    sce_xml.write(sce)
    return 0


def editSidFile(rat, sid, **kwargs):
    """
    Edit some parameters in the given Airmosaic sid file. Can edit LSU IP, TSTM IP and
    cells list. The latter must be passed in this format: ...
    :param rat: radio access technology in use (GSM/UMTS/LTE)
    :param sid: path to the Airmosaic sid file to be edited
    :param kwargs: lsu_ip,tstm_ip,cells,nodeb_ids,pcis,duplex_mode
    :return:
    """
    lsu_ip = None
    tstm_ip = None
    tstm_port = None
    cells = None
    nodeb_ids = None
    pcis = None
    duplex_modes = None
    ded_lsu_ip = None

    if 'lsu_ip' in kwargs:
        lsu_ip = kwargs['lsu_ip']
        if lsu_ip == '':
            lsu_ip = None
    if 'tstm_ip' in kwargs:
        tstm_ip = kwargs['tstm_ip']
        if ':' in tstm_ip:
            tstm_port = tstm_ip.rsplit(':')[1]
            tstm_ip = tstm_ip.rsplit(':')[0]
    if 'cells' in kwargs:
        cells = kwargs['cells']
    if 'nodeb_ids' in kwargs:
        nodeb_ids = kwargs['nodeb_ids']
    if 'pcis' in kwargs:
        pcis = kwargs['pcis']
    if 'duplex_mode' in kwargs:
        duplex_modes = kwargs['duplex_mode']
    if 'ded_lsu_ip' in kwargs:
        ded_lsu_ip = kwargs['ded_lsu_ip']
        if ded_lsu_ip == '':
            ded_lsu_ip = None

    if not (os.path.exists(sid)):
        pe_log(json_output, json_buffer,
               "*ERROR* Can't find sid file: %s Test will be aborted!" % sid)
        sys.exit("Can't find %s" % sid)

    # If a dedicated LSU ip has been defined it is the actual LSU IP in sid. The O&M IP is used only in 3G for
    # lsugetreport collection
    if ded_lsu_ip is not None:
        om_lsu_ip = lsu_ip
        lsu_ip = ded_lsu_ip

    try:
        sid_xml = ET.parse(sid)
    except ExpatError:
        pe_log(json_output, json_buffer,
               "*WARN* Warning: could not edit sid file")
        return -1
    root = sid_xml.getroot()
    # Change LSU ip
    if lsu_ip is not None:
        pe_log(json_output, json_buffer, '*DEBUG* Changing LSU ip...')
        elem = root.find('.//CommonServices[@LSUHostname]')
        if elem is not None:
            if elem is not None:
                if ded_lsu_ip is not None:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found LSUHostname: %s, changed to %s' % (elem.attrib, ded_lsu_ip))
                    elem.set('value', lsu_ip)
                else:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found LSUHostname: %s, changed to %s' % (elem.attrib, lsu_ip))
        # LSU ip address must be set in some other places in case of LTE sid
        if rat == 'LTE' or rat == '5Gv':
            elem = root.find('.//String[@name="__ltel2_ipaddress"]')
            if elem is not None:
                if ded_lsu_ip is not None:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __ltel2_ipaddress: %s, changed to %s' % (elem.attrib, ded_lsu_ip))
                    elem.set('value', lsu_ip)
                else:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __ltel2_ipaddress: %s, changed to %s' % (elem.attrib, lsu_ip))
                    elem.set('value', lsu_ip)
            elem = root.find('.//String[@name="__ipsig_ip"]')
            if elem is not None:
                if ded_lsu_ip is not None:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __ipsig_ip: %s, changed to %s' % (elem.attrib, ded_lsu_ip))
                    elem.set('value', lsu_ip)
                else:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __ipsig_ip: %s, changed to %s' % (elem.attrib, lsu_ip))
                    elem.set('value', lsu_ip)
            elem = root.find('.//String[@name="__lsu_ip_addr"]')
            if elem is not None:
                if ded_lsu_ip is not None:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __lsu_ip_addr: %s, changed to %s' % (elem.attrib, ded_lsu_ip))
                    elem.set('value', lsu_ip)
                else:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __lsu_ip_addr: %s, changed to %s' % (elem.attrib, lsu_ip))
                    elem.set('value', lsu_ip)
            elem = root.find('.//String[@name="__rtp_address"]')
            if elem is not None:
                if ded_lsu_ip is not None:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __rtp_address: %s, changed to %s' % (elem.attrib, ded_lsu_ip))
                    elem.set('value', lsu_ip)
                else:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Found __rtp_address: %s, changed to %s' % (elem.attrib, lsu_ip))
                    elem.set('value', lsu_ip)
        # In case of UMTS the O&M IP for lsugetreport can be set
        elif rat == 'UMTS':
            elem = root.find('.//String[@name="__alternative_lsu_ip"]')
            if elem is not None:
                pe_log(json_output, json_buffer,
                       '*DEBUG* Found __alternative_lsu_ip: %s, changed to %s' % elem.attrib)
                if ded_lsu_ip is not None:
                    pe_log(json_output, json_buffer,
                           '*DEBUG* Setting __alternative_lsu_ip to %s' %
                           om_lsu_ip)
                    elem.set('value', om_lsu_ip)
                else:
                    pe_log(
                        json_output, json_buffer,
                        '*DEBUG* Setting __alternative_lsu_ip to %s' % lsu_ip)
                    elem.set('value', lsu_ip)

    # Change TSTM ip
    if tstm_ip is not None:
        pe_log(json_output, json_buffer, '*DEBUG* Changing TSTM ip...')
        # Change TSTM ip in the old sid format
        elem = root.find('.//CommonServices[@TestManagerHostname]')
        if elem is not None:
            pe_log(json_output, json_buffer,
                   '*DEBUG* Found TestManagerHostname: %s, change to %s' % (elem.attrib, tstm_ip))
            elem.set('TestManagerHostname', tstm_ip)
        # Change TSTM IP in the new SID file format
        elem = root.find('.//String[@name="TstmIp"]')
        if elem is not None:
            pe_log(json_output, json_buffer,
                   '*DEBUG* Found TstmIp: %s, change to %s' % (elem.attrib, tstm_ip))
            elem.set('value', tstm_ip)
        # Change TSTM port
        if tstm_port is not None:
            elem = root.find('.//Integer[@name="__tstmtcpport"]')
            if elem is not None:
                pe_log(json_output, json_buffer,
                       '*DEBUG* Found __tstmtcpport: %s, change to %s' % (elem.attrib, tstm_port))
                elem.set('value', tstm_port)

    # Change cells
    if cells is not None:
        pe_log(json_output, json_buffer,
               '*DEBUG* Editing SID cells...\n"Cells" content is: %s' % cells)
        if rat == 'UMTS':
            if nodeb_ids is None:
                pe_log(
                    json_output, json_buffer,
                    '*DEBUG* NodeB IDs not given, setting all NodeB IDs to 0')
                nodeb_ids = ['0'] * len(cells)
            elif len(cells) != len(nodeb_ids):
                pe_log(
                    json_output, json_buffer,
                    '*WARN* Number of NodeB Ids is different from number of cells. Setting'
                    'all to 0')
                nodeb_ids = ['0'] * len(cells)
            # First, remove all the old cell entries
            cells_root = root.find('.//SpecificServices')
            cells_db = root.find('.//db[@name="CellId"]')
            cells_root.remove(cells_db)
            # Now, add the required entries
            cells_db = ET.Element('db', {
                'name': 'CellId',
                'version': '1.0',
                'formatname': 'CellId'
            })
            for elem, Telem in zip(cells, nodeb_ids):
                pe_log(
                    json_output, json_buffer,
                    '*DEBUG* Creating cell entry: Cell Id = %s\tNodeB Id = %s'
                    % (elem, Telem))
                cell_record_root = ET.Element(
                    'record', {'name': elem,
                               'modifiable': 'true'})
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'CellIdx',
                                           'value': elem}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'PSC',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'DL_ARFCN',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'UL_ARFCN',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'Sensitivity',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'PathLoss',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'CPichPower',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String',
                               {'name': 'NumOutOfSynch',
                                'value': ''}))
                cell_record_root.append(
                    ET.Element('Boolean', {'name': 'UseCell',
                                           'value': 'true'}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'tcell',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'NodeBId',
                                          'value': Telem}))
                cell_record_root.append(
                    ET.Element('String',
                               {'name': 'CellStatus',
                                'value': 'Unknown'}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'CellReady',
                                           'value': ''}))
                cells_db.append(cell_record_root)
            cells_root.append(cells_db)
        if rat == 'LTE':
            # Handle empty/too short Physical Cell Identifier lists
            if pcis is None:
                pe_log(
                    json_output, json_buffer,
                    '*DEBUG* Physical cell identifier not given. Trying to reuse those already in the sid file'
                )
                cell_entries = root.findall('.//db[@name="CellDb"]/record')
                old_cells = {}
                pcis = []
                # Loading PCIs from currently loaded sid
                for elem in cell_entries:
                    old_cells[elem.get('name')] = elem.find(
                        './/Integer[@name="PhysicalCellIdentifier"]').get(
                            'value')
                # Try to associate old PCIs to the new cells list, based on
                # cell id
                for elem in cells:
                    if elem in old_cells:
                        pe_log(json_output, json_buffer,
                               '*DEBUG* Using old PCI %s for cell %s' %
                               (old_cells[elem], elem))
                        pcis.append(old_cells[elem])
                    else:
                        pe_log(
                            json_output, json_buffer,
                            '*DEBUG* Using Cell Id as PCI for cell %s' % elem)
                        pcis.append(elem)
            elif len(cells) != len(pcis):
                pe_log(
                    json_output, json_buffer,
                    '*WARN* Number of Physical Cell Identifiers is different from number of cells. Trying to use the old values'
                )
                cell_entries = root.findall('.//db[@name="CellDb"]/record')
                old_cells = {}
                pcis = []
                # Loading PCIs from currently loaded sid
                for elem in cell_entries:
                    old_cells[elem.get('name')] = elem.find(
                        './/Integer[@name="PhysicalCellIdentifier"]').get(
                            'value')
                # Try to associate old PCIs to the new cells list, based on
                # cell id
                for elem in cells:
                    if elem in old_cells:
                        pe_log(json_output, json_buffer,
                               '*DEBUG* Using old PCI %s for cell %s' %
                               (old_cells[elem], elem))
                        pcis.append(old_cells[elem])
                    else:
                        pe_log(
                            json_output, json_buffer,
                            '*DEBUG* Using Cell Id as PCI for cell %s' % elem)
                        pcis.append(elem)

            # Handle empty/too short duplex mode lists
            if duplex_modes is None:
                pe_log(
                    json_output, json_buffer,
                    '*DEBUG* Duplex mode not given. Trying to reuse those already in the sid file'
                )
                cell_entries = root.findall('.//db[@name="CellDb"]/record')
                old_cells = {}
                duplex_modes = []
                # Loading duplex modes from currently loaded sid
                for elem in cell_entries:
                    old_cells[elem.get('name')] = elem.find(
                        './/String[@name="Mode"]').get('value')
                # Try to associate old duplex modes to the new cells list,
                # based on cell id
                for elem in cells:
                    if elem in old_cells:
                        pe_log(json_output, json_buffer,
                               '*DEBUG* Using old duplex mode %s for cell %s' %
                               (old_cells[elem], elem))
                        duplex_modes.append(old_cells[elem])
                    else:
                        pe_log(json_output, json_buffer,
                               '*DEBUG* Using FDD as duplex mode for cell %s' %
                               elem)
                        duplex_modes.append('FDD')
            elif len(cells) != len(duplex_modes):
                pe_log(
                    json_output, json_buffer,
                    '*WARN* Number of duplex modes is different from number of cells. Trying to use the old values'
                )
                cell_entries = root.findall('.//db[@name="CellDb"]/record')
                old_cells = {}
                duplex_modes = []
                # Loading duplex modes from currently loaded sid
                for elem in cell_entries:
                    old_cells[elem.get('name')] = elem.find(
                        './/String[@name="Mode"]').get('value')
                # Try to associate old duplex modes to the new cells list,
                # based on cell id
                for elem in cells:
                    if elem in old_cells:
                        pe_log(json_output, json_buffer,
                               '*DEBUG* Using old duplex mode %s for cell %s' %
                               (old_cells[elem], elem))
                        duplex_modes.append(old_cells[elem])
                    else:
                        pe_log(json_output, json_buffer,
                               '*DEBUG* Using FDD as duplex mode for cell %s' %
                               elem)
                        duplex_modes.append('FDD')
            # First, remove all the old cell entries
            cells_root = root.find('.//SpecificServices')
            cells_db = root.find('.//db[@name="CellDb"]')
            cells_root.remove(cells_db)
            # Now, add the required entries
            cells_db = ET.Element('db', {
                'name': 'CellDb',
                'version': '1.0',
                'formatname': 'CellDb'
            })
            for elem, Telem, Delem in zip(cells, pcis, duplex_modes):
                pe_log(
                    json_output, json_buffer,
                    '*DEBUG* Creating cell entry: Cell Id = %s\tPCI = %s\tDuplex mode = %s'
                    % (elem, Telem, Delem))
                cell_record_root = ET.Element(
                    'record', {'name': elem,
                               'modifiable': 'true'})
                cell_record_root.append(
                    ET.Element('Boolean', {'name': 'UseCell',
                                           'value': 'true'}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'CellIdx',
                                           'value': elem}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'Mode',
                                          'value': Delem}))
                cell_record_root.append(
                    ET.Element('Integer', {
                        'name': 'PhysicalCellIdentifier',
                        'value': Telem
                    }))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'FreqBand',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'UlEarfcn',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'DlEarfcn',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'NumAntennas',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer',
                               {'name': 'AntennaBitmask',
                                'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'OutPwrStr',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'OutPwr',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'Sens0Str',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'Sens0',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'Sens1Str',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'Sens1',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'Sens2Str',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'Sens2',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'Sens3Str',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'Sens3',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'SDRNum',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String',
                               {'name': 'CellStatus',
                                'value': 'Unknown'}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'CMAS',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'ETWS',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'SNR0',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'SNR1',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'PL0',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'PL1',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'RSPL0',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'RSPL1',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'PDSCHBL',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'PHICHNAKR',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'SibWindow',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String',
                               {'name': 'FadingFilename',
                                'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'LocalCellId',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Boolean', {'name': 'IsMaster',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'aggrId',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('Integer', {'name': 'icisId',
                                           'value': ''}))
                cell_record_root.append(
                    ET.Element('String', {'name': 'SDRId',
                                          'value': ''}))
                cell_record_root.append(
                    ET.Element('Boolean',
                               {'name': 'DlHARQEnable',
                                'value': ''}))
                cells_db.append(cell_record_root)
            cells_root.insert(0, cells_db)

    # Beautify xml output
    root = sid_xml.getroot()
    pe_log(json_output, json_buffer, '*DEBUG* Beautifying the output sid')
    _indent(root)
    sid_xml.write(sid, encoding='UTF-8')
    return 0


def resultAnalysis(**kwargs):
    """Function for postprocessing of test cases execution outputs'':'' lsu logs, TSTM logs, wireshark logs, airmosaic counters and Test result xml from Airmosaic

    :param rat: rat of the test executed "LTE", "UMTS" or "GSM"
    :param wireshark_analysis: set to True when result analysis check has to be done also on Wireshark capture file
    :param test_dir: directory where to put result file of analysis
    :param ppu: list of ppu for exctracting trcinfo log (e.g. ["10","20"])
    :param lsu_ip: ip of LSU (useful if save_lsu_logs=True)
    :param check_string: string to be checheck for counters in csv (e.g. "Cell,1,Layer 1->General Counters->DOWNLINK->BLER on PDSCH % - Total,lv,lt,0.1|Cell,1,Layer 1->General Counters->UPLINK->NACK on PHICH %,lv,lt,5")
    :param bugreport: full path of bugreport zip file to be analyzed
    :param save_lsu_logs(optional): default True, set to False if lsugetreport is not needed
    :param fail_threshold(optional): default 100, set to a lower value to get test passed also with some failures
    :param counters_check(optional): list of counters to be checked with rule, separated by \\"\\|\\". rules are for counters\\: lv for last value, av for average. For check \\: lt for less than, gt for greated than, eq for equal

    :return: "PASSED" of "FAILED" with a string of failed procedures

    """
    from .pylsu import getLSUlogs
    from .pymosaic import closeLocalAirMosaic
    fail_threshold = '100'
    remote_ip = None
    counters_check = None
    parse_traces = False
    save_lsu_logs = True
    wireshark_rcode = None
    counters_zip = None
    ppu_irat = None
    lsu_ip_irat = None
    is_irat = False
    same_lsu = False
    golderror = 0
    ppu = "10"
    tstmcore =0 

    import time
    
    if 'airmosaic_port' in kwargs:
        airmosaic_port = kwargs['airmosaic_port']
    else:
        airmosaic_port = "8090"
    if 'q' in kwargs:
        q=kwargs['q']
        print (q)
        sys.stdout = open( "output"+airmosaic_port+".out", "a+", buffering=0)
    else:
        q=None

    if 'rat' in kwargs:
        rat = kwargs['rat']
    else:
        return {"result": "failed", "error": "Missing mandatory rat parameter"}
    if 'test_dir' in kwargs:
        test_dir = kwargs['test_dir']
    else:
        return {
            "result": "failed",
            "error": "Missing mandatory test_dir parameter"
        }
    if 'lsu_ip' in kwargs:
        lsu_ip = kwargs['lsu_ip']
    else:
        return {
            "result": "failed",
            "error": "Missing mandatory lsu_ip parameter"
        }
    if 'ppu' in kwargs:
        ppu = kwargs['ppu']
    else:
        ppu = []
    if 'wireshark_analysis' in kwargs:
        try:
            wireshark_analysis = ast.literal_eval(kwargs['wireshark_analysis'])
        except:
            wireshark_analysis = False
    else:
        wireshark_analysis = False
    if 'check_string' in kwargs:
        check_string = kwargs['check_string']
    else:
        check_string = []
    if 'bugreport' in kwargs:
        bugreport = kwargs['bugreport']
    else:
        bugreport = []
    if 'counters' in kwargs:
        counters = kwargs['counters']
    else:
        counters = []
    if 'fail_threshold' in kwargs:
        fail_threshold = kwargs['fail_threshold']
    if 'counters_check' in kwargs:
        counters_check = kwargs['counters_check']
    if 'parse_traces' in kwargs:
        if isinstance(kwargs['parse_traces'], basestring):
            if kwargs['parse_traces'].lower() == 'true':
                parse_traces = True
        else:
            parse_traces = kwargs['parse_traces']
    if 'save_lsu_logs' in kwargs:
        if isinstance(kwargs['save_lsu_logs'], basestring):
            if kwargs['save_lsu_logs'].lower() == 'false':
                save_lsu_logs = False
            else:
                save_lsu_logs = kwargs['save_lsu_logs']
    if 'wireshark_rcode' in kwargs:
        wireshark_rcode = kwargs['wireshark_rcode']
    if 'counters_zip' in kwargs:
        counters_zip = kwargs['counters_zip']
    if 'lsu_ip_irat' in kwargs:
        lsu_ip_irat = kwargs['lsu_ip_irat']
        is_irat = True
    if 'ppu_irat' in kwargs:
        ppu_irat = kwargs['ppu_irat']
    if 'json_output' in kwargs:
        json_output = ast.literal_eval(kwargs['json_output'])
    else:
        json_output = False
    json_buffer = []
    regr_res = ''
    pe_log(json_output, json_buffer,
           ('*INFO* Result Analysis %s' % str(json_buffer)))
    #pe_log(json_output, json_buffer, '*DEBUG* resultAnalysis(): kwargs: %s' % str(kwargs))
    if 'res_failure' in kwargs:
        for logs in kwargs['res_failure']:
            if regr_res != "":
                regr_res += ","
            regr_res += " " + kwargs['res_failure'][logs]
    if lsu_ip == lsu_ip_irat:
        same_lsu = True

    if 'tstm_ip' in kwargs:
        tstm_ip = kwargs['tstm_ip']
    else:
        tstm_ip = None

    if 'tstms1_ip' in kwargs:
        tstms1_ip = kwargs['tstms1_ip']
    else:
        tstms1_ip = False
    if 'tstms1_path' in kwargs:
        tstms1_path = kwargs['tstms1_path']
    else:
        tstms1_path = None

    if isinstance(wireshark_analysis, basestring):
        if wireshark_analysis.lower() == 'true':
            wireshark_analysis = True
        else:
            wireshark_analysis = False
    if 'ppu' in ppu:
        ppu_list = list(set(ppu['ppu']))
    else:
        ppu_list = ['10']

    pe_log(json_output, json_buffer, '*DEBUG* Received PPU List: %s' % ppu)
    if is_irat:
        ppu_list_irat = ppu_irat.rsplit(',')
        if same_lsu:
            ppu_list += ppu_list_irat
            ppu += ',' + ppu_irat

    test_name = os.path.split(test_dir)[1]
    if test_name == '':
        test_name = os.path.split(test_dir[:-1])[1]

    ws_file_name = os.path.join(test_dir,
                                '%s.lsu' % '_'.join(test_name.rsplit('_')[1:]))

    if 'keep_on_server' not in kwargs:
        kwargs['keep_on_server']=True
        
    if save_lsu_logs==False:
        del kwargs['lsu_ip']

    ##SAVING LOGS
    try:
        closeLocalAirMosaic(airmosaic_port = airmosaic_port)
    except:
        pass
    time.sleep(5)
    kwargs['Log_ALL'] = True
    kwargs['test_home'] = kwargs['test_dir']


    res=save_test_logs(**kwargs)
    pe_log(json_output, json_buffer, "*DEBUG* RESULT of SAVE:"+str(res))
    if os.path.isfile(os.path.join(test_dir,"bugreport.zip")) == False:
        theZip = zipfile.ZipFile(os.path.join(test_dir,"bugreport.zip"), 'w', 8)
        try:
            theZip.write(res['airmosaic_logs'], "message.log")
        except:
            pass
        try:
            theZip.write(res['tstm_report'], "tstm.zip")
        except:
            pass
        theZip.close()
    # Saving lsugetreport, extracting traces and parsing traces for major
    # errors
    if parse_traces:
        saved_log = res['lsu_report']
        pe_log(json_output, json_buffer,
                '*DEBUG* Extracting tracelogs for PPUs: %s' % ppu_list)
        pe_log(json_output, json_buffer,
                '*DEBUG* parsing: %s' % saved_log)
        try:
            if tarfile.is_tarfile(saved_log):
                mytar = tarfile.open(saved_log)
                file_name_no_ext = '.'.join(
                    os.path.basename(saved_log).rsplit('.')[:-1])
                # Check if the new trclog format is being used
                new_trace_format = False
                for elem in mytar.getmembers():
                    if '%s/trace' % file_name_no_ext in elem.name:
                        new_trace_format = True
                        break
                if new_trace_format:
                    trclog_list = []
                    for elem in ppu_list:
                        last_mtime = 0
                        last_trclog = None
                        for memb in mytar.getmembers():
                            if "trclog.%s." % elem in memb.name:
                                if memb.mtime > last_mtime:
                                    last_mtime = memb.mtime
                                    last_trclog = memb
                                    pe_log(
                                        json_output, json_buffer,
                                        '*DEBUG* Extracting latest trclog for PPU %s: %s'
                                        % (elem, last_trclog.name))
                        try:
                            mytar.extract(last_trclog, test_dir)
                            os.rename(
                                os.path.join(test_dir, last_trclog.name),
                                os.path.join(test_dir,
                                                last_trclog.name.rsplit('/')[-1]))
                            trclog_list.append(
                                last_trclog.name.rsplit('/')[-1])
                        except:
                            pe_log(
                                json_output, json_buffer,
                                "*WARN* Couldn't extract the trace log for PPU %s from %s."
                                % (elem, saved_log))
                            continue
                    mytar.close()
                    for elem in trclog_list:
                        curr_ppu = elem.rsplit('.')[-2]
                        untar_trace_name = os.path.join(test_dir, elem)
                        dec_trace_name = os.path.join(test_dir, '%s.trclog%s' %
                                                        (test_name, curr_ppu))
                        dec_trace = open(dec_trace_name, 'w')
                        try:
                            subprocess.call(
                                ["trcinfo", untar_trace_name],
                                stdout=dec_trace)
                        except:
                            pe_log(json_output, json_buffer,
                                    "*WARN* Couldn't run trcinfo")
                            dec_trace.close()
                            continue
                        dec_trace.close()
                        # Checking for Fatal errors in the tracelog. If any is present the LSU is stopped
                        # so that it will be restarted at the beginning of
                        # the next test execution
                        dec_trace = open(dec_trace_name, 'r')
                        for line in dec_trace:
                            if (("fatal" in line.lower()) and
                                    not ("trcinfo.c" in line.lower()) and
                                    not ("FWOUT" in line) and
                                    not ("fatal = 0" in line) and
                                    not ('tcpreadblob' in line.lower())) or (
                                    "fifo full" in line.lower()):
                                pe_log(
                                    json_output, json_buffer,
                                    "*WARN* Stopping LSU due to the presence of Fatal errors in the ppu %s tracelog"
                                    % curr_ppu)
                                pe_log(json_output, json_buffer,
                                        '*INFO*' + line)

                                res = stopLSU(lsu_ip)
                                if res['result'] == 'success':
                                    pe_log(json_output, json_buffer,
                                            '*DEBUG*' + res['output'])
                                else:
                                    pe_log(json_output, json_buffer,
                                            "*WARN* Error stopping the LSU")
                                break
                            if "spool nores" in line.lower():
                                pe_log(
                                    json_output, json_buffer,
                                    "*WARN* Stopping LSU due to probable L2 Core"
                                )
                                res = stopLSU(lsu_ip)
                                if res['result'] == 'success':
                                    pe_log(json_output, json_buffer,
                                            '*DEBUG*' + res['output'])
                                else:
                                    pe_log(json_output, json_buffer,
                                            "*WARN* Error stopping the LSU")
                                break
                        dec_trace.close()
                        os.remove(untar_trace_name)
                    rmtree(os.path.join(test_dir, file_name_no_ext))
                else:
                    for elem in ppu_list:
                        trace_tar_dir = file_name_no_ext + "/tmp/trclog.%s.tar.gz" % elem
                        try:
                            mytar.extract(trace_tar_dir, test_dir)
                        except:
                            # Compressed tracelog might have a different
                            # extension
                            try:
                                trace_tar_dir = file_name_no_ext + "/tmp/trclog.%s.tgz" % elem
                                mytar.extract(trace_tar_dir, test_dir)
                            except:
                                pe_log(
                                    json_output, json_buffer,
                                    "*WARN* Couldn't extract the trace log for PPU %s from %s."
                                    % (elem, saved_log))
                                continue
                        os.rename(
                            os.path.join(test_dir, trace_tar_dir),
                            os.path.join(test_dir, "trclog.%s.tar.gz" % elem))
                        os.removedirs(
                            os.path.join(test_dir, file_name_no_ext, "tmp"))
                    mytar.close()
                    for elem in ppu_list:
                        second_tar_dir = os.path.join(
                            test_dir, "trclog.%s.tar.gz" % elem)
                        if tarfile.is_tarfile(second_tar_dir):
                            mytar = tarfile.open(second_tar_dir)
                            try:
                                mytar.extractall(test_dir)
                            except:
                                pe_log(
                                    json_output, json_buffer,
                                    "*WARN* Couldn't extract the trace log for PPU %s from %s."
                                    % (elem, second_tar_dir))
                                mytar.close()
                                continue
                            mytar.close()
                            untar_trace_name = os.path.join(
                                test_dir, "trclog.%s" % elem)
                            dec_trace_name = os.path.join(
                                test_dir, '%s.trclog%s' % (test_name, elem))
                            dec_trace = open(dec_trace_name, 'w')
                            try:
                                subprocess.call(
                                    ["trcinfo", untar_trace_name],
                                    stdout=dec_trace)
                            except:
                                pe_log(json_output, json_buffer,
                                        "*WARN* Couldn't run trcinfo")
                                dec_trace.close()
                                continue
                            dec_trace.close()
                            # Checking for Fatal errors in the tracelog. If any is present the LSU is stopped
                            # so that it will be restarted at the beginning
                            # of the next test execution
                            dec_trace = open(dec_trace_name, 'r')
                            for line in dec_trace:
                                if (("fatal" in line.lower()) and
                                        not ("trcinfo.c" in line.lower()) and
                                        not ("FWOUT" in line) and
                                        not ("fatal = 0" in line) and
                                        not ('tcpreadblob' in line.lower())) or (
                                        "fifo full" in line.lower()):
                                    pe_log(
                                        json_output, json_buffer,
                                        "*WARN* Stopping LSU due to the presence of Fatal errors in the ppu %s tracelog"
                                        % elem)
                                    res = pymosaic.stopLSU(lsu_ip)
                                    if res['result'] == 'success':
                                        pe_log(json_output, json_buffer,
                                                '*DEBUG*' + res['output'])
                                    else:
                                        pe_log(json_output, json_buffer,
                                                "*WARN* Error stopping the LSU")
                                    break
                                if "spool nores" in line.lower():
                                    pe_log(
                                        json_output, json_buffer,
                                        "*WARN* Stopping LSU due to probable L2 Core"
                                    )
                                    res = pymosaic.stopLSU(lsu_ip)
                                    if res['result'] == 'success':
                                        pe_log(json_output, json_buffer,
                                                '*DEBUG*' + res['output'])
                                    else:
                                        pe_log(json_output, json_buffer,
                                                "*WARN* Error stopping the LSU")
                                    break
                            dec_trace.close()
                            os.remove(untar_trace_name)
                            os.remove(second_tar_dir)
        except:
            pe_log(json_output, json_buffer,
                    '*DEBUG* Cannot parse lsugetreport...')

    # Wireshark log postprocessing
    if wireshark_analysis:
        pe_log(json_output, json_buffer,
               '*INFO*' + 'Wireshark log analysis results:')
        if rat == 'UMTS':
            tshark_check = pe_tshark_check.pe_ws_check(ws_file_name,
                                                       check_string)
        elif rat == 'LTE':
            tshark_check = pe_tshark_check_LTE.pe_ws_check_LTE(
                ws_file_name, check_string)
        # Check that no UEs failed and that the % of failing UEs is below the
        # threshold
        if (tshark_check[0] == 0) or (tshark_check[1] <=
                                      (1 - float(fail_threshold) / 100.0)):
            pass
        elif wireshark_rcode == 'failed':
            regr_res += " Wireshark crashed before the test ended"
        else:
            regr_res += " Wireshark log analysis indicates the presence of errors during test execution"

    #if tstms1_ip == True and tstms1_path == True:
    #    res = getTSTMLogsS1(tstms1_ip, tstms1_path, test_dir)

    # Extract and parse TSTM logs
    try:
        print (bugreport)
        zf = zipfile.ZipFile(bugreport)
    except (zipfile.BadZipfile, IOError,Exception):
        pe_log(json_output, json_buffer,
               "*WARN* Couldn't open bugreport: %s" % bugreport)
        zf = None
    if zf is not None:
        extracted=""
        for zfile in zf.infolist():
            # pe_log(json_output, json_buffer,  zfile.filename
            if zfile.filename == 'messages.log':
                zf.extract(zfile.filename, test_dir)
            else:
                if zfile.filename[-4:] == '.zip' and zfile.filename != 'tstm_sys_messages.zip':
                    # pe_log(json_output, json_buffer,  ('Extracting TSTM log
                    # from %s' % zfile.filename)
                    pe_log(
                        json_output, json_buffer,
                        '*DEBUG* Extracting TSTM log from %s' % zfile.filename)
                    extracted = str(zfile.filename)
                    zf.extract(zfile.filename, test_dir)
        zf.close()
        try:
            zf = zipfile.ZipFile(os.path.join(test_dir, str(extracted)), 'r')
        except (zipfile.BadZipfile, IOError):
            if extracted:
                pe_log(json_output, json_buffer,
                       "*WARN* Couldn't extract TSTM log from %s" % extracted)
            zf = None
        if zf is not None:
            try:
                filename_rat = {
                    'UMTS': 'UmtsUu_Tm.log.*',
                    'LTE': 'LTE_Uu_Tstm.log.*',
                    '5Gv': '5G_Uu_Tstm.log.*',
                    'GSM': 'Um_Tm.log.*'
                }
                for zfile in zf.infolist():
                    if re.search(filename_rat[rat], zfile.filename):
                        tstm_log = zfile.filename
                        if os.path.basename(
                                zfile.filename).rsplit('.')[-1] == 'log':
                            filename = "TSTM.log"

                        else:
                            filename = "TSTM.log.%s" % os.path.basename(
                                zfile.filename).rsplit('.')[-1]
                        outfile = open(os.path.join(test_dir, filename), 'wb')
                        outfile.write(zf.read(tstm_log))
                        outfile.flush()
                        outfile.close()
                        outfile = open(
                            os.path.join(test_dir, "TSTMGOLD.txt"), 'wt')
                        golderror = 0
                        tstmcore = 0
                        for line in open(os.path.join(test_dir, filename)):
                            # pe_log(json_output, json_buffer,  line
                            if ("GOLD" in line) or ("SCENLOG" in line) or (
                                    "epsbObjIdx" in line) or (
                                        "------- " in line) or (
                                            "Signal MS_MNG_IND" in line):
                                outfile.write(line)
                            if (((re).search("ERR\=[1-9]", line) is not None) or (
                                    re.search("script error", line) is not None
                            ) or (re.search("CORE DUMP", line) is not None)) and (re.search("RecvTmrTstmExit", line) is None):
                                if golderror == 0:
                                    pe_log(json_output, json_buffer, "*INFO* TSTM log errors:")
                                pe_log(json_output, json_buffer,
                                    '*INFO*' + line)
                                # pe_log(json_output, json_buffer,  " *INFO* "
                                # +line
                                if 'ERR=17016' in line:
                                    pe_log(json_output, json_buffer,
                                        '*DEBUG* Detected ERR=17016 ')
                                elif 'RecvTmrTstmExit' in line:
                                    pe_log(json_output, json_buffer,
                                        '*DEBUG* A bug')
                                else:
                                    if re.search("CORE DUMP", line) is not None:
                                        tstmcore = 1
                                    golderror = 1
                                    pe_log(json_output, json_buffer, '*DEBUG* Errore ' + line)
                        outfile.flush()
                        outfile.close()
                zf.close()
            except Exception as e:
                tstmcore=0
                pe_log(json_output, json_buffer,
                       '*WARN* Could not process TSTM file ' + str(e))
            try:
                os.remove(os.path.join(test_dir, str(extracted)))
            except:
                pe_log(json_output, json_buffer,
                       '*WARN* Could not delete file ' + os.path.join(
                           test_dir, str(extracted)))
        if golderror == 1:
            if regr_res != '':
                regr_res += ", "
            regr_res += "detected TSTM log errors"
        if tstmcore == 1:
            regr_res += " ( a tstm core dump detected) "
        if rat == 'LTES' or rat == '5GvS':
            # Parse airmosaic log
            # pe_log(json_output, json_buffer,  "Checking AM errors"
            if os.path.isfile(os.path.join(test_dir, "messages.log")):
                outfile = open(
                    os.path.join(test_dir, "messages_out.log"), 'wt')
                airmosaic_log_error = 0
                for line in open(os.path.join(test_dir, "messages.log")):
                    if "ERR=" in line:
                        tmp_line = line.replace(
                            "TstmSockThread Signal received: tstmIndex=null (RMT_CTRL_SAPI,RMT_CTRL_IND) MS_MNG_IND,",
                            "")
                        outfile.write(tmp_line)
                        if (re.search("ERR\=[1-9]", line) is
                                not None) and ("ERR=132" not in line):
                            pe_log(json_output, json_buffer,
                                   "*INFO* ERROR: %s" % tmp_line)
                            airmosaic_log_error = 1
                        if "ERR=203" in line:
                            pe_log(json_output, json_buffer, '*INFO*' + line)
                            airmosaic_log_error = 230
                        if ("SEVERE" in line) and ("refused" in line):
                            pe_log(json_output, json_buffer, '*INFO*' + line)
                            airmosaic_log_error = 1001
                outfile.flush()
                outfile.close()
                if airmosaic_log_error == 1:
                    # if regr_res!='':
                    #    regr_res+=", "
                    #regr_res += "detected Airmosaic log errors"
                    pe_log(json_output, json_buffer,
                           '*WARN*  detected Airmosaic log errors')
                elif airmosaic_log_error == 203:
                    if regr_res != '':
                        regr_res += ", "
                    regr_res += "Cell not available on Airmosaic"
                elif airmosaic_log_error == 1001:
                    if regr_res != '':
                        regr_res += ", "
                    regr_res += "Could not connect to TSTM"

    # Counters checks
    am_counters_rc = 0
    failed_counter_checks = ''
    data_to_plot = []
    #pe_log(json_output, json_buffer,  "AA" +str( counters_zip))
    if counters_zip is not None:
        try:
            zf = zipfile.ZipFile(counters_zip, 'r')
        except (zipfile.BadZipfile, IOError):
            pe_log(
                json_output, json_buffer,
                "*WARN* Couldn't extract counters csv from %s" % counters_zip)
            zf = None
        if zf is not None:
            for zfile in zf.infolist():
                pe_log(json_output, json_buffer,
                       '*DEBUG* Extracting counters csv: %s' % zfile.filename)
                outfile = open(
                    os.path.join(test_dir, os.path.basename(zfile.filename)),
                    'wb')
                outfile.write(zf.read(zfile))
                outfile.flush()
                outfile.close()
    if counters_check != None and counters_check !="":
        pe_log(json_output, json_buffer,
               "*INFO* Airmosaic counters check results:")
        checks_list = counters_check.rsplit('|')
        pe_log(json_output, json_buffer,
               '*DEBUG* Checks list: %s' % checks_list)
        counters_files = glob.glob(os.path.join(test_dir, '*.csv'))
        pe_log(json_output, json_buffer,
               '*DEBUG* Found counters csv files: %s' % counters_files)
        counters_csv_list = {}
        for counters_file in counters_files:
            if 'Subscribers_counters' in counters_file:
                pe_log(json_output, json_buffer,
                       '*DEBUG* Found Subscribers counters csv: %s' %
                       counters_file)
                counters_csv_list['subscribers'] = counters_file
            if 'Cells_counters' in counters_file:
                pe_log(json_output, json_buffer,
                       '*DEBUG* Found Cells counters csv: %s' % counters_file)
                counters_csv_list['cells'] = counters_file
            if 'Groups_counters' in counters_file:
                pe_log(json_output, json_buffer,
                       '*DEBUG* Found Groups counters csv: %s' % counters_file)
                counters_csv_list['groups'] = counters_file
        num_test=0
        num_failure=0
        for check in checks_list:
            num_test=num_test+1
            pe_log(json_output, json_buffer,
                   '*DEBUG* Running counters check: %s' % check)
            if len(check.rsplit(',')) != 6:
                pe_log(json_output, json_buffer,
                       " *DEBUG* Something wrong with check ")
                continue
            counter_type = check.rsplit(',')[0].replace("    ", '')
            counter_instance = check.rsplit(',')[1]
            counter_name = check.rsplit(',')[2]
            counter_result = check.rsplit(',')[3]
            counter_check = check.rsplit(',')[4]
            counter_threshold = check.rsplit(',')[5]
            # pe_log(json_output, json_buffer,  "Cnt type",counter_type
            if counter_type == 'Subscriber':
                try:
                    counters_csv_file = counters_csv_list['subscribers']
                except KeyError:
                    pe_log(
                        json_output, json_buffer,
                        "*WARN* Couldn't find Subscribers counters csv file!")
                    continue
            elif counter_type == 'Group':
                try:
                    counters_csv_file = counters_csv_list['groups']
                except KeyError:
                    pe_log(json_output, json_buffer,
                           "*WARN* Couldn't find Groups counters csv file!")
                    continue
            elif counter_type == 'Cell':
                try:
                    counters_csv_file = counters_csv_list['cells']
                    # pe_log(json_output, json_buffer,  "Checking cell"
                except KeyError:
                    pe_log(json_output, json_buffer,
                           "*WARN* Couldn't find Cells counters csv file!")
                    continue
            else:
                continue
            counter_vals = _get_counter_values(counters_csv_file, counter_name,
                                               counter_instance)
            timestamps = _get_counter_values(
                counters_csv_file, 'Timestamp (ms)', counter_instance)
            if len(counter_vals) == 0:
                pe_log(json_output, json_buffer,
                       "*WARN* Counter %s is not present in counter csv file!"
                       % counter_name)
                continue
            data_to_plot.append({
                'counter_type': counter_type,
                'timestamps': timestamps,
                'counter_vals': counter_vals,
                'counter_name': counter_name,
                'counter_instance': counter_instance
            })
            #print (data_to_plot)
            if counter_result == 'lv':
                # pe_log(json_output, json_buffer,  "TEsting Last Value"
                try:  # Sometimes the value in the last csv row is left empty by Airmosaic
                    counter_value = float(counter_vals[-1])
                    # pe_log(json_output, json_buffer,  counter_value
                except TypeError:
                    counter_value = float(counter_vals[-2])
                    # pe_log(json_output, json_buffer,  counter_value
                except ValueError:  # Raise a counter error if a counter has a 'bad' value
                    am_counters_rc += 2
                    pe_log(json_output, json_buffer, '*INFO*' + (
                        '<font color = "red"><b>Last value for counter "%s" for %s "%s" is non-numeric: %s</b></font>'
                        % (counter_name, counter_instance, counter_name,
                           counter_vals[-1])))
                    num_failure=num_failure+1
                    continue
                except:
                    pe_log(json_output, json_buffer,  "Dont know")
                value_string = ''
            elif counter_result == 'av':
                # pe_log(json_output, json_buffer,  "TEsting Average"
                if "PDSCH" in counter_name or "PUSCH" in counter_name:
                    counter_vals_stripped = [
                        item for item in counter_vals
                        if ((item != '0') and (item != 'null') and (
                            item != 'NA') and (item is not None) and (
                                float(item) > 20000))
                    ]
                else:
                    counter_vals_stripped = [
                        item for item in counter_vals
                        if ((item != '0') and (item != 'null') and (
                            item != 'NA') and (item is not None) and (
                                float(item) != 0))
                    ]
                if len(counter_vals_stripped) == 0:
                    counter_vals_stripped = ['0']
                counter_value = sum(map(float, counter_vals_stripped)) / float(
                    len(counter_vals_stripped))
                value_string = 'Average value of '
            else:
                continue
            if float(counter_value) > 10000:
                counter_value_print = humanize.naturalsize(counter_value, binary=True).replace("MiB","mbps").replace("KiB","kbps")
            else:
                counter_value_print = "%.2f" % float(counter_value)
            if float(counter_threshold) > 10000:
                counter_threshold_print = humanize.naturalsize(counter_threshold, binary=True).replace("MiB","mbps").replace("KiB","kbps")
            else:
                counter_threshold_print = "%.2f" % float(counter_threshold)

            comp_table={'gt':[ '>', (lambda x,y: x>=y)] , 'lt':['<',(lambda x,y: x<=y)], 'eq':["=",(lambda x,y: x==y)]}

            counter_check_print = comp_table[counter_check][0]
            if "Thr" in counter_name:
                add_s='/s'
                add_s=''
            else:
                add_s= ""
            #pe_log(json_output, json_buffer, '*INFO* CNT NAME:' + counter_name+ ' aaaa '+add_s)
            counter_name_category=counter_name.split("->")[-2]
            counter_check_print=counter_check_print.replace('.00','')
            counter_value_print=counter_value_print.replace('.00','')
            counter_threshold_print=counter_threshold_print.replace('.00','')
            if "RRC" in counter_name_category:
                counter_name_category=""
            counter_name= counter_name_category+" "+ counter_name.split("->")[-1]
            if comp_table[counter_check][1]( float(counter_value) ,float(counter_threshold))==False:
                pe_log(json_output, json_buffer, '*INFO*' +'<font color = "red"><b>%s%s for %s %s (%s%s) is not %s %s%s</b></font>' %
                    (value_string, counter_name, counter_type,counter_instance, counter_value_print , add_s, counter_check_print, counter_threshold_print, add_s))
                failed_counter_checks += '<font color = "red"><b>%s%s for %s %s: %s%s is not %s %s%s</b></font>\n' % (
                    value_string, counter_name, counter_type, counter_instance, counter_value_print , add_s, counter_check_print, counter_threshold_print, add_s)
                am_counters_rc += 2
                num_failure=num_failure+1
            else:
                pe_log(
                    json_output, json_buffer, '*INFO*' +'%s%s for %s %s (%s%s) %s  %s%s' %
                    (value_string, counter_name, counter_type,counter_instance, counter_value_print , add_s, counter_check_print, counter_threshold_print, add_s))
        pe_log(json_output, json_buffer, '*INFO*' + str(num_test-num_failure)+ ' check passed out of ' +str(num_test)) 
    # Create counters charts
    if len(data_to_plot) > 0:
        #pe_log(False,[],"*DEBUG* "+ str (data_to_plot))
        saved_plot = _save_counters_plot(test_dir, data_to_plot, 'Time (ms)')
    if am_counters_rc != 0:
        if regr_res != '':
            regr_res += ", "
        regr_res += 'found errors in scenario counters:\n' + failed_counter_checks
    if os.getenv('WORKSPACE') is not None:
        for chart in glob.glob(os.path.join(test_dir, '*.png')):
            copy(chart, os.getenv('WORKSPACE'))
    # If the test was succesful save all the logs in a compressed archive, in
    # order to save disk space
    xmlfile = os.path.join(test_dir, "Result.xml")
    pe_log(json_output, json_buffer, '*DEBUG* Checking Result.xml')
    if os.path.isfile(xmlfile):
        testresultxml = checkTestResultUtils("", path=xmlfile, fail_threshold=fail_threshold)
        if testresultxml['error'] != '':
            if regr_res != '':
                regr_res += ", "
            regr_res += "Failed AM TestResult:" + str(testresultxml['output'])
    else:
        pe_log(json_output, json_buffer, '*DEBUG* Couldn\'t find Result.xml')
    test_files = os.listdir(test_dir)
    if (regr_res == '') and (len(test_files) > 0):
        try:
            res_arch = tarfile.open(
                os.path.join(test_dir, '%s.tar.gz' % test_name), 'w:gz')
            for elem in test_files:
                try:
                    res_arch.add(os.path.join(test_dir, elem), arcname=elem)
                    if "tests_log.txt" not in elem:
                        os.remove(os.path.join(test_dir, elem))
                except:
                    pass
            res_arch.close()
        except:
            pass
    # pe_log(json_output, json_buffer,  regr_res
    if json_output == True:
        if regr_res != '':
            result = {
                'result': 'failed',
                'error': regr_res,
                'output': json_buffer
            }
        else:
            result = {'result': 'success', 'error': '', 'output': json_buffer}
    else:
        if regr_res != '':
            pe_log(json_output, json_buffer, '*INFO* Test FAILED')
            result = '*HTML*' + regr_res
        else:
            pe_log(json_output, json_buffer, '*INFO* Test PASSED')
            result = 0
    pe_log(json_output, json_buffer, '*INFO* Results located in %s' % test_dir )
    return result


def checkTestResultUtils(result_xml, *args, **kwargs):
    """Checks success rate for the given procedures after the test execution ended.
    Input arguments are:\n
    * _result_xml_ is a string containing the Airmosaic test result xml\n

    Optional arguments are:\n

    * A series of check definitions each passed as an argument in the form: group_name,session_name,procedure,threshold\n
    * _result_checks_ is a list of checks to be performed in this format: \n
        _[{'group':'group_name','session':'session_name','procedure':'procedure_name','threshold':'threshold'},...]_\n
        In both cases _threshold_ is the minimum success percentage in order to declare the test as passed.

    """
    result_checks = []
    path = ""
    # pe_log(json_output, json_buffer,  args
    if 'fail_threshold'in kwargs:
        fail_threshold= kwargs['fail_threshold']
    else:
        fail_threshold = 100
    if 'path'in kwargs:
        path = kwargs['path']
        resultfile = open(path, "r")
        result_xml = resultfile.read()
    if len(result_checks) == 0 and path == "":
        return {'result': 'failed', 'error': 'Nothing to check'}
    try:
        root = ET.fromstring(result_xml)
    except ExpatError:
        return {
            'result': 'failed',
            'error': 'Wrong Test Result format',
            'output': 'No Error'
        }
    #root = result_tree.getroot()
    succ_checks = 0
    errdescr = []
    toterr = 0
    for elem in root.iter('TestProcedure'):
        # pe_log(json_output, json_buffer,  "checkForErrors() debug: child attribs = {testname}".format(testname=elem.attrib)
        # pe_log(json_output, json_buffer,  "checkForErrors() debug: number of
        # failure = {nerrors}".format(nerrors=elem.attrib.get('NumFailure'))
        if elem.attrib.get('NumFailure') != '0' and elem.attrib.get(
                'NumFailure') != '':
            sessionname = root.find('.//%s/..' % elem.tag)
            groupname = root.find('.//%s/..' % sessionname.tag)
            # pe_log(json_output, json_buffer,  sessionname.tag,sessionname.attrib['SessionName']
            # pe_log(json_output, json_buffer,
            # groupname.tag,groupname.attrib['GroupName']
            try:
                if 100*(float(elem.attrib['NumFailure'])/(float(elem.attrib['NumSuccess']) +float(elem.attrib['NumFailure'])))> (100-fail_threshold):
                    errdescr.append({
                        'Group': groupname.attrib['GroupName'],
                        'Session': sessionname.attrib['SessionName'],
                        'TestProcedure': elem.attrib['TestProcedureKind'],
                        'NumFailure': elem.attrib['NumFailure']
                    })
                    toterr = toterr + 1
            except:
                pass

    # pe_log(json_output, json_buffer,  errdescr

    if errdescr == []:
        result = {'result': 'success', 'error': '', 'output': 'No Error'}
    else:
        result = {
            'result': 'failed',
            'error': 'Counter checks not passed.',
            'output': errdescr
        }
    return result


def freeDiskSpace(path):
    """Return disk usage statistics about the given path.
    Will return the namedtuple with attributes: 'total', 'used' and 'free',
    which are the amount of total, used and free space, in bytes.
    """
    DiskUsage = namedtuple('DiskUsage', 'total used free')
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return DiskUsage(total, used, free)


def createZipArchive(sid, sce, output_file):
    """Create a zip archive containing sid/usr/mdl/sce files and optionally mae/rclib/plib. Returns archive name, if succesful.

    :param sid: path to sid file
    :param sce: path to scenario file
    :param output_file: path to output archive
    :return: {'result':'success|failed','info':output_file}

    :example: createZipArchive("./Test.sid","../Test.sce","/tmp/Test.zip")
    :example output: {'result':'success','info':"/tmp/Test.zip"}

    """
    l1_files = ["NrPrach.l1t", "NrPusch.l1t", "NrUplinkFile.l1t", "init.l1t", "nrPdcch.l1t", "nrPdsch.l1t"]

    sid_path = os.path.dirname(sid)
    sce_path = os.path.dirname(sce)
    try:
        tree = ET.parse(sid)
    except ExpatError:
        return {'result': 'failed', 'error': 'Sid file is not correct.'}
    #sid_root = sid_tree.getroot()
    usr_name = tree.find('.//SpecificServices').get('SubscriberDbName')
    try:
        l1test = tree.find('.//SpecificServices').get('Perspective')
    except:
        l1test = ""
    usr_file = os.path.join(sid_path, usr_name)
    pe_log(json_output, json_buffer,  "*DEBUG* " + str(usr_file))
    mdl_name = getUsrFromSid(usr_file)
    pe_log(json_output, json_buffer,  "*DEBUG* " + str(mdl_name))
    mdl_file = os.path.join(sid_path, mdl_name)
    try:
        sce_tree = ET.parse(sce)
    except ExpatError:
        return {'result': 'failed', 'error': 'Sce file is not correct.'}
    sce_root = sce_tree.getroot()
    try:
        sce_amm_files = [
            os.path.join(sce_path, elem)
            for elem in sce_root.find('.//AmmExternalLinkedFiles')
            .attrib.values()
        ]
    except AttributeError:
        # In this case there are no linked mae,plib,rclib files
        sce_amm_files = []
    theZip = zipfile.ZipFile(output_file, 'w', 8)
    theZip.write(sid, os.path.basename(sid))
    theZip.write(usr_file, usr_name)
    theZip.write(mdl_file, mdl_name)
    theZip.write(sce, os.path.basename(sce))
    if l1test== "L1TEST_MODE":
        for file in l1_files:
            try:
                theZip.write(os.path.join(sid_path, file),file)
            except:
                return {'result': 'failed', 'error': 'file %s missing for L1 TEST MODE' % (file)}    
    for elem in sce_amm_files:
        theZip.write(elem, os.path.basename(elem))
    theZip.close()
    return {'result': 'success', 'info': output_file}


def copySimFiles(sid, sce, output_dir):
    """Create a zip archive containing sid/usr/mdl/sce files and optionally mae/rclib/plib. Returns archive name, if succesful.

    :param sid: path to sid file
    :param sce: path to scenario file
    :param output_file: path to output archive
    :return: {'result':'success|failed','info':output_file}

    :example: createZipArchive("./Test.sid","../Test.sce","/tmp/Test.zip")
    :example output: {'result':'success','info':"/tmp/Test.zip"}

    """
    l1_files = ["NrPrach.l1t", "NrPusch.l1t", "NrUplinkFile.l1t", "init.l1t", "nrPdcch.l1t", "nrPdsch.l1t"]

    sid_path = os.path.dirname(sid)
    sce_path = os.path.dirname(sce)
    try:
        tree = ET.parse(sid)
    except ExpatError:
        return {'result': 'failed', 'error': 'Sid file is not correct.'}
    #sid_root = sid_tree.getroot()
    usr_name = tree.find('.//SpecificServices').get('SubscriberDbName')
    usr_file = os.path.join(sid_path, usr_name)
    try:
        l1test = tree.find('.//SpecificServices').get('Perspective')
    except:
        l1test = ""
    pe_log(json_output, json_buffer,  "*DEBUG* " + str(usr_file))
    mdl_name = getUsrFromSid(usr_file)
    pe_log(json_output, json_buffer,  "*DEBUG* " + str(mdl_name))
    mdl_file = os.path.join(sid_path, mdl_name)
    try:
        sce_tree = ET.parse(sce)
    except ExpatError:
        return {'result': 'failed', 'error': 'Sce file is not correct.'}
    sce_root = sce_tree.getroot()
    try:
        sce_amm_files = [
            os.path.join(sce_path, elem)
            for elem in sce_root.find('.//AmmExternalLinkedFiles')
            .attrib.values()
        ]
    except AttributeError:
        # In this case there are no linked mae,plib,rclib files
        sce_amm_files = []

    copy2(sid, output_dir)
    copy2(usr_file, output_dir)
    copy2(mdl_file, output_dir)
    copy2(sce, output_dir)
    if l1test== "L1TEST_MODE":
        for file in l1_files:
            try:
                copy2(file, output_dir)
            except:
                return {'result': 'failed', 'error': 'file %s missing for L1 TEST MODE' % (file)}  
    for elem in sce_amm_files:
        copy2(elem, output_dir)
    return {'result': 'success', 'info': ""}


def get_test_logs(**kwargs):
    """Function for postprocessing of test cases execution outputs'':'' lsu logs, TSTM logs, wireshark logs, airmosaic counters and Test result xml from Airmosaic
    :param rat: rat of the test executed "5Gv", LTE", "UMTS" or "GSM"
    :param keep_on_server : if True data is saved for future download
    :
    :param wireshark_analysis: set to True when result analysis check has to be done also on Wireshark capture file
    :param test_dir: directory where to put result file of analysis
    """
    from .pylsu import getLSUlogs


def save_test_logs(**kwargs):
    """
    TO DO based on reverse engineering
    Function for saving logs of test cases execution.
    :param sid: (mandatory) sid filename used for test.
    :param q: Queue for exchange output message (used when used invoked by REST)
    :param rat: rat of the test executed, if not present it will be retrieved from sid, available value are: "5Gv", LTE", "UMTS", "GSM"
    :param keep_on_server : (mandatory) if True data is left on remote server and not downloaded.
    :param test_home: store directory for log files. A new directory will be created with name test_home+timestamp
    :param lsu_ip: ip of LSU (useful if save_lsu_logs=True)
    :param ppu: list of ppu for exctracting trcinfo log (e.g. ["0-1","0-2"])
    :param bugreport: full path of bugreport zip file to be analyzed
    :param json_output: variable where logs are stored
    :param tstms1_ip: ip address of test manager for S1 interface cose simulator.
    :param tstm_ip: ip address of test manager for Uu interface simulator.
    :param tstms1_path:
    :param tstms1_path:
    :param lsus1_ip: ip address of LSU for S1 interface core simulator.
    :param tstms1_dir: 
    :param zip_logs: True|False
    :param log_dur: True|False
    :param getlogs: dictionary containing filename for the saved logs{"lsu_report":"", "tstm_report":"", "lsus1_report":"", "tstms1_report":"", "airmosaic_logs":""}
            airmosaic_logs contains a list o names for renaming files...
    :param Log_ALL: True|False, if true  set true save_lsu_logs, save_tstm_logs, save_lsus1_logs, save_tstms1_logs, save_airmosaic_logs.
    :param save_lsu_logs: [ True|False=default ] set to False if lsugetreport is not needed
    :param save_tstm_logs: [ True|False=default ] set to False if tstm log is not needed
    :param save_lsus1_logs: [ True|False=default ] set to False if S1 lsugetreport is not needed
    :param save_tstms1_logs: [ True|False=default ] set to False if s1 test manager log is not needed
    :param save_airmosaic_logs: [ True|False=default ] set to False if AirMosaic log is not needed
    :param counters_check: set but not used ???
    :param test_dir: the vaue of test_dir is not not read, just set (???)
    
    |
    
    :return:{ 'ouput' : <log produced by function execution>, 'lsu_report': <log produced by lsu>, 'lsus1_report': <log produced by S1 lsu>,'tstm_report' : <log produced by tstm>, 'airmosaic_logs' : <log produced by Airmosaic>, 'tstms1_report' : <log produced by S1 tstm>, 'test_home': <folder wher logs are stored>}

    :example output: {  'ouput': ['*INFO* Logs will be saved in C:\\Temp\\20180620\\20180620144305_Testcase'],
                        'lsu_report': 'gen20180620-144833',
                        'airmosaic_logs': ['C:\\Users\\user\\AppData/Roaming/.airmosaic_lteuu/dev/var/log\\messages.log-20180620-144833', 'C:\\Users\\user\\AppData/Roaming/.airmosaic_lteuu/dev/var/log\\messages.log.1-20180620-144833'],
                        'lsus1_report': '',
                        'tstm_report': u'/home/user/lte_tstm/20180620-144605-Sid_p7090-7c81d0dd/',
                        'tstms1_report': '',
                        'test_home': u'C:\\Temp\\20180620\\20180620144305_Testcase'
                     }
    
    #
    #---  OLD description ---- 
    #outputs'':'' lsu logs, TSTM logs, wireshark logs, airmosaic counters and Test result xml from Airmosaic
    #
    #:param wireshark_analysis: set to True when result analysis check has to be done also on Wireshark capture file
    #:param test_dir: directory where to put result file of analysis
    #:param check_string: string to be checheck for counters in csv (e.g. "Cell,1,Layer 1->General Counters->DOWNLINK->BLER on PDSCH % - Total,lv,lt,0.1|Cell,1,Layer 1->General Counters->UPLINK->NACK on PHICH %,lv,lt,5")
    #:param fail_threshold(optional): default 100, set to a lower value to get test passed also with some failures
    #:param counters_check(optional): list of counters to be checked with rule, separated by \\"\\|\\". rules are for counters\\: lv for last value, av for average. For check \\: lt for less than, gt for greated than, eq for equal
    #
    #:return: "PASSED" of "FAILED" with a string of failed procedures
    #
    """
    from .pylsu import getLSUlogs
    from .pytstm import getTstmLog
    from .pytstms1 import getTSTMlogsS1, getAvailableTstmS1
    import os
    airmosaic_exe = {"LTE": "airmosaic_lteuu","UMTS":"airmosaic_umtsuu", "GSM": "airmosaic_gsmum","5Gv": "airmosaic_fiveguu"}
    remote_ip = None
    counters_check = None
    parse_traces = False
    counters_zip = None
    ppu_irat = None
    lsu_ip_irat = None
    is_irat = False
    same_lsu = False
    zip_logs = False
    ppu = "10"
    json_buffer = []
    json_output = True
    pe_threads = []
    pe_res = {}
    pe_log(json_output, json_buffer, '*DEBUG* save_test_logs() kwars= ' + str(kwargs))
    if 'q' in kwargs:
        q = kwargs['q']
    else:    
        q = None
    if 'rat' in kwargs:
        rat = kwargs['rat']
    else:
        try:
            pe_log(json_output, json_buffer, "*DEBUG* " +str(kwargs ['sid']))
            rat = getRatFromSid(kwargs ['sid'])
        except Exception as e:
            pe_log(json_output, json_buffer, "*INFO* "+(str(e)))
            return {
                "result": "failed",
                "error": "Mandatory rat parameter cannot be retrieved from SID"
            }
    if 'keep_on_server' in kwargs:
        keep_on_server = kwargs['keep_on_server']
        if type(keep_on_server) is not bool:
            keep_on_server = ast.literal_eval(keep_on_server)
    else:
        return {
            "result": "failed",
            "error": "Missing mandatory keep_on_server parameter"
        }
    if 'test_home' in kwargs and keep_on_server != True:
        test_home = kwargs['test_home']
    else:
        test_home = kwargs['test_home']#tempfile.mkdtemp()
        if test_home != "":
            pe_log(json_output, json_buffer, '*DEBUG* Logs will be saved in ' + str(test_home))

    if 'lsu_ip' in kwargs:
        lsu_ip = kwargs['lsu_ip']
    else:
        lsu_ip = None

    if 'ppu' in kwargs:
        ppu = kwargs['ppu']
    else:
        ppu = []

    if 'bugreport' in kwargs:
        bugreport = kwargs['bugreport']
    else:
        bugreport = []

    if 'json_output' in kwargs:
        json_output = ast.literal_eval(kwargs['json_output'])
    else:
        json_output = False

    #pe_log(json_output, json_buffer,  ('*INFO* Retrieving logs'))

    if 'tstms1_ip' in kwargs:
        tstms1_ip = kwargs['tstms1_ip']
    else:
        tstms1_ip = None
    if 'tstm_ip' in kwargs:
        tstm_ip = kwargs['tstm_ip']
    else:
        tstm_ip = None
    if 'tstms1_path' in kwargs:
        tstms1_path = kwargs['tstms1_path']
    else:
        tstms1_path = None

    if 'lsus1_ip' in kwargs:
        lsus1_ip = kwargs['lsus1_ip']
    else:
        lsus1_ip = None

    if 'tstms1_dir' in kwargs:
        tstms1_dir = kwargs['tstms1_dir']
    else:
        tstms1_dir = None        
        
    if 'save_airmosaic_logs' in kwargs:
        save_airmosaic_logs = kwargs['save_airmosaic_logs']
        if type(save_airmosaic_logs) is not bool:
            save_airmosaic_logs = ast.literal_eval(save_airmosaic_logs)
    else:
        save_airmosaic_logs = False

    if 'zip_logs' in kwargs:
        zip_logs = kwargs['zip_logs']
        if type(zip_logs) is not bool:
            zip_logs = ast.literal_eval(zip_logs)
    else:
        zip_logs = False
    if 'log_dur' in kwargs and kwargs['log_dur']!="":
        time_interval = kwargs['log_dur']
    else:
        time_interval = "ALL"
    pe_log(json_output, json_buffer, '*DEBUG* save_test_logs() Parsing sid')
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

    if "sid" in kwargs:
        try:
            alt_lsu_ip = ""
            ipsFromSid=getIPsFromSid(kwargs['sid'])
            for ips in ipsFromSid:
                if ips['name'] == 'LSU':
                    lsu_ip=ips['value']
                if ips['name'] == 'TstmIp':
                    tstm_ip=ips['value']     
                if ips['name'] == '__alternative_lsu_ip':
                    alt_lsu_ip=ips['value']   
            if alt_lsu_ip != "":
                lsu_ip = alt_lsu_ip
            pe_log(json_output, json_buffer, '*DEBUG* save_test_logs() LSU IP %s' % lsu_ip) 
            pe_log(json_output, json_buffer, '*DEBUG* save_test_logs() TSTM IP %s' % tstm_ip) 
            if test_home != "" and keep_on_server == False:
                #print os.path.split(kwargs['sid'])
                #print os.path.split(kwargs['sid'])[1][:-4]
                test_home = os.path.join ( test_home ,timestamp+"-"+ os.path.split(kwargs['sid'])[1][:-4])
                pe_log(json_output, json_buffer, '*INFO* Test home:'+ test_home)
                os.makedirs(test_home)
            #print ("TEST HOME:" +test_home+"###")
        except Exception as e:
            pe_log(json_output, json_buffer, '*INFO* Fail to get IP: %s' % str(e))
    test_name = os.path.split(test_home[:-1])[1]
    pe_log(json_output, json_buffer, '*DEBUG* save_test_logs() TEST_NAME:'+test_name)
    if "getlogs" in kwargs:
        try:
            if kwargs["getlogs"]["lsu_report"]!= "" :
                res = getLSUlogs(lsu_ip, test_home,getreportname = kwargs["getlogs"]["lsu_report"])
                pe_log(json_output, json_buffer, '*DEBUG* Saving lsugetreport result: %s' % res)
                pe_log(json_output, json_buffer, "*DEBUG* "+str(kwargs["getlogs"]["lsu_report"]))
            if kwargs["getlogs"]["tstm_report"]!= "":
                res = getTstmLog(tstm_ip, rat, test_dir = test_home,getreportname = kwargs["getlogs"]["tstm_report"])
                pe_log(json_output, json_buffer, '*DEBUG* Saving tstm log result: %s' % res)
            if kwargs["getlogs"]["lsus1_report"]!= "":
                res = getLSUlogs(lsu_ip, test_home,getreportname = kwargs["getlogs"]["lsu_report"])
                pe_log(json_output, json_buffer, '*DEBUG* Saving lsugetreport result: %s' % res)
                pe_log(json_output, json_buffer, "*DEBUG* "+str(kwargs["getlogs"]["lsu_report"]))
            if kwargs["getlogs"]["tstms1_report"]!= "":
                res = getTSTMlogsS1(tstms1_ip, "", test_home,getreportname = kwargs["getlogs"]["tstms1_report"])
                pe_log(json_output, json_buffer, '*DEBUG* Saving tstm log result: %s' % res)
            if kwargs["getlogs"]["airmosaic_logs"]!= "":
                for file in kwargs["getlogs"]["airmosaic_logs"]:
                    try:
                        pe_log(json_output, json_buffer, '*DEBUG*  moving '+file+" logs to "+ test_home)
                        os.rename(file, os.path.join(test_home,file.split('\\')[-1]))
                    except Exception as e:
                        pe_log(json_output, json_buffer, '*INFO* '+  str(e))
                        pass
            pe_log(json_output, json_buffer, '*INFO* Logs retieved succesfully, available in '+ test_home)
        except Exception as e:
            pe_log(json_output, json_buffer, "*INFO* Cannot retrieve all logs for "+str(e))
        return;
    if "Log_ALL" in kwargs and kwargs['Log_ALL']==True:
        save_lsu_logs = True
        save_tstm_logs = True
        save_lsus1_logs = True
        save_tstms1_logs = True
        save_airmosaic_logs = True
    else:
        try:
            save_lsu_logs = kwargs['save_lsu_logs']
        except:
            save_lsu_logs = False
        try:
            save_tstm_logs = kwargs['save_tstm_logs']
        except:
            save_tstm_logs = False        
        try:
            save_lsus1_logs = kwargs['save_lsus1_logs']
        except:
            save_lsus1_logs = False        
        try:
            save_tstms1_logs = kwargs['save_tstms1_logs']
        except:
            save_tstms1_logs = False        
        try:
            save_airmosaic_logs = kwargs['save_airmosaic_logs']
        except:
            save_airmosaic_logs = False        

    # Saving lsugetreport, extracting traces and parsing traces for major
    # errors
    pe_res["lsu"]={"report":""}
    pe_res["tstm"]={"report":""}
    pe_res["lsus1"]={"report":""}
    pe_res["tstms1"]={"report":""}
    
    if save_lsu_logs == True and lsu_ip!=None:
        pe_res['lsu']={'started':True}
        print (lsu_ip, test_home, pe_res,time_interval, timestamp , keep_on_server)
        t=threading.Thread(name='lsu',target=t_save_lsu_logs, args=(lsu_ip, test_home, pe_res,time_interval, timestamp , keep_on_server, lambda: stop_threads))
        pe_threads.append(t)

        
    if save_tstm_logs == True and tstm_ip!=None:
        pe_res['tstm']={'started':True}
        t=threading.Thread(name='tstm',target=t_save_tstm_logs, args=(tstm_ip, rat, test_home, pe_res,time_interval , timestamp , keep_on_server, lambda: stop_threads ))
        pe_threads.append(t)
        
        
    if save_lsus1_logs == True and lsus1_ip!=None:
        pe_res['lsus1']={'started':True}
        t=threading.Thread(name='lsus1',target=t_save_lsus1_logs, args=(lsus1_ip, test_home, pe_res,time_interval , timestamp, keep_on_server, lambda: stop_threads ))
        pe_threads.append(t)

    if save_tstms1_logs == True and tstms1_ip!=None:
        pe_res['tstms1']={'started':True}
        t=threading.Thread(name='tstms1',target=t_save_tstms1_logs, args=(tstms1_ip, tstms1_path, test_home, pe_res,time_interval , timestamp , keep_on_server, lambda: stop_threads ))
        pe_threads.append(t)

        
    numofthread=len(threading.enumerate())
    pe_log(json_output, json_buffer,"*DEBUG* Thread %s before start" % str(numofthread))
    for i in range(len(pe_threads)):
        pe_threads[i].start()
        pe_log(json_output, json_buffer,"*DEBUG* Thread %s started" %i)
    
    if save_airmosaic_logs == True:
        import os
        airmosaic_os_logs = {
            'win32': 'AppData/Roaming/.',
            'cli': 'AppData/Roaming/.',
            'darwin': 'Library/Application Support/',
            'linux2': '.',
            'linux': '.'
        }
        user_dir = os.path.expanduser("~")
        platform = sys.platform
        
        airmosaic_logs = os.path.join(user_dir, airmosaic_os_logs[platform]+airmosaic_exe[rat]+'/dev/var/log/messages.log*')
        AMfiles = glob.glob(airmosaic_logs)
        airmosaic_logs = []
        for file in AMfiles:
            if "-" not in file:
                try:
                    if test_home!="" and keep_on_server == False:
                        pe_log(json_output, json_buffer, '*INFO*  moving '+file+" logs to "+ test_home)
                        os.rename(file, os.path.join(test_home,file.split('\\')[-1]+"-" + timestamp))
                        airmosaic_logs.append(os.path.join(file.split('\\')[-1]+"-" + timestamp))
                    else:
                        pe_log(json_output, json_buffer, '*INFO*  moving '+file+" logs to "+ os.path.join(file+"-" + timestamp))
                        os.rename(file, os.path.join(file+"-" + timestamp))
                        airmosaic_logs.append(os.path.join(file+"-" + timestamp))
                except Exception as e:
                    pe_log(json_output, json_buffer, '*DEBUG* collecting log file error:'+  str(e))
                    pe_log(json_output, json_buffer, '*INFO* Airmosaic logs not saved')
                    pass
    else:
        airmosaic_logs = []
    pe_log(json_output, json_buffer, "*DEBUG* Wait for Join")
    # wait max 400 seconds then declare test failed
    # Put a nonblocking Check to be able to forward stop of test 
    numt = 0
    maxloop=0
    try:
        while len(threading.enumerate())> numofthread and maxloop<50:
            
            if numt != len(threading.enumerate()):
                print ("*DEBUG* save_test_logs active threads:"+str(threading.enumerate()))
                numt= len(threading.enumerate())
            if q and q.qsize()>0:
                #forward stop to all active threads
                stop_threads = True
                for t in pe_res:
                    print (t)
                    if pe_res[t]['started']==True:
                        print ("Stopping save_test_logs "+str(t))
                for tasks in pe_threads:
                    print ("Wait all tasks to finish")
                    tasks.join(20)
            maxloop=maxloop+1
            time.sleep(3)
            print ("Check:" +str(threading.enumerate()))
    except Exception as e:
        print ("Forced Closed "+str(e))
        return
    lsu_report=pe_res['lsu']['report']
    tstm_report = pe_res["tstm"]['report']
    lsus1_report =  pe_res["lsus1"]['report']
    tstm_s1_report = pe_res["tstms1"]['report']
    
    #print pe_res

    if zip_logs == True:
        test_files = os.listdir(test_home)
        pe_log(json_output, json_buffer, "*DEBUG* pyutils.save_test_logs(): test_home={0}, test_files={1} ".format(test_home, str(test_files)))
        if len(test_files) > 0:
            try:
                res_arch = tarfile.open(
                    os.path.join(test_home, '%s.tar.gz' % test_name), 'w:gz')
                for elem in test_files:
                    pe_log(json_output, json_buffer, '*DEBUG*  Adding:'+str(elem))
                    try:
                        res_arch.add(os.path.join(
                            test_home, elem), arcname=elem)
                        os.remove(os.path.join(test_home, elem))
                    except Exception as e:
                        pe_log(json_output, json_buffer, '*INFO* '+ str(e))
                        pass
                res_arch.close()
            except Exception as e:
                pe_log(json_output, json_buffer, '*INFO* '+ str(e))
                pass
    result= { 'ouput' : json_buffer, 'lsu_report': str(lsu_report), 'lsus1_report': lsus1_report,'tstm_report' : tstm_report, 'airmosaic_logs' : airmosaic_logs, 'tstms1_report' : tstm_s1_report, 'test_home': test_home}
    pe_log(json_output, json_buffer, "*INFO* LSU:"+str(lsu_report)+" TSTM:"+str(tstm_report)+ " LSUS1:"+str(lsus1_report)+" Airmosaic:"+ str(airmosaic_logs)+ "TSTM S1:"+ str(tstm_s1_report))
    print ("*INFO* pyutils.save_test_logs(): result=" +str(result))
    if keep_on_server == True:
        try:
            pe_log(json_output, json_buffer, "*INFO* Use following string to retrieve logs later:"+str(json.dumps(result, ensure_ascii=False)))
            f = open( os.path.join(test_home,'test_logs.txt'),'a+')
            f.write(str(json.dumps(result, ensure_ascii=False)))
            f.write("\n")
            f.close()
        except:
            pass
    return result

    
    
def t_save_lsu_logs(lsu_ip, test_home, pe_res, time_interval, timestamp , keep_on_server , stop=void()):
    from .pylsu import getLSUlogs
    pe_log(json_output, json_buffer, '*DEBUG* Saving LSU Logs')
    res = getLSUlogs(lsu_ip, test_home,time_interval = time_interval, timestamp = timestamp, keep_on_server = keep_on_server, stop = stop)
    pe_log(json_output, json_buffer,'*DEBUG* Saving lsugetreport result: %s' % res)
    if res['result'] == "success":
        lsu_report = res['report_name']
    else:
        lsu_report = ""
    pe_res['lsu']['report']=lsu_report
    pe_res['lsu']['started']=False
    return 
    
def t_save_tstm_logs(tstm_ip, rat, test_home,pe_res, time_interval = "", timestamp = "", keep_on_server = True , stop=void()):
    from .pytstm import getTstmLog
    if tstm_ip:
        tstm_report = getTstmLog(tstm_ip, rat,time_interval = time_interval, test_dir = test_home, timestamp = timestamp, keep_on_server = keep_on_server, stop = stop )
        pe_log(json_output, json_buffer, '*DEBUG* getTstmLog() resp.= '+ str( tstm_report))
    else:
        tstm_report = ""

    pe_res['tstm']['report']=tstm_report
    pe_res['tstm']['started']=False
    return 

def t_save_lsus1_logs(lsus1_ip, test_home,pe_res,  time_interval = "", timestamp = "", keep_on_server = True, stop=void()):
    from .pylsu import getLSUlogs
    lsus1_report=""
    if lsus1_ip:
        pe_log(json_output, json_buffer, '*DEBUG* Saving LSU S1 Logs')
        res = getLSUlogs(lsus1_ip, test_home,time_interval = time_interval, timestamp = timestamp, keep_on_server = keep_on_server, stop = stop)
        pe_log(json_output, json_buffer,
               '*DEBUG* Saving lsugetreport result: %s' % res)
        if res['result'] == "success":
            lsus1_report = res['report_name']
    else:
        lsus1_report=""
    pe_res['lsus1']['report']=lsus1_report
    pe_res['lsus1']['started']=False
    return
            
            
def t_save_tstms1_logs(tstms1_ip, tstms1_path , test_home,pe_res, time_interval = "", timestamp = "", keep_on_server = True , stop=void()):
    from .pytstms1 import getTSTMlogsS1, getAvailableTstmS1
    if tstms1_ip:
        pe_log(json_output, json_buffer, '*DEBUG* TSTM S1 IP:'+ str(tstms1_ip))
        tstms1_path=None
        if tstms1_path == None and tstms1_ip is not None:
            tstms1_path = getAvailableTstmS1(tstms1_ip)['s1tstm'][0]
            pe_log(json_output, json_buffer, '*DEBUG* TST:' + str(tstms1_path))
        if tstms1_ip is not None  and tstms1_path != None :
            tstm_s1_report = getTSTMlogsS1(tstms1_ip, tstms1_path, test_home, time_interval = time_interval, timestamp = timestamp, keep_on_server = keep_on_server, stop = stop)
            #print tstm_s1_report
            tstm_s1_report=tstm_s1_report['report_name']
        else:
            tstm_s1_report =""
    else:
        tstm_s1_report =""

    pe_res['tstms1']['report']=tstm_s1_report
    pe_res['tstms1']['started']=False
    return

    # Storing Airmosaic Logs
