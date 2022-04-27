#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import base64
import json
import logging
import re
from pathlib import Path

import pytest
import requests
import tenacity
import yaml
from lightkube.core.client import Client
from lightkube.resources.core_v1 import Service
from pytest_operator.plugin import OpsTest
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]


async def _get_password(ops_test: OpsTest) -> str:
    unit = ops_test.model.applications[APP_NAME].units[0]
    action = await unit.run_action("get-admin-password")
    action = await action.wait()
    return action.results["admin-password"]


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # build and deploy charm from local source folder
    charm = await ops_test.build_charm(".")
    resources = {"zinc-image": METADATA["resources"]["zinc-image"]["upstream-source"]}
    await ops_test.model.deploy(charm, resources=resources, application_name=APP_NAME)

    # issuing dummy update_status just to trigger an event
    await ops_test.model.set_config({"update-status-hook-interval": "10s"})

    await ops_test.model.wait_for_idle(apps=[APP_NAME], status="active", timeout=1000)
    assert ops_test.model.applications[APP_NAME].units[0].workload_status == "active"

    # effectively disable the update status from firing
    await ops_test.model.set_config({"update-status-hook-interval": "60m"})


@pytest.mark.abort_on_fail
async def test_application_is_up(ops_test: OpsTest):
    status = await ops_test.model.get_status()  # noqa: F821
    address = status["applications"][APP_NAME]["units"][f"{APP_NAME}/0"]["address"]

    url = f"http://{address}:4080"

    logger.info("querying unit address: %s", url)
    response = requests.get(url)
    assert response.status_code == 200


@pytest.mark.abort_on_fail
async def test_get_admin_password_action(ops_test: OpsTest):
    password = await _get_password(ops_test)
    assert re.match("[A-Za-z0-9]{24}", password)


@tenacity.retry(
    wait=wait_exponential(multiplier=2, min=1, max=30),
    stop=stop_after_attempt(10),
    reraise=True,
)
async def test_application_service_port_patch(ops_test: OpsTest):
    # Check the port has actually been patched
    client = Client()
    svc = client.get(Service, name=APP_NAME, namespace=ops_test.model_name)
    assert svc.spec.ports[0].port == 4080

    # Now try to actually hit the service
    status = await ops_test.model.get_status()  # noqa: F821
    address = status["applications"][APP_NAME].public_address

    url = f"http://{address}:4080"

    logger.info("querying app address: %s", url)
    response = requests.get(url)
    assert response.status_code == 200


async def test_can_auth_with_zinc(ops_test: OpsTest):
    # Now try to actually hit the service
    status = await ops_test.model.get_status()  # noqa: F821
    address = status["applications"][APP_NAME].public_address

    # Some data to populate
    data = {
        "Athlete": "DEMTSCHENKO, Albert",
        "City": "Turin",
        "Country": "RUS",
        "Discipline": "Luge",
        "Event": "Singles",
        "Gender": "Men",
        "Medal": "Silver",
        "Season": "winter",
        "Sport": "Luge",
        "Year": 2006,
    }

    # Encode the credentials for the API using the password from the charm action
    password = await _get_password(ops_test)
    creds = base64.b64encode(bytes(f"admin:{password}", "utf-8")).decode("utf-8")

    # We're going to send some data to the "games" index
    res = requests.put(
        url=f"http://{address}:4080/api/games/document",
        headers={"Content-type": "application/json", "Authorization": f"Basic {creds}"},
        data=json.dumps(data),
    )

    results = res.json()
    assert res.status_code == 200
    assert "id" in results.keys()

    logger.info("successfully queried the Zinc API, got response: '%s'", str(res.json()))
