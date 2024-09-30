#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


from pytest import mark

from . import ZINC
from .juju import Juju

O11Y_CHARMS = ["prometheus-k8s", "grafana-k8s", "loki-k8s", "parca-k8s"]
O11Y_RELS = ["metrics-endpoint", "grafana-dashboard", "log-proxy", "profiling-endpoint"]
ALL_CHARMS = [ZINC, *O11Y_CHARMS]


def test_deploy_charms(zinc_charm, zinc_oci_image):
    Juju.deploy(zinc_charm, alias=ZINC, resources={"zinc-image": zinc_oci_image})

    for charm in O11Y_CHARMS:
        Juju.deploy(charm, trust=True)

    Juju.wait_for_idle(ALL_CHARMS, timeout=1000)


@mark.parametrize("endpoint,remote", list(zip(O11Y_RELS, O11Y_CHARMS)))
def test_create_relation(endpoint, remote):
    # Create the relation
    Juju.integrate(f"{ZINC}:{endpoint}", remote)
    # Wait for the two apps to quiesce
    Juju.wait_for_idle([ZINC, remote], timeout=1000)


@mark.parametrize("endpoint,remote", list(zip(O11Y_RELS, O11Y_CHARMS)))
def test_remove_relation(endpoint, remote):
    # Remove the relation
    Juju.cli("remove-relation", f"{ZINC}:{endpoint}", remote)
    # Wait for the two apps to quiesce
    Juju.wait_for_idle([ZINC, remote], timeout=1000)
