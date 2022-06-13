# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import logging

import pytest
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
async def zinc_charm(ops_test: OpsTest):
    """Zinc charm used for integration testing."""
    charm = await ops_test.build_charm(".")
    return charm
