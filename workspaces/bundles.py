""" bundles stuff """

from .utilities import get_bundles, set_bundle

def workspacebundles(context, configuration=None, argument=None):
    """ lists all the bundles on the current directory, can set the new active one """
    if argument.strip():
        newbundle = argument.strip()
    else:
        newbundle = False
    text = "Available Bundles:\n```\n"
    try:
        #bundles = client.describe_workspace_bundles()
        bundles = get_bundles() #client.describe_workspace_bundles()

        #if bundles.get('Bundles'):
        #    for bundle in bundles.get('Bundles'):
        if bundles:
            for bundle in bundles:
                text += f" - ID: {bundle['BundleId']} Name: {bundle['Name']}"
                if bundle['BundleId'] == newbundle:
                    # set new bundle id
                    text += set_bundle(context, newbundle)
                elif not newbundle and (configuration.get('bundleid') and configuration.get('bundleid') == bundle['BundleId']): # pylint: disable=line-too-long
                    text += f""" <=- Current active bundle for bot provisioning"""
                text += f"\n\t- Type: {bundle['ComputeType']['Name']}"
                text += f" Root Disk: {bundle['RootStorage']['Capacity']}Gb "
                text += f" User Disk: {bundle['UserStorage']['Capacity']}Gb\n"""
        else:
            text += "No bundles found"
    except Exception as e: # pylint: disable=broad-except,invalid-name
        text = f"Error: {e}"
    return text + '\n```'
