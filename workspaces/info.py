""" implements workspaceinfo """

from boto3 import client as boto3client
from .utilities import get_bundle_name

def workspaceinfo(configuration, username):
    """ shows information for a given user's workspace """
    text = ""
    client = boto3client('workspaces')
    try:
        findworkspace = client.describe_workspaces(DirectoryId=configuration.get('directoryid'), UserName=username,)
        # {"Workspaces": [{"WorkspaceId": "ws-aaabbbccc", "DirectoryId": "d-696996669e",
        # "UserName": "example.user", "IpAddress": "10.0.11.138", "State": "AVAILABLE",
        # "BundleId": "wsb-aaabbbccc", "SubnetId": "wsb-aaaabbbbccccdddd",
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
                wsid = workspace.get('WorkspaceId')
                user = workspace.get('UserName')
                state = workspace.get('State')
                bundlename = get_bundle_name(workspace.get('BundleId'))
                text += f"Workspace {wsid} for user {user} in state {state} (Bundle: {bundlename})\n" #pylint: disable=line-too-long
        else:
            text = f"No workspaces found for username {username}"
    except Exception as e: # pylint: disable=broad-except,invalid-name
        return f"ERROR: {e}"

    return text
