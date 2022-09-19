#
#  USUvalve - Additional miscellaneous libraries
#  toolz.py | Version: 06.12.2021 | Tobias Heer <tobias.heer@acp.de>
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
import logging
import logging.handlers
import sys
import getopt
import yaml



# Global var assignment
#
full_sync = False
run_verbose = False
run_scope = None
dry_run = False
global_config = 'usuvalve.yml'
cfg = {}
logging.basicConfig(
   format='%(asctime)s %(levelname)-8s %(message)s',
   level=logging.INFO,
   datefmt='%Y-%m-%d %H:%M:%S')



# cmdline_output_usage
#   Output commandline usage if script called with -h or unknown arguments
#   ARGS: None
#   RETURNS: None
#
def cmdline_output_usage():
    print ('Usage: usuvalve.py [ -t ] [-f ] [-s <customer>] [-d] [-c </dir/to/configfile.yml>]')
    print ('    -t  Testing only. Do not trigger any changes on API')
    print ('    -f  Run full sync once - sync unconditionally')
    print ('    -s  Specify single dedicated scope / customer e.g. \'RPK\'')
    print ('    -d  Run in verbose mode with debug output')
    print ('    -c </dir/to/configfile.yml> Config file with optional path')
    print ('')
    return



# cmdline_read_opts
#   Output commandline usage if script called with -h or unknown arguments
#   ARGS: args, Arguments from system (sys.argv[1:])
#   RETURNS: None
#
def cmdline_read_opts(argv):
    try:
        opts, args = getopt.getopt(argv,"thfs:dc:")
    except getopt.GetoptError:
        cmdline_output_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--h', '-help', '--help'):
            cmdline_output_usage()
            sys.exit()
        elif opt in ('-t', '--t'):
            global dry_run
            logging.warning('Testing only mode activated')
            dry_run = True
        elif opt in ('-f', '--f'):
            global full_sync
            logging.warning('Single full sync mode activated')
            full_sync = True
        elif opt in ('-s', '--s'):
            global run_scope
            run_scope = arg
            logging.info('Scope specified to: ' + str(run_scope))
        elif opt in ('-d', '--d'):
            global run_verbose
            logging.info('Chatty verbose mode activated')
            run_verbose = True
        elif opt in ('-c', '--c'):
            global global_config
            global_config = arg
            logging.info('Config file specified: ' + str(global_config))
    return
cmdline_read_opts(sys.argv[1:])



# Library initialization stuff kicks in here
#
#
logger = logging.getLogger('usuvalve')
if run_verbose == True:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
try:
    handler = logging.handlers.SysLogHandler('/dev/log')
    formatter = logging.Formatter('%(name)s: [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
except Exception as e:
    logger.warning('Error creating syslog logging: ' + str(e))
if run_verbose == True:
    logger.setLevel(logging.DEBUG)



# load_yaml_config
#   Loads settings global YAML config file.
#   ARGS: None
#   RETURNS: None
#
def load_yaml_config():
    global cfg
    try:
        with open(global_config, 'r', encoding='utf8') as ymlfile:
            cfg = yaml.safe_load(ymlfile)
    except Exception as e:
        logger.critical('Error loading config file: ' + str(e))
        sys.exit(2)
    return
load_yaml_config()
