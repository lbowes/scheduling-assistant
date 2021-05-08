from typing import List, Dict, Tuple
from itertools import cycle


def prioritize(goal: Dict[str, int], past: List[Tuple[str, int]]) -> None:
    if not goal:
        return None

    sorted_activities = [name for name, score in sorted(goal.items(), key=lambda x: x[1], reverse=True)]
    activity_cycle = cycle(sorted_activities)

    total_score = sum(goal.values())
    goal_percent  = { act: float(score) / total_score for act, score in goal.items() if score > 0 }

    activity_names = goal.keys()
    current_time_spent_s = dict.fromkeys(activity_names, 0)
    time_required_s = dict.fromkeys(activity_names, 0)
    total_time_s = 0
    priority = next(activity_cycle)

    if past:
        for activity, dur_s in past:
            if activity not in goal:
                continue

            current_time_spent_s[activity] += dur_s
            total_time_s += dur_s

            alloc = { act: max((time_s / total_time_s) - goal_percent[act], 0) for act, time_s in current_time_spent_s.items() }
            completed_act = max(alloc, key=alloc.get)

            if current_time_spent_s[priority] > time_required_s[priority]:
                priority = next(activity_cycle)

            for act, time_spent_s in current_time_spent_s.items():
                future_time_spent_s = current_time_spent_s[completed_act] * (goal_percent[act] / goal_percent[completed_act])
                time_required_s[act] = abs(future_time_spent_s - time_spent_s)

        if time_required_s[priority] == 0:
            priority = next(activity_cycle)

    output = []

    start_idx = sorted_activities.index(priority)
    num_activities = len(goal)
    for i in range(num_activities):
        activity = sorted_activities[(start_idx + i) % num_activities]

        output.append((activity, time_required_s[activity]))

    return output
