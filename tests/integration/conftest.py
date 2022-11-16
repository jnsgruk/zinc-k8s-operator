# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import logging
from pathlib import Path

import yaml
from pytest import fixture
from pytest_operator.plugin import OpsTest

from .. import ZINC

logger = logging.getLogger(__name__)


@fixture(scope="module")
async def zinc_deploy_kwargs(ops_test: OpsTest, request):
    zinc_metadata = yaml.safe_load(Path("./metadata.yaml").read_text())
    zinc_channel = request.config.getoption("channel", default=None)
    build_from_source = zinc_channel is None
    if build_from_source:
        charm_path = await ops_test.build_charm(".")
        zinc_oci_image = zinc_metadata["resources"]["zinc-image"]["upstream-source"]
        return {
            "entity_url": charm_path,
            "application_name": ZINC,
            "resources": {"zinc-image": zinc_oci_image},
            "trust": True,
        }
    else:
        logger.info(f"Using zinc from charmhub with channel {zinc_channel}")
        return {
            "entity_url": "ch:zinc-k8s",
            "application_name": ZINC,
            "channel": zinc_channel,
            "trust": True,
        }
