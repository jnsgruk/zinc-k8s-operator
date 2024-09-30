# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import subprocess
from pathlib import Path

import yaml
from pytest import fixture

from . import TRAEFIK
from .juju import Juju


@fixture(scope="module")
def zinc_charm(request):
    """Zinc charm used for integration testing."""
    charm_file = request.config.getoption("--charm-path")
    if charm_file:
        return charm_file

    subprocess.run(
        ["/snap/bin/charmcraft", "pack", "--verbose"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return next(Path.glob(Path("."), "*.charm")).absolute()


@fixture(scope="module")
def zinc_oci_image():
    meta = yaml.safe_load(Path("./charmcraft.yaml").read_text())
    return meta["resources"]["zinc-image"]["upstream-source"]


@fixture(scope="module")
def traefik_lb_ip():
    model_name = Juju.status()["model"]["name"]
    proc = subprocess.run(
        [
            "/snap/bin/kubectl",
            "-n",
            model_name,
            "get",
            "service",
            f"{TRAEFIK}-lb",
            "-o=jsonpath='{.status.loadBalancer.ingress[0].ip}'",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    ip_address = proc.stdout.strip("'")
    return ip_address
