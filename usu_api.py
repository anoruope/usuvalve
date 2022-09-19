#
#  USUvalve - USU Valuemation API calls
#  usu_api.py | Version: 10.02.2022 | Tobias Heer <tobias.heer@acp.de>
#
#  Copyright (C) 2022, ACP IT Solutions GmbH
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
import time
from datetime import date, timedelta
from pprint import pprint

# Global var assignment
#
#host = "qs-test-api.bitbw-usu.bwl.de"
host = "api.bitbw-usu.bwl.de"
proxies={'http': None, 'https': None}


# count_records
#   Returns total number of asset records in USU Valuemation
#   ARGS: scope = dict with credentials for USU mandate scope
#         { 'user' = 'username', 'pass' = 'password'}
#   RETURNS: Integer containing number of records
#
def count_records(scope):
    global host
    url = 'https://' + host + '/REST-Service/api/macmon/LENGTH'
    try:
        result = requests.get(url, auth=(scope['user'],scope['pass']),
                              proxies=proxies)
        count_result = int(result.json()['numberOfRecords'])
    except Exception as e:
        raise Exception('API error while counting endpoints: ' + str(e))
    return count_result


#  get_listtsd(nth)
#   Returns JSON data from USU Valuemation in thousand steps
#   ARGS: scope = dict with credentials for USU mandate scope
#         { 'user' = 'username', 'pass' = 'password'}
#         nth = Integer of thousand step (1 = 0-1000, 2 = 1001-2000...)
#   RETURNS: endpoints = List of JSON USU Valumeation API data
#           {'admingruppe': 'BIT-2L-R43-DG-TFS',
#           'adresse': 'RAVENSBURG-HINZISTOBEL34-88212',
#           'betriebsmodell': 'Betreut',
#           'computername': 'JVARVB01CD0172',
#           'erstellt': '2017-04-26T16:04:07Z[UTC]',
#           'feldgruppe': 'PC',
#           'geaendert': '2020-03-10T13:29:11Z[UTC]',
#           'komponentebemerkung': 'Pilot Justiz Projekt',
#           'komponentenklasse': 'Desktop',
#           'komponentennr': 'KCD-0000110870',
#           'komponententyp': 'HP ProDesk 600 G3 SFF (JUS-17-CD-A1-1)',
#           'komponentestatus': 'ACT',
#           'kunde': 'JV',
#           'macadresse': 'C8:D3:FF:A0:0D:3D',
#           'orgeinheit_beschreibung': 'Justizvollzugsanstalt Ravensburg',
#           'orgeinheit_nr': 'JVA Ravensburg',
#           'raum': 'G 024',
#           'raumadresse': 'JUM00054_EG_G 024',
#           'seriennr': 'CZC713856T',
#           'systemart': 'Workstation Desktop',
#           'systemklasse': 'IT_Workplace',
#           'systemname': 'JVARVB01CD0172',
#           'systemnr': 'SCD-0000054888',
#           'systemstatus': 'ACT'},...
#
def get_listtsd(scope, nth=1):
    global host
    url = 'https://' + host + '/REST-Service/api/macmon/LISTTSD/' + str(nth)
    try:
        result = requests.get(url, auth=(scope['user'],scope['pass']),
                              proxies=proxies)
    except Exception as e:
        raise Exception('USU API error while fetching data: ' + str(e))
    try:
        if result.status_code >= 401:
            raise Exception('USU API error: '+str(result.status_code)+\
                            ' with user '+scope['user'])
        endpoints = result.json()
        if 'type' in endpoints \
        and endpoints['type'].lower() == 'error':
            raise Exception(str(endpoints['explanation']))
    except Exception as e:
        raise Exception('USU API while handling data: ' + str(e))
    if len(endpoints) == 1000:
        time.sleep(10)
        endpoints.extend(get_listtsd(scope,nth+1))
    return endpoints



# gen_date_range
#  Generating dict with date strings for endpoints_date_listtsd()
#  ARGS: ndays - Integer, history of days from past to tomorrow
#  RETURNS: date_rage dict:
#            {'fromDate' = <today - ndays - 1>,
#             'toDate' = <today + 1>} ...because we can't specify exact time
#
def gen_date_range(ndays):
    today = date.today()
    date_range = {}
    date_range['fromDate'] = (today - timedelta(days=ndays-1)).strftime("%Y-%m-%d")
    date_range['toDate'] = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    return date_range


#  get_ndays
#   Returns: JSON data from USU Valuemation in thousand steps by date
#   ARGS: scope = dict with credentials for USU mandate scope
#         { 'user' = 'username', 'pass' = 'password'}
#         ndays = Integer - history in days (default = 1 day)
#         nth = Integer - thousand steps (1 = 1-1000, 2 = 1001-2000...)
#   RETURNS: endpoints = List of JSON USU Valumeation API data
#           {'admingruppe': 'BIT-2L-R43-DG-TFS',
#           'adresse': 'RAVENSBURG-HINZISTOBEL34-88212',
#           'betriebsmodell': 'Betreut',
#           'computername': 'JVARVB01CD0172',
#           'erstellt': '2017-04-26T16:04:07Z[UTC]',
#           'feldgruppe': 'PC',
#           'geaendert': '2020-03-10T13:29:11Z[UTC]',
#           'komponentebemerkung': 'Pilot Justiz Projekt',
#           'komponentenklasse': 'Desktop',
#           'komponentennr': 'KCD-0000110870',
#           'komponententyp': 'HP ProDesk 600 G3 SFF (JUS-17-CD-A1-1)',
#           'komponentestatus': 'ACT',
#           'kunde': 'JV',
#           'macadresse': 'C8:D3:FF:A0:0D:3D',
#           'orgeinheit_beschreibung': 'Justizvollzugsanstalt Ravensburg',
#           'orgeinheit_nr': 'JVA Ravensburg',
#           'raum': 'G 024',
#           'raumadresse': 'JUM00054_EG_G 024',
#           'seriennr': 'CZC713856T',
#           'systemart': 'Workstation Desktop',
#           'systemklasse': 'IT_Workplace',
#           'systemname': 'JVARVB01CD0172',
#           'systemnr': 'SCD-0000054888',
#           'systemstatus': 'ACT'},...
#
def get_ndays(scope,ndays=1,nth=1):
    global host
    date_range = gen_date_range(ndays)
    url = 'https://' + host + '/REST-Service/api/macmon/DATE/CHANGE' + \
         '?fromDate='+ date_range['fromDate'] + \
         '&toDate='+ date_range['toDate']+ \
         '&nth='+ str(nth)
    #print(url)
    try:
        result = requests.get(url, auth=(scope['user'],scope['pass']),
                              proxies=proxies)
    except Exception as e:
        raise Exception('USU API error while fetching data: ' + str(e))
    try:
        if result.status_code >= 401:
            raise Exception('USU API error: '+str(result.status_code)+\
                            ' with user '+scope['user'])
        endpoints = result.json()
        if 'type' in endpoints \
        and endpoints['type'].lower() == 'error':
            if 'keine daten gefunden' in endpoints['explanation'].lower():
                return []
            raise Exception(str(endpoints['explanation']))
    except Exception as e:
        raise Exception('USU API while handling data: ' + str(e))
    if len(endpoints) == 1000:
        time.sleep(5)
        endpoints.extend(get_ndays(scope,ndays,nth+1))
    return endpoints


# Debug:
#scope = {'user': 'RPK', 'pass': 'lO4w***********nva0Z'}
#pprint(count_records(scope))
#pprint(get_listtsd(scope))
#pprint(get_ndays(scope,ndays=30))
