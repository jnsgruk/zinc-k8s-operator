# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import logging
from pathlib import Path

import yaml
from pytest import fixture
from pytest_operator.plugin import OpsTest

from . import ZINC

logger = logging.getLogger(__name__)


@fixture(scope="module")
async def zinc_deploy_kwargs(ops_test: OpsTest, request):
    zinc_metadata = yaml.safe_load(Path("./metadata.yaml").read_text())
    zinc_channel = request.config.getoption("channel", default=None)
    # Set some deploy args that are consistent irrespective of charm src
    args = {"application_name": ZINC, "trust": True}

    if zinc_channel is None:
        charm_path = await ops_test.build_charm(".")
        zinc_oci_image = zinc_metadata["resources"]["zinc-image"]["upstream-source"]
        args.update({"entity_url": charm_path, "resources": {"zinc-image": zinc_oci_image}})
    else:
        logger.info("Deploying zinc from charmhub with channel %s", zinc_channel)
        args.update({"entity_url": "zinc-k8s", "channel": zinc_channel})

    return args
