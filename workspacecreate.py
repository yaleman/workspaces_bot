""" implements the create-user workflow """

import json
from slack import WebClient
from slack.errors import SlackApiError

CREATEUSER_MODAL = {
    "type": "modal",
    "callback_id": "view_identifier",
    "title": {
        "type": "plain_text",
        "text": "My App",
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
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Let's create an AWS WorkSpace for your user!"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "input",
            "element": {
                "type": "plain_text_input"
            },
            "label": {
                "type": "plain_text",
                "text": "What's their username?",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": " "
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": ":honk: Click me to validate the username",
                    "emoji": True
                },
                "value": "create"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Where are they located?*"
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Click me"
                },
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Brisbane"
                        },
                        "value": "Brisbane"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Sydney"
                        },
                        "value": "Sydney"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Manila"
                        },
                        "value": "Manila"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Melbourne"
                        },
                        "value": "Melbourne"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Other"
                        },
                        "value": "Other"
                    }
                ]
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Who should I message when it's ready?*"
            },
            "accessory": {
                "type": "users_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select a user",
                    "emoji": True
                }
            }
        }
    ]
}

def workspacecreate(
        client,
        username,
        event,
        configuration,
    ):
    """ creates a workspace for a given user """
    if configuration.get('user_id') == 'UK6900NGK':
        try:
            slackclient = WebClient(token=configuration.get('slacktoken'))
            return slackclient.views_open(
                trigger_id=configuration.get('trigger_id'),
                view=CREATEUSER_MODAL
            )
        except SlackApiError as e:
            configuration['error'] = str(e)
            return json.dumps([event, configuration],indent=2)
        return ""
    else:
        try:
            retval = client.create_workspaces(
                Workspaces=[
                    {
                        'DirectoryId': configuration.get('directoryid'),
                        'UserName': username,
                        'BundleId': configuration.get('bundleid'),
                        'UserVolumeEncryptionEnabled': False,
                        'RootVolumeEncryptionEnabled': False,
                        'WorkspaceProperties': {
                            'RunningMode': configuration.get('runningmode'),
                            'RunningModeAutoStopTimeoutInMinutes': configuration.get('auto_stop_minutes'),
                            'RootVolumeSizeGib': configuration.get('rootvolumesize'),
                            'UserVolumeSizeGib': configuration.get('uservolumesize'),
                            'ComputeTypeName': configuration.get('computetypename'),
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
            # "WorkspaceId": "ws-aaabbbccc", "DirectoryId": "d-696996669e",
            # "UserName": "example.user", "State": "PENDING",
            # "BundleId": "wsb-aaabbbccc",
            # "UserVolumeEncryptionEnabled": false, "RootVolumeEncryptionEnabled": false
            # }
            text += f"Workspace {pendingrequest.get('WorkspaceId')} for user {pendingrequest.get('UserName')} is in state {pendingrequest.get('State')}\n" #pylint: disable=line-too-long
        return text
