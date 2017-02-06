#!/usr/bin/env python

from __future__ import print_function
import requests
import json
import time
import datetime
import argparse
import csv
import os.path
import sys

URL = ''
NAME = ''
PASSWORD = ''

TIME_OFFSET = 3600
HOUR_IN_MS = 28800000
TMP_FILE_PATH = '/tmp/super_duper_delta_script_9000'


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
    global HOUR_IN_MS
    global URL

    headers = {
        'Content-Type': 'application/json;charset=utf-8',
        'authToken': token
    }
    unix_time = int(round(time.time()) * 1000)

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

    code_list = []
    for elem in summary_records:
        # get highest code

        code_list.append(int(elem['code']))

    for elem in summary_records:
        if int(elem['code']) == max(code_list):
            worked_today = elem['duration']

    worked_until_now = worked_time_from_work_fund
    fund_until_now = actual_work_fund
    a = fund_until_now - HOUR_IN_MS
    b = worked_until_now - worked_today
    monthly_delta = b - a
    current_delta = duration * -1

    return current_delta, monthly_delta


def print_delta(message='', delta=''):
    print(message, end='')
    if delta < 0:
        print('\033[91m-', end='')
    else:
        print('\033[92m', end='')
    print(datetime.timedelta(milliseconds=abs(delta)), end='')
    print('\033[0m')


def print_delta_i3(delta):
    if delta < 0:
        print('-', end='')
    print(datetime.timedelta(milliseconds=abs(delta)))


def print_time_to_go_home(current_delta):
    global TIME_OFFSET
    time_to_go_home = round(time.time()) - (current_delta / 1000)

    time_to_go_home += TIME_OFFSET
    print()

    print('   Current time: ', end='')
    print(datetime.datetime.fromtimestamp(round(time.time() + TIME_OFFSET)))

    print('Time to go home: ', end='')
    print('\033[93m', end='')
    print(str(datetime.datetime.fromtimestamp(round(time_to_go_home))), end='')
    print('\033[0m')


def get_delta_from_csv():
    global TMP_FILE_PATH

    with open(TMP_FILE_PATH, 'r') as tmp_file:
        reader = csv.DictReader(tmp_file)
        for row in reader:
            delta_delta = int(abs(int(row['timestamp'])-int(time.time())))
            current_delta = round(int(row['current_delta']) + delta_delta*1000)
            monthly_delta = int(row['monthly_delta'])

    return current_delta, monthly_delta


def update_csv(current_delta, monthly_delta):
    global TMP_FILE_PATH

    with open(TMP_FILE_PATH, 'w') as tmp_file:
        fieldnames = ['timestamp', 'current_delta', 'monthly_delta']
        writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
        writer.writeheader()

        writer.writerow({
            'timestamp': int(round(time.time())),
            'current_delta': int(round(current_delta)),
            'monthly_delta': int(round(monthly_delta))
        })


def should_update():
    global TMP_FILE_PATH
    result = True

    with open(TMP_FILE_PATH, 'r') as tmp_file:
        reader = csv.DictReader(tmp_file)
        for row in reader:
            timestamp = row['timestamp']
            if round(abs(time.time()) - int(timestamp)) < 3600:
                result = False

    return result


def main():
    global TMP_FILE_PATH
    global URL
    global NAME
    global PASSWORD
    parser = argparse.ArgumentParser(description='Short sample app')
    parser.add_argument('--i3', action="store_true", default=False,
                        help='show only current delta, good for i3status')
    parser.add_argument('--force', action="store_true", default=False,
                        help='force new tmp file and update from server')
    args = parser.parse_args()
    dirname = os.path.dirname(sys.argv[0])
    print(dirname)

    if os.path.isfile(dirname+'/config.json'):
        with open(dirname+'/config.json', 'r') as config:
            data = json.load(config)
            URL = data['url']
            NAME = data['name']
            PASSWORD = data['password']

    # check if file exist
    if args.force or not os.path.isfile(TMP_FILE_PATH):
        # init file
        with open(TMP_FILE_PATH, 'w') as tmp_file:
            fieldnames = ['timestamp', 'current_delta', 'monthly_delta']
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                'timestamp': 0,
                'current_delta': 0,
                'monthly_delta': 0,
            })

    if args.force or should_update():
        token = get_token()
        current_delta, monthly_delta = get_deltas(token=token)
        update_csv(current_delta, monthly_delta)
    else:
        current_delta, monthly_delta = get_delta_from_csv()

    if not args.i3:
        print_delta(message='  Delta (Month): ', delta=monthly_delta)
        print_delta(message='Delta (Current): ', delta=current_delta)
        print_time_to_go_home(current_delta=current_delta)
    else:
        print_delta_i3(delta=current_delta)


if __name__ == "__main__":
    main()
