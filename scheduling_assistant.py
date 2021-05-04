from typing import Dict, List
from datetime import datetime
from secretsmanager import SecretsManager

import os
import math
import json 
import gspread 
import todoist 
from toggl.TogglPy import Toggl

from logic import calc_future_alloc


sm = SecretsManager(region='eu-west-2')


TOGGL = Toggl()
TOGGL.setAPIKey(sm.get_secret("TogglAPIToken"))
TOGGL_WORKSPACE_ID = TOGGL.getWorkspace(name=sm.get_secret("TogglWorkspaceName"))['id']


def run() -> None:
    print("Reading input configuration spreadsheet...")
    target_alloc_scores, since = get_input_config()

    print("Fetching current time allocation...")
    current_time_spent_s = get_current_time_spent_s(since)

    print("Calculating required future time allocation...")
    future_alloc = calc_future_alloc(current_time_spent_s, target_alloc_scores)
    
    target_activity_names = list(target_alloc_scores.keys())
    print("Writing output...")
    process_output(future_alloc, target_activity_names)


def get_input_config() -> Dict[str, any]:
    # Try to authorize the service account using local config file
    try:
        gs = gspread.service_account()
    except:
        # https://stackoverflow.com/questions/41369993/modify-google-sheet-from-aws-lambda
        credentials = json.loads(sm.get_secret("gspreadCredentials"))
        gs = gspread.service_account_from_dict(credentials)

    spreadsheet_name = sm.get_secret("SchedAssistInputSpreadsheetName")
    config_worksheet = gs.open(spreadsheet_name).sheet1

    cells = config_worksheet.get_all_values()

    num_rows = len(cells)
    num_cols = len(cells[0])

    since = None
    activity_header_coords = None
    score_header_coords = None

    for row in range(num_rows):
        for col in range(num_cols):
            value = cells[row][col]
            coords = (row, col)

            if value == "Since" and col < num_cols - 1:
                since = datetime.strptime(cells[row][col + 1], "%d/%m/%Y")
            elif value == "Activity":
                activity_header_coords = coords
            elif value == "Score":
                score_header_coords = coords

    if not since:
        print("Could not find reference date") 

    if not activity_header_coords:
        print("Could not find activity name data") 
        
    if not score_header_coords:
        print("Could not find activity score data") 

    if not (since and activity_header_coords and score_header_coords):
        raise ValueError("Incomplete input provided.")
        return

    activity_names = []
    activity_scores = []

    # Iterate through each activity
    start_activity_row = activity_header_coords[0] + 1
    start_score_row = score_header_coords[0] + 1

    for i in range(0, num_rows - start_activity_row):
        activity_name = cells[start_activity_row + i][activity_header_coords[1]]

        if activity_name:
            activity_names.append(activity_name)

            score = cells[start_score_row + i][score_header_coords[1]]
            activity_scores.append(int(score) if score else 0)

    # Extract the target allocation of time between activities
    target_alloc_scores = dict(zip(activity_names, activity_scores))

    return target_alloc_scores, since


def get_current_time_spent_s(since: datetime) -> Dict[str, int]:
    data = {
        'workspace_id': TOGGL_WORKSPACE_ID,
        'since': since
    }

    current_time_spent_s = {}

    time_entries = TOGGL.getDetailedReportPages(data=data)['data']

    # Get completed time entries
    for e in time_entries:
        duration_s = int(e['dur'] / 1000)

        project = e['project']
        if project:
            current_time_spent_s[project] = current_time_spent_s.get(project, 0) + duration_s

    # Get currently running time entry if there is one
    current_time_entry = TOGGL.request("https://api.track.toggl.com/api/v8/time_entries/current")['data']

    if current_time_entry:
        project_id = current_time_entry.get('pid', None)

        if project_id:
            project = TOGGL.request(f"https://api.track.toggl.com/api/v8/projects/{project_id}")
            
            current_entry_start = datetime.fromisoformat(current_time_entry['start'])
            duration = datetime.now().astimezone() - max(since.astimezone(), current_entry_start)

            project_name = project['data']['name']
            current_time_spent_s[project_name] = current_time_spent_s.get(project_name, 0) + duration.total_seconds()

    return current_time_spent_s


def process_output(future_alloc: Dict[str, any], target_activity_names: List[str]) -> None:
    update_toggl_projects(target_activity_names)
    upload_future_alloc_to_todoist(future_alloc)


def update_toggl_projects(target_activity_names: List[str]):
    """Make sure that all activities in the target set are available on Toggl, and any previously generated projects not
    used are deleted."""

    clients = TOGGL.request("https://api.track.toggl.com/api/v8/clients")
    SA_CLIENT_NAME = "SchedulingAssistant"

    sa_client_id = None

    if clients:
        sa_client_id = next((client['id'] for client in clients if client['name'] == SA_CLIENT_NAME), None)

    # If the scheduling asssistant client doesn't exist yet, we need to make one
    if not sa_client_id:
        data = {
            "client": {
                "name": SA_CLIENT_NAME,
                "wid": TOGGL_WORKSPACE_ID
            }
        }

        sa_client_id = TOGGL.postRequest("https://api.track.toggl.com/api/v8/clients", parameters=data)["data"]["id"]

    TOGGL_API_BASE_URL = "https://www.toggl.com/api/v8/"

    # Get a list of current Toggl projects bound to the SA client
    current_projects = TOGGL.request(f"https://api.track.toggl.com/api/v8/clients/{sa_client_id}/projects")
    current_project_names = []

    if current_projects:
        # Delete batch of old generated projects
        pids_to_delete = []

        for proj in current_projects:
            name = proj['name']
            client_id = proj.get('cid', None)

            if client_id and client_id == sa_client_id and name not in target_activity_names:
                # A project that was generated previously, but is no longer a priority
                pids_to_delete.append(proj['id'])

        if pids_to_delete:
            pids_to_delete_as_str = ','.join([str(pid) for pid in pids_to_delete])
            TOGGL.postRequest(TOGGL_API_BASE_URL + f"projects/{pids_to_delete_as_str}", method='DELETE')

        current_project_names = [p['name'] for p in current_projects]

    # Add any new projects
    data = { 
        "project": { 
            "name": "", 
            "wid": TOGGL_WORKSPACE_ID, 
            "cid": sa_client_id,
            "is_private": True
        }
    }

    for new_project in list(set(target_activity_names) - set(current_project_names)):
        data['project']['name'] = new_project
        TOGGL.postRequest(TOGGL_API_BASE_URL + "projects", parameters=data)


def duration_str(seconds: int) -> None:
    """Converts a number of seconds into a string describing an equivalent duration in hours and minutes."""
    hours, remaining_seconds = divmod(seconds, 3600)
    mins = math.floor(remaining_seconds / 60.0)

    hours = (str(int(hours)) + "h") if hours else ""
    mins = (str(mins) + "m") if mins else ""
    spacing = " " if (hours and mins) else ""

    return f"{hours}{spacing}{mins}"


def upload_future_alloc_to_todoist(future_alloc: Dict[str, any]) -> None:
    """Adds a set of highest priority activities to Todoist as tasks."""
    todoist_api_cache = os.environ.get('TODOIST_API_CACHE', '~/.todoist-sync')
    api = todoist.TodoistAPI(sm.get_secret("TodoistAPIToken"), cache=todoist_api_cache)
    api.sync()

    projects = api.state['projects']
    PROJECT_NAME = "Scheduling Assistant"
    output_project_id = None

    # If there are projects on Todoist...
    if projects:
        # collect a list of the ids of those with a name that matches the output project name
        matching_ids = []
        for proj in projects:
            if proj['name'] == PROJECT_NAME:
                matching_ids.append(proj['id'])

        # If we find more than one matching project, delete them all
        if len(matching_ids) > 1:
            for proj_id in matching_ids:
                api.projects.get_by_id(proj_id).delete()

        # If we find exactly one matching project, use this one to add tasks in future
        elif len(matching_ids) == 1:
            output_project_id = matching_ids[0]

    # If no output project could be found
    if not output_project_id:
        # then we create one here
        output_project_id = api.projects.add(PROJECT_NAME)['id']
    else:
        # otherwise, remove any existing tasks belonging to this project
        existing_tasks = filter(lambda task: task['project_id'] == output_project_id, api.state['items'])

        for t in existing_tasks:
            t.delete()

    allocation = future_alloc['allocation']

    # As long as there are tasks to upload...
    if allocation:
        # this gets the next task we should allocate time to
        priority = min(allocation, key=allocation.get)

        task_name = priority

        # ...and how much time is required on it
        min_required_time_s = future_alloc.get('min_required_time_s')
        if min_required_time_s:
            req_time_s = allocation[priority] * min_required_time_s
            task_name += " (" + duration_str(req_time_s) + ")"

        # before adding it to Todoist
        new_task = api.items.add(task_name, due={"string": "today"}, project_id=output_project_id)

    api.commit()
    

if __name__ == '__main__':
    run()
