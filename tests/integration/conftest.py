# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import logging
from pathlib import Path

import yaml
from pytest import fixture
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@fixture(scope="module")
async def zinc_charm(request, ops_test: OpsTest):
    """Zinc charm used for integration testing."""
    charm_file = request.config.getoption("--charm-path")
    if charm_file:
        return charm_file

    charm = await ops_test.build_charm(".")
    return charm


@fixture(scope="module")
def zinc_oci_image(ops_test: OpsTest):
    meta = yaml.safe_load(Path("./charmcraft.yaml").read_text())
    return meta["resources"]["zinc-image"]["upstream-source"]
