#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import asyncio
import base64
import gzip
import re

import requests
from lightkube.core.client import Client
from lightkube.resources.core_v1 import Service
from pytest import mark
from pytest_operator.plugin import OpsTest
from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential as wexp

from . import ZINC


async def _get_password(ops_test: OpsTest) -> str:
    unit = ops_test.model.applications[ZINC].units[0]
    action = await unit.run_action("get-admin-password")
    await action.wait()
    result = await ops_test.model.get_action_output(action.id)
    return result["admin-password"]


@mark.abort_on_fail
async def test_deploy(ops_test: OpsTest, zinc_deploy_kwargs):
    await asyncio.gather(
        ops_test.model.deploy(**await zinc_deploy_kwargs),
        ops_test.model.wait_for_idle(apps=[ZINC], status="active", timeout=1000),
    )


@mark.abort_on_fail
@retry(wait=wexp(multiplier=2, min=1, max=30), stop=stop_after_attempt(10), reraise=True)
async def test_application_is_up(ops_test: OpsTest):
    status = await ops_test.model.get_status()  # noqa: F821
    address = status["applications"][ZINC]["public-address"]
    response = requests.get(f"http://{address}:4080/version")
    return response.status_code == 200


@retry(wait=wexp(multiplier=2, min=1, max=30), stop=stop_after_attempt(10), reraise=True)
async def test_application_service_port_patch(ops_test: OpsTest):
    # Check the port has actually been patched
    client = Client()
    svc = client.get(Service, name=ZINC, namespace=ops_test.model_name)
    assert svc.spec.ports[0].port == 4080


@mark.abort_on_fail
async def test_get_admin_password_action(ops_test: OpsTest):
    password = await _get_password(ops_test)
    assert re.match("[A-Za-z0-9]{24}", password)


@retry(wait=wexp(multiplier=2, min=1, max=30), stop=stop_after_attempt(10), reraise=True)
async def test_can_auth_with_zinc(ops_test: OpsTest):
    # Now try to actually hit the service
    status = await ops_test.model.get_status()  # noqa: F821
    address = status["applications"][ZINC]["public-address"]

    # Load sample data from quickstart docs
    # https://github.com/zinclabs/zincsearch-docs/blob/beca3d17e7d3da15cbf5abfffefffdcbb833758d/docs/quickstart.md?plain=1#L114
    with gzip.open("./tests/integration/olympics.ndjson.gz", "r") as f:
        data = f.read()

    # Encode the credentials for the API using the password from the charm action
    password = await _get_password(ops_test)
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
