#
#  USUvalve - Transactional Library
#  tranz.py | Version: 07.12.2021 | Tobias Heer <tobias.heer@acp.de>
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
import json
import os
from datetime import date



# Global var assignment
#
path = '.'
cache = []
last_file = None



# cache_file()
#   Generates today's cache file with full path.
#   ARGS: None
#   RETURNS: cache_file - String with full path to file:
#            (e.g. /opt/usuvaleve/transaction/20211207.json)
#
def cache_file():
    file_name = date.today().strftime("%Y%m%d.json")
    cache_file = os.path.join(path, file_name)
    return cache_file



# rotate_cache()
#   Checks if the cache_file() has chanced and if cache flush is required.
#   ARGS: None
#   RETURNS: None
#
def rotate_cache():
    global cache, last_file
    if last_file is None:
        last_file = cache_file()
    if last_file != cache_file():
        cache = []
        last_file = cache_file()
    return



# write_cache()
#   Writes dict content as JSON to cache_file() location.
#   ARGS: data - List containg dicts of processed USU Valuemation endpoints
#   RETURNS: None
#
def write_cache(data):
    try:
        with open(cache_file(), 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception as e:
        raise Exception('Failed to write transcation data:' + str(e))
    return



# load_cache()
#   Loads JSON data from cache_file() as dict or returns an empty dict
#   ARGS: None
#   RETURNS: data - List containg dicts of processed USU Valuemation endpoints
#
def load_cache():
    try:
        with open(cache_file(), 'r') as f:
            data = json.load(f)
    except Exception as e:
        data = []
    return data



# append_cache()
#   Appends new dict of USU Valuemation endpoint to the cache and
#   writes it to the cache_file(). If cache has zero dict elements, try
#   loading cache_file()
#   ARGS: data - Dict of single USU Valuemation endpoint data
#   RETURNS: None
#
def append_cache(data):
    global cache
    if len(cache) < 1:
        cache = load_cache()
    cache.append(data)
    write_cache(cache)
    return



# is_done()
#   Checks if given endpoint data was already processed in this days cache
#   ARGS: endpoint - Dict of single USU Valuemation endpoint data
#   RETURNS: True - Endpoint was processed / found in transaction cache
#            False - Endpoint was not processed or more recent change detected.
#
def is_done(endpoint):
    global cache
    if len(cache) < 1:
        cache = load_cache()
    for cached_endpoint in cache:
        if endpoint['macadresse'] == cached_endpoint['macadresse'] \
        and endpoint['geaendert'] == cached_endpoint['geaendert']:
            return True
    return False
