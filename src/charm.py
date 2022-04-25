#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

import logging
import secrets
import string

from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from ops.charm import ActionEvent, CharmBase, WorkloadEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class ZincCharm(CharmBase):
    """Charmed Operator for Zinc; a lightweight elasticsearch alternative."""

    _name = "zinc"
    _log_path = "/zinc.log"
    _logging_relation = "logging"
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self._stored.set_default(initial_admin_password="")
        self.framework.observe(self.on.zinc_pebble_ready, self._on_zinc_pebble_ready)
        self.framework.observe(self.on.get_admin_password_action, self._on_get_admin_password)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade)
        self._service_patcher = KubernetesServicePatch(self, [(self.app.name, 4080, 4080)])

        # Set up observability services
        self._init_metrics()
        self._init_logs()
        self._init_dashboards()

    def _init_metrics(self):
        self.metrics_endpoint_provider = MetricsEndpointProvider(
            self,
            jobs=[
                {
                    "static_configs": [{"targets": ["*:4080"]}],
                }
            ],
        )

    def _init_logs(self):
        self._loki_logs = LogProxyConsumer(
            self, relation_name=self._logging_relation, log_files=[self._log_path]
        )
        self.framework.observe(self._loki_logs.on.promtail_digest_error, self._on_promtail_error)

    def _init_dashboards(self):
        self._grafana_dashboards = GrafanaDashboardProvider(
            self, relation_name="grafana-dashboard"
        )

    def _on_promtail_error(self, event):
        logger.error(str(event))

    def _on_upgrade(self, event: WorkloadEvent):
        container = self.unit.get_container(self._name)
        container.add_layer(self._name, self._pebble_layer, combine=True)
        container.replan()

    def _on_zinc_pebble_ready(self, event: WorkloadEvent):
        """Define and start a workload using the Pebble API."""
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload

        # If we've not got an initial admin password, then generate one
        if not self._stored.initial_admin_password:
            self._stored.initial_admin_password = self._generate_password()

        # Define an initial Pebble layer configuration
        container.add_layer(self._name, self._pebble_layer, combine=True)
        container.autostart()
        self.unit.status = ActiveStatus()

    def _on_get_admin_password(self, event: ActionEvent) -> None:
        """Returns the initial generated password for the admin user as an action response."""
        if not self._stored.initial_admin_password:
            self._stored.initial_admin_password = self._generate_password()
        event.set_results({"admin-password": self._stored.initial_admin_password})

    @property
    def _pebble_layer(self) -> Layer:
        return Layer(
            {
                "services": {
                    self._name: {
                        "override": "replace",
                        "summary": self._name,
                        "command": '/bin/sh -c "/go/bin/zinc | tee {}"'.format(self._log_path),
                        "startup": "enabled",
                        "environment": {
                            "ZINC_DATA_PATH": "/go/bin/data",
                            "ZINC_FIRST_ADMIN_USER": "admin",
                            "ZINC_FIRST_ADMIN_PASSWORD": self._stored.initial_admin_password,
                            "ZINC_PROMETHEUS_ENABLE": "true",
                        },
                    }
                },
            }
        )

    def _generate_password(self) -> str:
        """Generates a random 24 character password."""
        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(24))


if __name__ == "__main__":  # pragma: nocover
    main(ZincCharm, use_juju_for_storage=True)
