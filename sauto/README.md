SAuto Automation Framework

Current Version: 1.0.0

Supported Devices:

RF Matrix\n
JFW Attenuator\n
MXA Signal Analysis\n

NOTE: Device configuration is in the this_device_conf.json file\n


Installation:

Network requirement:
	Network connection is required in update and install the dependency packages

OS:
	Ubuntu 12.04+
	Debain wheezy
	Windows
	##TODO Need manual install
	Arch
	Centos
	OSX

Required environment:
	Pyhon3/Python2
	##TODO Need manual installation if not ubuntu/debain
	SQLite

How to install Python:
	on ubuntu/debain: (Note: you may need 'sudo' to install packages)
		apt-get update
		apt-get install python3
		apt-get install python3-pip

Automation Installation:
	download or copy the whole folder of 'sauto'
	cd into the folder where sauto located
	run command: (Note: you may be asked password to promote sudo)
		python3 setup.py install - for python3
		python setup.py install - for python2

	Follow the instruction to complete initial configuration



Scripting

scripts templates path:

under folder <path>/sauto/scripts/templates


## TODO add help function to configure devices and manage database

