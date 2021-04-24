from typing import List, Dict


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


