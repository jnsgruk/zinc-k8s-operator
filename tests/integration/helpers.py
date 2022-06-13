# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import requests
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


async def zinc_is_up(ops_test: OpsTest, app_name="zinc-k8s"):
    address = await get_unit_ip(ops_test, app_name)
    response = requests.get(f"http://{address}:4080/version")
    return response.status_code == 200


async def get_unit_ip(ops_test: OpsTest, app_name, unit=0):
    status = await ops_test.model.get_status()  # noqa: F821
    return status["applications"][app_name]["units"][f"{app_name}/{unit}"]["address"]


async def unit_data(ops_test, unit_name, endpoint=None):
    if endpoint is None:
        raw_data = (await ops_test.juju("show-unit", unit_name))[1]
    else:
        raw_data = (await ops_test.juju("show-unit", unit_name, "--endpoint", "metrics-endpoint"))[
            1
        ]

    if not raw_data:
        raise ValueError(f"no unit info could be grabbed for {unit_name}")
    data = yaml.safe_load(raw_data)

    app_data = data[unit_name]["relation-info"][0]["application-data"]
    related_unit_data = data[unit_name]["relation-info"][0]["related-units"]

    return app_data, related_unit_data
