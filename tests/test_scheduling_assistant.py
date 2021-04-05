import pytest
import subprocess
import os
import json
from typing import Dict, List
from random import shuffle

from scheduling_assistant import calculate_action


def test_action_calculation() -> None:
    # ==================== Normal input ====================
    # Case 1
    current_time_spent_s = { "A": 2 }
    target_alloc = { "A": 1, "B": 1 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": { "B": 1.0 }, "min_required_time_s": 2 }

    # Case 2
    current_time_spent_s = { "C": 8, "D": 2 }
    target_alloc = { "C": 9, "D": 1 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": { "C": 1.0 }, "min_required_time_s": 10 }

    # Case 3
    current_time_spent_s = { "A": 3, "B": 2, "C": 5 }
    target_alloc = { "A": 0.2, "B": 0.4, "C": 0.4 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": { "B": 0.8, "C": 0.2 }, "min_required_time_s": 5 }

    # Case 4
    current_time_spent_s = { "C": 8, "D": 2 }
    target_alloc = { "C": 0.9, "D": 0.1 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": { "C": 1.0 }, "min_required_time_s": 10 }

    # Case 5
    current_time_spent_s = { "A": 1, "B": 2, "C": 3 }
    target_alloc = { "B": 0.25, "C": 0.75 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": { "C": 1.0 }, "min_required_time_s": 3 }

    # ==================== No past activities ====================
    current_time_spent_s = {}
    target_alloc = { "C": 0.5, "D": 0.5 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": target_alloc }

    current_time_spent_s = None
    target_alloc = { "C": 0.5, "D": 0.5 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": target_alloc }

    # ==================== No relevant past activities ====================
    current_time_spent_s = { "A": 2 }
    target_alloc = { "C": 0.5, "D": 0.5 }
    future = calculate_action(current_time_spent_s, target_alloc)
    assert future == { "allocation": target_alloc }
