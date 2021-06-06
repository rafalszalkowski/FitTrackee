import json

from fittrackee.federation.models import Actor
from flask import Flask


class TestWellKnowNodeInfo:
    def test_it_returns_error_if_federation_is_disabled(
        self, app: Flask, actor_1: Actor
    ) -> None:
        client = app.test_client()
        response = client.get(
            '/.well-known/nodeinfo',
            content_type='application/json',
        )

        assert response.status_code == 403
        data = json.loads(response.data.decode())
        assert 'error' in data['status']
        assert (
            'Error. Federation is disabled for this instance.'
            in data['message']
        )

    def test_it_returns_instance_nodeinfo_url_if_federation_is_enabled(
        self, app_with_federation: Flask, actor_1: Actor
    ) -> None:
        client = app_with_federation.test_client()
        response = client.get(
            '/.well-known/nodeinfo',
            content_type='application/json',
        )

        assert response.status_code == 200
        data = json.loads(response.data.decode())
        nodeinfo_url = (
            f'https://{app_with_federation.config["AP_DOMAIN"]}/nodeinfo/2.0'
        )
        assert data == {
            'links': [
                {
                    'rel': 'http://nodeinfo.diaspora.software/ns/schema/2.0',
                    'href': nodeinfo_url,
                }
            ]
        }


class TestNodeInfo:
    def test_it_returns_error_if_federation_is_disabled(
        self, app: Flask, actor_1: Actor
    ) -> None:
        client = app.test_client()
        response = client.get(
            '/nodeinfo/2.0',
            content_type='application/json',
        )

        assert response.status_code == 403
        data = json.loads(response.data.decode())
        assert 'error' in data['status']
        assert (
            'Error. Federation is disabled for this instance.'
            in data['message']
        )

    def test_it_returns_instance_nodeinfo_if_federation_is_enabled(
        self,
        app_with_federation: Flask,
        actor_1: Actor,
        app_version: str,
    ) -> None:
        client = app_with_federation.test_client()
        response = client.get(
            '/nodeinfo/2.0',
            content_type='application/json',
        )

        assert response.status_code == 200
        data = json.loads(response.data.decode())
        assert data == {
            'version': '2.0',
            'software': {'name': 'fittrackee', 'version': app_version},
            'protocols': ['activitypub'],
            'usage': {'users': {'total': 1}, 'localWorkouts': 0},
            'openRegistrations': True,
        }
