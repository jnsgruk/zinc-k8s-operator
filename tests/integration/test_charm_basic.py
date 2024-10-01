#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import base64
import gzip
import json
from urllib.request import Request, urlopen

from . import ZINC, retry
from .juju import Juju


def _get_password() -> str:
    result = Juju.cli("list-secrets", "--format", "json")
    secrets = json.loads(result.stdout)
    secret_name = next(k for k, v in secrets.items() if v["owner"] == ZINC)

    result = Juju.cli("show-secret", secret_name, "--format", "json", "--reveal")
    secret = json.loads(result.stdout)

    return secret[secret_name]["content"]["Data"]["password"]


def test_deploy(zinc_charm, zinc_oci_image):
    Juju.deploy(zinc_charm, alias=ZINC, resources={"zinc-image": zinc_oci_image})
    Juju.wait_for_idle([ZINC], timeout=1000)


@retry(retry_num=10, retry_sleep_sec=3)
def test_application_is_up():
    address = Juju.status()["applications"][ZINC]["address"]
    response = urlopen(f"http://{address}:4080/version")

    assert response.status == 200


@retry(retry_num=10, retry_sleep_sec=3)
def test_can_auth_with_zinc():
    # Now try to actually hit the service
    address = Juju.status()["applications"][ZINC]["address"]

    # Load sample data from quickstart docs
    # https://github.com/zinclabs/zincsearch-docs/blob/beca3d17e7d3da15cbf5abfffefffdcbb833758d/docs/quickstart.md?plain=1#L114
    with gzip.open("./tests/integration/olympics.ndjson.gz", "r") as f:
        data = f.read()

    # Encode the credentials for the API using the password from the charm action
    password = _get_password()
    creds = base64.b64encode(bytes(f"admin:{password}", "utf-8")).decode("utf-8")

    # Bulk ingest some data
    req = Request(f"http://{address}:4080/api/_bulk")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Basic {creds}")

    response = urlopen(req, data)
    response_data = json.loads(response.read())

    assert response.status == 200
    assert response_data["message"] == "bulk data inserted"
    assert response_data["record_count"] == 36935
