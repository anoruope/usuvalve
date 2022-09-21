
import requests
import json
import base64
import os
from os import path
from dotenv import load_dotenv

import toolz

# Global var assignment
#
execution_path = os.getcwd()
load_dotenv(path.join(execution_path, '.env'))

ise_host = toolz.cfg['ise']['hostname']
ise_user = os.getenv('USER')
ise_pass = os.getenv('PASSWD')
userpass = ise_user + ':' + ise_pass
encoded_userpass = base64.b64encode(userpass.encode()).decode()
url_base = ise_host + "/ers/config/endpoint"


def query_endpoint(mac,method="GET", payload={}):
    global url_base
    try:
        url = 'https://' + url_base + "?filter=mac.EQ." + mac
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


    