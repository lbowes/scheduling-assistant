import math
from typing import Dict
from pendulum import duration


def check_target_alloc(target_alloc: Dict[str, float]):
    # Validate a target allocation set
    target_allocs = target_alloc.values()

    # The values in this dictionary represent percentages that must sum to equal 1
    if not math.isclose(sum(target_allocs), 1.0, abs_tol=0.0001):
        raise ValueError("Sum of target allocation values must equal 1") 
    
    # To spend 0% of overall time on an activity, requires that you spend an infinite amount of time on others
    if 0.0 in target_allocs:
        raise ValueError("Target allocation set cannot contain 0")


def calc_extra_time_required(current_time_spent: Dict[str, duration], target_alloc: Dict[str, float], time_spent_s: int):
    # Calculate the minimum amount of extra time required (in seconds) to match `target_alloc`, having already spent
    # `time_spent_s` seconds total in `current_time_spent` 
    time_required_s = 0

    for act, target in target_alloc.items():
        required_time_s = (current_time_spent[act].seconds / target_alloc[act]) - time_spent_s

        if required_time_s > time_required_s:
            time_required_s = required_time_s

    return time_required_s


def calculate_action(current_time_spent: Dict[str, duration], target_alloc: Dict[str, float]):
    # Calculate the percentage allocation of future time between a set of activities, given a target allocation between
    # them and the current amount of time spent on each.
    check_target_alloc(target_alloc)

    action = { "allocation": target_alloc }

    if not current_time_spent:
        return action

    for target_act in target_alloc:
        if target_act not in current_time_spent:
            current_time_spent[target_act] = duration()

    time_spent_s = sum(current_time_spent.values(), duration()).seconds

    time_required_s = calc_extra_time_required(current_time_spent, target_alloc, time_spent_s)

    if time_required_s <= 0:
        return action

    action["min_required_time"] = duration(seconds=time_required_s)
    action["allocation"] = {}

    total_time_s = time_spent_s + time_required_s

    for act, target in target_alloc.items():
        allocation = (target_alloc[act] * total_time_s - current_time_spent[act].seconds) / time_required_s

        if allocation:
            action["allocation"][act] = allocation

    return action
