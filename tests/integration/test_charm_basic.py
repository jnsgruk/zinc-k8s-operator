#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import base64
import gzip
import re

import requests
import sh
from pytest import mark

from . import ZINC
from .juju import juju, retry, run_action, status, wait_for_idle


def _get_password() -> str:
    result = run_action(f"{ZINC}/0", "get-admin-password")
    return str(result["admin-password"])


@mark.abort_on_fail
def test_deploy(zinc_charm, zinc_oci_image):
    print(sh.ls("-la", zinc_charm))
    juju("deploy", zinc_charm, ZINC, "--resource", f"zinc-image={zinc_oci_image}")
    wait_for_idle([ZINC])


@mark.abort_on_fail
@retry(retry_num=10, retry_sleep_sec=3)
def test_application_is_up():
    address = status()["applications"][ZINC]["address"]
    response = requests.get(f"http://{address}:4080/version")
    return response.status_code == 200


@mark.abort_on_fail
def test_get_admin_password_action():
    password = _get_password()
    assert re.match("[A-Za-z0-9-_]{24}", password)


@mark.abort_on_fail
@retry(retry_num=5, retry_sleep_sec=3)
def test_can_auth_with_zinc():
    # Now try to actually hit the service
    address = status()["applications"][ZINC]["address"]

    # Load sample data from quickstart docs
    # https://github.com/zinclabs/zincsearch-docs/blob/beca3d17e7d3da15cbf5abfffefffdcbb833758d/docs/quickstart.md?plain=1#L114
    with gzip.open("./tests/integration/olympics.ndjson.gz", "r") as f:
        data = f.read()

    # Encode the credentials for the API using the password from the charm action
    password = _get_password()
    creds = base64.b64encode(bytes(f"admin:{password}", "utf-8")).decode("utf-8")

    # Bulk ingest some data
    res = requests.post(
        url=f"http://{address}:4080/api/_bulk",
        headers={"Content-type": "application/json", "Authorization": f"Basic {creds}"},
        data=data,
    )

    results = res.json()

    assert res.status_code == 200
    assert results["message"] == "bulk data inserted"
    assert results["record_count"] == 36935
