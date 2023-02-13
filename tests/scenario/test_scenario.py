from unittest.mock import patch

import pytest
from ops import pebble
from scenario import State, Container, Relation

from charm import ZincCharm

@pytest.fixture(autouse=True, scope='function')
def setup():
    with patch("charm.KubernetesServicePatch"):
        with patch.object(ZincCharm, "_request_version", lambda *_: "0.0-test"):
            yield


def test_nothing_happens_on_start():
    # arrange
    state = State()
    # act
    out = state.trigger('start', ZincCharm)
    # assert

    # ignore juju log and storedstate changes
    out.juju_log = []
    out.stored_state = state.stored_state
    assert out.jsonpatch_delta(state) == []


def test_pebble_ready_admin_password():
    # arrange
    container = Container(name='zinc', can_connect=True)
    state = State(
        containers=[
            container
        ]
    )
    # act
    out = state.trigger(container.pebble_ready_event, ZincCharm)
    # assert
    assert out.status.unit == ('active', '')
    env = out.get_container('zinc').layers['zinc'].services['zinc'].environment
    stored_state = next(filter(lambda sst: sst.owner_path == 'ZincCharm', out.stored_state))
    assert env['ZINC_FIRST_ADMIN_PASSWORD'] == stored_state.content['initial_admin_password']


def test_update_status():
    # arrange
    state = State(
        containers=[
            Container(
                name='zinc',
                can_connect=True,
                layers={
                    'zinc': pebble.Layer(
                        {'services': {'zinc': {'startup': 'enabled'}}}
                    )
                })
        ]
    )
    # act
    out = state.trigger('update_status', ZincCharm)
    # assert
    assert out.status.app_version == "0.0-test"


def test_ingress_integration():
    # arrange
    relation = Relation("ingress", interface="ingress")
    state = State(
        leader=True,
        relations=[
            relation
        ]
    )
    # act
    out = state.trigger(relation.created_event, ZincCharm)
    # assert
    assert out.relations[0].local_app_data['model']
    assert out.relations[0].local_app_data['name']
    assert out.relations[0].local_app_data['host']
    assert out.relations[0].local_app_data['port']
