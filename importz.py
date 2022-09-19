#
#  USUvalve - Import libraries
#  importz.py | Version: 14.12.2021 | Tobias Heer <tobias.heer@acp.de>
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
# <None>


# usu_to_cppm_dict
#   Creates ClearPass endpoint dict from USU dict for an API call.
#   ARGS: usu_endpoint: JSON USU Valumeation API endpoint dict
#         usu_cfg:  dict with yaml configuration content of column mapping
#   RETURNS: cppm_api_dict: dict required for an Clearpass API call:
#       mac_address (string, optional): MAC Address of the endpoint,
#       description (string, optional): Description of the endpoint,
#       status (string, optional) = ['Known' or 'Unknown' or 'Disabled']:
#               Status of the endpoint,
#       device_insight_tags (string, optional): List of Device Insight Tags,
#       attributes (object, optional): Additional attributes(key/value pairs)
#                   may be stored with the endpoint
#
def usu_to_cppm_dict(usu_endpoint, usu_cfg):
    cppm_api_dict = {}
    usu_cfg_mac_field = usu_cfg['field_is_mac']
    cppm_api_dict['mac_address'] = usu_endpoint[usu_cfg_mac_field]
    cppm_api_dict['attributes'] = {}
    try:
        for cppm_key in usu_cfg['cppm_default_values']:
            if cppm_key.lower() in ['description',
                                    'status',
                                    'device_insight_tags']:
                cppm_api_dict[cppm_key.lower()] = \
                usu_cfg['cppm_default_values'][cppm_key]
            else:
                cppm_api_dict['attributes'][cppm_key] = \
                usu_cfg['cppm_default_values'][cppm_key]
    except Exception as e:
        raise Exception('Failed to add defaults in ClearPass endpoint '+\
                        'dictionary for '+ usu_endpoint[usu_cfg_mac_field] +\
                        ' and key "' + str(cppm_key) + '"')
    try:
        for column in usu_cfg['field_mapping']:
            cppm_key = usu_cfg['field_mapping'][column]
            if cppm_key.lower() in ['description',
                                    'status',
                                    'device_insight_tags']:
                cppm_api_dict[cppm_key.lower()] = usu_endpoint[str(column)]
            else:
                if not str(column) in usu_endpoint:
                    continue
                cppm_api_dict['attributes'][cppm_key] = \
                usu_endpoint[str(column)].strip()
    except Exception as e:
        raise Exception('Failed mapping to Clearpass endpoint dictionay for '+ \
                        usu_endpoint[usu_cfg_mac_field] + ' and key "' + \
                        str(cppm_key) + '"')
    return cppm_api_dict
