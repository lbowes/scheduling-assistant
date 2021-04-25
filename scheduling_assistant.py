from typing import Dict, List
from datetime import datetime
from secretsmanager import SecretsManager

import gspread 
import json 
import todoist 
from toggl.TogglPy import Toggl

from logic import calc_future_alloc


sm = SecretsManager(region='eu-west-2')


TOGGL = Toggl()
TOGGL.setAPIKey(sm.get_secret("TogglAPIToken"))
TOGGL_WORKSPACE_ID = TOGGL.getWorkspace(name=sm.get_secret("TogglWorkspaceName"))['id']


def main(events, context) -> None:
    print("Reading input configuration spreadsheet...")
    target_alloc_scores = get_target_alloc_scores()

    ref_date = datetime(2021, 1, 1)
    print("Fetching current time allocation...")
    current_time_spent_s = get_current_time_spent_s(since=ref_date)

    print("Calculating required future time allocation...")
    future_alloc = calc_future_alloc(current_time_spent_s, target_alloc_scores)
    
    target_activity_names = list(target_alloc_scores.keys())
    print("Writing output...")
    process_output(future_alloc, target_activity_names)


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
        pid = current_time_entry['pid']
        project = TOGGL.request(f"https://api.track.toggl.com/api/v8/projects/{pid}")
        
        current_entry_start = datetime.fromisoformat(current_time_entry['start'])
        duration = datetime.now().astimezone() - max(since.astimezone(), current_entry_start)

        project_name = project['data']['name']
        current_time_spent_s[project_name] = current_time_spent_s.get(project_name, 0) + duration.total_seconds()

    return current_time_spent_s


def get_target_alloc_scores() -> Dict[str, any]:
    # Try to authorize the service account using local config file
    #try:
    #    gs = gspread.service_account()
    #except:
        # https://stackoverflow.com/questions/41369993/modify-google-sheet-from-aws-lambda
    credentials = json.loads(sm.get_secret("gspreadCredentials"))
    gs = gspread.service_account_from_dict(credentials)

    spreadsheet_name = sm.get_secret("SchedAssistInputSpreadsheetName")
    config_worksheet = gs.open(spreadsheet_name).sheet1

    cells = config_worksheet.get_all_values()

    num_rows = len(cells)
    num_cols = len(cells[0])

    activity_header_coords = None
    score_header_coords = None

    for row in range(num_rows):
        for col in range(num_cols):
            value = cells[row][col]

            coords = (row, col)

            if value == "Activity":
                activity_header_coords = coords
            elif value == "Score":
                score_header_coords = coords

    if not activity_header_coords:
        print("Could not find activity name data") 
        
    if not score_header_coords:
        print("Could not find activity score data") 

    if not (activity_header_coords and score_header_coords):
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

    return target_alloc_scores


def process_output(future_alloc: Dict[str, any], target_activity_names: List[str]) -> None:
    update_toggl_projects(target_activity_names)
    upload_future_alloc_to_todoist(future_alloc, target_activity_names)


def update_toggl_projects(target_activity_names: List[str]):
    """Make sure all activities in the target set are available on Toggl."""

    # Get a list of current Toggl projects
    projects = TOGGL.request(f"https://www.toggl.com/api/v8/workspaces/{TOGGL_WORKSPACE_ID}/projects")
    current_project_names = [p['name'] for p in projects] if projects else []

    data = { 
        "project": { 
            "name": "", 
            "wid": TOGGL_WORKSPACE_ID, 
            "is_private": True 
        }
    }

    # Add any target activities that are not already projects
    for new_project in list(set(target_activity_names) - set(current_project_names)):
        data['project']['name'] = new_project
        TOGGL.postRequest("https://www.toggl.com/api/v8/projects", parameters=data)


def upload_future_alloc_to_todoist(future_alloc: Dict[str, any], target_activity_names: List[str]):
    api = todoist.TodoistAPI(sm.get_secret("TodoistAPIToken"), cache='/tmp/.todoist-sync')
    api.sync()

    # Get list of current Todoist projects
    projects = api.state['projects']
   
    PROJECT_NAME = "Scheduling Assistant"
    indicator_project_id = next((proj['id'] for proj in projects if proj['name'] == PROJECT_NAME), None)

    if not indicator_project_id:
        indicator_project_id = api.projects.add(PROJECT_NAME)['id']

    # Work out what the priority activity is
    allocation = future_alloc['allocation']
    priority = max(allocation, key=allocation.get)

    task_name = priority + " " + str(datetime.now())

    # ...and how much time is required on it
    min_required_time_s = future_alloc.get('min_required_time_s')
    if min_required_time_s:
        req_time_s = allocation[priority] * min_required_time_s
        hours, remaining_seconds = divmod(req_time_s, 3600)
        mins = round(remaining_seconds / 60.0)
        task_name += " ({0}h {1}m)".format(hours, mins)

    # Remove any existing tasks added by this application
    priority_task_found = False
    TODAY = { "string": "today" }

    for task in api.state['items']:
        if task['project_id'] == indicator_project_id:
            if not priority_task_found and task['content'].startswith(priority):
                priority_task_found = True
                api.items.update(task['id'], content=task_name, due=TODAY, project_id=indicator_project_id)
            else:
                task.delete()

    if not priority_task_found:
        api.items.add(task_name, due=TODAY, project_id=indicator_project_id)

    api.commit()
    

if __name__ == '__main__':
    main(None, None)
