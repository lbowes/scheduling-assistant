import pytest
from typing import Dict
from pendulum import duration

from scheduling_assistant import calculate_action


def test_calculate_action():
    # ==================== Normal input ====================
    # Case 1
    current_time_spent = { "A": duration(hours=2) }
    target_alloc = { "A": 0.5, "B": 0.5 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": { "B": 1.0 }, "min_required_time": duration(hours=2) }

    # Case 2
    current_time_spent = { "C": duration(hours=8), "D": duration(hours=2) }
    target_alloc = { "C": 0.9, "D": 0.1 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": { "C": 1.0 }, "min_required_time": duration(hours=10) }

    # Case 3
    current_time_spent = { "A": duration(hours=3), "B": duration(hours=2), "C": duration(hours=5) }
    target_alloc = { "A": 0.2, "B": 0.4, "C": 0.4 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": { "B": 0.8, "C": 0.2 }, "min_required_time": duration(hours=5) }

    # Case 4
    current_time_spent = { "C": duration(hours=8), "D": duration(hours=2) }
    target_alloc = { "C": 0.9, "D": 0.1 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": { "C": 1.0 }, "min_required_time": duration(hours=10) }

    # Case 5
    current_time_spent = { "A": duration(hours=1), "B": duration(hours=2), "C": duration(hours=3) }
    target_alloc = { "B": 0.25, "C": 0.75 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": { "C": 1.0 }, "min_required_time": duration(hours=3) }

    # ==================== No past activities ====================
    current_time_spent = {}
    target_alloc = { "C": 0.5, "D": 0.5 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": target_alloc }

    current_time_spent = None
    target_alloc = { "C": 0.5, "D": 0.5 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": target_alloc }

    # ==================== No relevant past activities ====================
    current_time_spent = { "A": duration(hours=2) }
    target_alloc = { "C": 0.5, "D": 0.5 }
    future = calculate_action(current_time_spent, target_alloc)
    assert future == { "allocation": target_alloc }

    # ==================== Invalid target allocation set ====================
    current_time_spent = { "C": duration(hours=3), "D": duration(hours=3) }

    # Case 1
    with pytest.raises(ValueError) as invalid_target_msg:
        calculate_action(current_time_spent, {})
        invalid_target_msg.match("Sum of target allocation values must equal 1")

    # Case 2
    with pytest.raises(ValueError) as invalid_target_msg:
        calculate_action(current_time_spent, { "C": 0.5 })
        invalid_target_msg.match("Sum of target allocation values must equal 1")

    # Case 3
    with pytest.raises(ValueError) as invalid_target_msg:
        calculate_action(current_time_spent, {"A": 1.0, "B": 0.0})
        invalid_target_msg.match("Target allocation set cannot contain 0")


    # ==================== todo ====================
    
