import pytest

from logic import prioritize


#def test_calc_future_alloc() -> None:
#    # ==================== Normal input ====================
#    # Case 1
#    current_time_spent_s = { "A": 2 }
#    target_alloc = { "A": 1, "B": 1 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": { "B": 1.0 }, "min_required_time_s": 2 }
#
#    # Case 2
#    current_time_spent_s = { "C": 8, "D": 2 }
#    target_alloc = { "C": 9, "D": 1 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": { "C": 1.0 }, "min_required_time_s": 10 }
#
#    # Case 3
#    current_time_spent_s = { "A": 3, "B": 2, "C": 5 }
#    target_alloc = { "A": 0.2, "B": 0.4, "C": 0.4 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": { "B": 0.8, "C": 0.2 }, "min_required_time_s": 5 }
#
#    # Case 4
#    current_time_spent_s = { "C": 8, "D": 2 }
#    target_alloc = { "C": 0.9, "D": 0.1 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": { "C": 1.0 }, "min_required_time_s": 10 }
#
#    # Case 5
#    current_time_spent_s = { "A": 1, "B": 2, "C": 3 }
#    target_alloc = { "B": 0.25, "C": 0.75 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": { "C": 1.0 }, "min_required_time_s": 3 }
#
#    # ==================== No past activities ====================
#    current_time_spent_s = {}
#    target_alloc = { "C": 0.5, "D": 0.5 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": target_alloc }
#
#    current_time_spent_s = None
#    target_alloc = { "C": 0.5, "D": 0.5 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": target_alloc }
#
#    # ==================== No relevant past activities ====================
#    current_time_spent_s = { "A": 2 }
#    target_alloc = { "C": 0.5, "D": 0.5 }
#    future = calc_future_alloc(current_time_spent_s, target_alloc)
#    assert future == { "allocation": target_alloc }


def test_prioritize_no_target() -> None:
    goal = {}
    past = []
    future = prioritize(goal, past)
    assert future == None


def test_prioritize_no_past() -> None:
    past = []

    goal = { "A": 3, "B": 2 }
    future = prioritize(goal, past)
    assert future == [ ("A", 0), ("B", 0) ]

    goal = { "X": 4, "Y": 5 }
    future = prioritize(goal, past)
    assert future == [ ("Y", 0), ("X", 0) ]

    goal = { "P": 7 }
    future = prioritize(goal, past)
    assert future == [ ("P", 0) ]


def test_prioritize_equal() -> None:
    goal = { "A": 1, "B": 1 }

    past = [ ("A", 2), ("B", 1) ]
    future = prioritize(goal, past)
    assert future == [ ("B", 1), ("A", 0) ]


def test_prioritize_not_started() -> None:
    goal = { "A": 1, "B": 1, "C": 1, "D": 1, "E": 1, "F": 1}
    
    past = [ ("B", 1), ("A", 20), ("B", 20), ("C", 10) ]
    future = prioritize(goal, past)
    print("future: " + str(future))
    assert future == [ ("C", 11), ("D", 21), ("E", 21), ("F", 21), ("A", 1), ("B", 0) ]





















































#Priority:            A
#Processing activity: B
#Duration:            1
#Current time spent:  {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
#Time required:       {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
#Switching priority to B
#
#
#Priority:            B
#Processing activity: A
#Duration:            20
#Current time spent:  {'A': 0, 'B': 1, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
#Time required:       {'A': 1.0, 'B': 0.0, 'C': 1.0, 'D': 1.0, 'E': 1.0, 'F': 1.0}
#Switching priority to C
#
#
#Priority:            C
#Processing activity: B
#Duration:            20
#Current time spent:  {'A': 20, 'B': 1, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
#Time required:       {'A': 0.0, 'B': 19.0, 'C': 20.0, 'D': 20.0, 'E': 20.0, 'F': 20.0}
#
#
#Priority:            C
#Processing activity: C
#Duration:            10
#Current time spent:  {'A': 20, 'B': 21, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
#Time required:       {'A': 1.0, 'B': 0.0, 'C': 21.0, 'D': 21.0, 'E': 21.0, 'F': 21.0}
