# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import os
import subprocess
from pathlib import Path

import jubilant
import yaml
from pytest import fixture

from . import TRAEFIK


@fixture(scope="module")
def juju():
    with jubilant.temp_model() as juju:
        yield juju


@fixture(scope="module")
def zinc_charm(request):
    """Zinc charm used for integration testing."""
    charm_file = request.config.getoption("--charm-path")
    if charm_file:
        return charm_file

    working_dir = os.getenv("SPREAD_PATH", Path("."))

    subprocess.run(
        ["/snap/bin/charmcraft", "pack", "--verbose"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=working_dir,
        check=True,
    )

    return next(Path.glob(Path(working_dir), "*.charm")).absolute()


@fixture(scope="module")
def zinc_oci_image():
    meta = yaml.safe_load(Path("./charmcraft.yaml").read_text())
    return meta["resources"]["zinc-image"]["upstream-source"]


@fixture(scope="module")
def traefik_lb_ip(juju: jubilant.Juju):
    model_name = juju.model
    assert model_name is not None

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
