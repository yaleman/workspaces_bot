#!/usr/bin/python

""" terrible slack bot for interacting with AWS workspaces

needs to have workspaces access for its role, and expects to respond to slash commands from behind an API gateway

Required list of environment variables:

ADMINS (Comma-separated list of slack user_id's, easy to grab by running /workspacedebug)
ADMIN_CHANNEL (Slack channel ID)
DIRECTORYID (Current DirectoryId for interactions)
BUNDLEID (Current BundleId for provisioning)

BUNDLEID_APSE1 (singapore bundle ID)
BUNDLEID_APSE2 (sydney)
SLACKTOKEN (Slack OAuth Token - https://api.slack.com/apps/<appid>/oauth)

Optional environment variables:
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/workspaces.html#WorkSpaces.Client.create_workspaces

AUTO_STOP_MINUTES (Default 180)
ROOTVOLUMESIZE (Default 80)
USERVOLUMESIZE (Default 50)
COMPUTETYPENAME ('VALUE'|'STANDARD'|'PERFORMANCE'|'POWER'|'GRAPHICS'|'POWERPRO'|'GRAPHICSPRO')
RUNNINGMODE ('AUTO_STOP'|'ALWAYS_ON')
"""

import base64
import json
import urllib.parse

from slack import WebClient
import boto3


from workspaceconfig import * # pylint: disable=wildcard-import,unused-wildcard-import
from workspaces.bundles import workspacebundles
import workspaces.create
from workspaces.debug import workspacedebug
from workspaces.info import workspaceinfo
from workspaces.list import workspacelist
from workspaces.terminate import workspaceterminate
from workspaces.utilities import return_message, validcommand

ERROR_403 = {'statusCode' : 403, 'body' : "Nope"}


# Event:
# ```
# {json.dumps(event, indent=2)}
# ```

def dump_debug(event, payload, message_source="Fallthrough"): # pylint: disable=unused-argument
    """ posts a slack message with a load of debug info """
    slackclient = WebClient(token=CONFIGURATION.get('slacktoken'))
    slackclient.chat_postEphemeral(
        #channel=CONFIGURATION.get('jamestoken'),
        channel=CONFIGURATION.get('adminchannel'),
        user=CONFIGURATION['jamesid'],
        text=f"""
*{message_source}:*


Payload:
```
{json.dumps(payload, indent=4)}
```
"""
    )
    return return_message("Dumping Debug")


def lambda_handler(event, context): # pylint: disable=unused-argument
    """ main function for this lambda """
    #print("********** EVENT **********")
    #print(json.dumps(event, indent=2))
    client = boto3.client(
        'workspaces',
        )


    if event.get('isBase64Encoded', False):
        data = base64.b64decode(event.get('body', False))
    else:
        data = event.get('body', False)

    if event.get('fromotherlambda'):
        print("Running from another Lambda call")
        print("**************** EVENT DATA FOR CROSS_LAMBDA EXECUTION ***********************")
        print(json.dumps(event))
        if event.get('action') == 'workspacecreate':
            workspaces.create.create(event.get('username'), event.get('configuration'))
        elif event.get('action') == 'workspacecreate_doit':
            #workspaces.create.create(event.get('username'), event.get('configuration'))
            print("Doing workspacecreate_doit")
            workspaces.create.do_creation(event)
        return return_message("well done")

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

    if data.get('payload'):
        payload = json.loads(urllib.parse.unquote(data.get('payload')))
        #print("********** PAYLOAD **********")
        #print(json.dumps(payload, indent=2))
        # this isn't a slash command, it's probably something else
        if payload.get('type') == 'block_actions':          # you've taken an action in a view
            # search through the actions
            for action in payload.get('actions'):
                if action.get('action_id') == 'create_from_modal':
                    pass
                    #return workspaces.create.create_from_modal(client, payload=payload, configuration=CONFIGURATION)
            # someone clicked a thing in a block
            print("Made it to unhandled block action")
            print("Actions:")
            print(json.dumps(payload.get('actions'), indent=2))
            return dump_debug(event, payload, 'made it to block actions')

        elif payload.get('type') == "view_submission":      # you're hitting submit on a view
            if payload.get('view'):
                if payload['view'].get('callback_id') == workspaces.create.ID_VIEW_CREATEUSER:
                    return workspaces.create.handle_view_submission(event, payload, CONFIGURATION)
                else:
                    print(f"Got a submission of type '{payload['view'].get('callback_id')}' - cannot handle that.'")
        else:
            #print("********** PAYLOAD **********")
            #print(json.dumps(payload, indent=2))
            print(f"Got a payload type '{payload['type']}' - unhandled")
        return return_message("payload sent, wtf?")

    elif validcommand(data.get('command', False), VALID_COMMANDS): #pylint: disable=no-else-return
        command = data.get('command')[1:]
        command_user = data.get('user_id')
        CONFIGURATION['user_id'] = command_user
        CONFIGURATION['trigger_id'] = data.get('trigger_id')
        CONFIGURATION['channel_id'] = data.get('channel_id')
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
        elif command == 'workspacecreate': #pylint: disable=no-else-return
            #response = return_message(workspaces.create.create(argument, event=event, configuration=CONFIGURATION)) # pylint: disable=line-too-long
            #if response:
            #    message = return_message(response)
            #else:

            print("trying to run myself asynchronously")
            # trigger myself again in another way
            lambdaclient = boto3.client('lambda')
            response = lambdaclient.invoke(
                FunctionName='workspacebot',
                InvocationType='Event',
                Payload=json.dumps({
                    'username' : argument,
                    'configuration' : CONFIGURATION,
                    'fromotherlambda' : True,
                    'action' : 'workspacecreate',
                }),
            )
            if response.get('StatusCode') == 202:
                return return_message("Working on it...")
            else:
                return return_message(f"Failed to call workspaces.create(): {str(response)}")

        elif command == 'workspacebundles':
            return return_message(workspacebundles(context, configuration=CONFIGURATION, argument=argument))
        elif command == 'workspaceterminate':
            return return_message(workspaceterminate(client, configuration=CONFIGURATION, username=argument))
        elif command == 'workspaceinfo':
            return return_message(workspaceinfo(client, configuration=CONFIGURATION, username=argument))
        elif command == 'workspacelist':
            return return_message(workspacelist(configuration=CONFIGURATION, argument_object=argument))
        elif command == 'workspacedebug':
            return return_message(workspacedebug(event, context, data))
        else:
            return return_message("That command didn't do anything, sorry.")
    else:
        return dump_debug(event, payload)
