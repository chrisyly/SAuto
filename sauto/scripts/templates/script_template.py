#!/usr/bin/python3

import sprint_config
import argparse
import signal
import sys


## \brief Pre-Test session
#
# Test environment setting up, device initialization
#
# \return 0 if pass, otherwise failure code
##
def pre_test():
	return 0



## \brief Test session
#
# Testing steps
#
# \return 0 if pass, otherwise failure code
##
def test():
	return 0



## \brief Post-Test session
#
# Post Processing test results, teardown the test setting
#
# \return 0 if pass, otherwise failure code
##
def post_test():
	return 0



## \brief system signal handler
#
# Capture the user keyboard interrupt signal (Ctrl + C)
# reset/release resources before exit the program
##
def signal_handler(sig, frame):
	sprint_config.utility.info('Captured keyboard interrupt.\nSafe exiting the process:')
	## TODO Add clean up steps here
	exit(1)



## setting up the template for testing
def main():
	signal.signal(signal.SIGINT, signal_handler) ## register the signal handler
	pre_test()
	test()
	post_test()



## \brief Global Constant for vendor constants
########################## Global Constants #########################
# Add global constant here							# Default Value #
#####################################################################


## \brief give the entry for main when execute from command line
if __name__ == "__main__":
	main()
