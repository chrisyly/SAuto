Simple Automation Framework (SAuto)
===============================================

Current Version
-----------------------------
2.4.0

Supported Devices
-----------------------------
Quintech RF Matrix  
	- QRB RF Matrix  
	- RBM RF Matrix  
JFW Attenuation Assembly  
Keysight MXA Signal Analyzer  
Keysight MXG Signal Generator  


Installation
-----------------------------
Network Requirement:  
	Network connection is required in intial updates and installing the dependency packages  

OS:  
	Ubuntu 12.04 and +  
	Debain wheezy  
	Arch  
	Centos  
	OSX  
	Windows 7 and later  

Required Environment:  
	Python (optional)  
	Python3  
	SQLite database  

How to install Python/Python3:  
	on ubuntu/debain: (Note: you may need 'sudo' to install packages)  
		apt-get update  
		apt-get install python (optional)  
		apt-get install python3  

Automation Installation:  
	1. Download or copy the whole folder of 'sauto'  
	2. cd into the folder where sauto located  
	3. Run command: (Note: you may need to promote 'sudo' to install packages)  
		python3 setup.py install - for python3  
		python setup.py install - for python2  
	4. Follow the instruction to complete initial configuration  


Scripting
===============================================

scripts templates
------------------------
under folder <path>/sauto/scripts/templates


Others
===============================================

sqlitebrowser
-----------------------
sqlitebrowser is an optional GUI interface to manage the SQLite database

Apache2 file server (Windows Exclusive)
-----------------------
Setting up Apache2 file server for the controller to download SAuto archive and testing logs

ADB
-----------------------
Android Debug Bridge if want to enable Android devices remote control
