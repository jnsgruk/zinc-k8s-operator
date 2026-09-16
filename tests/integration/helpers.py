# Copyright 2026 Jon Seager (@jnsgruk)
# See LICENSE file for licensing details.

"""Check the security contexts of deployed charm containers."""

import lightkube
from lightkube.resources.core_v1 import Pod


def generate_container_securitycontext_map(metadata: dict) -> dict[str, dict[str, int]]:
    """Read workload identities and include the Juju charm user."""
    contexts = {
        name: {"runAsUser": container["uid"], "runAsGroup": container["gid"]}
        for name, container in metadata["containers"].items()
    }
    contexts["charm"] = {"runAsUser": 170, "runAsGroup": 170}
    return contexts


def get_pod_names(client: lightkube.Client, model: str, app: str) -> list[str]:
    """Find every pod for an application in its model namespace."""
    pods = client.list(Pod, namespace=model, labels={"app.kubernetes.io/name": app})
    return [pod.metadata.name for pod in pods]


def assert_security_context(
    client: lightkube.Client,
    pod_name: str,
    container_name: str,
    contexts: dict[str, dict[str, int]],
    model: str,
) -> None:
    """Assert the deployed container identity, including pod-level defaults."""
    pod = client.get(Pod, pod_name, namespace=model)
    container = next((c for c in pod.spec.containers if c.name == container_name), None)
    assert container is not None, f"Missing container {container_name} in {pod_name}"
    for key, expected in contexts[container_name].items():
        actual = getattr(container.securityContext, key, None)
        if actual is None:
            actual = getattr(pod.spec.securityContext, key, None)
        assert actual == expected, (
            f"{pod_name}/{container_name}: {key}={actual}, expected {expected}"
        )
