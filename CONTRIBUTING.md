# Contributing

## Overview

This documents explains the processes and practices recommended for contributing enhancements to
this operator.

- Generally, before developing enhancements to this charm, you should consider [opening an issue
  ](https://github.com/jnsgruk/zinc-k8s-operator/issues) explaining your use case.
- If you would like to chat with us about your use-cases or proposed implementation, you can reach
  us [on Matrix](https://ubuntu.com/community/communications/matrix) or [Discourse](https://discourse.charmhub.io/).
- Familiarising yourself with the [Operator Framework](https://ops.readthedocs.io/en/latest/) library
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically examines
  - code quality
  - test coverage
  - user experience for Juju administrators this charm.
- Please help us out in ensuring easy to review branches by rebasing your pull request branch onto
  the `main` branch. This also avoids merge commits and creates a linear Git commit history.

## Developing

This project uses [`uv`](https://github.com/astral-sh/uv) for managing dependencies and virtual
environments.

You can create a virtual environment manually should you wish, though most of that is taken
care of automatically if you use the `Makefile` provided:

```bash
make format        # update your code according to linting rules
make lint          # code style
make unit          # unit tests

# The following exist, but should not be run directly without `spread`.
# See 'Running Tests' below.
❯ make integration   # run integration tests (run with `spread`)
```

To create the environment manually:

```bash
uv venv
source .venv/bin/activate
uv sync --all-extras
```

## Running tests

Unit tests can be run locally with no additional tools by running `make unit`. All of the project's unit tests are designed to run agnostic of machine and network, and shouldn't require any additional dependencies other than those injected by `uv run` and the `Make` target.

Integration testing uses `spread` in LXD virtual machines, both locally and in CI.
Concierge prepares Canonical Kubernetes (`k8s`) from `1.35-classic/stable`, Juju from
`4/stable`, and LXD from `latest/stable` inside each test VM. The Kubernetes track is
the newest one with a stable release at the time of this update; patch releases
follow that track. CI also uses `latest/stable` for the host LXD used by Spread and
the charm/ROCK builds. For local runs, install or refresh the host LXD from
`latest/stable` before running Spread.

To validate the rock's default non-root UID/GID and writable Zinc and Promtail paths, build it
with `rockcraft pack`, then load it into Docker and run the image test:

```bash
sudo skopeo --insecure-policy copy oci-archive:./zinc_1.0.0-beta1_amd64.rock docker-daemon:zinc:non-root-test
ZINC_TEST_IMAGE=zinc:non-root-test make rock-test
```

The test temporarily mounts a static BusyBox to inspect the bare image without adding a shell
to the shipped rock. The basic deployment integration tests also check the charm and workload
container security contexts. These tests require Juju 3.6 or later.
The [`charm-user` setting](https://canonical.com/juju/docs/charmcraft/4.3/reference/files/charmcraft-yaml-file/)
was introduced in Juju 3.6.

CI uploads the validated rock to `ttl.sh` under a name unique to the workflow run and attempt,
with a six-hour expiry. Every integration job waits for that upload and sets the checked-out
`charmcraft.yaml` image resource to the test image before running Spread. Both the Python
integration fixtures and the shell deployment test read this resource, so they deploy the
rock built by that workflow. This follows the
[Ubuntu manpages operator's CI setup](https://github.com/canonical/ubuntu-manpages-operator/blob/main/.github/workflows/build-and-test.yaml).

Local integration runs use the `upstream-source` in `charmcraft.yaml`. To test a rebuilt rock
in Kubernetes, upload it to a registry reachable by the cluster and set that resource to the
uploaded image before running Spread. The mounted data volume must also be writable by
UID/GID 584792, which the basic deployment tests exercise when Zinc starts and ingests data.

To show the available integration tests:

```bash
$ charmcraft.spread --list lxd:
lxd:ubuntu-24.04:tests/spread/deploy-bash
lxd:ubuntu-24.04:tests/spread/deploy-python
lxd:ubuntu-24.04:tests/spread/ingress-path
lxd:ubuntu-24.04:tests/spread/ingress
lxd:ubuntu-24.04:tests/spread/observability-relations
```

All tests use Juju 4; there are no Juju-version variants.

```bash
# Run all of the tests
$ charmcraft.spread -v lxd:

# Run a particular test
$ charmcraft.spread -v lxd:ubuntu-24.04:tests/spread/deploy-python
```

### Troubleshooting Failing Tests

If you're working on a test that's failing, you can use `spread` to get an interactive shell inside the test environment on failure, which allows for easier debugging. To enable this, add `--debug` to your `charmcraft.spread` commands. For example:

```bash
❯ charmcraft.spread -v --debug lxd:ubuntu-24.04:tests/spread/deploy-python
```

If the above tests were to fail, you'd be dropped into an interactive shell before the machine is reaped.

## Build charm

Build the charm in this git repository using:

```bash
charmcraft pack
```

### Deploy

```bash
# Create a model
juju add-model dev
# Enable DEBUG logging
juju model-config logging-config="<root>=INFO;unit=DEBUG"
# Deploy the charm
juju deploy ./zinc-k8s_amd64.charm \
  --resource zinc-image="$(yq '.resources.zinc-image.upstream-source' charmcraft.yaml)"
```
