# Contributing

## Overview

This documents explains the processes and practices recommended for contributing enhancements to
this operator.

- Generally, before developing enhancements to this charm, you should consider [opening an issue
  ](https://github.com/jnsgruk/zinc-k8s-operator/issues) explaining your use case.
- If you would like to chat with us about your use-cases or proposed implementation, you can reach
  us at [Canonical Mattermost public channel](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
- Familiarising yourself with the [Charmed Operator Framework](https://juju.is/docs/sdk) library
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

```shell
make fmt           # update your code according to linting rules
make lint          # code style
make unit          # unit tests
```

To create the environment manually:

```bash
uv venv
source .venv/bin/activate
uv sync --all-extras
```

## Running integration tests

Integration testing is taken care of using `spread`. Currently, there are two supported backends -
tests can either be run in LXD virtual machines, or on a pre-provisioned server (such as a Github
Actions runner or development VM).

To show the available integration tests, you can:

```bash
$ charmcraft test --list lxd:
lxd:ubuntu-24.04:tests/spread/deploy:juju_3_5
lxd:ubuntu-24.04:tests/spread/deploy:juju_3_6
lxd:ubuntu-24.04:tests/spread/ingress-path:juju_3_5
lxd:ubuntu-24.04:tests/spread/ingress-path:juju_3_6
lxd:ubuntu-24.04:tests/spread/ingress:juju_3_5
lxd:ubuntu-24.04:tests/spread/ingress:juju_3_6
lxd:ubuntu-24.04:tests/spread/observability-relations:juju_3_6
lxd:ubuntu-24.04:tests/spread/observability-relations:juju_3_5
```

From there, you can either run all of the tests, or a selection:

```bash
# Run all of the tests
$ charmcraft test -v lxd:

# Run a particular test
$ charmcraft test -v lxd:ubuntu-24.04:tests/spread/deploy:juju_3_5
```

To run any of the tests on a locally provisioned machine, use the `github-ci` backend, e.g.

```bash
# List available tests
$ charmcraft test --list github-ci:

# Run all of the tests
$ charmcraft test -v github-ci:

# Run a particular test
$ charmcraft test -v github-ci:ubuntu-24.04:tests/spread/deploy:juju_3_5
```

## Build charm

Build the charm in this git repository using:

```shell
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
