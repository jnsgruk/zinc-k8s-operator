# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import PropertyMock, patch

import pytest
from ops.pebble import ServiceStatus
from ops.testing import ActiveStatus, Container, Context, PeerRelation, Secret, State, TCPPort

from charm import ZincCharm
from zinc import Zinc


@pytest.fixture
def charm():
    with patch("charm.Zinc.version", new_callable=PropertyMock(return_value="0.2.6")):
        yield ZincCharm


@pytest.fixture
def loaded_ctx(charm):
    ctx = Context(charm)
    container = Container(name="zinc", can_connect=True)
    return (ctx, container)


def _fetch_zinc_password_from_pebble_plan(state: State):
    return (
        state.get_container("zinc")
        .layers["zinc"]
        .services["zinc"]
        .environment["ZINC_FIRST_ADMIN_PASSWORD"]
    )


def test_zinc_pebble_ready(loaded_ctx):
    ctx, container = loaded_ctx
    state = State(containers=[container])

    result = ctx.run(ctx.on.pebble_ready(container=container), state)

    assert result.get_container("zinc").layers["zinc"] == Zinc().pebble_layer("")
    assert result.get_container("zinc").service_statuses == {"zinc": ServiceStatus.ACTIVE}
    assert result.opened_ports == frozenset({TCPPort(4080)})
    assert result.workload_version == "0.2.6"
    assert result.unit_status == ActiveStatus()


def test_update_status(loaded_ctx):
    ctx, container = loaded_ctx
    state = State(containers=[container])

    result = ctx.run(ctx.on.pebble_ready(container=container), state)
    assert result.workload_version == "0.2.6"

    with patch("charm.Zinc.version", new_callable=PropertyMock(return_value="0.4.0")):
        result = ctx.run(ctx.on.update_status(), result)
        assert result.workload_version == "0.4.0"

    assert result.unit_status == ActiveStatus()


def test_zinc_password_no_relation(loaded_ctx):
    ctx, container = loaded_ctx
    state = State(containers=[container])

    result = ctx.run(ctx.on.pebble_ready(container=container), state)

    password = _fetch_zinc_password_from_pebble_plan(result)
    assert len(password) == 0


def test_zinc_password_from_relation(loaded_ctx):
    ctx, container = loaded_ctx
    secret = Secret(tracked_content={"password": "deadbeef"}, owner="app")
    state = State(
        containers=[container],
        secrets={secret},
        relations=[
            PeerRelation(
                endpoint="zinc-peers", local_app_data={"initial-admin-password": secret.id}
            )
        ],
    )

    result = ctx.run(ctx.on.pebble_ready(container=container), state)

    password = _fetch_zinc_password_from_pebble_plan(result)
    assert password == "deadbeef"


def test_zinc_password_create_as_leader(loaded_ctx):
    ctx, container = loaded_ctx
    state = State(
        containers=[container],
        leader=True,
        relations=[PeerRelation(endpoint="zinc-peers", local_app_data={})],
    )

    result = ctx.run(ctx.on.pebble_ready(container=container), state)

    password = _fetch_zinc_password_from_pebble_plan(result)
    assert len(password) == 32


def test_zinc_password_create_as_non_leader(loaded_ctx):
    ctx, container = loaded_ctx
    state = State(
        containers=[container],
        leader=False,
        relations=[PeerRelation(endpoint="zinc-peers", local_app_data={})],
    )

    result = ctx.run(ctx.on.pebble_ready(container=container), state)

    password = _fetch_zinc_password_from_pebble_plan(result)
    assert len(password) == 0
