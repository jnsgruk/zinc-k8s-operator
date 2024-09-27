#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.


import json

import pytest
import requests
import sh

from . import ZINC
from .juju import juju, run_action, status, wait_for_idle

TRAEFIK = "traefik-k8s"


@pytest.mark.abort_on_fail
def deploy(zinc_charm, zinc_oci_image):
    """Test that Zinc can be related with Traefik for ingress."""
    apps = [ZINC, TRAEFIK]
    juju("deploy", zinc_charm, ZINC, "--resource", f"zinc-image={zinc_oci_image}")
    juju(
        "deploy",
        TRAEFIK,
        "--channel=latest/edge",
        "--config",
        "routing_mode=subdomain",
        "--config",
        "external_hostname=foo.bar",
    )

    juju("integrate", *apps)
    wait_for_idle(apps)


@pytest.mark.abort_on_fail
def test_ingress_setup():
    """Test that Zinc/Traefik are configured correctly."""
    model_name = status()["model"]["name"]
    result = run_action(f"{TRAEFIK}/0", "show-proxied-endpoints")
    j = json.loads(result["proxied-endpoints"])
    assert j[ZINC] == {"url": f"http://{model_name}-{ZINC}.foo.bar/"}


@pytest.mark.abort_on_fail
def test_ingress_functions_correctly():
    model_name = status()["model"]["name"]

    result = sh.kubectl(
        "-n",
        model_name,
        "get",
        "service",
        f"{TRAEFIK}-lb",
        "-o=jsonpath='{.status.loadBalancer.ingress[0].ip}'",
    )
    ip_address = result.strip("'")

    r = requests.get(
        f"http://{ip_address}:80/version",
        headers={"Host": f"{model_name}-{ZINC}.foo.bar"},
    )

    assert r.status_code == 200
    assert "version" in r.json()
