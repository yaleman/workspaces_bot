""" terminate things """

import boto3.session
from loguru import logger
from slack import WebClient


def workspacerestart(event: dict):
    """ restarts a workspace """

    configuration = event.get('configuration', {})
    workspaceid = event.get('workspaceid', {})

    text = ""
    for region in configuration.get("directorymap"):
        session = boto3.session.Session(region_name=region)
        client = session.client("workspaces")
        try:
            findworkspace = client.describe_workspaces(WorkspaceIds=[workspaceid])
        except Exception as client_exception: # pylint: disable=broad-except
            logger.error(
                f"Exception raised while describing workspace: {client_exception}"
            )
            continue

        if findworkspace.get("Workspaces"):
            logger.debug("Found valid workspace, doing restart")
            logger.debug(findworkspace.get("Workspaces"))
            # example:
            # [{'WorkspaceId': 'ws-xw49vm7pm', 'DirectoryId': 'd-9667124436',
            # 'UserName': 'james.hodgkinson',
            # 'IpAddress': '10.137.10.76', 'State': 'STOPPED', 'BundleId': 'wsb-2mm9q6rvm',
            # 'SubnetId': 'subnet-0cd0c960cacab9e7e',
            # 'ComputerName': 'EC2AMAZ-3SE72K6', 'WorkspaceProperties':
            # {'RunningMode':
            # 'AUTO_STOP', 'RunningModeAutoStopTimeoutInMinutes': 60,
            # 'RootVolumeSizeGib': 80, 'UserVolumeSizeGib': 50, 'ComputeTypeName': 'STANDARD'},
            # 'ModificationStates': []}]
            workspaceinfo = findworkspace.get("Workspaces")[0]
            if workspaceinfo.get('State') == "STOPPED":
                logger.warning("Can't restart a workspace in State=STOPPED")
                text = "This workspace is stopped, can't restart it"
                continue

            try:
                response = client.reboot_workspaces(
                    RebootWorkspaceRequests=[{"WorkspaceId": workspaceid}]
                )
                logger.debug(f"Response from reboot request: {response}")
                if response.get('FailedRequests'):
                    text = f"Failed request: {response.get('FailedRequests')}"
                elif response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                    text = f"Success! Restarting {workspaceid} - this typically takes 15 minutes."

            except Exception as reboot_error: # pylint: disable=broad-except
                text = f"Exception raised while attempting to reboot {workspaceid} in {region}: {reboot_error}"
                logger.error(text)

    # message the user with the results
    slackclient = WebClient(token=configuration.get('slacktoken'))
    logger.debug("Messaging user to advise...")

    slackclient.chat_postEphemeral(
        channel=configuration.get('channel_id'),
        user=configuration.get('user_id'),
        text=text
    )
    return True
