#
#  USUvalve - Aruba Clearpass Endpoint API calls
#  cppm_api.py | Version: 06.12.2021 | Tobias Heer <tobias.heer@acp.de>
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
import requests
import json
import base64


import toolz

# Global var assignment
#
authz_bearer = "Bearer 7521**********************3c23c2"
host = "bitna5008mvcp1"
proxies={'http': None, 'https': None}


ise_host = toolz.cfg['ise']['hostname']
userpass = "admin" + ':' + "ISEc0ld"
encoded_userpass = base64.b64encode(userpass.encode()).decode()
url_base = ise_host + "/ers/config/endpoint"

# generate_header
#   Returns full HTTP header with current bearer of cppm_api module
#   ARGS: -
#   RETURNS: HTTP header for requests module (string)
#
def generate_header():
    return  {"Authorization": authz_bearer, "Content-Type": "application/json"}




# endpoint_query
#   Queries ClearPass endpoint DB for specified mac and returns attributes.
#   Function returns 'None' if endpoint doesn't exists ands fails if
#   API returns status != '200'.
#   ARGS: mac = String with MAC Address (e.g. 00:11:22:33:44:aA)
#   RETURNS: 'None' if endpoint doesn't exists, or cppm endpoint data:
#   {"id": 17591,
#   "mac_address": "54ee75de8c15",
#   "status": "Known",
#   "attributes": {
#     "USU-CUSTOMER": "GESTA",
#     "USU-ORG-CODE": "LG Konstanz",
#     "VLAN-OVERRIDE": "0",
#     "USU-ADMIN-GROUP": "BIT-2L-R43-DG-TFS",
#     "USU-LAST-CHANGE": "14.02.2019 15:26",
#     "USU-SYSTEM-CODE": "SCN-0000018041",
#     "USU-SYSTEM-NAME": "LGEKNZ01CN0046",
#     "USU-SYSTEM-TYPE": "Lenovo ThinkPad X1 Yoga (JUS-16-CN-B1-1)",
#     "USU-SYSTEM-CLASS": "Notebook",
#     "USU-LOCATION-ROOM": "03. Apr",
#     "USU-LOCATION-SITE": "KONSTANZ-GERICHTSGASSE15-78462",
#     "USU-SYSTEM-SERIAL": "R90P22WF",
#     "LEGACY-SWITCH-NAME": "de-lvgs-konstB-ds-01.de-lvgs-konstB.local",
#     "LEGACY-SWITCH-PORT": "Gi1/0/17",
#     "LEGACY-SWITCH-VLAN": "202",
#     "USU-COMPONENT-CODE": "KCN-0000127100",
#     "USU-ORG-DESCRIPTION": "Landgericht Konstanz",
#     "USU-LOCATION-BUILDING": "2. OG",
#     "VLAN-PREFER-NAD-DEFAULT": "false" },
#     "_links": {
#     "self": {
#       "href": "https://10.127.134.32/api/endpoint/17591"}
#       }
#     }
#


def endpoint_query(mac): # checks if the endpoint specified already exists
    global host
    url = 'https://' + host + '/api/endpoint/mac-address/' + str(mac)
    endpoints = []
    try:
        result = requests.get(url, headers=generate_header(), verify = False)
    except Exception as e:
        raise Exception('API error querying endpoint: ' + str(e))
    if result.status_code == 404:
        return None
    if result.status_code >= 300:
        raise Exception('API HTTP status returns error while querying endpoint: ' + \
                        result.json()['detail'])
    try:
        endpoint = result.json()
    except Exception as e:
        raise Exception('API error while reading endpoint attributes: ' + str(e))
    return endpoint


def query_endpoint(mac,method="GET", payload={}):
    global ise_host
    try:
        url = 'https://' + ise_host + "/ers/config/endpoint?filter=mac.EQ." + mac
        headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'ERS-Media-Type': 'identity.endpoint.1.2',
        'Authorization': 'Basic ' + encoded_userpass,
        }
        response = requests.request(method, url, headers=headers, verify = False, data=payload)
        if response.status_code == 404:
            return None
        if response.status_code >= 300:
            raise Exception('API HTTP status returns error while querying endpoint: ' + \
                response.json()['detail'])
    except Exception as ex:
        print(str(ex))
        raise Exception('API error querying endpoint: ' + str(ex))
    try:
        endpoint_response = response.json()
    except Exception as ex:
        print(str(ex))
        raise Exception('API error while reading endpoint attributes: ' + str(ex))
    return endpoint_response

# endpoint_list
#   Generates list of endpoints by calling Clearpass API
#   ARGS: page_limit = maximum returned endpoints by single API call (int)
#   RETURNS: list with dictionary of endpoints:
#       id (integer, optional): Numeric ID of the endpoint,
#       mac_address (string, optional): MAC Address of the endpoint,
#       description (string, optional): Description of the endpoint,
#       status (string, optional) = ['Known' or 'Unknown' or 'Disabled']:
#               Status of the endpoint,
#       device_insight_tags (string, optional): List of Device Insight Tags,
#       attributes (object, optional): Additional attributes(key/value pairs)
#                   may be stored with the endpoint
#
def endpoint_list(page_limit=1000):
    global host
    url = 'https://' + host + '/api/endpoint?limit=' + str(page_limit)
    endpoints = []
    try:
        result = requests.get(url, headers=generate_header(), proxies=proxies)
    except Exception as e:
        raise Exception('API error reading endpoints: ' + str(e))
    if result.status_code >= 300:
        raise Exception('API returns error while listing endpoinst: ' + \
                        result.json()['detail'])
    try:
        endpoints = result.json()['_embedded']['items']
        while result_should_scrolled(result):
            result = requests.get(result.json()['_links']['next']['href'], \
                                  headers=generate_header(), proxies=proxies)
            endpoints = endpoints + result.json()['_embedded']['items']
    except Exception as e:
        raise Exception('API error reading following endpoints: ' + str(e))
    return endpoints


def request(extrapath,method="GET", payload={}):
    global url_base
    try:
        url = 'https://' + url_base + extrapath
        headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'ERS-Media-Type': 'identity.endpoint.1.2',
        'Authorization': 'Basic ' + encoded_userpass,
        }
        response = requests.request(method, url, headers=headers, verify = False, data=payload)
        return { "status":response.status_code, "text": response.json()}
    except Exception as ex:
        print(str(ex))
        raise Exception('API error while reading endpoint attributes: ' + str(ex))
            

#  result_should_scrolled
#   Returns 'None' if there is no further page with additional endpoints in response
#   ARGS: result = result of API call
#   RETURNS: result of API call or None if '_links' key is missing in result dict
#
def result_should_scrolled(result):
    if 'next' in  result.json()['_links']:
        return result
    else:
        return None



# endpoint_create
#   Creates endpoint of given endpoint dictionary by calling Clearpass API
#   ARGS: endpoint_dict = dictionay of clearpass endpoint attributes:
#       id (integer, optional): Numeric ID of the endpoint,
#       mac_address (string, optional): MAC Address of the endpoint,
#       description (string, optional): Description of the endpoint,
#       status (string, optional) = ['Known' or 'Unknown' or 'Disabled']:
#               Status of the endpoint,
#       device_insight_tags (string, optional): List of Device Insight Tags,
#       attributes (object, optional): Additional attributes(key/value pairs)
#                   may be stored with the endpoint
#   RETURNS: None
#
def endpoint_create(endpoint_dict, dry_run=False):
    global host
    path = '/api/endpoint'
    url = 'https://' + host + path
    try:
        if dry_run:
            print('    Emulating API POST call: '+url)
            print('    ' + str(json.dumps(endpoint_dict)))
            return
        else:
            result = requests.post(url, data=json.dumps(endpoint_dict), \
                                   headers=generate_header(), proxies=proxies)
            #return # delete me
    except Exception as e:
        raise Exception('API error creating endpoint: ' + str(e))
    if result.status_code >= 300:
        raise Exception('API returns error while creating endpoint object: ' + \
                        json.dumps(endpoint_dict) + ': ' + \
                        result.json()['detail'], result.status_code)
    return


def create_endpoint(json_data):
    try:
        new_object = json.dumps(json_data)
        new_object = new_object.replace("'","")
        extra_path = ""
        response = request(extra_path,"POST", new_object)
        if response.status_code == 404:
            return None
        if response.status_code >= 300:
            raise Exception('API HTTP status returned an error while creating endpoint: ' + \
                response.json()['detail'])

    except Exception as ex:
        print(str(ex))
        raise Exception('API HTTP status returned an error while creating endpoint: ' + str(ex))

def update_endpoint(json_data, id):
    try:
        new_object = json.dumps(json_data)
        new_object = new_object.replace("'","")
        extra_path = "/" + str(id)
        response = request(extra_path,"PUT", new_object)
        if response["text"] == "" or response["text"] == None:
            print(str(response["status"]))
        else:
            response_text = str(response["text"])
        if response.status_code == 404:
            return None
        if response.status_code >= 300:
            raise Exception('API HTTP status returned an error while updating endpoint: ' + response.json()['detail'])

    except Exception as ex:
        print(str(ex))
        raise Exception('API HTTP status returned an error while updating endpoint: ' + str(ex))

# endpoint_update
#   Updates endpoint with given endpoint dictionary by calling Clearpass API
#   ARGS: endpoint_dict = dictionay of clearpass endpoint attributes:
#       id (integer, optional): Numeric ID of the endpoint,
#       mac_address (string, optional): MAC Address of the endpoint,
#       description (string, optional): Description of the endpoint,
#       status (string, optional) = ['Known' or 'Unknown' or 'Disabled']:
#               Status of the endpoint,
#       device_insight_tags (string, optional): List of Device Insight Tags,
#       attributes (object, optional): Additional attributes(key/value pairs)
#                   may be stored with the endpoint
#   RETURNS: None
#
def endpoint_update(endpoint_dict, dry_run=False):
    global host
    if not 'mac_address' in endpoint_dict:
        raise Exception ('Skipping endpoint update - missing mac_address: ' + \
                        str(json.dumps(endpoint_dict)))
    path = '/api/endpoint/mac-address/'
    url = 'https://' + host + path + endpoint_dict['mac_address']
    try:
        if dry_run:
            print('    Emulating API PATCH call: '+url)
            print('    ' + str(json.dumps(endpoint_dict)))
            return
        else:
            result = requests.patch(url, data=json.dumps(endpoint_dict), \
                                    headers=generate_header(), proxies=proxies)
            #return # delete me
    except Exception as e:
        raise Exception('API error updating endpoint object: ' + \
                        str(json.dumps(endpoint_dict)) + ': ' + str(e))
    if result.status_code >= 300:
        raise Exception('API returns error while updating endpoint: '+ \
                        str(json.dumps(endpoint_dict)) + ': ' + \
                        result.json()['detail'], result.status_code)
    return



# endpoint_mac_delete
#   Deletes specified endpoint by calling Clearpass API
#   ARGS: endpoint_mac (string with MAC address e.g. '001122334455')
#   RETURNS: None
#
# def endpoint_mac_delete(endpoint_mac):
#     global host
#     path = '/api/endpoint/mac-address/'
#     url = 'https://' + host + path + endpoint_mac
#     try:
#     #    result = requests.delete(url, headers=generate_header())
#         print('Debug: Del ' + str(json.dumps(endpoint_dict)))
#     except Exception as e:
#         raise Exception('API error deleting endpoint: ' + str(e))
#     if result.status_code >= 300:
#         raise Exception('API returns error while deleting endpoint '+ \
#                         str(endpoint_mac) + ': ' + result.json()['detail'], \
#                         result.status_code)
#     return
