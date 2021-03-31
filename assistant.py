import requests
from typing import Dict, List
from datetime import datetime
from requests.auth import HTTPBasicAuth

from action_calculation import calculate_action
from secrets import workspace_id, api_token


HEADERS = {'content-type': 'application/json'}


# https://github.com/ynop/togglore/blob/master/togglore/toggl.py
def get_toggl_time_entries_since(reference_point: datetime) -> List[Dict[str, any]]:
    entries = []

    total = 1
    per_page = 0
    page = 0

    while page * per_page < total:
        page += 1

        url = 'https://toggl.com/reports/api/v2/details?workspace_id={}&since={}&until={}&user_agent=_&page={}'.format(
            workspace_id,
            reference_point,
            datetime.now(),
            page)

        response = requests.get(url, headers=HEADERS, auth=HTTPBasicAuth(api_token, 'api_token')).json()

        total = response['total_count']
        per_page = response['per_page']

        for time in response['data']:
            entries.append(time)

    return entries


PROJECTS = {}


def get_toggl_project_name(project_id: int) -> Dict[str, any]:
    name = PROJECTS.get(project_id)

    if not name:
        url = "https://api.track.toggl.com/api/v8/projects/{0}".format(project_id)
        response = requests.get(url, headers=HEADERS, auth=HTTPBasicAuth(api_token, 'api_token')).json()

        name = response['data']['name']
        PROJECTS[project_id] = name

    return name


def extract_current_time_spent_from_toggl() -> Dict[str, int]:
    time_spent_s = {}

    for e in get_toggl_time_entries_since(datetime(2021, 1, 1)):
        duration_s = seconds=int(e['dur'] / 1000)
        project_id = e['pid']

        if project_id:
            project_name = get_toggl_project_name(project_id)

            time_spent_s[project_name] = time_spent_s.get(project_name, 0) + duration_s

    return time_spent_s
    

if __name__ == '__main__':
    current_time_spent_s = extract_current_time_spent_from_toggl()

    # todo: this should still come from a file
    target_alloc_points = {
        "A": 1,
        "B": 1
    }

    action = calculate_action(current_time_spent_s, target_alloc_points)
    print("action: " + str(action))
