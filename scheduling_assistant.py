"""
Usage:
    scheduling_assistant.py --config=<FILE>
    scheduling_assistant.py -h | --help

Options:
    -c --config=<FILE>    Config file
    -h --help  Show this screen
"""


from docopt import docopt
from typing import Dict, List
from datetime import datetime
from pendulum import duration
import json

import gspread 
import todoist 
from toggl.TogglPy import Toggl


args = docopt(__doc__)
with open(args['--config'], 'r') as config_file:
    CONFIG = json.load(config_file)


def main() -> None:
    print("Reading input configuration spreadsheet...")
    cfg = get_input_config()

    ref_date = datetime.strptime(cfg['reference_date'], "%d/%m/%Y")
    print("Fetching current time allocation...")
    current_time_spent_s = get_current_time_spent_s(since=ref_date)

    target_alloc_scores = cfg['target_alloc_scores']
    print("Calculating required future time allocation...")
    future_alloc = calc_future_alloc(current_time_spent_s, target_alloc_scores)
    
    target_activity_names = list(target_alloc_scores.keys())
    print("Writing output...")
    process_output(future_alloc, target_activity_names)


def get_current_time_spent_s(since: datetime) -> Dict[str, int]:
    toggl_cfg = CONFIG['toggl']

    toggl = Toggl()
    toggl.setAPIKey(toggl_cfg['api_token'])

    workspace = toggl.getWorkspace(name=toggl_cfg['workspace_name'])

    data = {
        'workspace_id': workspace['id'],
        'since': since
    }

    time_entries = toggl.getDetailedReportPages(data=data)['data']

    current_time_spent_s = {}

    for e in time_entries:
        duration_s = int(e['dur'] / 1000)

        project = e['project']
        if project:
            current_time_spent_s[project] = current_time_spent_s.get(project, 0) + duration_s

    return current_time_spent_s


def get_input_config() -> Dict[str, any]:
    gs = gspread.service_account()
    config_worksheet = gs.open(CONFIG['google_spreadsheet']).sheet1

    cells = config_worksheet.get_all_values()

    num_rows = len(cells)
    num_cols = len(cells[0])

    ref_date = None
    activity_header_coords = None
    score_header_coords = None

    for row in range(num_rows):
        for col in range(num_cols):
            value = cells[row][col]

            coords = (row, col)

            if value == "Reference Date" and col < num_cols - 1:
                ref_date = cells[row][col + 1]
            elif value == "Activity":
                activity_header_coords = coords
            elif value == "Score":
                score_header_coords = coords

    if not ref_date:
        print("Could not find reference date") 

    if not activity_header_coords:
        print("Could not find activity name data") 
        
    if not score_header_coords:
        print("Could not find activity score data") 

    if not (ref_date and activity_header_coords and score_header_coords):
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

    return {
        "reference_date": ref_date,
        "target_alloc_scores": target_alloc_scores
    }


def calc_future_alloc(current_time_spent_s: Dict[str, int], target_alloc_scores: Dict[str, int]) -> Dict[str, any]:
    """Calculate the percentage allocation of future time between a set of activities, given a target allocation between
    them and the current amount of time spent on each."""
    total_score = sum(target_alloc_scores.values())
    target_alloc = { act: float(score) / total_score for act, score in target_alloc_scores.items() if score > 0 }

    future_alloc = { "allocation": target_alloc }

    if not current_time_spent_s:
        return future_alloc

    for target_act in target_alloc:
        if target_act not in current_time_spent_s:
            current_time_spent_s[target_act] = 0

    relevant_time_spent_s = sum(current_time_spent_s[act] for act in target_alloc)

    time_required_s = 0

    for act, target in target_alloc.items():
        required_time_s = (current_time_spent_s[act] / target_alloc[act]) - relevant_time_spent_s

        if required_time_s > time_required_s:
            time_required_s = required_time_s

    if time_required_s <= 0:
        return future_alloc

    future_alloc["min_required_time_s"] = time_required_s
    future_alloc["allocation"] = {}

    total_time_s = relevant_time_spent_s + time_required_s

    for act, target in target_alloc.items():
        target_alloc[act]
        total_time_s
        current_time_spent_s[act]
        time_required_s

        allocation = (target_alloc[act] * total_time_s - current_time_spent_s[act]) / time_required_s

        if allocation:
            future_alloc["allocation"][act] = allocation

    return future_alloc


def process_output(future_alloc: Dict[str, any], target_activity_names: List[str]) -> None:
    # Update Toggl projects
    # todo

    # Output current priority to Todoist
    upload_future_alloc_to_todoist(future_alloc, target_activity_names)


def upload_future_alloc_to_todoist(future_alloc: Dict[str, any], target_activity_names: List[str]):
    api = todoist.TodoistAPI(CONFIG['todoist_api_token'])
    api.sync()

    # Remove any existing tasks added by this application
    tasks = api.state['items']
    for task in tasks:
        if any(task['content'].startswith(t) for t in target_activity_names):
            task.delete()

    # Work out what the priority activity is
    allocation = future_alloc['allocation']
    priority = max(allocation, key=allocation.get)

    task_name = priority

    # ...and how much time is required on it
    min_required_time_s = future_alloc.get('min_required_time_s')
    if min_required_time_s:
        req_time = duration(seconds=allocation[priority] * min_required_time_s)
        hours = req_time.in_hours()
        mins = req_time.minutes
        task_name += " ({}h {}m)".format(hours, mins)

    api.items.add(task_name, due={ "string": "today" })

    api.commit()
    

if __name__ == '__main__':
    main()
