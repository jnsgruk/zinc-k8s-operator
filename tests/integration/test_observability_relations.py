#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import logging

from pytest import mark

logger = logging.getLogger(__name__)

ZINC = "zinc-k8s"
O11Y_CHARMS = ["prometheus-k8s", "grafana-k8s", "loki-k8s"]
O11Y_RELS = ["metrics-endpoint", "grafana-dashboard", "logging"]
ALL_CHARMS = [ZINC, *O11Y_CHARMS]


@mark.abort_on_fail
async def test_deploy_charms(ops_test, zinc_charm, zinc_oci_image):
    await asyncio.gather(
        ops_test.model.deploy(zinc_charm, resources={"zinc-image": zinc_oci_image}, trust=True),
        ops_test.model.deploy("prometheus-k8s", channel="edge", trust=True),
        ops_test.model.deploy("loki-k8s", channel="edge", trust=True),
        ops_test.model.deploy("grafana-k8s", channel="edge", trust=True),
        ops_test.model.wait_for_idle(apps=ALL_CHARMS, status="active", timeout=1000),
    )


@mark.abort_on_fail
@mark.parametrize("remote", O11Y_CHARMS)
async def test_create_relation(ops_test, remote):
    # Create the relation
    await ops_test.model.add_relation(ZINC, remote)
    # Wait for the two apps to quiesce
    await ops_test.model.wait_for_idle(apps=[ZINC, remote], status="active", timeout=1000)


@mark.abort_on_fail
@mark.parametrize("endpoint,remote_app", list(zip(O11Y_RELS, O11Y_CHARMS)))
async def test_remove_relation(ops_test, endpoint, remote_app):
    # Remove the relation
    await ops_test.model.applications[ZINC].remove_relation(endpoint, remote_app)
    # Wait for the two apps to quiesce
    await ops_test.model.wait_for_idle(apps=[ZINC], status="active", timeout=1000)
