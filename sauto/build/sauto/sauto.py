#!/usr/bin/python3

## \file sauto.py
# \brief SAuto framework main module
#
# SAuto is an automation framework. It mainly focus on:
# 1. Discover remote devices with SAuto daemon running (same sub-network)
# 2. Remote control devices
# 3. Support multi-platfrom
#
# SAuto should handle all process automatically, user only need to define what command to send
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import os, sys
import subprocess
import socket
import threading
import argparse
import utility

## \brief SAuto Framework Class defination
#
# Version: 0.0.1
# Required-package: utility.py
# SAuto class generate a SAuto node in the current network
# Discoverable and managable by other SAuto node in the same network
##
class SAuto:
    ## \brief Devices list dictionary
    device_list = {}
    this_device = {}
    ## \brief Debug flag setting
    daemon = {}
    ## \brief Reading buffer size
    buffer_size = 65535


    ## \brief SAuto constructor
    #
    # SELF is always the first device
    # broadcast_thread - thread broadcast SELF device information to local network
    # execution_thread - thread listening to port + 1 and responding to incoming package
    # discover_thread - thread receiving all package from port 8888 (default) and add valid device to device_list
    # health_thread - thread checking devices in the device_list if is reachable
    ##
    def __init__(self, port = 8888, debug = 'INFO'):
        self.__loadConfig(port)
        self.__setDebugMode(debug)

        broadcast_thread = threading.Thread(target = self.__broadcast, args = (1, self.daemon['broadcast']))
        broadcast_thread.daemon = True
        broadcast_thread.start()

        execution_thread = threading.Thread(target = self.__execution, args = (self.daemon['execution'],))
        execution_thread.daemon = True
        execution_thread.start()

        discover_thread = threading.Thread(target = self.__discover, args = (1, self.daemon['discover']))
        discover_thread.daemon = True
        discover_thread.start()

        health_thread = threading.Thread(target = self.__healthCheck, args = (30, self.daemon['health']))
        health_thread.daemon = True
        health_thread.start()

        pass
        ## --- End of Contructor --- ##


    ## \brief private setDebugMode function
    #
    # set the debug level by given argument:
    # INFO: print out all message except regular health check info
    # CLIENT: print out all INFO message but only send command execution result back to remote
    # DEBUG: print out all message
    # DAEMON: does not print out any message
    #
    # Default debug mode is INFO
    ##
    def __setDebugMode(self, debug = 'INFO'):
        if debug == 'INFO':
            self.daemon['broadcast'] = False
            self.daemon['execution'] = False
            self.daemon['discover'] = False
            self.daemon['health'] = True
        elif debug == 'CLIENT':
            self.daemon['broadcast'] = False
            self.daemon['execution'] = True
            self.daemon['discover'] = False
            self.daemon['health'] = True
        elif debug == 'DEBUG':
            self.daemon['broadcast'] = False
            self.daemon['execution'] = False
            self.daemon['discover'] = False
            self.daemon['health'] = False
        elif debug == 'DAEMON':
            self.daemon['broadcast'] = True
            self.daemon['execution'] = True
            self.daemon['discover'] = True
            self.daemon['health'] = True
        else: # default is 'INFO'
            self.daemon['broadcast'] = False
            self.daemon['execution'] = False
            self.daemon['discover'] = False
            self.daemon['health'] = True 



    ## \brief private loadConfig method
    #
    # setting up all configuration for the device
    # NOTE: This method is managing all related configuration and modules
    # TODO: Adding more dependencies here
    #
    # \param port The port number for initializing SAuto node, see __get_host for details
    ##
    def __loadConfig(self, port = 8888):
        self.__get_host(port) ## call self.__get_host(1234) to change port to 1234



    ## \brief private get_host method
    #
    # Setting IP protocol and host information for this_device
    # Adding the 'SELF' to device_list when constructing SAuto
    # The SAuto instance is configured running at given port
    # NOTE: it also means to separate different SAuto network:
    # [IMPORTANT] give the same different port for each test bed
    #
    # \param port The port number will be set for this_device and initialize the SAuto
    # Node broadcast on the same port. The execution port is +1 of the given port number
    ##
    def __get_host(self, port = 8888):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
            if 'IP' in self.this_device and IP != self.this_device['IP']:
                utility.warn('*** IP Change Detected! ***\n    Old IP: ' + self.this_device['IP'] + '\n    New IP: ' + IP, False)
        except Exception as e:
            utility.warn(str(e) + "\n    Setting IP to 127.0.0.1", False)
            IP = '127.0.0.1'
        finally:
            self.this_device['HOST'] = socket.gethostname()
            self.this_device['IP'] = IP
            self.this_device['PORT'] = port
            self.this_device['BROADCAST_IP'] = utility.regexParser(IP, '(.*)\.[0-9]{1,3}', True) + '.255'
            self.this_device['STATUS'] = 'REACHABLE'
            self.device_list['SELF'] = self.this_device
            s.close()



    ## \brief paivate execution function
    #
    # A thread will listening to this_device['PORT' + 1] and 
    # response to incoming package if command is recognized
    #
    # NOTE: User should not call this function, use execute() command instead
    #
    # \param daemon Print out the info message if set False, default is False
    ##
    def __execution(self, daemon = False):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((self.this_device['IP'], self.this_device['PORT'] + 1))
            while True:
                message = s.recvfrom(self.buffer_size)
                command = message[0].decode('utf-8')
                ## TODO TODO TODO start building command here !!!!!!!!!!!!
                if command == 'PING!':
                    no_print = True     ## set no_print to False to print health check message
                    if not no_print: utility.info("Receive health check package from [" + str(message[1][0]) + ":" + str(message[1][1]) + "]")
                    self.__callback(message[1][0], message[1][1], 'PONG!', no_print)
                elif command:
                    if not daemon: utility.info("Receive command from [" + str(message[1][0]) + ":" + str(message[1][1]) + "]")
                    if not daemon: utility.info("Executing command: [" + command + "]\n----------------------- Result ------------------------")
                    execute_thread = threading.Thread(target = self.__execute_command, args = (command, message, daemon))
                    execute_thread.daemon = True
                    execute_thread.start()
        except Exception as e:
            utility.warn(str(e) + "\n>>> Continue ...")
        finally:
            s.close()



    ## \brief private local execute_command function
    #
    # After receive the package from remote, open a new thread and execute the command
    # Call the callback function and return the result back to remote
    #
    # NOTE: User should not call this funtion explictly, it should automatically
    # called whenever a remote command comes and create a thread to execute this function
    #
    # \param command The string command to be execute on SELF machine
    # \param message The remote decoded package
    # \param daemon Print out the info message if set False, default is False
    ##
    def __execute_command(self, command, message, daemon = False):
        ## Removed timeout
        try:
            result = subprocess.check_output(command, shell = True).decode('utf-8')
            if not daemon: print (result)
            self.__callback(message[1][0], message[1][1], result, daemon)
        except Exception as e:
            utility.warn(str(e) + "\n>>> Continue", True)
            self.__callback(message[1][0], message[1][1], str(e), daemon)



    ## \brief private braddcast the SELF device to network
    #
    # A single thread should call this function to keep broadcast SELF information
    # to the network.    Broadcast is sending self.this_device information
    #
    # NOTE: User should not call this function explictly, a thread should be initilized
    # when constructing the SAuto
    #
    # \param delay The broadcast interval delay time, default is 1 second
    # \param daemon Print out the info message if set False, default is False
    ##
    def __broadcast(self, delay = 1, daemon = False):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            if not daemon: utility.info("Starting broadcasting at: [" + self.this_device['BROADCAST_IP'] + ":" + str(self.this_device['PORT']) + "]")
            while True:
                self.__loadConfig(self.this_device['PORT'])
                s.sendto(str(self.this_device).encode('utf-8'), (self.this_device['BROADCAST_IP'], int(self.this_device['PORT'])))
                utility.sleep(delay, True)
        except Exception as e:
            utility.warn(str(e) + "\n>>> Continue ...")
        finally:
            s.close()



    ## \brief private function for discovering SAuto node
    #
    # A single thread should call this function to discover the SAuto node in the
    # same network
    # __discover is listening to the broadcast port + 1
    # for example if broadcast on 8888:
    # listening on 8889 for discovering, which means change the broadcast port will create a 
    # different SAuto network (NOTE: potiential overlap)
    #
    # NOTE: User should not call this function explictly, a thread should be initilized
    # when constructing the SAuto
    #
    # \param delay The delay for each discovering process, this is not a very necessary delay
    # but could prevent possbile package overlap
    # \param daemon Print out the info message if set False, default is False
    ##
    def __discover(self, delay = 1, daemon = False):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind(('', self.this_device['PORT']))
                while True:
                    message = utility.strToDict(s.recvfrom(self.buffer_size)[0].decode('utf-8'))
                    if message and message['HOST'] != self.this_device['HOST']:
                        if message['HOST'] not in self.device_list or (message['HOST'] in self.device_list and self.device_list[message['HOST']]['STATUS'] != 'REACHABLE'):
                            if not daemon: utility.info("Discovered device [" + message['HOST'] + "] at [" + message['IP'] + "]")
                            self.device_list[message['HOST']] = message
                            break
                utility.sleep(delay, True)
            except Exception as e:
                utility.warn(str(e) + "\n>>> Continue ...")
            finally:
                s.close()



    ## \brief private callback function when receiving remote package
    #
    # Whenever a remote package is received, it is necessary to response to the remote with
    # this callback function
    # __callback is usually be used for __execution
    #
    # \param ip The IP address of the remote node
    # \param port The port number of the remote node
    # \param message The package content be sent to the remote node
    # \param daemon Print out the info message if set False, default is False
    ##
    def __callback(self, ip, port, message = '', daemon = False):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if not daemon: utility.info("Responding to [" + ip + ":" + str(port) + "]")
            s.sendto(str(message).encode('utf-8'), (ip, port))
        except Exception as e:
            utility.warn(str(e) + "\n>>> Continue ...")



    ## \brief private healthCheck function
    #
    # Whenever SAuto is created, a thread will be generate to run __healthCheck
    # __healthcheck will send a "PING!" to all device in device_list at a given
    # interlval (default 30 seconds) and processing the response to update device_list
    #
    # \param interval The health check interval, in second unit
    # \param daemon Print out info message if set False, default is False
    ##
    def __healthCheck(self, interval = 300, daemon = False):
        while True:
            utility.sleep(interval, True)
            for key in list(self.device_list.keys()):
                if key is 'SELF': next
                ## if self.device_list[key]['STATUS'] is 'UNREACHABLE': next # Skip the unreachable devices
                else:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.settimeout(2)
                        s.sendto('PING!'.encode('utf-8'), (self.device_list[key]['IP'], self.device_list[key]['PORT'] + 1))
                        message = s.recvfrom(self.buffer_size)
                        s.settimeout(None)
                        if message[0].decode('utf-8') != 'PONG!':
                            utility.warn("Health check device at [" + self.device_list[key]['IP'] + ":" + str(self.device_list[key]['PORT']) + "] not responding correctly! Mark device [" + key+ "] UNKNOWN" , False)
                            self.device_list[key]['STATUS'] = 'UNKNOWN'
                        else:
                            self.device_list[key]['STATUS'] = 'REACHABLE'
                    except Exception as e:
                        if key in self.device_list and self.device_list[key]['STATUS'] == 'REACHABLE':
                            utility.warn("Health check device at [" + self.device_list[key]['IP'] + "] failed! Mark device [" + key + "] UNREACHABLE" , False)
                            self.device_list[key]['STATUS'] = 'UNREACHABLE'
                    finally:
                        s.close()
            if not daemon:
                utility.info("        Health Check Result:\n--------------------------------------------------------------------------------")
                for device in self.device_list:
                    print(self.device_list[device]['STATUS'] + '    ' + self.device_list[device]['HOST'] + ': [' + self.device_list[device]['IP'] + ']')
 


    ## \brief Execute command on remote device
    #
    # Execute a remote command on a device
    #
    # \param device A dictionary object with device information, device['IP'] and device['PORT']
    # can not be empty
    # \param command A string command be sent and executed on remote device
    # \param timeout If the response not received within timeout, an exception will be thrown
    # \param daemon Print out info message if set False, default is False
    # \return response[0].decode('utf-8') The response result from remote device
    ##
    def execute(self, device, command, timeout = 20, daemon = False):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(timeout)
            if not daemon: utility.info("Sending command: [" + str(command) + "] to " + device['IP'] + ":" + str(device['PORT'] + 1))
            s.sendto(str(command).encode('utf-8') ,(device['IP'], device['PORT'] + 1))
            response = s.recvfrom(self.buffer_size)
            s.settimeout(None)
            if response: utility.info("Response from [" + response[1][0] + ":" + str(response[1][1]) + "]\n" + response[0].decode('utf-8'))
        except Exception as e:
            utility.warn(str(e) + "\n>>> Continue ...")
        finally:
            s.close()
            return response[0].decode('utf-8')



    ## \brief Get the dictionary device_list
    #
    # \param daemon Print out the info message if set False, default is False
    # \return self.device_list The disctionary object of device_list
    ##
    def getDevices(self, daemon = False):
        if not daemon:
            utility.info("Current alive devices list:\n--------------------------------------")
            utility.pp(self.device_list)
        return self.device_list



    ## \brief Get the dictionary of device_list['SELF'] (Same as this_device)
    #
    # \param name The name of the device in the device_list, defalut is 'SELF'
    # NOTE: instead of name, in the future implementatin using tag for returning multiple devices
    # \param daemon Print out the info message if set False, default is False
    # \return device_list[name] if key 'name' is found, otherwise return device_list['SELF']
    ##
    def getDevice(self, name = 'SELF', daemon = False):
        if name in self.device_list:
            if not daemon:
                utility.info("Getting device " + name + " from devices list\n----------------------------------------------")
                utility.pp(self.device_list[name])
            return self.device_list[name]
        else:
            utility.warn("Device [" + str(name) + "] NOT found, return SELF", False)
            return self.device_list['SELF']


#################################################
    ## TODO TODO TODO
    ## run a process on a device
    def run():
        return 0

    ## TODO TODO TODO
    ## TCP/IP
    ## Serial
    ## USB
    ## Bluetooth
    ## file transfer
#################################################


## \brief SAuto Framework Main funtion, provide the CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:    python3 sauto.py -h or --help for instructions
# (alternatively) run with command:    ./sauto.py
##
def main():
	global PORT, debug_flag, NAME, TIMEOUT
	parser = argparse.ArgumentParser(description='SAuto Framework CLI tools')
	parser.add_argument('-e', '--execute', metavar='Command', nargs='+', help='Execute the remote command on sauto Devices')
	parser.add_argument('-n', '--name', metavar='Device Hostname', help='The hostname of the remote device for execute command, if not given, execute on self')
	parser.add_argument('-p', '--port', metavar='Port Number', type=int, help='The port for initialize the SAuto Framework. The communication port is always given port number add 1')
	parser.add_argument('-t', '--timeout', metavar='Timeout in seconds', type=int, help='The timeout value when executing command on remote device')
	parser.add_argument('-d', '--debug', metavar='[INFO/CLIENT/DEBUG/DAEMON]', help='Set debug flag : [INFO/CLIENT/DEBUG/DAEMON], else using default INFO')
	parser.add_argument('-D', '--daemon', dest='DAEMON', action='store_true', help='Execute the SAuto in daemon mode')
	args = parser.parse_args()
	## Varify the port number?
	if args.port: PORT = args.port
	if args.debug in ['INFO', 'CLIENT', 'DEBUG', 'DAEMON']: debug_flag = args.debug
	if args.name: NAME = args.name
	if args.timeout: TIMEOUT = args.timeout
	sauto = SAuto(port = PORT, debug = debug_flag)
	utility.sleep(3, True)
	if args.execute:
		sauto.execute(sauto.getDevice(NAME), ' '.join(args.execute), timeout = TIMEOUT)
	if args.DAEMON:
		while True: utility.sleep(30, True)


######################## Default Values #########################
PORT = 8888                                     # Default Value #
debug_flag = 'INFO'                             # Default Value #
NAME = 'SELF'                                   # Default Value #
TIMEOUT = 20                                    # Default Value #
#################################################################


## \brief Provide the the entry for main function when execute from command line
if __name__ == "__main__":
    main()
