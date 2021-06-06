from datetime import datetime

import pytest
from flask import Flask

from fittrackee.users.exceptions import (
    FollowRequestAlreadyProcessedError,
    NotExistingFollowRequestError,
)
from fittrackee.users.models import FollowRequest, User


class TestUserModel:
    def test_user_model(self, app: Flask, user_1: User) -> None:
        assert '<User \'test\'>' == str(user_1)

        serialized_user = user_1.serialize()
        assert 'test' == serialized_user['username']
        assert 'created_at' in serialized_user
        assert serialized_user['admin'] is False
        assert serialized_user['first_name'] is None
        assert serialized_user['last_name'] is None
        assert serialized_user['bio'] is None
        assert serialized_user['location'] is None
        assert serialized_user['birth_date'] is None
        assert serialized_user['picture'] is False
        assert serialized_user['timezone'] is None
        assert serialized_user['weekm'] is False
        assert serialized_user['language'] is None
        assert serialized_user['nb_sports'] == 0
        assert serialized_user['nb_workouts'] == 0
        assert serialized_user['total_distance'] == 0
        assert serialized_user['total_duration'] == '0:00:00'

    def test_encode_auth_token(self, app: Flask, user_1: User) -> None:
        auth_token = user_1.encode_auth_token(user_1.id)
        assert isinstance(auth_token, str)

    def test_encode_password_token(self, app: Flask, user_1: User) -> None:
        password_token = user_1.encode_password_reset_token(user_1.id)
        assert isinstance(password_token, str)

    def test_decode_auth_token(self, app: Flask, user_1: User) -> None:
        auth_token = user_1.encode_auth_token(user_1.id)
        assert isinstance(auth_token, str)
        assert User.decode_auth_token(auth_token) == user_1.id


class TestUserFollowingModel:
    def test_user_2_sends_follow_requests_to_user_1(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
    ) -> None:
        follow_request = user_2.send_follow_request_to(user_1)

        assert follow_request in user_2.sent_follow_requests.all()

    def test_user_1_receives_follow_requests_from_user_2(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
    ) -> None:
        follow_request = user_2.send_follow_request_to(user_1)

        assert follow_request in user_1.received_follow_requests.all()

    def test_user_has_pending_follow_request(
        self,
        app: Flask,
        user_1: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        assert (
            follow_request_from_user_2_to_user_1
            in user_1.pending_follow_requests
        )

    def test_user_has_no_pending_follow_request(
        self,
        app_with_federation: Flask,
        user_1: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        follow_request_from_user_2_to_user_1.updated_at = datetime.now()
        assert user_1.pending_follow_requests == []

    def test_user_approves_follow_request(
        self,
        app_with_federation: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
        follow_request_from_user_3_to_user_1: FollowRequest,
    ) -> None:
        follow_request = user_1.approves_follow_request_from(user_2)

        assert follow_request.is_approved
        assert user_1.pending_follow_requests == [
            follow_request_from_user_3_to_user_1
        ]

    def test_user_refuses_follow_request(
        self,
        app_with_federation: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        follow_request = user_1.refuses_follow_request_from(user_2)

        assert not follow_request.is_approved
        assert user_1.pending_follow_requests == []

    def test_it_raises_error_if_follow_request_does_not_exists(
        self,
        app_with_federation: Flask,
        user_1: User,
        user_2: User,
    ) -> None:
        with pytest.raises(NotExistingFollowRequestError):
            user_1.approves_follow_request_from(user_2)

    def test_it_raises_error_if_user_approves_follow_request_already_processed(  # noqa
        self,
        app_with_federation: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        follow_request_from_user_2_to_user_1.updated_at = datetime.now()

        with pytest.raises(FollowRequestAlreadyProcessedError):
            user_1.approves_follow_request_from(user_2)
