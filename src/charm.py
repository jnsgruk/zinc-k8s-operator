#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

import logging
import secrets
import string

import ops
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.parca.v0.parca_scrape import ProfilingEndpointProvider
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from zinc import Zinc

logger = logging.getLogger(__name__)


class ZincCharm(ops.CharmBase):
    """Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

    _stored = ops.StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(initial_admin_password="")
        self.framework.observe(self.on.zinc_pebble_ready, self._on_zinc_pebble_ready)
        self.framework.observe(self.on.get_admin_password_action, self._on_get_admin_password)
        self.framework.observe(self.on.update_status, self._on_update_status)

        self._container = self.unit.get_container("zinc")
        self._zinc = Zinc()

        # Provide ability for Zinc to be scraped by Prometheus using prometheus_scrape
        self._scraping = MetricsEndpointProvider(
            self,
            relation_name="metrics-endpoint",
            jobs=[{"static_configs": [{"targets": [f"*:{self._zinc.port}"]}]}],
        )

        # Enable log forwarding for Loki and other charms that implement loki_push_api
        self._logging = LogProxyConsumer(
            self, relation_name="log-proxy", log_files=[self._zinc.log_path]
        )

        # Provide grafana dashboards over a relation interface
        self._grafana_dashboards = GrafanaDashboardProvider(
            self, relation_name="grafana-dashboard"
        )

        # Enable profiling over a relation with Parca
        self._profiling = ProfilingEndpointProvider(
            self, jobs=[{"static_configs": [{"targets": [f"*:{self._zinc.port}"]}]}]
        )

        self._ingress = IngressPerAppRequirer(self, port=self._zinc.port)

    def _on_zinc_pebble_ready(self, event: ops.WorkloadEvent):
        """Define and start a workload using the Pebble API."""
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload

        # If we've not got an initial admin password, then generate one
        if not self._stored.initial_admin_password:
            self._stored.initial_admin_password = self._generate_password()

        # Define an initial Pebble layer configuration
        container.add_layer(
            "zinc", self._zinc.pebble_layer(self._stored.initial_admin_password), combine=True
        )
        container.replan()
        self.unit.set_workload_version(self._zinc.version)
        self.unit.open_port(protocol="tcp", port=self._zinc.port)

        self.unit.status = ops.ActiveStatus()

    def _on_update_status(self, _):
        """Update the status of the application."""
        if self._container.can_connect() and self._container.get_services("zinc"):
            self.unit.set_workload_version(self._zinc.version)

    def _on_get_admin_password(self, event: ops.ActionEvent) -> None:
        """Return the initial generated password for the admin user as an action response."""
        if not self._stored.initial_admin_password:
            self._stored.initial_admin_password = self._generate_password()
        event.set_results({"admin-password": self._stored.initial_admin_password})

    def _generate_password(self) -> str:
        """Generate a random 24 character password."""
        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(24))


if __name__ == "__main__":  # pragma: nocover
    ops.main(ZincCharm, use_juju_for_storage=True)
