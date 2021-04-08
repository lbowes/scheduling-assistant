"""
Usage:
    scheduling_assistant.py --config=<FILE> [--output=<FILE>]
    scheduling_assistant.py -h | --help

Options:
    -c --config=<FILE>    Config file
    -o --output=<FILE>    Output file
    -h --help  Show this screen
"""


from docopt import docopt
from typing import Dict, List
from datetime import datetime
from pendulum import duration
import json

import gspread 
from toggl.TogglPy import Toggl


def main(args) -> None:
    current_time_spent_s = get_current_time_spent_s(args['--config'])
    target_alloc_points = get_target_allocation()

    action = calculate_action(current_time_spent_s, target_alloc_points)
    
    process_output(action, args['--output'])


def get_current_time_spent_s(config_file: str) -> Dict[str, int]:
    with open(config_file, 'r') as f:
        config = json.load(f)
        api_token = config['api_token']
        workspace_name = config['workspace_name']

    toggl = Toggl()
    toggl.setAPIKey(api_token)

    workspaces = toggl.getWorkspaces()

    workspace_id = toggl.getWorkspace(name=workspace_name)['id']

    ref_time = datetime(2021, 1, 1)

    data = {
        'workspace_id': workspace_id,
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
    gc = gspread.service_account()
    worksheet = gc.open("target_activity_allocation").sheet1

    activity_names = worksheet.col_values(1)[1:]
    activity_points = [int(v) for v in worksheet.col_values(2)[1:]]

    return dict(zip(activity_names, activity_points))


def calculate_action(current_time_spent_s: Dict[str, int], target_alloc_points: Dict[str, int]) -> Dict[str, any]:
    """Calculate the percentage allocation of future time between a set of activities, given a target allocation between
    them and the current amount of time spent on each."""
    total_points = sum(target_alloc_points.values())
    target_alloc = {act: float(points) / total_points for act, points in target_alloc_points.items() if points > 0}

    action = { "allocation": target_alloc }

    if not current_time_spent_s:
        return action

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
        return action

    action["min_required_time_s"] = time_required_s
    action["allocation"] = {}

    total_time_s = relevant_time_spent_s + time_required_s

    for act, target in target_alloc.items():
        target_alloc[act]
        total_time_s
        current_time_spent_s[act]
        time_required_s

        allocation = (target_alloc[act] * total_time_s - current_time_spent_s[act]) / time_required_s

        if allocation:
            action["allocation"][act] = allocation

    return action


def process_output(action: Dict[str, any], output_file: str) -> None:
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as output_file:
            json.dump(action, output_file, ensure_ascii=False, indent=4)
    else:
        # print results to console
        allocation = dict(sorted(action['allocation'].items(), key=lambda item: item[1], reverse=True))

        if 'min_required_time_s' in action:
            min_required_time = duration(seconds=action['min_required_time_s'])

            for activity, percent in allocation.items():
                print(activity + ": " + str(min_required_time * percent))
        else:
            for activity, percent in allocation.items():
                print(activity + ": " + "{0:.0%}".format(percent))


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)
