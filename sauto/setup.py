## \file setup.py
# \brief SAuto framework installer
#
# setup.py using python setuptools to install dependency packages and compile the code
# Network connection is required to install the packages
# (Optional) Following the screen instructions, user can define the default SQLite database path
# (Optional) Following the screen instructions, user can edit the SQLite database with SQLitebrowser GUI (Ubuntu OS only)
#
# \author Liyu Ying
# \email lying0401@gmail.com
##


import tarfile
import json
import socket
from pprint import pprint
import os, sys, platform, subprocess
from setuptools import setup, find_packages


# Get the OS
os_name = os.name
os_platform = platform.platform()

# Get the root path
root_path = os.path.dirname(os.path.realpath(__file__))

# Get the main IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
	s.connect(('10.255.255.255', 1))
	IP = s.getsockname()[0]
except Exception as e:
	utility.warn(str(e) + "\n    Setting IP to 127.0.0.1", True)
	IP = '127.0.0.1'
finally:
	s.close()

# Get the long discription from the README file
def readme(file_name = 'README.md'):
	with open(os.path.join(root_path, file_name)) as f:
		return f.read()


def setSQLite(config_json, default = True):
	## set up default environment settings
	global sqlite_path
	path = os.path.dirname(os.path.realpath(__file__))
	sqlite_file = ''
	if not default: sqlite_file = input("Please enter SQLite DB name (root path: " + path + "/)\nName: [Press Enter to use default]")
	else:
		sqlite_file = 'simple.sqlite'
	if sqlite_file:
		sqlite_path = path + '/' + sqlite_file
	else:
		sqlite_path = path + '/simple.sqlite'
	config_json['SQLITE']['Master'] = sqlite_path
	with open(path + '/config_files/this_device_conf.json', 'w') as this_device_conf:
		json.dump(config_json, this_device_conf)
	print('[INFO] SQLite DB path set at:\n    ' + sqlite_path)


# Prompt to sudo if not
# TODO Python2 package installation has some issue
if os_name == 'posix':
	if os.geteuid() != 0:
		if sys.version_info >= (3, 0): subprocess.call(['sudo', '-E', 'python3', 'setup.py', sys.argv[1]])
		else: subprocess.call(['sudo', '-E', 'python', 'setup.py', sys.argv[1]])
		exit(1)

print("""


		\033[92m#####################################################
		#                                                   #
		#                Automation Installer               #
		#                                                   #
		#####################################################\033[0m


			Downloading and Installing python packages
-------------------------------------------------------------------""")


setup(
	name = 'SimpleAutomation',
	version = '2.4.0',
	description = 'Simple automation framework',
	url = 'https://github.com/chrisyly/SAuto.git', # TODO: open a github repo
	author = 'Liyu Ying',
	author_email = 'lying0401@gmail.com',
	long_description = readme('README.md'),
	zip_safe = False,
	include_package_data = True,
	license = '',
	classifiers = [
		'Development Status :: 3 - Alpha',
		'Framework :: SAuto',
		'Intended Audience :: Developers',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Topic :: Software Development :: Libraries :: Python modules',
		'Topic :: Software Development :: Libraries :: Application Frameworks',
	],
	keywords = 'Simple Automation Framework & Libraries',
	packages = find_packages(),
	package_dir = {'lib': 'build'},
        install_requires = ['colorama', 'requests', 'python-jenkins', 'json2html', 'django_logtail', 'django-cors-headers', 'humanize', 'pexpect'],
)


########### Linux Installer ###########
## Installing GUI for SQLite browser
if os_name == 'posix':
	print("\n===================== \033[92mInstall SQLite Browser GUI\033[0m ========================")
	if 'Ubuntu' in os_platform:
		subprocess.check_call(['add-apt-repository', '-y', 'ppa:linuxgndu/sqlitebrowser'])
		subprocess.check_call(['apt-get', 'update'])
		subprocess.check_call(['apt-get', '-y', 'install', 'sqlitebrowser'])
	elif 'centos' in os_platform:
		print ("\n\n\n Not yet support centos OS\n\n\n")

	print("\n=================== \033[92mConfiguring system environment\033[0m ========================")



	## path = os.path.join('var','www','html')
	## if not os.path.exists(path):
	## 	os.mkedirs(path)
	## Create the file path for hosting the archive files
	os.system('mkdir -p /var/www/html/sauto')
	os.system('mkdir -p /var/www/html/sauto/logs')
	os.system('chmod 777 /var/www/html/sauto/logs')


	## Add the script in /etc/init.d for bootup
	with open('/etc/init.d/sauto', 'w') as sauto:
		sauto.write('#!/bin/bash\n')
		## init.d settings
		sauto.write("""### BEGIN INIT INFO
# Provides:          sauto
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start SAuto at boot time
# Description:       Controls SAuto Automation Server
### END INIT INFO\n""")
		sauto.write("do_start()\n{\n    mkdir /var/www/html/sauto/logs/`date +%Y-%m-%d` >> /dev/null 2>&1 || true\n")
		sauto.write("    mkdir /var/www/html/sauto/logs/system >> /dev/null 2>&1 || true\n")
		sauto.write("    chmod 777 /var/www/html/sauto/logs/`date +%Y-%m-%d`\n")
		sauto.write("    python3 -u " + root_path + "/build/sauto/sauto.py -d DEBUG -D >> /var/www/html/sauto/logs/system/sauto.log &\n")
		## sauto.write("    python3 -u " + root_path + "/web_app/manage.py runserver " + IP + ":8890 > /var/www/html/sauto/logs/system/webapp.log &\n}\n")

		sauto.write("""
force_stop()
{
	ps -ef | grep 'sauto' | grep -v grep | awk '{print $2}' | xargs -r kill -9
}

case "$1" in
	start)
		do_start
		;;
	stop)
		force_stop
		;;
	restart|force-reload)
		force_stop
		do_start
		;;
	*)
		force_stop
		do_start
		;;
esac
""")

	## Give execution authorization to sauto
	os.system('sudo chmod +x /etc/init.d/sauto')
	if 'Ubuntu' in os_platform: os.system('sudo update-rc.d sauto defaults')
	elif 'centos' in os_platform: os.system('sudo chkconfig sauto on')

	## Archieve the automation build
	with tarfile.open('/var/www/html/sauto/sauto.tar.gz', "w:gz") as tar:
		tarfile = os.path.dirname(os.path.realpath(__file__))
		tar.add(tarfile, arcname='sauto')


	## Export root path to a file for automation environment setup
	path = os.path.dirname(os.path.realpath(__file__))
	sqlite_path = path + '/simple.sqlite'
	print('[INFO] Setting SAuto root path to: [' + path + ']')
	with open('/var/www/html/sauto/rootpath.conf', 'w') as rootpath:
		rootpath.write(path)


	## Read this_device_conf.json
	print("\n\033[92mThe Default JSON configuration file at [" + path + '/config_files/this_device_conf.json]\033[0m\n======================================================================================\n')
	json_config = json.loads(readme("config_files/this_device_conf.json"))
	print(json.dumps(json_config, indent = 4, sort_keys = True))


	print('''\033[92m
===================================================
=       Setting the default SQLite Database       =
===================================================
\033[0m''')

	## Check if user want to change the SQLITE path
	command = input('\nDo you want to change the default SQLite DB path (SQLITE.Master)?\n(Yes/No) [Press Enter to keep default]:')
	if command in ('Yes', 'y', 'Y', 'yes', 'YES'): setSQLite(json_config, False)
	else: setSQLite(json_config)

	## Ask if user want to modify database
	if 'Ubuntu' in os_platform:
		command = input("\nDo you want to modify the database?\n(Yes/No) [Press Enter to skip]:")
		if command in ('Yes', 'y', 'Y', 'yes', 'YES'): subprocess.Popen(['sqlitebrowser', sqlite_path, '-t', 'lte_cell'])
	elif 'centos' in os_platform:
		print('\n\n\ncentos Linux is not yet support, please configure the database with sqlite3')

	## Restart the services
	os.system('sudo service sauto stop')
	os.system('sudo service sauto start')


############## Windows Installer #############
if os_name == 'nt':
	## TODO TODO TODO
	print("TODO")

print("\n\n   \033[92mAutomation Installation & Configuration Done\033[0m\n==========================================================")
