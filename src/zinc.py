#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Assist with client interactions with Zinc."""

import json
import logging
import time
import urllib.request

logger = logging.getLogger(__name__)


class Zinc:
    """Represent a Zinc instance in the workload."""

    _port = 4080
    _log_path = "/var/log/zincsearch/zinc.log"

    def pebble_layer(self, initial_password) -> dict:
        """Return a Pebble layer for managing Zinc."""
        return {
            "services": {
                "zinc": {
                    "override": "replace",
                    "summary": "zinc",
                    "command": f"/bin/busybox sh -c '/bin/zincsearch | /bin/busybox tee {self.log_path}'",
                    "startup": "enabled",
                    "environment": {
                        "ZINC_DATA_PATH": "/data",
                        "ZINC_FIRST_ADMIN_USER": "admin",
                        "ZINC_FIRST_ADMIN_PASSWORD": initial_password,
                        "ZINC_PROMETHEUS_ENABLE": True,
                        "ZINC_TELEMETRY": False,
                        "ZINC_PROFILER": True,
                    },
                }
            },
        }

    @property
    def log_path(self) -> int:
        """Report the path that Zinc is configured to output logs."""
        return self._log_path

    @property
    def port(self) -> int:
        """Report the TCP port that Zinc is bound to."""
        return self._port

    @property
    def version(self) -> str:
        """Reports the current Zinc version."""
        try:
            return self._request_version()
        # Catching Exception is not ideal, but we don't care much for the error here, and just
        # default to setting a blank version since there isn't much the admin can do!
        except Exception as e:
            logger.warning("unable to get version from API: %s", str(e))
            logger.debug(e, exc_info=True)
            return ""

    def _request_version(self) -> str:
        """Fetch the version from the running workload using the Zinc API."""
        retries = 0
        while True:
            try:
                res = urllib.request.urlopen(f"http://localhost:{self._port}/version")
                return json.loads(res.read().decode())["version"]
            except Exception:
                if retries == 3:
                    raise
                retries += 1
                time.sleep(3)
