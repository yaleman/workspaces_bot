""" workspaces utility functions """


from .utilities import get_bundles, get_workspaces

def workspacelist(configuration, argument_object, region='ap-southeast-1'):
    """ lists the currently provisioned workspaces """
    bundle_data = {}
    for bundle in get_bundles():
        bundle_data[bundle.get('BundleId')] = bundle
    text = ""
    states = {}
    workspace_field = {
        'WorkspaceId' : {
            'default' : len("Workspace ID")+2,
            'current' : 0,
            'text' : "Workspace ID",
            },
        'UserName' : {
            'default' : len("Username")+2,
            'current' : 0,
            'text' : "Username",
        },
        'ComputerName' : {
            'default' : len("Hostname")+2,
            'current' : 0,
            'text' : 'Hostname',
            },
    }
    try:
        print("Getting workspaces")
        workspaces = get_workspaces(configuration=configuration, region=region)
        print("done!")
        #if findworkspace.get('Workspaces'):
        if workspaces:
            # find the set of states
            print(f"found {len(workspaces)} workspaces")
            for workspace in workspaces[5:]:
                if workspace.get('State') not in states:
                    states[workspace.get('State')] = []
                states[workspace.get('State')].append(workspace)
            # iterate through states
            for state in states:
                if argument_object.strip() != '' and argument_object.lower() != state.lower():
                    continue

                text += f"{state} ({len(states[state])})\n```"
                # calculate field layouts
                for field in workspace_field:
                    lengths = [workspace_field[field]['default']] + [len(w.get(field, 'n/a')) for w in states[state]]
                    workspace_field[field]['current'] = max(lengths)
                    fstring = '{:<'+str(max(lengths))+'}\t'
                    text += fstring.format(workspace_field[field]['text'])
                text += "Bundle Name\n"
                # display code
                for workspace in states[state]:
                    workspacebundle = bundle_data.get(workspace.get('BundleId'))
                    bundlename = 'not pulled' #workspacebundle.get("Name")
                    for field in workspace_field:
                        fstring = '{:<'+str(workspace_field[field]['current'])+'}\t'
                        if workspace.get(field):
                            text += fstring.format(workspace.get(field))
                        else:
                            text += fstring.format("n/a")
                    if workspace.get('BundleId'):
                        text += f"{bundlename}\n"
                    else:
                        text += "n/a\n"
                text += "```\n"
        else:
            text = f"No workspaces found?"
    except Exception as e: # pylint: disable=broad-except,invalid-name
        return f"ERROR: {e} - {e.args}"
    return text
