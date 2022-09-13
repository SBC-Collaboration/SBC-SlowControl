# import daemon
# import time
#
# def do_something():
#     i = 0
#     while i<=2:
#         with open("/home/hep/Downloads/current_time.txt", "w") as f:
#         # with open("~/Downloads//current_time.txt", "w") as f:
#             f.write("The time is now " + time.ctime())
#         # print(1)
#         time.sleep(5)
#         i += 1
#
# def run():
#     # do_something()
#     try:
#         # with daemon.DaemonContext(working_directory="/home/hep/Downloads/"):
#         with daemon.DaemonContext():
#             do_something()
#     except Exception as e:
#         print(e)
#
# if __name__ == "__main__":
#     run()

import os
import json
import requests
import pandas as pd
from datetime import datetime


def fetch(url: str) -> list:
    res = requests.get(url)
    return json.loads(res.content)


def process(users: list) -> pd.DataFrame:
    processed = []
    for user in users:
        processed.append({
            'ID': user['id'],
            'Name': user['name'],
            'Username': user['username'],
            'Email': user['email'],
            'Phone': user['phone'],
            'Company': user['company']['name']
        })
    return pd.DataFrame(processed)


def save(users: pd.DataFrame, path: str) -> None:
    users.to_csv(path, index=False)


if __name__ == '__main__':
    users = fetch(url='https://jsonplaceholder.typicode.com/users')
    users = process(users=users)
    curr_timestamp = int(datetime.timestamp(datetime.now()))
    path = os.path.abspath(f'/home/hep/Documents/cron-tutorial/output/users_{curr_timestamp}.csv')
    save(users=users, path=path)