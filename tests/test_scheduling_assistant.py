import pytest
import subprocess
import os
import json
from typing import Dict, List
from random import shuffle
from faker.providers.lorem.en_US import Provider

from action_calculation import calculate_action


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


def random_json_file_names(tmp_path, faker, count) -> List[str]:
    random_words = list(set(Provider.word_list))
    shuffle(random_words)

    return [tmp_path / str(w + ".json") for w in random_words[0:count]]


def test_script_incomplete_args(tmp_path, faker) -> None:
    history_file = random_json_file_names(tmp_path, faker, 1)[0]

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

    # Incomplete arguments
    cmd = "python action_calculation.py --history \"{0}\""
    exit_status = os.system(cmd.format(history_file))
    assert exit_status != 0
    

def test_script_complete_args(tmp_path, faker) -> None:
    history_file, target_alloc_file, action_output_file = random_json_file_names(tmp_path, faker, 3)

    current_time_spent_s = { "A": 2 }
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(current_time_spent_s, f, ensure_ascii=False, indent=4)

    target_alloc = { "A": 1, "B": 1 }
    with open(target_alloc_file, 'w', encoding='utf-8') as f:
        json.dump(target_alloc, f, ensure_ascii=False, indent=4)

    # Complete arguments
    cmd = "python action_calculation.py --history \"{0}\" --target \"{1}\"".format(history_file, target_alloc_file)
    exit_status = os.system(cmd)
    assert exit_status == 0

    # With output file
    cmd += " --output \"{0}\"".format(action_output_file)
    exit_status = os.system(cmd)
    assert exit_status == 0

    # Check output file
    assert os.path.exists(action_output_file)

    with open(action_output_file, 'r') as f:
        action = json.load(f)

    assert action == { "allocation": { "B": 1.0 }, "min_required_time_s": 2 }
