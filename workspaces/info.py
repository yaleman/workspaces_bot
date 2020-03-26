""" implements workspaceinfo """

from boto3.session import Session

from slack import WebClient
from .utilities import get_bundle_name

def multiregion(event):
    """ shows information for a given user's workspace

    need to pass username in the event
    """
    print("workspaces.info.multiregion() starting")

    username = event.get('username')
    configuration = event.get('configuration')

    user_workspaces = []
    for region in event.get('configuration').get('regions'):
        # need to get the directoryid for each region
        directoryid = configuration.get('directorymap', {}).get(region)
        if not directoryid:
            print(f"Couldn't find directoryid for region '{region}' in workspaces.info.multiregion()")
            continue

        try:
            session = Session(
                region_name=region
            )
        except Exception as ERROR: # pylint: disable=broad-except,invalid-name
            error_message = f"Failed to instantiate session with region {region}: {ERROR}"
            print(error_message)
            return False
        try:
            client = session.client('workspaces')
            findworkspace = client.describe_workspaces(
                DirectoryId=directoryid,
                UserName=username,
            )
            if findworkspace.get('Workspaces'):
                for workspace in findworkspace.get('Workspaces'):
                    wsid = workspace.get('WorkspaceId')
                    state = workspace.get('State')
                    bundlename = get_bundle_name(workspace.get('BundleId'))
                    user_workspaces.append(f"{wsid} in state {state} (Region: {region} Bundle: {bundlename})") #pylint: disable=line-too-long

        except Exception as e: # pylint: disable=broad-except,invalid-name
            error_message = f"ERROR: {e}"
            print(error_message)
            return False

    # message the user with the results
    slackclient = WebClient(token=configuration.get('slacktoken'))
    print("Messaging user to advise...")

    if not user_workspaces:
        response = slackclient.chat_postEphemeral(
            channel=configuration.get('channel_id'),
            user=configuration.get('user_id'),
            text=f"No workspaces found for username {username}"
        )
    else:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Workspace information for user {username}"
                }
            },
        ]
        for workspace in user_workspaces:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• {workspace}"
                }
                })
        response = slackclient.chat_postEphemeral(
            channel=configuration.get('channel_id'),
            user=configuration.get('user_id'),
            #text=f"Results for workspaceinfo {username}:\n{text}",
            blocks=blocks,
        )
    print(response)
