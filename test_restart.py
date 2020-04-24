""" tests the restart functionality """
from workspaceconfig import CONFIGURATION

from loguru import logger # pylint: disable=wrong-import-order

from workspaces.restart import workspacerestart
import workspaces.utilities

# def test_workspace_restart():
#     """ tests the restart functionality """
#     found_workspaces = workspaces.utilities.get_workspaces_for_user(configuration=CONFIGURATION, username='james.hodgkinson')
#     logger.debug(found_workspaces)
#     # example:
#     # [{'WorkspaceId': 'ws-xw49vm7pm', 'DirectoryId': 'd-9667124436', 'UserName': 'james.hodgkinson', 'IpAddress': '10.137.10.76', 'State': 'STOPPED', 'BundleId': 'wsb-2mm9q6rvm', 'SubnetId': 'subnet-0cd0c960cacab9e7e', 'ComputerName': 'EC2AMAZ-3SE72K6', 'WorkspaceProperties': {'RunningMode': 'AUTO_STOP', 'RunningModeAutoStopTimeoutInMinutes': 60, 'RootVolumeSizeGib': 80, 'UserVolumeSizeGib': 50, 'ComputeTypeName': 'STANDARD'}, 'ModificationStates': [], 'region': 'ap-southeast-1'}]
#     workspace_to_restart = 'ws-xw49vm7pm'
#     logger.info(f"Attempting to restart {workspace_to_restart}")
#     response = workspacerestart({'configuration' : CONFIGURATION, 'workspaceid' : workspace_to_restart})
#     logger.info(f"Response from command: {response}")

# if __name__ == '__main__':
#     test_workspace_restart()