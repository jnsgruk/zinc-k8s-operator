#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from urllib.request import Request, urlopen

from . import TRAEFIK, ZINC, retry
from .juju import Juju


def test_deploy(zinc_charm, zinc_oci_image):
    """Test that Zinc can be related with Traefik for ingress."""
    apps = [ZINC, TRAEFIK]
    traefik_config = {"routing_mode": "path", "external_hostname": "foo.bar"}

    Juju.deploy(zinc_charm, alias=ZINC, resources={"zinc-image": zinc_oci_image})
    Juju.deploy(TRAEFIK, config=traefik_config, trust=True)
    Juju.integrate(*apps)
    Juju.wait_for_idle(apps, timeout=1000)


def test_ingress_setup():
    """Test that Zinc/Traefik are configured correctly."""
    result = Juju.run(f"{TRAEFIK}/0", "show-proxied-endpoints")
    j = json.loads(result["proxied-endpoints"])

    assert j[ZINC] == {"url": f"http://foo.bar/{Juju.model_name()}-{ZINC}"}


@retry(retry_num=24, retry_sleep_sec=5)
def test_ingress_functions_correctly(traefik_lb_ip):
    req = Request(f"http://{traefik_lb_ip}:80/{Juju.model_name()}-{ZINC}/version")
    req.add_header("Host", "foo.bar")

    response = urlopen(req)
    response_data = json.loads(response.read())

    assert response.status == 200
    assert "version" in response_data
