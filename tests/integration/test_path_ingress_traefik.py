#!/usr/bin/env python3
# Copyright 2024 Jon Seager (@jnsgruk)
# See LICENSE file for licensing details.

import json
from urllib.request import Request, urlopen

import jubilant

from . import TRAEFIK, ZINC, retry


def test_deploy(juju: jubilant.Juju, zinc_charm, zinc_oci_image):
    """Test that Zinc can be related with Traefik for ingress."""
    apps = [ZINC, TRAEFIK]
    traefik_config = {"routing_mode": "path", "external_hostname": "foo.bar"}

    juju.deploy(zinc_charm, app=ZINC, resources={"zinc-image": zinc_oci_image})
    juju.deploy(TRAEFIK, config=traefik_config, trust=True)
    juju.integrate(*apps)
    juju.wait(jubilant.all_active)


def test_ingress_setup(juju: jubilant.Juju):
    """Test that Zinc/Traefik are configured correctly."""
    result = juju.run(f"{TRAEFIK}/0", "show-external-endpoints")
    j = json.loads(result.results["external-endpoints"])

    model_name = juju.model
    assert model_name is not None
    assert j[ZINC] == {"url": f"http://foo.bar/{model_name}-{ZINC}"}


@retry(retry_num=24, retry_sleep_sec=5)
def test_ingress_functions_correctly(juju: jubilant.Juju, traefik_lb_ip):
    model_name = juju.model
    assert model_name is not None

    req = Request(f"http://{traefik_lb_ip}:80/{model_name}-{ZINC}/version")
    req.add_header("Host", "foo.bar")

    response = urlopen(req)
    response_data = json.loads(response.read())

    assert response.status == 200
    assert "version" in response_data
