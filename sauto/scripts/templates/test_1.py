#!/usr/bin/python3

import json
## import lsu
import sprint_config

def main():
    #get current busy cell
    ## lsu.getBusyCells()

    ## Add the argument for reading the vendor name/id from input
    # data_set = sprint_config.loadSQLite('', 1)
    data_set = json.loads('{"3":1}')

    ## sprint config - CELL configuration only
    ## NOTE this is merged into sprint_config.vendorConfig
    # lsu.cellConfig(data_set[0]['lsu_id'], data_set[0]['cell_id'], False)  # using config file
    # lsu.cellConfig(data_set[0]['lsu_id'], data_set[0]['cell_id'])         # using rest api

    ## vendors IDs in the in_use vendors will be mark in_use=1 in the database
    ## release the vendors when the test is done
    #in_use_vendors = sprint_config.vendorConfig(data_set, use_rest = True)
    in_use_vendors = sprint_config.vendorConfig(json.loads('{"3":1}'), use_rest = True)
    # sprint_config.triggerJenkins('test_job')

    ## Release the vendors
    for vendor in in_use_vendors:
        sprint_config.setBusy('vendor', 'id=' + str(vendor), in_use = 0)

if __name__ == "__main__":
    main()
