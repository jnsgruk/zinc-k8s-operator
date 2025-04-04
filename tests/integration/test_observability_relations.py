#!/usr/bin/env python3
# Copyright 2024 Jon Seager (@jnsgruk)
# See LICENSE file for licensing details.


import jubilant
from pytest import mark

from . import ZINC

O11Y_CHARMS = ["prometheus-k8s", "grafana-k8s", "loki-k8s", "parca-k8s"]
O11Y_RELS = ["metrics-endpoint", "grafana-dashboard", "log-proxy", "profiling-endpoint"]
ALL_CHARMS = [ZINC, *O11Y_CHARMS]


def test_deploy_charms(juju: jubilant.Juju, zinc_charm, zinc_oci_image):
    juju.deploy(zinc_charm, app=ZINC, resources={"zinc-image": zinc_oci_image})

    for charm in O11Y_CHARMS:
        juju.deploy(charm, trust=True)

    juju.wait(jubilant.all_active, timeout=1000)


@mark.parametrize("endpoint,remote", list(zip(O11Y_RELS, O11Y_CHARMS)))
def test_create_relation(juju: jubilant.Juju, endpoint, remote):
    # Create the relation
    juju.integrate(f"{ZINC}:{endpoint}", remote)
    # Wait for the two apps to quiesce
    juju.wait(jubilant.all_active, timeout=1000)


# @mark.parametrize("endpoint,remote", list(zip(O11Y_RELS, O11Y_CHARMS)))
# def test_remove_relation(juju: jubilant.Juju, endpoint, remote):
#     # Remove the relation
#     juju.cli("remove-relation", f"{ZINC}:{endpoint}", remote)
#     # Wait for the two apps to quiesce
#     juju.wait(jubilant.all_active, timeout=1000)
