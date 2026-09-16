# Copyright 2026 Jon Seager (@jnsgruk)
# See LICENSE file for licensing details.

"""Validate the bare rock using a temporary, externally mounted static BusyBox."""

import os
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
import yaml


@pytest.fixture(scope="module")
def image():
    metadata = yaml.safe_load(Path("rockcraft.yaml").read_text())
    return os.environ.get("ZINC_TEST_IMAGE", f"{metadata['name']}:{metadata['version']}")


@pytest.fixture(scope="module")
def busybox(tmp_path_factory):
    directory = tmp_path_factory.mktemp("busybox")
    directory.chmod(0o755)
    subprocess.run(["docker", "pull", "busybox:1.37.0-musl"], check=True)
    container = (
        subprocess.check_output(["docker", "create", "busybox:1.37.0-musl"]).decode().strip()
    )
    try:
        subprocess.run(["docker", "cp", f"{container}:/bin/busybox", str(directory)], check=True)
    finally:
        subprocess.run(["docker", "rm", container], check=True)
    (directory / "busybox").chmod(0o755)
    return directory


def test_non_root_identity_and_path_access(image, busybox):
    # Do not override --user: this must validate the image's default runtime identity.
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--mount",
            f"type=bind,src={busybox},dst=/probe,readonly",
            "--entrypoint",
            "/probe/busybox",
            image,
            "sh",
            "-ec",
            """
            test "$(/probe/busybox id -u)" = 584792
            test "$(/probe/busybox id -g)" = 584792
            test -x /bin/zincsearch
            test -x /bin/go-runner
            for path in /var/lib/zincsearch /opt/promtail /etc/promtail; do
                test -r "$path" && test -w "$path" && test -x "$path"
                printf 'non-root write check' > "$path/non-root-check"
                test "$(/probe/busybox cat "$path/non-root-check")" = 'non-root write check'
                /probe/busybox rm "$path/non-root-check"
            done
            """,
        ],
        check=True,
    )


def test_zinc_starts_as_non_root(image, busybox):
    container = (
        subprocess.check_output(
            [
                "docker",
                "run",
                "--detach",
                "--publish",
                "127.0.0.1::4080",
                "--env",
                "ZINC_FIRST_ADMIN_USER=admin",
                "--env",
                "ZINC_FIRST_ADMIN_PASSWORD=non-root-image-test",
                "--mount",
                f"type=bind,src={busybox},dst=/probe,readonly",
                image,
            ]
        )
        .decode()
        .strip()
    )
    try:
        address = (
            subprocess.check_output(["docker", "port", container, "4080/tcp"]).decode().strip()
        )
        for attempt in range(30):
            try:
                with urlopen(f"http://{address}/version", timeout=2) as response:
                    assert response.status == 200
                break
            except (URLError, TimeoutError, ConnectionError):
                if attempt == 29:
                    subprocess.run(["docker", "logs", container], check=True)
                    raise
                time.sleep(1)
        subprocess.run(
            [
                "docker",
                "exec",
                container,
                "/probe/busybox",
                "sh",
                "-ec",
                """
                pid=$(/probe/busybox pgrep -f '^/bin/zincsearch$')
                test -n "$pid"
                test "$(/probe/busybox awk '/^Uid:/ {print $2,$3,$4,$5}' /proc/$pid/status)" = '584792 584792 584792 584792'
                test "$(/probe/busybox awk '/^Gid:/ {print $2,$3,$4,$5}' /proc/$pid/status)" = '584792 584792 584792 584792'
                test -s /var/lib/zincsearch/zinc.log
                """,
            ],
            check=True,
        )
    finally:
        subprocess.run(["docker", "rm", "--force", container], check=True)
