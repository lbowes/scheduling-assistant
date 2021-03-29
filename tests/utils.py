import json
from os.path import join, dirname
from typing import Dict
from action_calculation import load_target_activity_allocation, load_activity_history


def get_json_test_data_file_path(name: str) -> str:
    file_name = join("data", name + ".json")
    return join(dirname(__file__), file_name)


def load_test_target_activities(allocation_name: str) -> Dict[str, any]:
    """Utility function for loading a test set of activity allocation targets from a file"""
    file_path = get_json_test_data_file_path(allocation_name)
    return load_target_activity_allocation(file_path)


def load_test_activity_history(history_name: str) -> Dict[str, any]:
    """Utility function for loading a test set of activity allocation targets from a file"""
    file_path = get_json_test_data_file_path(history_name)
    return load_activity_history(file_path)
