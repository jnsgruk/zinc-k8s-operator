#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import functools
import json
import logging
import time

import sh


def retry(retry_num, retry_sleep_sec):
    def decorator(func):
        # preserve information about the original function, or the func name will be "wrapper" not "func"
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retry_num):
                try:
                    return func(*args, **kwargs)  # should return the raw function's return value
                except Exception:
                    time.sleep(retry_sleep_sec)
            logging.error("func %s retry failed", func)
            raise Exception("Exceed max retry num: {} failed".format(retry_num))

        return wrapper

    return decorator


def juju(*args):
    return sh.juju(*args, _env={"NO_COLOR": "true"})


def status() -> dict:
    s = juju("status", "--format", "json")
    return json.loads(s)


def run_action(unit, action) -> dict:
    action = juju("run", "--format=json", unit, action)
    result = json.loads(action)
    return result[unit]["results"]


def _unit_statuses(application: str):
    units = status()["applications"][application]["units"]
    return [
        f"{units[u]['workload-status']['current']}/{units[u]['juju-status']['current']}"
        for u in units
    ]


@retry(retry_num=24, retry_sleep_sec=5)
def wait_for_idle(applications):
    results = []
    for a in applications:
        results.extend(_unit_statuses(a))

    if set(results) != {"active/idle"}:
        raise Exception
