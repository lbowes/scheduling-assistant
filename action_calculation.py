"""
Calculate the actions required to reach a specific allocation of time between a set of activities, given information
about how much time has already been spent on them.

Usage:
    action_calculation.py --history=<FILE> --target=<FILE> [--output=<FILE>]
    action_calculation.py -h | --help

Options:
    --history=<FILE>   Current time spent on activities
    --target=<FILE>    Target activity allocation
    --output=<FILE>    Output file to store actions
    -h --help  Show this screen
"""


import math
import json
from docopt import docopt
from typing import Dict


def calc_extra_time_required(current_time_spent_s: Dict[str, int], target_alloc: Dict[str, float], time_spent_s: int) -> int:
    """Calculate the minimum amount of extra time required (in seconds) to match `target_alloc`, having already spent
    `time_spent_s` seconds total in `current_time_spent` """
    time_required_s = 0

    for act, target in target_alloc.items():
        required_time_s = (current_time_spent_s[act] / target_alloc[act]) - time_spent_s

        if required_time_s > time_required_s:
            time_required_s = required_time_s

    return time_required_s


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

    time_required_s = calc_extra_time_required(current_time_spent_s, target_alloc, relevant_time_spent_s)

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


def save_action_to(file_path: str, action: Dict[str, any]) -> None:
    """Save an output action to file"""
    with open(file_path, 'w', encoding='utf-8') as output_file:
        if "min_required_time" in action:
            action["min_required_time"] = action["min_required_time"].seconds

        json.dump(action, output_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    args = docopt(__doc__)

    with open(args['--history'], 'r') as given:
        current_time_spent_s  = json.load(given)

    with open(args['--target'], 'r') as goal:
        target_alloc_points  = json.load(goal)

    action = calculate_action(current_time_spent_s, target_alloc_points)
    
    output_file = args['--output']

    if output_file:
        save_action_to(output_file, action)
    else:
        print("todo: print results to console")
