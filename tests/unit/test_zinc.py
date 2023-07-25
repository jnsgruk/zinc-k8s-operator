# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import patch

from zinc import Zinc


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.zinc = Zinc()

    def test_property_pebble_layer(self):
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
        self.assertEqual(self.zinc.pebble_layer("password"), expected)

    def test_property_port_returns_int(self):
        self.assertIsInstance(self.zinc.port, int)

    def test_property_port_returns_str(self):
        self.assertIsInstance(self.zinc.log_path, str)
        self.assertTrue(self.zinc.log_path[0] == "/")

    @patch("charm.Zinc._request_version", lambda x: "0.2.6")
    def test_version_returns_str(self):
        self.assertIsInstance(self.zinc.version, str)
        self.assertEqual(self.zinc.version, "0.2.6")

    @patch("charm.Zinc._request_version")
    def test_version_returns_empty_string_when_request_fails(self, request_version):
        request_version.side_effect = Exception
        self.assertIsInstance(self.zinc.version, str)
        self.assertEqual(self.zinc.version, "")
