""" implements the create-user workflow """

import json
import boto3.session
from slack import WebClient
from slack.errors import SlackApiError

from .utilities import return_message

def dump_debug(event, configuration, payload):
    """ posts a slack message with a load of debug info """
    slackclient = WebClient(token=configuration.get('slacktoken'))
    slackclient.chat_postEphemeral(
        #channel=CONFIGURATION.get('jamestoken'),
        channel=configuration.get('adminchannel'),
        user=configuration['jamesid'],
        text=f"""
*Dump_debug:*

Event:
```
{json.dumps(event, indent=2)}
```

Payload:
```
{json.dumps(payload, indent=4)}
```
"""
    )
    return return_message("Dumping Debug")

ID_VIEW_CREATEUSER = 'view_createuser'
ID_BLOCK_USERNAME = "create_block_username"
ID_FIELD_USERNAME = "create_field_username"
ID_BLOCK_TEAM = "create_block_team"
ID_FIELD_TEAM = "create_field_team"
ID_BLOCK_LOCATION = "create_block_location"
ID_FIELD_LOCATION = "create_field_location"

ID_BLOCK_REGION = "create_block_region"
ID_FIELD_REGION = "create_field_region"

# ID_BLOCK_NOTIFY_PERSON = "create_block_notify"
# ID_FIELD_NOTIFY_PERSON = "create_field_notify"

def select_block(block_id, field_id, options, label):
    """ returns a select input block element """
    retval = {
        "block_id" : block_id,
        "type" : "input",
        "element" : {
            "action_id" : field_id,
            "type": "static_select",
            "placeholder": {
                "type": "plain_text",
                "emoji": True,
                "text": "Click me"
            },
            "options" : []
        },
        "label": {
            "type": "plain_text",
            "text": label,
            "emoji" : True,
        },
    }
    for option in options:
        retval['element']['options'].append({
            "text": {
                "type": "plain_text",
                "emoji": True,
                "text": option
            },
            "value": option
        })
    return retval


CREATEUSER_MODAL = {
    "type": "modal",
    "callback_id": ID_VIEW_CREATEUSER,
    "title": {
        "type": "plain_text",
        "text": "Create a Workspace",
        "emoji": True
    },
    "submit": {
        "type": "plain_text",
        "text": "Submit",
        "emoji": True
    },
    "close": {
        "type": "plain_text",
        "text": "Cancel",
        "emoji": True
    },
    "blocks": [
        # {
        #     "type": "section",
        #     "text": {
        #         "type": "mrkdwn",
        #         "text": "Let's create an AWS WorkSpace for your user!"
        #     }
        # },
        # {
        #     "type": "divider"
        # },

        {
            "block_id" : ID_BLOCK_USERNAME,
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id" : ID_FIELD_USERNAME,
                "placeholder": {
                    "type": "plain_text",
                    "text": "firstname.lastname",
                    "emoji" : True,
                }
            },
            "label": {
                "type": "plain_text",
                "text": "What's their domain username?",
                "emoji": True
            }
        },
        select_block(ID_BLOCK_REGION, ID_FIELD_REGION, ['ap-southeast-2', 'ap-southeast-1'], "Workspace Region"),
        select_block(ID_BLOCK_LOCATION, ID_FIELD_LOCATION, ['Brisbane', 'Sydney', 'Melbourne'], "User Location"),
        select_block(ID_BLOCK_TEAM, ID_FIELD_TEAM, ['WebCentral', 'ARQ Care', 'TPP Wholesale'], "Team"),
        # {
        #     "type": "input",
        #     "block_id": ID_BLOCK_NOTIFY_PERSON,
        #     "label": {
        #         "type": "plain_text",
        #         "text": "Notify this user when it is up",
        #         "emoji" : True,
        #     },
        #     "element": {
        #         "type": "users_select",
        #         "action_id": ID_FIELD_NOTIFY_PERSON,
        #         "placeholder": {
        #             "type": "plain_text",
        #             "text": "Select a user",
        #             "emoji" : True,
        #         }
        #     }
        # }
    ]
}

def do_create(configuration, username, region='ap-southeast-2', tags=[]): # pylint: disable=dangerous-default-value
    """ does the creation of a workspace """
    print(f"Starting session in {region}")
    session = boto3.session.Session(
        region_name=region,
        )
    bundlemap = {
        'ap-southeast-1' : configuration.get('bundleid_apse1'),
        'ap-southeast-2' : configuration.get('bundleid_apse2'),
    }
    directorymap = {
        'ap-southeast-1' : configuration.get('directoryid_apse1'),
        'ap-southeast-2' : configuration.get('directoryid_apse2'),
    }

    client = session.client('workspaces')
    return client.create_workspaces(
                Workspaces=[
                    {
                        'DirectoryId': directorymap[region],
                        'UserName': username,
                        'BundleId': bundlemap[region],
                        'UserVolumeEncryptionEnabled': False,
                        'RootVolumeEncryptionEnabled': False,
                        'WorkspaceProperties': {
                            'RunningMode': configuration.get('runningmode'),
                            'RunningModeAutoStopTimeoutInMinutes': configuration.get('auto_stop_minutes'),
                            'RootVolumeSizeGib': configuration.get('rootvolumesize'),
                            'UserVolumeSizeGib': configuration.get('uservolumesize'),
                            'ComputeTypeName': configuration.get('computetypename'),
                        },
                        'Tags' : tags,
                    },
                ])


def create(
        username,
        configuration,
    ):
    """ creates a workspace for a given user """
    print("workspacecreate() start")
    # if configuration.get('user_id') == configuration.get('jamesid'):
    try:
        #print("take the username, find the right block and set the initial value")
        for index, block in enumerate(CREATEUSER_MODAL['blocks']):
            #if block.get('type') == 'input':
            if block.get('block_id') == ID_BLOCK_USERNAME:
                CREATEUSER_MODAL['blocks'][index]['element']['initial_value'] = username
                print("Updated create_field_username field")
                # remove the placeholder if we set username
        print("pop a modal for the user")
        slackclient = WebClient(token=configuration.get('slacktoken'))
        print(f"trigger ID: {configuration.get('trigger_id')}")
        slackclient.views_open(
            trigger_id=configuration.get('trigger_id'),
            view=CREATEUSER_MODAL
        )
    except SlackApiError as ERROR: # pylint: disable=invalid-name
        print(f"SlackApiError: {ERROR}")
        configuration['error'] = str(ERROR)

        slackclient = WebClient(token=configuration.get('slacktoken'))
        print("Messaging user to advise...")
        response = slackclient.chat_postEphemeral(
            channel=configuration.get('channel_id'),
            user=configuration.get('user_id'),
            text="Failed to pop up the 'create user' dialogue, can you try that again?",
        )
        print(response)
        return False
    return return_message("Hi James. Did the modal pop?")
    # else:
    #     try:
    #         retval = do_create(configuration, username, )
    #     except Exception as e: # pylint: disable=broad-except,invalid-name
    #         return {'ERROR' : e}
    #     text = ""
    #     for failedrequest in retval.get('FailedRequests'):
    #         text += f"Failed to create workspace for '{failedrequest['WorkspaceRequest']['UserName']}': {failedrequest['ErrorMessage']}\n" #pylint: disable=line-too-long
    #     for pendingrequest in retval.get('PendingRequests'):
    #         text += f"Workspace {pendingrequest.get('WorkspaceId')} for user {pendingrequest.get('UserName')} is in state {pendingrequest.get('State')}\n" #pylint: disable=line-too-long
    #     return text

def handle_view_submission(event, payload, configuration): # pylint: disable=unused-argument
    """ handles when users hit submit from the create workspace view """
    print("Received user submssion form")
    # create user view submission
    #retval = "You probably shouldn't see this?"
    if payload['view'].get('state', {}).get('values'):
        #VIEWSTATE = payload['view']['state']
        #if VIEWSTATE.get('values'):
        STATE_VALUES = payload['view']['state'].get("values") # pylint: disable=invalid-name
        print(f"STATE Values: {STATE_VALUES}")
        endstate = {}
        for value in STATE_VALUES:
            if value == ID_BLOCK_USERNAME:
                # here's the username the user set
                endstate['username'] = STATE_VALUES[value][ID_FIELD_USERNAME].get('value').replace('+', ' ')
            elif value == ID_BLOCK_LOCATION:
                endstate['location'] = STATE_VALUES[ID_BLOCK_LOCATION][ID_FIELD_LOCATION]['selected_option'].get('value').replace('+', ' ') #pylint: disable=line-too-long
            elif value == ID_BLOCK_TEAM:
                endstate['team'] = STATE_VALUES[ID_BLOCK_TEAM][ID_FIELD_TEAM]['selected_option'].get('value').replace('+', ' ') #pylint: disable=line-too-long
            # elif value == ID_BLOCK_NOTIFY_PERSON:
                # endstate['notify'] = STATE_VALUES[ID_BLOCK_NOTIFY_PERSON][ID_FIELD_NOTIFY_PERSON]['selected_user']
            elif value == ID_BLOCK_REGION:
                endstate['region'] = STATE_VALUES[ID_BLOCK_REGION][ID_FIELD_REGION]['selected_option'].get('value').replace('+', ' ') #pylint: disable=line-too-long
            else:
                # uh, what?
                pass
        print(f"User submitted create form: {json.dumps(endstate, indent=2)}") # pylint: disable=line-too-long
        print("Doing do_create() in another call")
        tags = [
            {
                'Key' : 'Location',
                'Value' : endstate.get('location', "Unknown Location"),
            },
            {
                'Key' : 'Team',
                'Value' : endstate.get('team', 'Unknown Team'),
            },
        ]

        # call the lambda asynchronously so we can get back to the user in time...
        lambdaclient = boto3.client('lambda')
        lambdaclient.invoke(
            FunctionName='workspacebot',
            InvocationType='Event',
            Payload=json.dumps({
                'fromotherlambda' : True,
                'action' : 'workspacecreate_doit',
                'configuration' : configuration,
                'username' : endstate['username'],
                'region' : endstate['region'],
                'tags' : tags
            }),
        )



    else:
        print("No values in payload['view'].get('state', {}).get('values')")

    RETURN_UPDATE_MODAL = { #pylint: disable=invalid-name
        'statusCode' : 200,
        'headers' : {
            'Content-Type' : 'application/json',
            },
        "isBase64Encoded" : False,
        'body' : json.dumps({
            "response_action": "update",
            "view": {
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Thanks!"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Your create task has been submitted, I'll message you when there's an update."
                        }
                    }
                ]
            }
        }),
    }


    RETURN_CLOSE_MODAL = { #pylint: disable=invalid-name,unused-variable
        'statusCode' : 200,
        "headers": {
            "Content-Type": "application/json",
        },
        'body' : json.dumps({"response_action": "clear"}),
        "isBase64Encoded" : False
    }
    print("Updating the modal...")
    #print(json.dumps(RETURN_UPDATE_MODAL, indent=2))
    return RETURN_UPDATE_MODAL

def do_creation(event):
    """ final step in the "create workspace" interface, actually creates the workspace for the user """
    region = event.get('region')
    retval = do_create(
        configuration=event.get('configuration'),
        username=event.get('username'),
        region=region,
        tags=event.get('tags'),
    )
    print(retval)
    slackclient = WebClient(token=event.get('configuration').get('slacktoken'))
    messages_to_send = []
    # message them about failed requests
    if retval.get('FailedRequests'):
        for failedrequest in retval.get('FailedRequests'):
            username = failedrequest.get('WorkspaceRequest').get('UserName')
            failmessage = failedrequest.get('ErrorMessage')
            messages_to_send.append(f"The request to create a WorkSpace for '{username}' in region: {region} failed: {failmessage}") # pylint: disable=line-too-long
    # message the user about successful requests
    if retval.get('PendingRequests'):
        for pendingrequest in retval.get('PendingRequests'):
            messages_to_send.append(f"Workspace {pendingrequest.get('WorkspaceId')} for user {pendingrequest.get('UserName')} is in state {pendingrequest.get('State')}\n") # pylint: disable=line-too-long
    # send the messages
    for message in messages_to_send:
        slackclient.chat_postEphemeral(
            channel=event.get('configuration').get('channel_id'),
            user=event.get('configuration').get('user_id'),
            text=message,
        )
