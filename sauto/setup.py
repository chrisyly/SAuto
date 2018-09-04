import tarfile
import json
from pprint import pprint
import os, sys, platform, subprocess
from setuptools import setup, find_packages




# Get the long discription from the README file
def readme(file_name = 'README'):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)) as f:
        return f.read()


def setSQLite(config_json, default = True):
    ## set up default environment settings
    global sqlite_path
    path = os.path.dirname(os.path.realpath(__file__))
    sqlite_file = ''
    if not default: sqlite_file = input("Please enter SQLite DB name (root path: " + path + "/)\nName: [Press Enter to use default]")
    else:
        sqlite_file = 'default.sqlite'
    if sqlite_file:
        sqlite_path = path + '/' + sqlite_file
    else:
        sqlite_path = path + '/default.sqlite'
    config_json['SQLITE']['Master'] = sqlite_path
    with open(path + '/this_device_conf.json', 'w') as this_device_conf:
        json.dump(config_json, this_device_conf)
    print('[INFO] SQLite DB path set at:\n    ' + sqlite_path)


# Get the OS
os_name = os.name
os_platform = platform.platform()

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
    name = 'sauto',
    version = '1.0.0',
    description = 'Simple Automation Framework',
    url = 'https://github.com/chrisyly/SAuto.git',
    author = 'Liyu Ying',
    author_email = 'lying0401@gmail.com',
    long_description = readme('README'),
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
    keywords = 'Sprint Automation Framework & Libraries',
    packages = find_packages(),
    package_dir = {'lib': 'build'},
    install_requires = ['colorama', 'requests', 'python-jenkins'],
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



    ## Create the file path for hosting the archive files
    os.system('mkdir -p /var/www/html/sauto')


    ## Add the script in /etc/init.d for bootup
    with open('/etc/init.d/sauto', 'w') as sauto:
        sauto.write('#!/bin/bash\n')
        sauto.write("""### BEGIN INIT INFO
# Provides:          sauto
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start SAuto at boot time
# Description:       Controls SAuto Automation Server
### END INIT INFO\n""")
        sauto.write('python3 ' + os.path.dirname(os.path.realpath(__file__)) + '/build/sauto/sauto.py -d DEBUG -D &')

    ## Give execution authorization to sauto
    os.system('sudo chmod +x /etc/init.d/sauto')
    os.system('sudo update-rc.d sauto defaults')

    ## Archieve the automation build
    with tarfile.open('/var/www/html/sauto/sauto.tar.gz', "w:gz") as tar:
        tarfile = os.path.dirname(os.path.realpath(__file__))
        tar.add(tarfile, arcname='sauto')


    ## Export root path to a file for automation environment setup
    path = os.path.dirname(os.path.realpath(__file__))
    sqlite_path = path + '/default.sqlite'
    print('[INFO] Setting SAuto root path to: [' + path + ']')
    with open('/var/www/html/sauto/rootpath.conf', 'w') as rootpath:
        rootpath.write(path)


    ## Read airmosaic_conf.json
    print("\n\033[92mThe Default JSON configuration file at [" + path + '/airmosaic_conf.json]\033[0m\n======================================================================================\n')
    json_config = json.loads(readme("this_device_conf.json"))
    print(json.dumps(json_config, indent = 4, sort_keys = True))


    print('''\033[92m
===================================================
=       Setting the default SQLite Database       =
===================================================
\033[0m''')

    ## Check if user want to change the SQLITE path
    command = input("\nDo you want to change the default SQLite DB path (SQLITE.Master)?\n(Yes/No) [Press Enter to keep default]:")
    if command in ('Yes', 'y', 'Y', 'yes', 'YES'): setSQLite(json_config, False)
    else: setSQLite(json_config)

    ## Ask if user want to modify database
    if 'Ubuntu' in os_platform:
        command = input("\nDo you want to modify the database?\n(Yes/No) [Press Enter to skip]:")
        if command in ('Yes', 'y', 'Y', 'yes', 'YES'): subprocess.Popen(['sqlitebrowser', sqlite_path, '-t', 'lte_cell'])
    elif 'centos' in os_platform:
        print('\n\n\ncentos Linux is not yet support, please configure the database with sqlite')


############## Windows Installer #############
if os_name == 'nt':
    ## TODO TODO TODO
    print("TODO")

print("\n\n   \033[92mSprint Automation Installation & Configuration Done\033[0m\n==========================================================")
