""" terminate things """


def workspaceterminate(client, configuration, username):
    """ terminates a workspace for a given user """
    text = ""
    try:
        findworkspace = client.describe_workspaces(DirectoryId=configuration.get('directoryid'), UserName=username,)
        # {"Workspaces":
        #   [
        #   {"WorkspaceId": "ws-aaabbbccc", "DirectoryId": "d-696996669e",
        #    "UserName": "example.user", "IpAddress": "10.0.11.138",
        # "State": "AVAILABLE", "BundleId": "wsb-aaabbbccc", "SubnetId": "wsb-aaaabbbbccccdddd",
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
