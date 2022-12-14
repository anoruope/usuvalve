#
#  USUvalve
#  usuvalve.py | Version: 14.12.2021 | Tobias Heer <tobias.heer@acp.de>
#
#  Copyright (C) 2021, ACP IT Solutions GmbH
#  All Rights Reserved.
#
#  NOTICE:  All information contained herein is, and remains
#  the property of ACP IT Solutions GmbH. Unauthorized copying of this software
#  or parts is also strictly prohibited proprietary and confidential.
#  Dissemination of this information or reproduction of this material is strictly
#  forbidden unless prior written permission is obtained from ACP IT solutions GmbH.
#



# Include base and 3rd party code
#
import sys
import json
import time
import traceback


# Include own code
#
import toolz
import cppm_api
import usu_api
import importz
import tranz
import ise_api


# Global var assignment
#
cppm_api.host =                 toolz.cfg['clearpass']['hostname']
cppm_api.authz_bearer =         toolz.cfg['clearpass']['authz_bearer']
ise_api.host =                  toolz.cfg['ise']['hostname']
ise_api.userpass =              toolz.cfg['ise']['username'] +':'+ toolz.cfg['ise']['password']

tranz.path =                    toolz.cfg['transaction']['path']



# load_scopes()
#  Iterates over all CPPM customers in config file to generate dict of credentials.
#  ARGS: type - String of customer type ('clearpass' or 'ise')
#  RETURNS: scopes - list dictionary containing HTTP Basic auth credentials:
#           e.g. {'user': 'RPK', 'pass': 's3cr3t'}, {'user': 'GESTA'...
#
def load_scopes(type):
    scopes = []
    for mapping in toolz.cfg[type]['user_mapping']:
        scopes.append({'user': mapping['user'], \
                       'customer': mapping['customer'], \
                       'pass': mapping['password']})
    return scopes


# has_mac_address()
#  If endpoint missing mandatory mac address data, generate debug output and
#  returns boolsch 'False', otherwise function returns 'True'.
#  ARGS: endpoints = JSON USU Valumeation API endpoint dict
#  RETURNS: 'True' or 'False' if dictionary contains mac address field
#
def has_mac_address(endpoint): # I couldn't get his to really work. Maybe i am missing something
    usu_cfg_mac_field = toolz.cfg['usu']['field_is_mac']
    if usu_cfg_mac_field in endpoint:
        return True
    unknown_info = {}
    list_key_info = [ 'kunde', 'systemname', 'komponententyp', 'seriennr' ]
    for key_info in list_key_info:
        if key_info in endpoint:
            unknown_info[key_info] = endpoint[key_info]
    toolz.logger.debug('Skipping endpoint:' + \
                       json.dumps(unknown_info))
    return False



# inject_insight_adaopt()
#  Logs resulting attribute changes, if an endpoint requires an update.
#  ARGS: cppm_api_dict = dictionay prepated clearpass endpoint attributes +
#        cppm_endpoint = already existing dictionay clearpass endpoint:
#        id (integer, optional): Numeric ID of the endpoint,
#        mac_address (string, optional): MAC Address of the endpoint,
#        description (string, optional): Description of the endpoint,
#        status (string, optional) = ['Known' or 'Unknown' or 'Disabled']:
#                Status of the endpoint,
#        device_insight_tags (string, optional): List of Device Insight Tags,
#        attributes (object, optional): Additional attributes(key/value pairs)
#                    may be stored with the endpoint
#  RETURNS: cppm_api_dict = dictionay of clearpass endpoint attributes +
#                           INSIGHT-ADOPT key-value pairs
#                           (e.g. {..., INSIGHT-ADOPT-ENABLE: True, ...})
#
def inject_insight_adaopt(cppm_api_dict, cppm_endpoint):
    cppm_cfg_key = toolz.cfg['clearpass']['insight_adopt']['key']
    cppm_cfg_query = toolz.cfg['clearpass']['insight_adopt']['query']
    cppm_cfg_target = toolz.cfg['clearpass']['insight_adopt']['target']
    cppm_cfg_value = toolz.cfg['clearpass']['insight_adopt']['value']

    if cppm_endpoint is not None \
    and ('attributes' in cppm_endpoint \
    and ('VLAN-OVERRIDE' in cppm_endpoint['attributes'] \
    and int(cppm_endpoint['attributes']['VLAN-OVERRIDE']) > 0) \
    or ('INSIGHT-ADOPT-ENABLE' in cppm_endpoint['attributes'] \
    and bool(cppm_endpoint['attributes']['INSIGHT-ADOPT-ENABLE']))):
        return cppm_api_dict

    if 'insight_adopt' in  toolz.cfg['clearpass'] \
    and 'attributes' in cppm_api_dict \
    and cppm_cfg_key \
    in cppm_api_dict['attributes'] \
    and toolz.cfg['clearpass']['insight_adopt']['query'] == \
    cppm_api_dict['attributes'][cppm_cfg_key]:
        cppm_api_dict['attributes'][cppm_cfg_target] = cppm_cfg_value
        toolz.logger.info('Enabling INSIGHT-ADOPT for endpoint ' + \
                          cppm_api_dict['mac_address'])
    return cppm_api_dict



# cnt_endpoint_chg()
#  Logs resulting attribute changes, if an endpoint requires an update and
#  counts and returns the number of changes.
#  ARGS: old_dict = dict of existing endpoint attributes
#        new_dict = dict of attributes generated based on USU data
#  RETURNS: cnt_chg = Counter of necessary changes for the endpoint
#
def cnt_endpoint_chg(old_dict, new_dict):
    cnt_chg = 0
    for key,value in old_dict.items():
        if key in new_dict \
        and old_dict[key] != new_dict[key]:
            cnt_chg += 1
            toolz.logger.info('   Updating field '+str(key)+' to '+ \
                              str(new_dict[key]) + '   - old: '+ str(value))
    for key,value in new_dict.items():
        if key not in old_dict:
            cnt_chg += 1
            toolz.logger.info('   Adding field '+str(key)+' to '+ \
                              str(new_dict[key]))
    return cnt_chg

'''
pr??ft, ob der als Parameter ??bergebene Wert ein bestimmtes Kriterium erf??llt, 
Ist dies der Fall, wird der Wert durch eine bestimmte Variable ersetzt.
'''
def validate_value(value):
    if value == "-" or value == "." or value == "_" or value == "'" or value == ":" or value == "*" or value == "!" or value == "&" or value == "=" or value == "":
        new_value = "Unbekannt"
        return new_value
    else:
        return value


# sync_to_cppm()
#  Queries Clearpass for existing endpoint data. USU Valuemation dict gets
#  converted by importz library and INSIGHT-ADOPT features is applied on demand.
#  If endpoint is missing in the endoint database, cppm_api library is used to
#  to create a endpoint. Existing endpoints will be patched by
#  cppm_api.endpoint_update function.
#  ARGS: endpoint = JSON USU Valumeation API endpoint dict
#  RETURNS: None
#
def sync_to_cppm(endpoint):
    usu_cfg_mac_field = toolz.cfg['usu']['field_is_mac']
    try:
        cppm_endpoint = cppm_api.endpoint_query(endpoint[usu_cfg_mac_field])
    except Exception as e:
        toolz.logger.warning('Error quering clearpass endpoint data'+\
                             ' for \''+endpoint[usu_cfg_mac_field]+'\':' +str(e))
        return
    try:
        cppm_api_dict = importz.usu_to_cppm_dict(endpoint, toolz.cfg['usu'])
        cppm_api_dict = inject_insight_adaopt(cppm_api_dict, cppm_endpoint)
        #toolz.logger.debug(str(endpoint))
        #toolz.logger.debug(str(cppm_api_dict))
    except Exception as e:
        toolz.logger.warning('Error creating dict for ClearPass API: '+str(e))

    if cppm_endpoint is None:
        toolz.logger.info('Creating endpoint ' + endpoint[usu_cfg_mac_field])
        cppm_api.endpoint_create(cppm_api_dict, toolz.dry_run)
    else:
        if cnt_endpoint_chg(cppm_endpoint['attributes'],
                            cppm_api_dict['attributes']) > 0:
            toolz.logger.info('Modifying endpoint '+endpoint[usu_cfg_mac_field])
            cppm_api.endpoint_update(cppm_api_dict, toolz.dry_run)
    return



def create_ise_dict(ise_api_dict,mac):
    template = toolz.cfg["usu"]
    field_mapping = template["field_mapping"]
    customAttributes = {}

    for mapping in field_mapping:
        new_key_values_dict = {mapping: validate_value(ise_api_dict[0].get(mapping,""))}
        customAttributes.update(new_key_values_dict)

    json_data = {"ERSEndPoint": {
                    "mac": mac, \
                    "customAttributes": {}
                    }
                }
    
    json_data["ERSEndPoint"]["customAttributes"]["customAttributes"] = customAttributes
    return json_data



def check_value_changed(response,new_ise_dict):
    response_data = response["ERSEndPoint"]
    new_ise_dict_data = new_ise_dict["ERSEndPoint"]
    if response_data["mac"] == new_ise_dict_data["mac"]:
        response_custom_attributes = response_data["customAttributes"]["customAttributes"]
        new_ise_custom_attributes = new_ise_dict_data["customAttributes"]["customAttributes"]
        for key in response_custom_attributes:
            if response_custom_attributes[key] == new_ise_custom_attributes.get(key):
                changevalue = False
            else:
                changevalue = True
                return changevalue
        for key in new_ise_custom_attributes:
            if new_ise_custom_attributes[key] == response_custom_attributes.get(key):
                changevalue = False
            else:
                changevalue = True
                return changevalue
    return changevalue



def sync_to_ise(endpoint):
    usu_cfg_mac_field = toolz.cfg['usu']['field_is_mac']
    try:
        ise_endpoint = ise_api.query_endpoint(endpoint[usu_cfg_mac_field])
    except Exception as e:
        toolz.logger.warning('Error quering ise endpoint data'+\
                             ' for \''+endpoint[usu_cfg_mac_field]+'\':' +str(e))
        return
    try:
        ise_api_dict = importz.usu_to_cppm_dict(endpoint, toolz.cfg['usu'])
        cppm_api_dict = inject_insight_adaopt(cppm_api_dict, ise_endpoint)
        #toolz.logger.debug(str(endpoint))
        #toolz.logger.debug(str(cppm_api_dict))
    except Exception as e:
        toolz.logger.warning('Error creating dict for ISE API: '+str(e))

    new_ise_dict = create_ise_dict(ise_api_dict) # Creates a modified ISE dictionary
    if ise_endpoint["SearchResult"]["total"] == 0:
        #toolz.logger.info('Creating endpoint ' + endpoint[usu_cfg_mac_field]) Funktioniert nicht
        ise_api.create_endpoint(new_ise_dict)
    else:
        resources = ise_endpoint["SearchResult"]["resources"]
        id = resources[0]["id"]
        extra_path = "/" + id
        response = ise_api.request(extra_path)
        value_changed = check_value_changed(response["text"],new_ise_dict)
        if value_changed == True:
            #toolz.logger.info('Modifying endpoint '+ endpoint[usu_cfg_mac_field])
            ise_api.update_endpoint(new_ise_dict, id)

# staging_sync()
#  Verifies for mandatory MAC address field in list of endpoint dicts. If full
#  sync isn't enabled it checks the transaction cache if todays USU data was
#  already processed. In full sync mode, USU API is queried for complete list
#  of all endpoints.
#  ARGS: endpoints = List of JSON USU Valumeation API endpoint dicts
#        target = String of 'clearpass' or 'ise' what the target API will be
#  RETURNS: None
#
def staging_sync(endpoints, target):
    usu_cfg_mac_field = toolz.cfg['usu']['field_is_mac']
    for endpoint in endpoints:
        if not has_mac_address(endpoint):
            continue
        if not toolz.full_sync and tranz.is_done(endpoint):
            continue
        toolz.logger.debug('Processing endpoint \''+\
                           endpoint[usu_cfg_mac_field]+'\'')
        try:
            if target == 'clearpass':
                sync_to_cppm(endpoint)
            if target == 'ise':
                sync_to_ise(endpoint)
                #toolz.logger.warning('Syncing to ISE not yet implemented')
            if not toolz.full_sync:
                tranz.append_cache(endpoint)
        except Exception as e:
            toolz.logger.warning('Failed to handle USU endpoint: '+\
                                 json.dumps(endpoint) + ' - ' + str(e) + '\n' + \
                                 str(traceback.format_exc()))
        #return
    return



# Global main stuff kicks in here
#
#
toolz.logger.info('Starting USUvalve')
while True:
    tranz.rotate_cache()
    target = 'ise'
    scopes = load_scopes(target)
    for scope in scopes:
        if toolz.run_scope and scope['customer'] != toolz.run_scope:
            continue
        time.sleep(10)    
        toolz.logger.debug('Evaluating data of customer user \''+scope['user']+'\'')
        if toolz.full_sync:
            endpoints = (usu_api.get_listtsd(scope))
        else:
            endpoints = (usu_api.get_ndays(scope,ndays=1)) # if endpoint has been updated for a day
        staging_sync(endpoints, target)
        toolz.logger.debug('Completed '+str(len(endpoints)) + \
                           ' endpoints of customer user \'' + scope['user']+'\'')
    toolz.logger.debug('Cycle of all customer users completed')
    if toolz.full_sync:
        toolz.logger.info('Full sync completed')
        sys.exit(0)
