# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import os
import subprocess
import time
from collections.abc import Callable
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


def _get_traefik_lb_ip(
    model_name: str,
    *,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    sleep: Callable[[int], None] = time.sleep,
    attempts: int = 24,
    retry_sleep_sec: int = 5,
) -> str:
    """Wait for Traefik's LoadBalancer service to be assigned a usable address."""

    def _kubectl_service_jsonpath(jsonpath: str) -> str:
        proc = run(
            [
                "/snap/bin/kubectl",
                "-n",
                model_name,
                "get",
                "service",
                f"{TRAEFIK}-lb",
                f"-o=jsonpath={jsonpath}",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return proc.stdout.strip().strip("'")

    for attempt in range(attempts):
        ip_address = _kubectl_service_jsonpath("{.status.loadBalancer.ingress[0].ip}")
        if ip_address:
            return ip_address

        if attempt < attempts - 1:
            sleep(retry_sleep_sec)

    if cluster_ip := _kubectl_service_jsonpath("{.spec.clusterIP}"):
        return cluster_ip

    raise AssertionError("Traefik service address was not assigned")


@fixture(scope="module")
def traefik_lb_ip(juju: jubilant.Juju):
    model_name = juju.model
    assert model_name is not None

    return _get_traefik_lb_ip(model_name)
