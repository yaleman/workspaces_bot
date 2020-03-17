#!/usr/bin/python

""" terrible slack bot for interacting with AWS workspaces

needs to have workspaces access for its role, and expects to respond to slash commands from behind an API gateway

Required list of environment variables:

ADMINS (Comma-separated list of slack user_id's, easy to grab by running /workspacedebug)
ADMIN_CHANNEL (Slack channel ID)
DIRECTORYID (Current DirectoryId for interactions)
BUNDLEID (Current BundleId for provisioning)

Optional environment variables:
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/workspaces.html#WorkSpaces.Client.create_workspaces

AUTO_STOP_MINUTES (Default 180)
ROOTVOLUMESIZE (Default 80)
USERVOLUMESIZE (Default 50)
COMPUTETYPENAME ('VALUE'|'STANDARD'|'PERFORMANCE'|'POWER'|'GRAPHICS'|'POWERPRO'|'GRAPHICSPRO')
RUNNINGMODE ('AUTO_STOP'|'ALWAYS_ON')
"""

import os
import base64
import json
import boto3

ADMINS = os.environ.get('ADMINS', '').split(',')
ADMIN_CHANNEL = os.environ.get('ADMIN_CHANNEL', False)
DIRECTORYID = os.environ.get('DIRECTORYID')
BUNDLEID = os.environ.get('BUNDLEID')

AUTO_STOP_MINUTES = os.environ.get('AUTO_STOP_MINUTES', 180)
RUNNINGMODE = os.environ.get('RUNNINGMODE', 'AUTO_STOP')
ROOTVOLUMESIZE = os.environ.get('ROOTVOLUMESIZE', 80)
USERVOLUMESIZE = os.environ.get('USERVOLUMESIZE', 50)
COMPUTETYPENAME = os.environ.get('COMPUTETYPENAME', 'STANDARD')

ADMIN_COMMANDS = [
    'workspacecreate',
    'workspaceterminate',
    'workspacebundles',
    'workspacelist',
    ]
USER_COMMANDS = [
    'workspaceinfo',
    'workspacedebug',
    ]
VALID_COMMANDS = ADMIN_COMMANDS + USER_COMMANDS

ERROR_403 = {'statusCode' : 403, 'body' : "Nope"}

def return_message(message):
    """ returns a message object for slack """
    return {'statusCode': 200, 'body': message,}


def workspacecreate(client, username):
    """ creates a workspace for a given user """
    try:
        retval = client.create_workspaces(
            Workspaces=[
                {
                    'DirectoryId': DIRECTORYID,
                    'UserName': username,
                    'BundleId': BUNDLEID,
                    'UserVolumeEncryptionEnabled': False,
                    'RootVolumeEncryptionEnabled': False,
                    'WorkspaceProperties': {
                        'RunningMode': RUNNINGMODE,
                        'RunningModeAutoStopTimeoutInMinutes': AUTO_STOP_MINUTES,
                        'RootVolumeSizeGib': ROOTVOLUMESIZE,
                        'UserVolumeSizeGib': USERVOLUMESIZE,
                        'ComputeTypeName': COMPUTETYPENAME
                    }
                },
            ])
    except Exception as e: # pylint: disable=broad-except,invalid-name
        return {'ERROR' : e}
    text = ""
    for failedrequest in retval.get('FailedRequests'):
        text += f"Failed to create workspace for '{failedrequest['WorkspaceRequest']['UserName']}': {failedrequest['ErrorMessage']}\n" #pylint: disable=line-too-long
    for pendingrequest in retval.get('PendingRequests'):
        # {
        # "WorkspaceId": "ws-kvf38h1dw", "DirectoryId": "d-976716669e",
        # "UserName": "james.hodgkinson", "State": "PENDING",
        # "BundleId": "wsb-24k81ycr4",
        # "UserVolumeEncryptionEnabled": false, "RootVolumeEncryptionEnabled": false
        # }
        text += f"Workspace {pendingrequest.get('WorkspaceId')} for user {pendingrequest.get('UserName')} is in state {pendingrequest.get('State')}\n" #pylint: disable=line-too-long
    return text

def set_bundle(context, bundleid):
    """ sets the bundle on the lambda """
    # get the current config
    client = boto3.client('lambda')
    response = client.get_function_configuration(
        FunctionName=context.function_name,
        #Qualifier='string'
        )
    environment = response.get('Environment')
    environment['Variables']['BUNDLEID'] = bundleid

    response = client.update_function_configuration(
        FunctionName=context.function_name,
        Environment=environment,
    )
    if response.get('LastUpdateStatus') == 'Successful':
        return " <=- Set as new active bundle"
    else:
        return f"\n\nERROR Setting Bundle:\n{json.dumps(response, indent=2)}"

def workspacebundles(context, client, argument=None):
    """ lists all the bundles on the current directory, can set the new active one """
    if argument.strip():
        newbundle = argument.strip()
    else:
        newbundle = False
    text = "Available Bundles:\n```\n"
    try:
        bundles = client.describe_workspace_bundles()

        if bundles.get('Bundles'):
            for bundle in bundles.get('Bundles'):
                text += f" - ID: {bundle['BundleId']} Name: {bundle['Name']}"
                if bundle['BundleId'] == newbundle:
                    # set new bundle id
                    text += set_bundle(context, newbundle)
                elif not newbundle and (os.environ.get('BUNDLEID') and os.environ.get('BUNDLEID') == bundle['BundleId']):
                    text += f""" <=- Current active bundle for bot provisioning"""
                text += f"\n\t- Type: {bundle['ComputeType']['Name']}"
                text += f" Root Disk: {bundle['RootStorage']['Capacity']}Gb "
                text += f" User Disk: {bundle['UserStorage']['Capacity']}Gb\n"""
        else:
            text += "No bundles found"
    except Exception as e: # pylint: disable=broad-except,invalid-name
        text = f"Error: {e}"
    return text + '\n```'


def workspaceterminate(client, username):
    """ terminates a workspace for a given user """
    text = ""
    try:
        findworkspace = client.describe_workspaces(DirectoryId=DIRECTORYID, UserName=username,)
        # {"Workspaces":
        #   [
        #   {"WorkspaceId": "ws-kvf38h1dw", "DirectoryId": "d-976716669e",
        #    "UserName": "james.hodgkinson", "IpAddress": "10.136.11.138",
        # "State": "AVAILABLE", "BundleId": "wsb-24k81ycr4", "SubnetId": "subnet-0e25fa192e9ff4f8a",
        # "ComputerName": "EC2AMAZ-CCUQCD5",
        # "WorkspaceProperties":
        # {"RunningMode": "AUTO_STOP", "RunningModeAutoStopTimeoutInMinutes": 180,
        # "RootVolumeSizeGib": 80, "UserVolumeSizeGib": 50, "ComputeTypeName": "STANDARD"
        # },
        # "ModificationStates": []
        # }],
        # "ResponseMetadata": {
        #   "RequestId": "1071abab-96fb-4d6f-a3ea-8abfba3202eb",
        # "HTTPStatusCode": 200,
        # "HTTPHeaders": {
        #   "x-amzn-requestid": "1071abab-96fb-4d6f-a3ea-8abfba3202eb", "content-type": "application/x-amz-json-1.1",
        #   "content-length": "468", "date": "Mon, 16 Mar 2020 10:31:25 GMT"
        # },
        # "RetryAttempts": 0}}
        if findworkspace.get('Workspaces'):
            for workspace in findworkspace.get('Workspaces'):
                retval = client.terminate_workspaces(
                    TerminateWorkspaceRequests=[
                        {
                            'WorkspaceId': workspace['WorkspaceId']
                            },
                        ]
                    )
                text += f"Terminating {workspace.get('WorkspaceId')} for {username}... "
                if retval.get('FailedRequests'):
                    text += "Error: {json.dumps(retval.get('FailedRequests')}"
                text += "request successful. Workspace will be offline in approximately five minutes.\n"
        else:
            text = f"No workspaces found for username {username}"
    except Exception as e: # pylint: disable=broad-except,invalid-name
        return f"ERROR: {e}"

    return text

def workspaceinfo(client, username):
    """ shows information for a given user's workspace """
    text = ""
    try:
        findworkspace = client.describe_workspaces(DirectoryId=DIRECTORYID, UserName=username,)
        # {"Workspaces": [{"WorkspaceId": "ws-kvf38h1dw", "DirectoryId": "d-976716669e",
        # "UserName": "james.hodgkinson", "IpAddress": "10.136.11.138", "State": "AVAILABLE",
        # "BundleId": "wsb-24k81ycr4", "SubnetId": "subnet-0e25fa192e9ff4f8a",
        # "ComputerName": "EC2AMAZ-CCUQCD5",
        # "WorkspaceProperties":
        # {
        # "RunningMode": "AUTO_STOP", "RunningModeAutoStopTimeoutInMinutes": 180,
        # "RootVolumeSizeGib": 80, "UserVolumeSizeGib": 50, "ComputeTypeName": "STANDARD"
        # },
        # "ModificationStates": []}], "ResponseMetadata":
        # {
        # "RequestId": "1071abab-96fb-4d6f-a3ea-8abfba3202eb", "HTTPStatusCode": 200,
        # "HTTPHeaders":
        # {
        # "x-amzn-requestid": "1071abab-96fb-4d6f-a3ea-8abfba3202eb", "content-type": "application/x-amz-json-1.1",
        # "content-length": "468", "date": "Mon, 16 Mar 2020 10:31:25 GMT"
        # },
        # "RetryAttempts": 0}}
        if findworkspace.get('Workspaces'):
            for workspace in findworkspace.get('Workspaces'):
                text += f"Workspace {workspace.get('WorkspaceId')} for user {workspace.get('UserName')} in state {workspace.get('State')} (Bundle ID: {workspace.get('BundleId')}\n" #pylint: disable=line-too-long
        else:
            text = f"No workspaces found for username {username}"
    except Exception as e: # pylint: disable=broad-except,invalid-name
        return f"ERROR: {e}"

    return text

def workspacelist(client):
    """ lists the currently provisioned workspaces """
    text = ""
    states = {}
    try:
        findworkspace = client.describe_workspaces(DirectoryId=DIRECTORYID)
        # {"Workspaces":
        # [{"WorkspaceId": "ws-kvf38h1dw", "DirectoryId": "d-976716669e",
        # "UserName": "james.hodgkinson", "IpAddress": "10.136.11.138", "State": "AVAILABLE",
        # "BundleId": "wsb-24k81ycr4",
        # "SubnetId": "subnet-0e25fa192e9ff4f8a", "ComputerName": "EC2AMAZ-CCUQCD5",
        # "WorkspaceProperties":
        # {
        # "RunningMode": "AUTO_STOP", "RunningModeAutoStopTimeoutInMinutes": 180,
        # "RootVolumeSizeGib": 80, "UserVolumeSizeGib": 50, "ComputeTypeName": "STANDARD"
        # },
        # "ModificationStates": []}
        # ],
        # "ResponseMetadata":
        # {
        # "RequestId": "1071abab-96fb-4d6f-a3ea-8abfba3202eb", "HTTPStatusCode": 200,
        # "HTTPHeaders":
        # {
        # "x-amzn-requestid": "1071abab-96fb-4d6f-a3ea-8abfba3202eb", "content-type": "application/x-amz-json-1.1",
        # "content-length": "468", "date": "Mon, 16 Mar 2020 10:31:25 GMT"
        # },
        # "RetryAttempts": 0
        # }
        # }
        if findworkspace.get('Workspaces'):
            for workspace in findworkspace.get('Workspaces'):
                if workspace.get('State') not in states:
                    states[workspace.get('State')] = []
                states[workspace.get('State')].append(workspace)

            for state in states:
                text += f"Workspaces in state '{state}'\n```\n"
                for workspace in states[state]:
                    text += f"id: {workspace.get('WorkspaceId')} computer name: {workspace.get('ComputerName')} user: {workspace.get('UserName')} bundle: {workspace.get('BundleId')}\n" #pylint: disable=line-too-long
                text += '```\n'
        else:
            text = f"No workspaces found?"
    except Exception as e: # pylint: disable=broad-except,invalid-name
        return f"ERROR: {e}"
    return text


def validcommand(command):
    """ checks if the command is a valid command """
    if not command:
        return False
    elif command.startswith('/'):
        command = command[1:]
    elif command.startswith('%2F'):
        command = command[3:]
    if command in VALID_COMMANDS:
        return True
    return False

def workspacedebug(event, context, data):
    """ dumps, well, pretty much everything """
    #context_keys = [key for key in dir(context) if not key.startswith("_")]
    context_data = {
        'function_name' : context.function_name
#           "aws_request_id",
#   "client_context",
#   "function_name",
#   "function_version",
#   "get_remaining_time_in_millis",
#   "identity",
#   "invoked_function_arn",
#   "log",
#   "log_group_name",
#   "log_stream_name",
#   "memory_limit_in_mb"
    }

    text = f"""EVENT DATA
```
{json.dumps(event, indent=2)}
```

CONTEXT DATA

```
{json.dumps(context_data, indent=2)}
```

DECODED BODY DATA
```
{json.dumps(data, indent=2)}
```"""
    return text

def lambda_handler(event, context): # pylint: disable=unused-argument
    """ main function for this lambda """
    client = boto3.client(
        'workspaces',
        )

    if event.get('isBase64Encoded', False):
        data = base64.b64decode(event.get('body', False))
    else:
        data = event.get('body', False)
    # neeed to set the admin channel
    if not ADMIN_CHANNEL:
        return return_message("No ADMIN_CHANNEL defined in configuration, I can't work :slightly_frowning_face:")

    if not data:
        return ERROR_403

    elements = data.decode('utf-8').replace('%2F', '/').split("&")
    element_data = [element.split('=') for element in elements]

    data = {}
    for (key, value) in element_data:
        data[key] = value

    if not validcommand(data.get('command', False)): #pylint: disable=no-else-return
        return return_message(f"Invalid command: {data.get('command')}")
    else:
        command = data.get('command')[1:]
        command_user = data.get('user_id')

        # if you're an admin you can run it anywhere, if you're calling it from
        # the admin channel anyone can run admin commands
        if command in ADMIN_COMMANDS:
            if (data.get('channel_id') != ADMIN_CHANNEL) and (command_user not in ADMINS):
                return return_message(f"You need to be an admin to use {command}")

        argument = data.get('text')
        userlength = len(argument.split("+"))
        if userlength > 1:
            argument = argument.replace('+', ' ')
            return return_message(f"aws bot only works for one argument, was provided {userlength} in argument: '{argument}'") #pylint: disable=line-too-long

        if command == 'workspacecreate': #pylint: disable=no-else-return
            return return_message(workspacecreate(client, argument))
        elif command == 'workspacebundles':
            return return_message(workspacebundles(context, client, argument))
        elif command == 'workspaceterminate':
            return return_message(workspaceterminate(client, argument))
        elif command == 'workspaceinfo':
            return return_message(workspaceinfo(client, argument))
        elif command == 'workspacelist':
            return return_message(workspacelist(client))
        elif command == 'workspacedebug':
            return return_message(workspacedebug(event, context, data))
        else:
            return return_message("That command didn't do anything, sorry.")
