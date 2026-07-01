# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

import subprocess

import pytest

from tests.integration.conftest import _get_traefik_lb_ip


def test_get_traefik_lb_ip_waits_until_service_has_ip():
    """Return the first non-empty Traefik LoadBalancer IP."""
    calls = []
    outputs = ["", "'10.1.2.3'"]

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout=outputs.pop(0), stderr="")

    sleeps = []

    assert _get_traefik_lb_ip("test-model", run=fake_run, sleep=sleeps.append) == "10.1.2.3"
    assert sleeps == [5]
    assert len(calls) == 2
    assert calls[0][0] == [
        "/snap/bin/kubectl",
        "-n",
        "test-model",
        "get",
        "service",
        "traefik-k8s-lb",
        "-o=jsonpath={.status.loadBalancer.ingress[0].ip}",
    ]
    assert calls[0][1]["check"] is True
    assert calls[0][1]["stdout"] is subprocess.PIPE
    assert calls[0][1]["stderr"] is subprocess.PIPE
    assert calls[0][1]["text"] is True


def test_get_traefik_lb_ip_uses_cluster_ip_if_lb_ip_never_appears():
    """Fall back to the service ClusterIP if MetalLB never assigns a LoadBalancer IP."""
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[-1] == "-o=jsonpath={.spec.clusterIP}":
            return subprocess.CompletedProcess(command, 0, stdout="10.152.183.42", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    address = _get_traefik_lb_ip("test-model", run=fake_run, sleep=lambda _: None, attempts=2)

    assert address == "10.152.183.42"
    assert commands[-1] == [
        "/snap/bin/kubectl",
        "-n",
        "test-model",
        "get",
        "service",
        "traefik-k8s-lb",
        "-o=jsonpath={.spec.clusterIP}",
    ]


def test_get_traefik_lb_ip_fails_clearly_if_no_service_address_appears():
    """Raise a clear failure when neither LoadBalancer IP nor ClusterIP appears."""

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    with pytest.raises(AssertionError, match="Traefik service address was not assigned"):
        _get_traefik_lb_ip("test-model", run=fake_run, sleep=lambda _: None, attempts=2)
