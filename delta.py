#!/usr/bin/env python

from __future__ import print_function
import requests
import json
import time
import datetime
import argparse

URL = ''
NAME = ''
PASSWORD = ''

TIME_OFFSET = 3600
HOUR_IN_MS = 28800000
CURRENT_TIME = round(time.time())


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_token():
    global NAME
    global PASSWORD
    global URL

    headers = {
        'Content-Type': 'application/json;charset=utf-8',
        'Connection': 'keep-alive'
    }

    params = json.dumps({
        'username': NAME,
        'password': list(PASSWORD),
        'companyId': 1,
        'roleCode': 'EMP',
    })

    url = URL + '/cxf/accounts/login'

    r = requests.post(
        url=url,
        headers=headers,
        data=params,
    )

    token = json.loads(r.text)['authToken']
    return token

def get_deltas(token):
    global CURRENT_TIME
    global HOUR_IN_MS
    global URL

    headers = {
        'Content-Type': 'application/json;charset=utf-8',
        'authToken': token
    }
    unix_time = int(CURRENT_TIME * 1000)

    url = URL + '/cxf/attendance/person/work-fund-state'

    r = requests.post(
        url=url,
        headers=headers,
        data=str(unix_time),
    )

    worked_time_from_work_fund = json.loads(r.text)['workedTimeFromWorkFund']
    actual_work_fund = json.loads(r.text)['actualWorkFund']
    summary_records = json.loads(r.text)['summaryRecords']
    duration = json.loads(r.text)['difference']

    for elem in summary_records:
        if elem['code'] == '108':
            worked_today = elem['duration']

    worked_until_now = worked_time_from_work_fund
    fund_until_now = actual_work_fund
    a = fund_until_now - HOUR_IN_MS
    b = worked_until_now - worked_today
    monthly_delta = b-a
    current_delta = duration * -1

    return current_delta, monthly_delta

def print_delta(message='', delta=''):
    print(message, end='')
    if delta < 0:
        print('-', end='')
    print(datetime.timedelta(milliseconds=abs(delta)))

def print_time_to_go_home(current_delta):
    global CURRENT_TIME
    global TIME_OFFSET
    time_to_go_home = CURRENT_TIME - (current_delta/1000)

    time_to_go_home += TIME_OFFSET

    print('Current time: ', end='')
    print(datetime.datetime.fromtimestamp(round(CURRENT_TIME+TIME_OFFSET)))

    print('Time to go home: ', end='')
    print(str(datetime.datetime.fromtimestamp(round(time_to_go_home))))

def main():
    parser = argparse.ArgumentParser(description='Short sample app')

    parser.add_argument('--i3', action="store_true", default=False)

    args = parser.parse_args()

    token = get_token()
    current_delta, monthly_delta = get_deltas(token=token)

    if not args.i3:
        print_delta(message='Delta (Month): ', delta=monthly_delta)
        print_delta(message='Delta (Current): ', delta=current_delta)
        print_time_to_go_home(current_delta=current_delta)
    else:
        print_delta(delta=current_delta)

if __name__ == "__main__":
    main()

