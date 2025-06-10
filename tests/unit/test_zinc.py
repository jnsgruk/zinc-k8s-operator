# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import patch

import pytest

from zinc import Zinc


@pytest.fixture()
def zinc():
    return Zinc()


def test_property_pebble_layer(zinc):
    expected = {
        "services": {
            "zinc": {
                "override": "replace",
                "summary": "zinc",
                "command": "/bin/go-runner --log-file=/var/lib/zincsearch/zinc.log --also-stdout=true --redirect-stderr=true /bin/zincsearch",
                "startup": "enabled",
                "environment": {
                    "ZINC_DATA_PATH": "/var/lib/zincsearch",
                    "ZINC_FIRST_ADMIN_USER": "admin",
                    "ZINC_FIRST_ADMIN_PASSWORD": "password",
                    "ZINC_PROMETHEUS_ENABLE": True,
                    "ZINC_TELEMETRY": False,
                    "ZINC_PROFILER": True,
                },
            }
        },
    }
    assert zinc.pebble_layer("password") == expected


def test_property_port_returns_int(zinc):
    assert isinstance(zinc.port, int)


def test_property_port_returns_str(zinc):
    assert isinstance(zinc.log_path, str)
    assert zinc.log_path[0] == "/"


@patch("charm.Zinc._request_version", lambda x: "0.2.6")
def test_version_returns_str(zinc):
    assert isinstance(zinc.version, str)
    assert zinc.version == "0.2.6"


@patch("charm.Zinc._request_version")
def test_version_returns_empty_string_when_request_fails(request_version, zinc):
    request_version.side_effect = Exception
    assert isinstance(zinc.version, str)
    assert zinc.version == ""
