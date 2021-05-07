from typing import List, Dict, Tuple
from itertools import cycle


#def calc_future_alloc(current_time_spent_s: Dict[str, int], target_alloc_scores: Dict[str, int]) -> Dict[str, any]:
#    """Calculate the percentage allocation of future time between a set of activities, given a target allocation between
#    them and the current amount of time spent on each."""
#    total_score = sum(target_alloc_scores.values())
#    target_alloc = { act: float(score) / total_score for act, score in target_alloc_scores.items() if score > 0 }
#
#    future_alloc = { "allocation": target_alloc }
#
#    if not current_time_spent_s:
#        return future_alloc
#
#    for target_act in target_alloc:
#        if target_act not in current_time_spent_s:
#            current_time_spent_s[target_act] = 0
#
#    relevant_time_spent_s = sum(current_time_spent_s[act] for act in target_alloc)
#
#    time_required_s = 0
#
#    for act, target in target_alloc.items():
#        required_time_s = (current_time_spent_s[act] / target_alloc[act]) - relevant_time_spent_s
#
#        if required_time_s > time_required_s:
#            time_required_s = required_time_s
#
#    if time_required_s <= 0:
#        return future_alloc
#
#    future_alloc["min_required_time_s"] = time_required_s
#    future_alloc["allocation"] = {}
#
#    total_time_s = relevant_time_spent_s + time_required_s
#
#    for act, target in target_alloc.items():
#        target_alloc[act]
#        total_time_s
#        current_time_spent_s[act]
#        time_required_s
#
#        allocation = (target_alloc[act] * total_time_s - current_time_spent_s[act]) / time_required_s
#
#        if allocation:
#            future_alloc["allocation"][act] = allocation
#
#    return future_alloc


def prioritize(goal: Dict[str, int], past: List[Tuple[str, int]]) -> None:
    if not goal:
        return None

    # This gives the order in which to complete activities
    sorted_activities = [name for name, score in sorted(goal.items(), key=lambda x: x[1], reverse=True)]
    activity_cycle = cycle(sorted_activities)

    total_score = sum(goal.values())
    goal_percent  = { act: float(score) / total_score for act, score in goal.items() if score > 0 }

    current_time_spent_s = dict.fromkeys(goal.keys(), 0)
    time_required_s = current_time_spent_s.copy()
    total_time_s = 0
    priority = next(activity_cycle)

    first_iteration = True

    for activity, dur_s in past:
        if activity not in goal:
            continue

        current_time_spent_s[activity] += dur_s
        total_time_s += dur_s

        if current_time_spent_s[priority] >= time_required_s[priority] and not first_iteration:
            priority = next(activity_cycle)

        for act, time_spent_s in current_time_spent_s.items():
            if time_spent_s > goal_percent[act] * total_time_s:
                print("completed act " + act + " with goal percent " + str(goal_percent[act]) + " after spending " +
                        str(time_spent_s) + " out of " + str(goal_percent[act] * total_time_s))
                completed_act = act

        for act, time_spent_s in current_time_spent_s.items():
            future_time_spent_s = current_time_spent_s[completed_act] * (goal_percent[act] / goal_percent[completed_act])
            time_required_s[act] = abs(future_time_spent_s - time_spent_s)

        print("\n\n\n")
        first_iteration = False

    output = []

    start_idx = sorted_activities.index(priority)
    num_activities = len(goal)
    for i in range(num_activities):
        activity = sorted_activities[(start_idx + i) % num_activities]

        output.append((activity, time_required_s[activity]))

    return output


if __name__ == '__main__':
    goal = { "A": 1, "B": 1, "C": 1, "D": 1, "E": 1, "F": 1}
    
    past = [ ("B", 1), ("A", 20), ("B", 20), ("C", 10) ]
    future = prioritize(goal, past)
    print("future: " + str(future))
    assert future == [ ("C", 11), ("D", 21), ("E", 21), ("F", 21), ("A", 1), ("B", 0) ]
