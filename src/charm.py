#!/usr/bin/env python3
# Copyright 2024 Jon Seager (@jnsgruk)
# See LICENSE file for licensing details.

"""Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

import logging
import secrets

import ops
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.parca_k8s.v0.parca_scrape import ProfilingEndpointProvider
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer

from zinc import Zinc

logger = logging.getLogger(__name__)


class ZincCharm(ops.CharmBase):
    """Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.zinc_pebble_ready, self._on_zinc_pebble_ready)
        self.framework.observe(
            self.on.zinc_peers_relation_changed, self._on_zinc_peers_relation_changed
        )
        self.framework.observe(self.on.update_status, self._on_update_status)

        self._container = self.unit.get_container("zinc")
        self._zinc = Zinc()

        # The Traefik ingress library records whether the requested workload
        # port is open when it publishes relation data. On Juju 4 the ingress
        # relation can be established before pebble-ready, so open the port
        # before the ingress library has a chance to auto-publish data.
        self.unit.open_port(protocol="tcp", port=self._zinc.port)

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

        self._ingress = IngressPerAppRequirer(
            self,
            port=self._zinc.port,
            strip_prefix=True,
        )
        self.framework.observe(self.on.ingress_relation_changed, self._on_ingress_relation_changed)

    def _on_zinc_pebble_ready(self, event: ops.WorkloadEvent):
        """Define and start a workload using the Pebble API."""
        if not self.model.get_relation("zinc-peers"):
            event.defer()
            self.unit.status = ops.WaitingStatus("waiting for peer relation")
            return

        if not self.unit.is_leader() and not self._has_generated_password():
            event.defer()
            self.unit.status = ops.WaitingStatus("waiting for leadership")
            return

        self._configure_zinc()

    def _on_zinc_peers_relation_changed(self, _):
        """Start Zinc once the peer relation is available."""
        if self._container.can_connect() and (
            self.unit.is_leader() or self._has_generated_password()
        ):
            self._configure_zinc()

    def _configure_zinc(self):
        """Define and start Zinc using the Pebble API."""
        password = self._generated_password()
        self._container.make_dir(self._zinc.log_dir, make_parents=True, permissions=0o755)
        self._container.add_layer("zinc", self._zinc.pebble_layer(password), combine=True)
        self._container.replan()

        self.unit.set_workload_version(self._zinc.version)
        self.unit.open_port(protocol="tcp", port=self._zinc.port)
        self._refresh_ingress_requirements()

        self.unit.status = ops.ActiveStatus()

    def _has_generated_password(self) -> bool:
        """Whether the generated admin password secret is already available."""
        relation = self.model.get_relation("zinc-peers")
        return bool(relation and relation.data[self.app].get("initial-admin-password"))

    def _on_ingress_relation_changed(self, _):
        """Refresh ingress data once Juju has assigned a bind address."""
        if self._container.can_connect():
            self._refresh_ingress_requirements()

    def _refresh_ingress_requirements(self):
        """Publish ingress data using the unit IP as Traefik's backend host."""
        self.unit.open_port(protocol="tcp", port=self._zinc.port)

        for relation in self.model.relations["ingress"]:
            binding = self.model.get_binding(relation)
            address = None
            if binding is not None and binding.network.bind_address is not None:
                address = str(binding.network.bind_address)

            self._ingress.provide_ingress_requirements(
                host=address,
                ip=address,
                port=self._zinc.port,
            )

    def _on_update_status(self, _):
        """Update the status of the application."""
        if self._container.can_connect() and self._container.get_services("zinc"):
            self.unit.set_workload_version(self._zinc.version)

    def _generated_password(self) -> str:
        """Report the generated admin password; generate one if it doesn't exist."""
        # If the peer relation is not ready, just return an empty string
        relation = self.model.get_relation("zinc-peers")
        if not relation:
            return ""

        # If the secret already exists, grab its content and return it
        secret_id = relation.data[self.app].get("initial-admin-password", None)
        if secret_id:
            secret = self.model.get_secret(id=secret_id)
            return secret.peek_content().get("password")

        if self.unit.is_leader():
            content = {"password": secrets.token_urlsafe(24)}
            secret = self.app.add_secret(content)
            # Store the secret id in the peer relation for other units if required
            relation.data[self.app]["initial-admin-password"] = secret.id
            return content["password"]
        else:
            return ""


if __name__ == "__main__":  # pragma: nocover
    ops.main(ZincCharm)
