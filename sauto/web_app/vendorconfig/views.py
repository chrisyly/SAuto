# -*- coding: utf-8 -*-

## \file views.py
# \brief Django main view file
#
# Default Django views module responding to http request
# modules to be use for responding are defined from url.py
#
# \author Liyu Ying
# \email lying0401@gmail.com
##

from __future__ import unicode_literals
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django import forms
import socket
import lsu
import rf_matrix
import jfw
import sql
import mxa
import utility
import json
import sprint_config
from json2html import *
from datetime import date
import sys,os


## TODO TODO TODO instead of using json2html template, generate an edittable table for the web app
## TODO TODO TODO add loadSQLite for all devices

## \brief Load the device configuration from the given config file path
#
# If the the config file path is not given, the program will tend to
# use the default path.   The config file is a json file, loadConfig is
# looking for the key 'JFW' and get TCP IP address as well as the
# Port for the remote JFW box. If key is not found, a default value
# will be loaded
# NOTE: This function can be called explictly to load user configurations
#
# \param confPath a string value contain the path to the json file
##
def loadConfig(confPath = '/home/sprint/sauto/airmosaic_conf.json'):
	global jenkins_ip, self_ip
	config = utility.loadConfig(confPath)
	if 'error' not in config:
		if 'JENKINS' in config: jenkins_ip = config['JENKINS']['Master']
		else: utility.warn('No Jenkins configuration found in [' + confPath + ']', False)
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			s.connect(('10.255.255.255', 1))
			self_ip = s.getsockname()[0]
		except Exception as e:
			self_ip = '127.0.0.1'
		finally:
			s.close()
	return None



## \brief The base response content for web app
#
# The base response content includes (load from SQLite database):
# 1. a pre-configured vendor table
# 2. a pre-configured RF-Matrix table
# 3. a pre-configured JFW table
# 4. a pre-configured MXA table
# 5. a pre-configured LSU table
# 6. a pre-configured LTE_Cell table
# 7. A Jenkins Job list loaded dynamically from local/remote Jenkins
# (Jenkins IP address is loaded from configure file)
#
# \return response The dictionary object contains all pre-configured table
##

######## Backup table format #########
    ## vendor_table = "'" + 'Pre-configured Vendor<br>' + str(json2html.convert(json = sql.getSQLite('SELECT vendor_id, rf_matrix_output_port, tag, mxa_id, lsu_id FROM pre_config_vendor'), table_attributes='blueTable')) + '<br>Available Vendor<br>' + str(json2html.convert(json = sql.getSQLite('SELECT * FROM vendor'), table_attributes='blueTable')) + "'"
    ## vendor_table = "'" + str(json2html.convert(json = sql.getSQLite('SELECT DISTINCT vendor.*, pre_config_vendor.rf_matrix_output_port, pre_config_vendor.mxa_id, pre_config_vendor.lsu_id, rf_matrix_db.jfw_id, rf_matrix_db.jfw_port, rf_matrix_db.CELLID FROM vendor , pre_config_vendor, rf_matrix_db INNER JOIN vendor pre_config_vendor ON pre_config_vendor.vendor_id = vendor.id AND rf_matrix_db.port = pre_config_vendor.rf_matrix_output_port AND rf_matrix_db.rf_matrix_id = vendor.rf_matrix_id'), table_attributes='blueTable')) + "'"
######################################
def baseResponse():
	vendor_table = '"' + str(sql.getSQLite('SELECT id, name, freq, pci, tech, BW, ULEARFCN, DLEARFCN, rf_matrix_id FROM vendor')) + '"'
	pre_configured_vendor_table = '"' + str(sql.getSQLite('SELECT DISTINCT pre_config_vendor.vendor_id, pre_config_vendor.rf_matrix_output_port, pre_config_vendor.tag, pre_config_vendor.lsu_id, pre_config_vendor.aggr_id, rf_matrix_db.CELLID FROM pre_config_vendor, rf_matrix_db, vendor WHERE pre_config_vendor.rf_matrix_output_port=rf_matrix_db.port AND vendor.rf_matrix_id=rf_matrix_db.rf_matrix_id AND pre_config_vendor.vendor_id = vendor.id ORDER BY pre_config_vendor.vendor_id ASC')) + '"'
	rf_matrix_table = '"' + str(sql.getSQLite('SELECT * FROM rf_matrix')) + '"'
	## TODO multiple JFW
	## TODO rebuild JFW table
	jfw_atten = sprint_config.jfw.healthCheck(daemon = True)
	jfw_sql_list = sql.getSQLite('SELECT DISTINCT jfw_id, jfw_port, CELLID, output_device FROM rf_matrix_db WHERE jfw_port != "" ORDER BY jfw_port ASC')
	for record in jfw_sql_list:
		record['atten'] = jfw_atten[str(record['jfw_port'])]
	jfw_table = '"' + str(jfw_sql_list) + '"'
	mxa_table = '"' + str(sql.getSQLite('SELECT * FROM mxa')) + '"'
	lsu_json = lsu.getCellContent(True)
	## TODO multiple LSU
	## add evaluatedStatus for sdr table if sdr is not busy
	lsu_sdr_table = str(json2html.convert(json = lsu_json['sdrStatus'], table_attributes='blueTable'))
	lsu_fdd_json = []
	lsu_tdd_json = []
	for index,each_properties in enumerate(lsu_json['fddCellStatus']):
		if 'a0Bcch' not in each_properties['genericProperties']: each_properties['genericProperties']['a0Bcch'] = 'N/A'
		if 'a0Pathloss' not in each_properties['genericProperties']: each_properties['genericProperties']['a0Pathloss'] = 'N/A'
		if 'a0Rsrp' not in each_properties['genericProperties']: each_properties['genericProperties']['a0Rsrp'] = 'N/A'
		if 'a1Bcch' not in each_properties['genericProperties']: each_properties['genericProperties']['a1Bcch'] = 'N/A'
		if 'a1Rsrp' not in each_properties['genericProperties']: each_properties['genericProperties']['a1Rsrp'] = 'N/A'
		if 'a1Pathloss' not in each_properties['genericProperties']: each_properties['genericProperties']['a1Pathloss'] = 'N/A'
		if 'bler' not in each_properties['genericProperties']: each_properties['genericProperties']['bler'] = 'N/A'
		if 'cellId' not in each_properties['genericProperties']: each_properties['genericProperties']['cellId'] = 'N/A'
		if 'nack' not in each_properties['genericProperties']: each_properties['genericProperties']['nack'] = 'N/A'
		del each_properties['genericProperties']['sfn']
		del each_properties['genericProperties']['bound']
		del each_properties['genericProperties']['type']
		del each_properties['genericProperties']['ppu']
		del each_properties['genericProperties']['antennas']
		lsu_fdd_json.append(each_properties['genericProperties'])
	lsu_fdd_table = str(json2html.convert(json = lsu_fdd_json, table_attributes='blueTable'))
	for index,each_properties in enumerate(lsu_json['tddCellStatus']):
		if 'a0Bcch' not in each_properties['genericProperties']: each_properties['genericProperties']['a0Bcch'] = 'N/A'
		if 'a0Pathloss' not in each_properties['genericProperties']: each_properties['genericProperties']['a0Pathloss'] = 'N/A'
		if 'a0Rsrp' not in each_properties['genericProperties']: each_properties['genericProperties']['a0Rsrp'] = 'N/A'
		if 'a1Bcch' not in each_properties['genericProperties']: each_properties['genericProperties']['a1Bcch'] = 'N/A'
		if 'a1Rsrp' not in each_properties['genericProperties']: each_properties['genericProperties']['a1Rsrp'] = 'N/A'
		if 'a1Pathloss' not in each_properties['genericProperties']: each_properties['genericProperties']['a1Pathloss'] = 'N/A'
		if 'bler' not in each_properties['genericProperties']: each_properties['genericProperties']['bler'] = 'N/A'
		if 'cellId' not in each_properties['genericProperties']: each_properties['genericProperties']['cellId'] = 'N/A'
		if 'nack' not in each_properties['genericProperties']: each_properties['genericProperties']['nack'] = 'N/A'
		del each_properties['genericProperties']['sfn']
		del each_properties['genericProperties']['bound']
		del each_properties['genericProperties']['type']
		del each_properties['genericProperties']['ppu']
		del each_properties['genericProperties']['antennas']
		lsu_tdd_json.append(each_properties['genericProperties'])
	lsu_tdd_table = str(json2html.convert(json = lsu_tdd_json, table_attributes='blueTable'))
	lsu_table = '"' + str(sql.getSQLite('SELECT * FROM lsu')) + '"'
	## NOTE Deprecated  lte_cell_table = "'" + str(json2html.convert(json = sql.getSQLite('SELECT * FROM lte_cell'), table_attributes='blueTable')) + "'"
	try:
		## NOTE add nextBuildNumber?
		jenkins_json = utility.getRequest(jenkins_ip + '/api/json?tree=jobs[name,description,url]')
		for job in jenkins_json['jobs']:
			del job['_class']
		jenkins_json['pre_configured_vendors'] = sql.getSQLite('SELECT vendor_id, rf_matrix_output_port, tag, mxa_id, lsu_id FROM pre_config_vendor')
		jenkins_table = '"' + str(jenkins_json) + '"'
	except Exception as e:
		utility.warn(str(e), True)
		jenkins_table = ""
	response = {
		"vendor": vendor_table,
		"pre_configured_vendor": pre_configured_vendor_table,
		"rf_matrix": rf_matrix_table,
		"jfw": jfw_table,
		"mxa": mxa_table,
		"lsu": lsu_table,
		"lsu_sdr_status": lsu_sdr_table,
		"lsu_fdd_status": lsu_fdd_table,
		"lsu_tdd_status": lsu_tdd_table,
		## NOTE Deprecated "lte_cell": lte_cell_table,
		"jenkins": jenkins_table
	}
	return response



## \brief The main index response
#
# The main index returns page index.html in the template
# The response contents contain pre-configured data from SQLite database
#
# \param request The HTTP request object from web app
# \return the renderred index page with response body
##
def index(request):
	response = baseResponse()
	return render(request, 'index.html', response)



## \brief Response function for vendor Configuration
#
# Responding to Vendor Configuration request:
#   Take whatever user input and try to configure all devices
# ORlsu_json[0]['info']['fddCellStatus']
# Responding to pre-configured vendor configuration request:
#   Take either ID or Name (Name will be ignore if ID provided) of pre-configured vender in SQLite database
#
# \param request The HTTP request object from web app
# \return the renderred index page with result in the response body
##
def vendorConfig(request):
	if request.method == "POST":
		vendor = request.POST.dict()

		vendor_list = []
		if 'vendor_id' in vendor and vendor['vendor_id']:
			vendor_list = sprint_config.loadSQLite(vendor_id = vendor['vendor_id'])
		elif 'vendor_name' in vendor and vendor['vendor_name']:
			vendor_list = sprint_config.loadSQLite(vendor_name = vendor['vendor_name'])
		elif 'vendor_tag' in vendor and vendor['vendor_tag']:
			vendor_list = sprint_config.loadSQLite(vendor_tag = vendor['vendor_tag'])
		else:
			vendor_list.append(vendor)
		utility.info("\n\n    ================= Vendor Configuration ==================\n\n\n")
		utility.pp(vendor_list)
		try:
			sprint_config.vendorConfig(vendor_list)
			response = baseResponse()
			response['result'] = 'Succeed!'
		except Exception as e:
			utility.error(str(e))
			response = baseResponse()
			response['response'] = vendor
			response['result'] = 'Failed!'

	return render(request, 'index.html', response)



## \brief Response function for RF Matrix Configurationlsu_json[0]['info']['fddCellStatus']
#
# Responding to RF Matrix configuration request:
#   Read and configure RF Matrix with the request body contents:
#     RF Matrix ID
#     input port
#     output port
# Configure the RF Matrix correspondingly
#
# \param request The HTTP request object from web app
# \return the renderred index page with result in the response body
##
def rfMatrixConfig(request):
	if request.method == "POST":
		device = request.POST.dict()
		utility.info("\n\n    ================== RF Matrix Configuration =================\n\n\n")
		try:
			rf_matrix.loadSQLite(device['rf_matrix_id'])
			response = baseResponse()
			response['response'] = device
			if rf_matrix.connectRFMatrix('\x30', device['rf_matrix_input_port'], device['rf_matrix_output_port']): response['result'] = 'Result: Input port [' + device['rf_matrix_input_port'] + '] is connected to output port [' + device['rf_matrix_output_port'] + ']'
			else: responsse['result'] = 'Result: Failed!'
		except Exception as e:
			utility.error(str(e))
			response['result'] = 'Failed!'
	return render(request, 'index.html', response)



## \brief Response function for JFW Configuration
#
# Responding to RF JFW configuration request:
#   Read and configure JFW with the request body contents:
#     JFW ID
#     JFW port
#     JFW Atten levellsu_json[0]['info']['fddCellStatus']
# Configure the JFW correspondingly
#
# \param request The HTTP request object from web app
# \return the renderred index page with result in the response body
##
def jfwConfig(request):
	if request.method == "POST":
		device = request.POST.dict()
		utility.info("\n\n    ================== JFW Configuration =================\n\n\n")
		try:
			jfw.loadSQLite(device['jfw_id'])
			result = 'Result: ' + jfw.connectJFW('SAR' + str(device['jfw_port']) + ' ' + str(device['jfw_atten']))
			
			response = baseResponse()
			response['response'] = device
			response['result'] = 'Result: ' + result
		except Exception as e:
			utility.error(str(e))
			## response['result'] = 'Result: ' + str(e) + ' - Maybe JFW is exceeding limited user connections!'
	## NOTE return HttpResponse(response, content_type="application/json")
	return render(request, 'index.html', response)



## \brief Response function for MXA Configuration
#
# Responding to MXA configuration request:
#   Read and configure MXA with the request body contents:
#     MXA ID
#     Frequency
#     Technology (tdd/fdd)
#     PCI
# Configure the MXA correspondingly
#
# \param request The HTTP request object from web app
# \return the renderred index page with result in the response body
##
def mxaConfig(request):
	mode = {'FDD': 'LTE', 'fdd': 'LTE', 'Fdd': 'LTE',
			'TDD': 'LTETDD', 'tdd': 'LTETDD', 'Tdd': 'LTETDD'}
	if request.method == "POST":
		device = request.POST.dict()
		utility.info("\n\n    ================== MXA Configuration =================\n\n\n")
		response['response'] = device
		try:
			mxa.loadSQLite(device['mxa_id'])
			mxa.setMode(mode[device['tech']])
			mxa.setFrequency(device['freq'])
			mxa.setCID(device['pci'])
			mxa.setRang(0)
			mxa.setSyncType('RS')
			response = baseResponse()
			response['result'] = 'Result: ' + str(mxa.getEVMResult(3))
		except Exception as e:
			utility.error(str(e))
			response = baseResponse()
			response['result'] = 'Result: Failed!'
	return render(request, 'index.html', response)



## \brief Response function for Jenkins Configuration
#
# Responding to Jenkins configuration request:
#   Read and configure Jenkins with the request body contents:
#     Jenkins Job Name
#     NOTE: The Jenkins IP address and Port is loaded from configure file
# Trigger the Jenkins job correspondingly
#
# \param request The HTTP request object from web app
# \return the renderred index page with result in the response body
##
def jenkinsConfig(request):
	if request.method == "POST":
		jobs = request.POST.dict()
		utility.pp(jobs)
		response = baseResponse()
		utility.info("\n\n    ================== Trigger Jenkins =================\n\n\n")
		try:
			if not jobs['new_job_name']:
				sprint_config.triggerJenkins(name = jobs['job_name'], localhost = jenkins_ip)
				response['response'] = jobs
				response['result'] = 'Result: Jenkins job [' + jobs['job_name'] + '] triggered!'
			else:
				sprint_config.createJenkinsJob(job_name = jobs['new_job_name'], xml_config = __jenkinsXMLBuilder(jobs), localhost = jenkins_ip)
				utility.sleep(5, True)
				sprint_config.triggerJenkins(name = jobs['new_job_name'], localhost = jenkins_ip)
				response = baseResponse()
				response['response'] = jobs
				response['result'] = 'Result: Jenkins job [' + jobs['new_job_name'] + '] triggered!'
		except Exception as e:
			utility.error(str(e))
			response = baseResponse()
			response['response'] = jobs
			response['result'] = 'Result: Failed!    Reason: ' + str(e)
	return render(request, 'index.html', response)



## \brief Jenkins XML configuration builder function
#
# Build the Jenkins job XML configuration file
# This XML file is using vendor configuration information adding the following steps in the new job:
#    1. Adding the vendor configuration script to the build step
#    2. After the configuration success, invoke the Prisma jobs
# This XML builder only be called when user define a new job name on the web interface
#
# \param jobs The configuration json object
# \return xml The xml content string for Jenkins createJenkinsJob API
##
def __jenkinsXMLBuilder(jobs):
	## TODO add vendor ID check
	## TODO check if job already created
	## If execute the shell command on the same machine, do not use client.py, [DEBUG] using client to execute on remote machine
	command = 'python3 ' + root_path + '/build/lib/sprint_config.py -D ' + (('-i ' + jobs['vendor_id']) if jobs['vendor_id'] else (('-t ' + jobs['vendor_tag']) if jobs['vendor_tag'] else '-h'))
	if self_ip not in jenkins_ip:
		command = 'python3 /home/prisma/sauto/build/sauto/client.py -D -i ' + self_ip + " -e '" + command + "'"
	time_schedule = ""
	if jobs['time_schedule']:
		time_schedule = str(int(jobs['time_schedule'][3:5])) + " " + str(int(jobs['time_schedule'][0:2])) + " * * *"
	xml = """
<project>
	<actions/>
	<description>Wraper job for """ + jobs['job_name'] + """ test</description>
	<keepDependencies>false</keepDependencies>
	<properties/>
	<scm class="hudson.scm.NullSCM"/>
	<canRoam>true</canRoam>
	<disabled>false</disabled>
	<blockBuildWhenDownstreamBuilding>true</blockBuildWhenDownstreamBuilding>
	<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
	<triggers>
		<hudson.triggers.TimerTrigger>
			<spec>""" + time_schedule + """</spec>
		</hudson.triggers.TimerTrigger>
	</triggers>
	<concurrentBuild>false</concurrentBuild>
	<builders>
		<hudson.tasks.Shell>
			<command>## run client.py to configure the environment then goto down stream job
""" + command + """
			</command>
		</hudson.tasks.Shell>
	</builders>
	<publishers>
		<hudson.tasks.test.AggregatedTestResultPublisher plugin="junit@1.24">
			<includeFailedBuilds>true</includeFailedBuilds>
		</hudson.tasks.test.AggregatedTestResultPublisher>
		<hudson.tasks.BuildTrigger>
			<childProjects>""" + jobs['job_name'] + """</childProjects>
			<threshold>
				<name>SUCCESS</name>
				<ordinal>0</ordinal>
				<color>BLUE</color>
				<completeBuild>true</completeBuild>
			</threshold>
		</hudson.tasks.BuildTrigger>
		<hudson.plugins.emailext.ExtendedEmailPublisher plugin="email-ext@2.62">
			<recipientList>lying0401@gmail.com</recipientList>
			<configuredTriggers>
				<hudson.plugins.emailext.plugins.trigger.AlwaysTrigger>
					<email>
						<recipientList>lying0401@gmail.com</recipientList>
						<subject>$PROJECT_DEFAULT_SUBJECT</subject>
						<body>$PROJECT_DEFAULT_CONTENT</body>
						<recipientProviders>
							<hudson.plugins.emailext.plugins.recipients.DevelopersRecipientProvider/>
							<hudson.plugins.emailext.plugins.recipients.ListRecipientProvider/>
						</recipientProviders>
						<attachmentsPattern/>
						<attachBuildLog>false</attachBuildLog>
						<compressBuildLog>false</compressBuildLog>
						<replyTo>$PROJECT_DEFAULT_REPLYTO</replyTo>
						<contentType>project</contentType>
					</email>
				</hudson.plugins.emailext.plugins.trigger.AlwaysTrigger>
			</configuredTriggers>
			<contentType>default</contentType>
			<defaultSubject>$DEFAULT_SUBJECT</defaultSubject>
			<defaultContent>$DEFAULT_CONTENT</defaultContent>
			<attachmentsPattern/>
			<presendScript>$DEFAULT_PRESEND_SCRIPT</presendScript>
			<postsendScript>$DEFAULT_POSTSEND_SCRIPT</postsendScript>
			<attachBuildLog>true</attachBuildLog>
			<compressBuildLog>false</compressBuildLog>
			<replyTo>$DEFAULT_REPLYTO</replyTo>
			<from/>
			<saveOutput>false</saveOutput>
			<disabled>false</disabled>
		</hudson.plugins.emailext.ExtendedEmailPublisher>
	</publishers>
	<buildWrappers>
		<hudson.plugins.ansicolor.AnsiColorBuildWrapper plugin="ansicolor@0.5.2">
			<colorMapName>xterm</colorMapName>
		</hudson.plugins.ansicolor.AnsiColorBuildWrapper>
	</buildWrappers>
</project>
"""
	return xml



## TODO
def lsuConfig(request):
	response = baseResponse()
	return render(request, 'index.html', response)



## TODO
def lteCellConfig(request):
	response = baseResponse()
	return render(request, 'index.html', response)


def updateDatabase(request):
	if request.method == "POST":
		inputData = request.POST.dict()
		utility.pp(inputData)
		## TODO TODO Use Json to Query instead
		sql.insertSQLite(inputData['database_name'], "lsu_id, mxa_id, rf_matrix_output_port, vendor_id, tag, aggr_id", inputData['lsu_id'] + "," + inputData['mxa_id'] + "," + inputData['rf_matrix_output_port'] + "," + inputData['vendor_id'] + ',"' + inputData['vendor_tag'] + '",' + inputData['aggr_id'])
		utility.sleep(2, True)
		response = baseResponse()
		utility.info("[Test] Update the database with query: " + str(inputData))
		response['result'] = 'Result: ' + "Added new pre-configured vendor"
	## return HttpResponse('')
	return render(request, 'index.html', response)
		


## TODO TODO TODO jsonToQuery
def jsonToQuery(json_input):
	if 'method' in json_input:
		keys = ''
		values = ''
		for key, value in json_input:
			if key != 'method' and key != 'database_name' and key != 'query':
				if keys == '':
					keys += key
					if str(value).isdigit(): values += value
					else: values += ('"' + value + '"')
				else:
					keys += (',' + key)
					if str(value).isdigit(): values += (',' + value)
					else: values += (',"' + value + '"')

		if json_input['method'] == 'insert':
			## sql.insertSQLite(json_input['database_name'], keys, values)
			return 1
		if json_input['method'] == 'delete':
			## if "query" in json_input: sql.deleteSQLite(json_input['database_name'], json_input['query'])
			return 1
		if json_input['method'] == 'update':
			## if "query" in json_input: sql.updateSQLite(json_input['database_name'], keys, values, json_input['query'])
			## else: sql.updateSQLite(json_input['database_name'], keys, values)
			return 1
		
'''
## Rest API
def testAPI(request):
	if request.method == 'GET':
		return
	elif request.method == 'POST':
		return
'''

class htmlForm(forms.Form):
	name = forms.CharField(label='Name')



## \brief Global Configuration
#
# \param jenkins_ip the ip address of the Jenkins server, will be loaded from configure file
##
########################### Global Configuration ########################
jenkins_ip = 'http://127.0.0.1:8080'                    # Default Value #
root_path = '/'                                         # Default Value #
self_ip = '127.0.0.1'									# Default Value #
#########################################################################


## \brief Load the default configuration from SAuto framework
try:
	with open('/var/www/html/sprint/rootpath.conf', 'r') as conf_file:
		path = conf_file.read()
		if path:
			loadConfig(path + '/airmosaic_conf.json')
			root_path = path
		else: loadConfig()
except Exception as e:
	utility.error(str(e), True)
