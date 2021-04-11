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
    current_time_spent_s = get_current_time_spent_s()
    target_alloc_points = get_target_allocation()

    future_alloc = calc_future_alloc(current_time_spent_s, target_alloc_points)
    
    target_activity_names = list(target_alloc_points.keys())
    process_output(future_alloc, target_activity_names)


def get_current_time_spent_s() -> Dict[str, int]:
    toggl_cfg = CONFIG['toggl']

    toggl = Toggl()
    toggl.setAPIKey(toggl_cfg['api_token'])

    workspace = toggl.getWorkspace(name=toggl_cfg['workspace_name'])

    ref_time = datetime(2021, 1, 1)

    data = {
        'workspace_id': workspace['id'],
        'since': ref_time
    }

    time_entries = toggl.getDetailedReportPages(data=data)['data']

    current_time_spent_s = {}

    for e in time_entries:
        duration_s = int(e['dur'] / 1000)

        project = e['project']
        if project:
            current_time_spent_s[project] = current_time_spent_s.get(project, 0) + duration_s

    return current_time_spent_s


def calc_total_time_spent_across(time_entries: List[Dict[str, any]]) -> Dict[str, int]:
    time_spent_s = {}

    for e in time_entries:
        duration_s = seconds=int(e['dur'] / 1000)

        project = e['project']
        if project:
            time_spent_s[project] = time_spent_s.get(project, 0) + duration_s

    return time_spent_s


def get_target_allocation() -> Dict[str, int]:
    gs = gspread.service_account()
    target_alloc_worksheet = gs.open(CONFIG['google_spreadsheet']).sheet1

    activity_names = target_alloc_worksheet.col_values(1)[1:]
    activity_points = [int(v) for v in target_alloc_worksheet.col_values(2)[1:]]

    return dict(zip(activity_names, activity_points))


def calc_future_alloc(current_time_spent_s: Dict[str, int], target_alloc_points: Dict[str, int]) -> Dict[str, any]:
    """Calculate the percentage allocation of future time between a set of activities, given a target allocation between
    them and the current amount of time spent on each."""
    total_points = sum(target_alloc_points.values())
    target_alloc = {act: float(points) / total_points for act, points in target_alloc_points.items() if points > 0}

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
