#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

import json
import logging
import secrets
import string
import subprocess
import urllib.request

from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.parca.v0.parca_scrape import ProfilingEndpointProvider
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.charm import ActionEvent, CharmBase, WorkloadEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus
from ops.pebble import Layer
from tenacity import retry, stop_after_delay

logger = logging.getLogger(__name__)


class ZincCharm(CharmBase):
    """Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

    _stored = StoredState()
    _log_path = "/var/log/zinc.log"

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(initial_admin_password="")
        self.framework.observe(self.on.zinc_pebble_ready, self._on_zinc_pebble_ready)
        self.framework.observe(self.on.get_admin_password_action, self._on_get_admin_password)
        self.framework.observe(self.on.update_status, self._on_update_status)

        # Provide ability for Zinc to be scraped by Prometheus using prometheus_scrape
        self._scraping = MetricsEndpointProvider(
            self,
            relation_name="metrics-endpoint",
            jobs=[{"static_configs": [{"targets": ["*:4080"]}]}],
        )

        # Enable log forwarding for Loki and other charms that implement loki_push_api
        self._logging = LogProxyConsumer(self, relation_name="logging", log_files=[self._log_path])

        # Provide grafana dashboards over a relation interface
        self._grafana_dashboards = GrafanaDashboardProvider(
            self, relation_name="grafana-dashboard"
        )

        # Enable profiling over a relation with Parca
        self._profiling = ProfilingEndpointProvider(
            self, jobs=[{"static_configs": [{"targets": ["*:4080"]}]}]
        )

        self._ingress = IngressPerAppRequirer(self, port=4080)

    def _on_zinc_pebble_ready(self, event: WorkloadEvent):
        """Define and start a workload using the Pebble API."""
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload

        # If we've not got an initial admin password, then generate one
        if not self._stored.initial_admin_password:
            self._stored.initial_admin_password = self._generate_password()

        # Define an initial Pebble layer configuration
        container.add_layer("zinc", self._pebble_layer, combine=True)
        container.replan()
        self.unit.set_workload_version(self.version)

        try:
            subprocess.check_call(["open-port", "4080/tcp"])
        except subprocess.CalledProcessError as e:
            logger.error("failed to open port: %s", str(e))

        self.unit.status = ActiveStatus()

    def _on_update_status(self, _):
        """Update the status of the application."""
        self.unit.set_workload_version(self.version)

    def _on_get_admin_password(self, event: ActionEvent) -> None:
        """Return the initial generated password for the admin user as an action response."""
        if not self._stored.initial_admin_password:
            self._stored.initial_admin_password = self._generate_password()
        event.set_results({"admin-password": self._stored.initial_admin_password})

    @property
    def _pebble_layer(self) -> Layer:
        return Layer(
            {
                "services": {
                    "zinc": {
                        "override": "replace",
                        "summary": "zinc",
                        "command": '/bin/sh -c "/go/bin/zinc | tee {}"'.format(self._log_path),
                        "startup": "enabled",
                        "environment": {
                            "ZINC_DATA_PATH": "/go/bin/data",
                            "ZINC_FIRST_ADMIN_USER": "admin",
                            "ZINC_FIRST_ADMIN_PASSWORD": self._stored.initial_admin_password,
                            "ZINC_PROMETHEUS_ENABLE": True,
                            "ZINC_TELEMETRY": False,
                            "ZINC_PROFILER": True,
                        },
                    }
                },
            }
        )

    @property
    def version(self) -> str:
        """Reports the current Zinc version."""
        container = self.unit.get_container("zinc")
        if container.can_connect() and container.get_services("zinc"):
            try:
                return self._request_version()
            # Catching Exception is not ideal, but we don't care much for the error here, and just
            # default to setting a blank version since there isn't much the admin can do!
            except Exception as e:
                logger.warning("unable to get version from API: %s", str(e))
                logger.debug(e, exc_info=True)
                return ""
        return ""

    @retry(stop=stop_after_delay(10))
    def _request_version(self) -> str:
        """Fetch the version from the running workload using the Zinc API."""
        res = urllib.request.urlopen("http://localhost:4080/version")
        return json.loads(res.read().decode())["version"]

    def _generate_password(self) -> str:
        """Generate a random 24 character password."""
        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(24))


if __name__ == "__main__":  # pragma: nocover
    main(ZincCharm, use_juju_for_storage=True)
