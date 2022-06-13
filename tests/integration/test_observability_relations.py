#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import json
import logging
from pathlib import Path

import pytest
import yaml

from tests.integration.helpers import unit_data, zinc_is_up

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
ZINC_NAME = "zinc"
PROMETHEUS_NAME = "prometheus"
LOKI_NAME = "loki"
GRAFANA_NAME = "grafana"


@pytest.mark.abort_on_fail
async def test_prometheus_scrape_create_relation(ops_test, zinc_charm):
    """Test that Zinc can be related with Prometheus over prometheus_scrape."""
    zinc_resources = {"zinc-image": METADATA["resources"]["zinc-image"]["upstream-source"]}
    await asyncio.gather(
        ops_test.model.deploy(zinc_charm, resources=zinc_resources, application_name=ZINC_NAME),
        ops_test.model.deploy("prometheus-k8s", channel="edge", application_name=PROMETHEUS_NAME),
    )
    apps = [ZINC_NAME, PROMETHEUS_NAME]
    # Wait for the deployments to settle
    await ops_test.model.wait_for_idle(apps=apps, status="active")
    # Check that the zinc API is up
    assert await zinc_is_up(ops_test, ZINC_NAME) is True
    # Crete the relation
    await ops_test.model.add_relation(ZINC_NAME, PROMETHEUS_NAME)
    # Wait for the two apps to quiesce
    await ops_test.model.wait_for_idle(apps=apps, status="active")


@pytest.mark.abort_on_fail
async def test_loki_push_api_create_relation(ops_test, _):
    """Test that Zinc can be related with Loki."""
    # Deploy Loki
    await ops_test.model.deploy("loki-k8s", channel="edge", application_name=LOKI_NAME)

    apps = [ZINC_NAME, LOKI_NAME]
    # Wait for the deployments to settle
    await ops_test.model.wait_for_idle(apps=apps, status="active")
    # Check that the zinc API is up
    assert await zinc_is_up(ops_test, ZINC_NAME) is True
    # Crete the relation
    await ops_test.model.add_relation(ZINC_NAME, LOKI_NAME)
    # Wait for the two apps to quiesce
    await ops_test.model.wait_for_idle(apps=apps, status="active")


@pytest.mark.abort_on_fail
async def test_grafana_dashboard_create_relation(ops_test, _):
    """Test that Zinc can be related with Grafana."""
    # Deploy Grafana
    await ops_test.model.deploy("grafana-k8s", channel="edge", application_name=GRAFANA_NAME)

    apps = [ZINC_NAME, GRAFANA_NAME]
    # Wait for the deployments to settle
    await ops_test.model.wait_for_idle(apps=apps, status="active")
    # Check that the zinc API is up
    assert await zinc_is_up(ops_test, ZINC_NAME) is True
    # Crete the relation
    await ops_test.model.add_relation(ZINC_NAME, GRAFANA_NAME)
    # Wait for the two apps to quiesce
    await ops_test.model.wait_for_idle(apps=apps, status="active")


@pytest.mark.abort_on_fail
async def test_prometheus_scrape_relation_data(ops_test, _):
    app_data, related_unit_data = await unit_data(
        ops_test, f"{PROMETHEUS_NAME}/0", "metrics-endpoint"
    )
    zinc_unit_data = related_unit_data[f"{ZINC_NAME}/0"]["data"]
    scrape_meta = json.loads(app_data["scrape_metadata"])

    assert (
        app_data["scrape_jobs"]
        == '[{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:4080"]}]}]'
    )

    assert scrape_meta["application"] == ZINC_NAME
    assert scrape_meta["unit"] == f"{ZINC_NAME}/0"
    assert scrape_meta["charm_name"] == METADATA["name"]

    assert zinc_unit_data["prometheus_scrape_unit_name"] == f"{ZINC_NAME}/0"
