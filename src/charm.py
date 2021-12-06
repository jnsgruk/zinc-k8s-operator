#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class ZincCharm(CharmBase):
    """Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.zinc_pebble_ready, self._on_zinc_pebble_ready)

    def _on_zinc_pebble_ready(self, event):
        """Define and start a workload using the Pebble API."""
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "zinc layer",
            "description": "pebble config layer for zinc",
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
        container.add_layer("zinc", pebble_layer, combine=True)
        container.autostart()
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(ZincCharm)
