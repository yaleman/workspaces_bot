""" utilities functions """

import json
import boto3
from boto3.session import Session

def call_lambda(payload: dict):
    """ calls workspacebot for chained events """
    if 'action' not in payload:
        raise ValueError(f"need to feed an action in the payload, payload was: {json.dumps(payload, indent=2)}")
    if 'configuration' not in payload:
        raise ValueError(f"need to feed configuration in the payload, payload was: {json.dumps(payload, indent=2)}")
    payload['fromotherlambda'] = True
    lambdaclient = boto3.client('lambda')
    lambdaclient.invoke(
        FunctionName='workspacebot',
        InvocationType='Event',
        Payload=json.dumps(payload),
    )

def dump_debug(event, configuration, payload):
    """ posts a slack message with a load of debug info """
#     slackclient = WebClient(token=configuration.get('slacktoken'))
#     slackclient.chat_postEphemeral(
#         #channel=CONFIGURATION.get('jamestoken'),
#         channel=configuration.get('adminchannels'),
#         user=configuration['jamesid'],
    print(f"""
*Dump_debug:*

Event:
{json.dumps(event, indent=2)}

Configuration:
{json.dumps(configuration, indent=2)}

Payload:
{json.dumps(payload, indent=4)}
""")
    return return_message("Dumping Debug")

def get_bundle_name(bundleid):
    """ returns the name of a given bundle id """
    bundles = get_bundles()
    if not bundles:
        return "Error getting bundle name"
    for bundle in bundles:
        if bundleid == bundle.get('BundleId'):
            return bundle.get('Name')
    return "Unknown bundle name"

def get_bundles(region='ap-southeast-2'):
    """ returns a dict with information about the available bundles """
    session = Session(
        region_name=region,
    )
    client = session.client('workspaces')
    try:
        response = client.describe_workspace_bundles()
        return response.get('Bundles')
    except Exception: #pylint: disable=broad-except
        return False



def get_workspaces(configuration, token=None, region='ap-southeast-2'):
    """ does the describe workspaces call and works around paging """
    session = Session(
        region_name=region
    )
    client = session.client('workspaces')
    if token:
        response = client.describe_workspaces(
            DirectoryId=configuration.get('directoryid'),
            NextToken=token,
        )
    else:
        response = client.describe_workspaces(
            DirectoryId=configuration.get('directoryid'),
        )

    if not response.get('Workspaces'):
        retval = False
    else:
        retval = response.get('Workspaces')
        if response.get('NextToken'):
            # there are more things to ask for
            retval.extend(
                get_workspaces(
                    configuration=configuration,
                    region=region,
                    token=response.get('NextToken'),
                    ),
                )
    return retval


def return_message(message):
    """ returns a message object for slack """
    return {'statusCode': 200, 'body': message,}


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
        retval = " <=- Set as new active bundle"
    else:
        retval = f"\n\nERROR Setting Bundle:\n{json.dumps(response, indent=2)}"
    return retval

def validcommand(command, valid_commands):
    """ checks if the command is a valid command """
    if not command:
        return False
    # clean up weird slack formatting things
    if command.startswith('/'):
        command = command[1:]
    if command.startswith('%2F'):
        command = command[3:]
    if command in valid_commands:
        return True
    return False
