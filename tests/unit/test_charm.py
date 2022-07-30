# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import re
import unittest
from unittest.mock import Mock, PropertyMock, patch

from ops.model import ActiveStatus
from ops.pebble import Layer
from ops.testing import Harness

from charm import ZincCharm

unittest.TestCase.maxDiff = None


@patch("charm.ZincCharm._request_version", lambda x: "0.2.6")
class TestCharm(unittest.TestCase):
    @patch("charm.KubernetesServicePatch", lambda x, y: None)
    def setUp(self):
        self.harness = Harness(ZincCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    @patch("charm.ZincCharm._generate_password", lambda x: "password")
    def test_zinc_pebble_ready(self):
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("zinc")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        self.assertEqual(self.harness.charm._stored.initial_admin_password, "")
        container = self.harness.model.unit.get_container("zinc")

        # Emit the pebble-ready event for zinc
        self.harness.charm.on.zinc_pebble_ready.emit(container)
        # Check that we generated a password for Zinc
        self.assertEqual(self.harness.charm._stored.initial_admin_password, "password")

        # Check we've got the plan we expected
        updated_plan = self.harness.get_container_pebble_plan("zinc").to_dict()
        self.assertEqual(self.harness.charm._pebble_layer.to_dict(), updated_plan)

        # Check the service was started
        service = self.harness.model.unit.get_container("zinc").get_service("zinc")
        self.assertTrue(service.is_running())

        # Check workload version
        self.assertEqual(self.harness.get_workload_version(), "0.2.6")
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_update_status(self):
        self.assertEqual(self.harness.get_workload_version(), None)
        self.harness.container_pebble_ready("zinc")
        self.assertEqual(self.harness.get_workload_version(), "0.2.6")

        with patch("charm.ZincCharm.version", new_callable=PropertyMock(return_value="0.4.0")):
            self.harness.charm.on.update_status.emit()
            self.assertEqual(self.harness.get_workload_version(), "0.4.0")

    @patch("charm.ZincCharm._generate_password")
    def test_get_admin_password_action(self, generate):
        mock_event = Mock()
        generate.return_value = "password"
        # Reset the stored admin password if there is a value already there
        self.harness.charm._stored.initial_admin_password = ""

        # Trigger the event handler
        self.harness.charm._on_get_admin_password(mock_event)
        # Ensure stored state was updated with a generated password
        self.assertEqual(self.harness.charm._stored.initial_admin_password, "password")
        generate.assert_called_once()
        # Make sure we return the generated password
        mock_event.called_once_with({"admin-password": "password"})
        # Call again and make sure we don't call the generate_password again
        generate.reset_mock()
        self.harness.charm._on_get_admin_password(mock_event)
        generate.assert_not_called()

    def test_property_pebble_layer(self):
        self.harness.charm._stored.initial_admin_password = "password"
        expected = Layer(
            {
                "services": {
                    "zinc": {
                        "override": "replace",
                        "summary": "zinc",
                        "command": '/bin/sh -c "/go/bin/zinc | tee /var/log/zinc.log"',
                        "startup": "enabled",
                        "environment": {
                            "ZINC_DATA_PATH": "/go/bin/data",
                            "ZINC_FIRST_ADMIN_USER": "admin",
                            "ZINC_FIRST_ADMIN_PASSWORD": "password",
                            "ZINC_PROMETHEUS_ENABLE": True,
                            "ZINC_TELEMETRY": False,
                            "ZINC_PROFILER": True,
                        },
                    }
                },
            }
        )
        self.assertEqual(self.harness.charm._pebble_layer.to_dict(), expected.to_dict())

    def test_generate_password(self):
        password = self.harness.charm._generate_password()
        # Test that we generate a 24-character alphanumeric password
        self.assertTrue(re.match("[A-Za-z0-9]{24}", password))
