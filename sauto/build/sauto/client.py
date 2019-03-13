#!/usr/bin/python3

## \file client.py
# \brief SAuto framework simple client module
#
# SAuto simple client is a simplified tool for execution on a client machine:
# 1. Remote control devices and get the response
# 2. Support multi-platfrom
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

import socket
import argparse

## execute command on remote device
## return remote device result
def execute(device, command, daemon = False):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.settimeout(300)
		if not daemon: print("Sending command: [" + str(command) + "] to " + device['IP'] + ":" + str(device['PORT']))
		s.sendto(str(command).encode('utf-8') ,(device['IP'], device['PORT']))
		response = s.recvfrom(65535) ## \brief Receive buffer size
		s.settimeout(None)
		if response: print("Response from [" + response[1][0] + ":" + str(response[1][1]) + "]\n" + response[0].decode('utf-8'))
	except Exception as e:
		print(str(e) + "\n>>> Continue ...")
	finally:
		return response[0].decode('utf-8')
		s.close()



## \brief SAuto Framework Simple Client, provide the client CLI tool
#
# The main function using the argparse module to allow command line optional argument
# run the command:    python3 client.py -h or --help for instructions
# (alternatively) run with command:    ./client.py
##
def main():
	######################## Default Values #########################
	PORT = 8889                                     # Default Value #
	IP = '127.0.0.1'                                # Default Value #
	#################################################################
	parser = argparse.ArgumentParser(description='SAuto Framework Simple Client CLI tools')
	parser.add_argument('-e', '--execute', metavar='Command', nargs='+', help='Execute the remote command on JFW box')
	parser.add_argument('-i', '--ip', metavar='IP Address', help='The IP address of the remote device for execute command')
	parser.add_argument('-p', '--port', metavar='Port Number', type=int, help='The communication port for executing remote command. Default is 8889')
	parser.add_argument('-D', '--daemon', dest='DAEMON', action='store_true', help='Execute all commands without throwing any exceptions')
	args = parser.parse_args()
	## Varify the port number?
	if args.port: PORT = args.port
	if args.ip: IP = args.ip
	if args.execute:
		execute({'IP' : IP, 'PORT' : PORT}, ' '.join(args.execute), daemon = args.DAEMON)


## \brief Provide the the entry for main function when execute from command line
if __name__ == "__main__":
	main()
