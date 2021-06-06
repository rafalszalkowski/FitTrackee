import json
from uuid import uuid4

from flask import Flask

from fittrackee.federation.models import Actor


class TestFederationUser:
    def test_it_returns_404_if_user_does_not_exist(self, app: Flask) -> None:
        client = app.test_client()
        response = client.get(
            f'/federation/user/{uuid4().hex}',
        )

        assert response.status_code == 404
        data = json.loads(response.data.decode())
        assert 'not found' in data['status']
        assert 'User does not exist.' in data['message']

    def test_it_returns_json_resource_descriptor_as_content_type(
        self, app: Flask, actor_1: Actor
    ) -> None:
        client = app.test_client()
        response = client.get(
            f'/federation/user/{actor_1.preferred_username}',
        )

        assert response.status_code == 200
        assert response.content_type == 'application/jrd+json; charset=utf-8'

    def test_it_returns_actor(self, app: Flask, actor_1: Actor) -> None:
        client = app.test_client()
        response = client.get(
            f'/federation/user/{actor_1.preferred_username}',
        )

        data = json.loads(response.data.decode())
        assert data == actor_1.serialize()
