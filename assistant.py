import requests
from typing import Dict
from datetime import datetime
from requests.auth import HTTPBasicAuth

from action_calculation import calculate_action
from secrets import workspace_id, api_token


# https://github.com/ynop/togglore/blob/master/togglore/toggl.py
def time_entries(start: datetime, end: datetime):
    entries = []

    headers = {'content-type': 'application/json'}

    total = 1
    per_page = 0
    page = 0

    while page * per_page < total:
        page += 1

        url = 'https://toggl.com/reports/api/v2/details?workspace_id={}&since={}&until={}&user_agent=_&page={}'.format(
            workspace_id,
            start,
            end,
            page)

        response = requests.get(url, headers=headers, auth=HTTPBasicAuth(api_token, 'api_token')).json()

        total = response['total_count']
        per_page = response['per_page']

        for time in response['data']:
            entries.append(time)

    return entries


def extract_current_time_spent_from_toggl() -> Dict[str, int]:
    entries = time_entries(datetime(2021, 1, 1), datetime.now())

    for e in entries:
        print("name: " + e.get('description') + " duration: " + str(int(e.get('dur')) / 1000))

    # todo: convert time entries into an allocation


if __name__ == '__main__':
    # todo: get this from toggl
    current_time_spent_s = extract_current_time_spent_from_toggl()

    # todo: this should still come from a file
    target_alloc_points = {}

    action = calculate_action(current_time_spent_s, target_alloc_points)
    print("action: " + str(action))
