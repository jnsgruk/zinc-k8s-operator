# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import Mock, PropertyMock, patch

from charm import ZincCharm
from ops.model import ActiveStatus
from ops.testing import Harness

PASSWORD = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


def _prime_password_secret(harness) -> str:
    id = harness.add_model_secret(owner=harness.charm.app, content={"password": PASSWORD})
    rel_id = harness.add_relation("zinc-peers", "zinc-k8s")
    harness.update_relation_data(rel_id, harness.charm.app.name, {"initial-admin-password": id})
    return id


@patch("charm.Zinc._request_version", lambda x: "0.2.6")
class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(ZincCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_zinc_pebble_ready(self):
        self.harness.set_can_connect("zinc", True)
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("zinc")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        container = self.harness.model.unit.get_container("zinc")

        # Ensure there is a password secret in the peer relation
        _prime_password_secret(self.harness)
        # Emit the pebble-ready event for zinc
        self.harness.charm.on.zinc_pebble_ready.emit(container)

        # Check we've got the plan we expected
        updated_plan = self.harness.get_container_pebble_plan("zinc").to_dict()
        self.assertEqual(self.harness.charm._zinc.pebble_layer(PASSWORD), updated_plan)

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

        with patch("charm.Zinc.version", new_callable=PropertyMock(return_value="0.4.0")):
            self.harness.charm.on.update_status.emit()
            self.assertEqual(self.harness.get_workload_version(), "0.4.0")

    def test_get_admin_password_action(self):
        mock_event = Mock()
        _prime_password_secret(self.harness)
        # Trigger the event handler
        self.harness.charm._on_get_admin_password(mock_event)
        # Make sure we return the generated password
        mock_event.called_once_with({"admin-password": PASSWORD})

    def test_zinc_password_no_relation(self):
        self.harness.set_leader(True)
        new_secret = self.harness.charm._generated_password()
        self.assertEqual(new_secret, "")

    def test_zinc_password_create(self):
        self.harness.set_leader(True)
        self.harness.add_relation("zinc-peers", "zinc-k8s")
        new_secret = self.harness.charm._generated_password()
        self.assertEqual(len(new_secret), 32)

    def test_zinc_password_from_peer_data(self):
        self.harness.set_leader(True)
        _prime_password_secret(self.harness)
        secret = self.harness.charm._generated_password()
        self.assertEqual(secret, PASSWORD)
