# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest

from ops.model import ActiveStatus
from ops.testing import Harness

from charm import ZincCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(ZincCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_zinc_pebble_ready(self):
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("zinc")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Expected plan after Pebble ready with default config
        expected_plan = {
            "services": {
                "zinc": {
                    "override": "replace",
                    "summary": "zinc",
                    "command": "/go/bin/zinc",
                    "startup": "enabled",
                    "environment": {
                        "FIRST_ADMIN_USER": "admin",
                        "FIRST_ADMIN_PASSWORD": "#Pa55word!",
                    },
                }
            },
        }
        container = self.harness.model.unit.get_container("zinc")
        self.harness.charm.on.zinc_pebble_ready.emit(container)
        # Get the plan now we've run PebbleReady
        updated_plan = self.harness.get_container_pebble_plan("zinc").to_dict()
        # Check we've got the plan we expected
        self.assertEqual(expected_plan, updated_plan)
        # Check the service was started
        service = self.harness.model.unit.get_container("zinc").get_service("zinc")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
