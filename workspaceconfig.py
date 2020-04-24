""" configuration stuff """
import os

ADMINS = os.environ.get('ADMINS', '').split(',')
ADMIN_CHANNELS = os.environ.get('ADMIN_CHANNELS', "").split(',')
DIRECTORYID = os.environ.get('DIRECTORYID')
BUNDLEID = os.environ.get('BUNDLEID')

AUTO_STOP_MINUTES = os.environ.get('AUTO_STOP_MINUTES', 180)
RUNNINGMODE = os.environ.get('RUNNINGMODE', 'AUTO_STOP')
ROOTVOLUMESIZE = os.environ.get('ROOTVOLUMESIZE', 80)
USERVOLUMESIZE = os.environ.get('USERVOLUMESIZE', 50)
COMPUTETYPENAME = os.environ.get('COMPUTETYPENAME', 'STANDARD')
SLACKTOKEN = os.environ.get('SLACKTOKEN')

CONFIGURATION = {
    'directoryid' : DIRECTORYID,
    'directoryid_apse1' : os.environ.get('DIRECTORYID_APSE1'),
    'directoryid_apse2' : os.environ.get('DIRECTORYID_APSE2'),
    'directorymap' : {
        'ap-southeast-1' : os.environ.get('DIRECTORYID_APSE1'),
        'ap-southeast-2' : os.environ.get('DIRECTORYID_APSE2'),
    },
    'bundleid' : BUNDLEID,
    'bundleid_apse1' : os.environ.get('BUNDLEID_APSE1'),
    'bundleid_apse2' : os.environ.get('BUNDLEID_APSE2'),
    'auto_stop_minutes' : AUTO_STOP_MINUTES,

    'regions' : os.environ.get('REGIONS', "").split(","),
    'runningmode' : RUNNINGMODE,
    'rootvolumesize' : ROOTVOLUMESIZE,
    'uservolumesize' : USERVOLUMESIZE,
    'computetypename' : COMPUTETYPENAME,
    'slacktoken' : SLACKTOKEN,
    'jamesid' : 'UK6900NGK', #used for troubleshooting
    'adminchannel' : ADMIN_CHANNELS, # "G0100BR9Y20",
}

ADMIN_COMMANDS = [
    'workspacecreate',
    'workspaceterminate',
    'workspacebundles',
    'workspacelist',
    'workspacerestart',
    ]
USER_COMMANDS = [
    'workspaceinfo',
    'workspacedebug',
    ]
VALID_COMMANDS = ADMIN_COMMANDS + USER_COMMANDS
