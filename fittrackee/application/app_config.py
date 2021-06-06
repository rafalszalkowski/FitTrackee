from typing import Dict, Union

from flask import Blueprint, current_app, request
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from fittrackee import db
from fittrackee.responses import (
    HttpResponse,
    InvalidPayloadErrorResponse,
    handle_error_and_return_response,
)
from fittrackee.users.decorators import authenticate_as_admin

from .models import AppConfig
from .utils import update_app_config_from_database, verify_app_config

config_blueprint = Blueprint('config', __name__)


@config_blueprint.route('/config', methods=['GET'])
def get_application_config() -> Union[Dict, HttpResponse]:
    """
    Get Application config

    **Example request**:

    .. sourcecode:: http

      GET /api/config HTTP/1.1
      Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "data": {
          "gpx_limit_import": 10,
          "is_registration_enabled": false,
          "max_single_file_size": 1048576,
          "max_zip_file_size": 10485760,
          "max_users": 0,
          "map_attribution": "&copy; <a href=http://www.openstreetmap.org/copyright>OpenStreetMap</a> contributors"
        },
        "status": "success"
      }

    :statuscode 200: success
    :statuscode 500: Error on getting configuration.
    """

    try:
        config = AppConfig.query.one()
        return {'status': 'success', 'data': config.serialize()}
    except (MultipleResultsFound, NoResultFound) as e:
        return handle_error_and_return_response(
            e, message='Error on getting configuration.'
        )


@config_blueprint.route('/config', methods=['PATCH'])
@authenticate_as_admin
def update_application_config(auth_user_id: int) -> Union[Dict, HttpResponse]:
    """
    Update Application config

    Authenticated user must be an admin

    **Example request**:

    .. sourcecode:: http

      GET /api/config HTTP/1.1
      Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "data": {
          "gpx_limit_import": 10,
          "is_registration_enabled": true,
          "max_single_file_size": 1048576,
          "max_zip_file_size": 10485760,
          "max_users": 10
        },
        "status": "success"
      }

    :param integer auth_user_id: authenticate user id (from JSON Web Token)

    :<json integer gpx_limit_import: max number of files in zip archive
    :<json boolean is_registration_enabled: is registration enabled ?
    :<json integer max_single_file_size: max size of a single file
    :<json integer max_zip_file_size: max size of a zip archive
    :<json integer max_users: max users allowed to register on instance

    :reqheader Authorization: OAuth 2.0 Bearer Token

    :statuscode 200: success
    :statuscode 400: invalid payload
    :statuscode 401:
        - Provide a valid auth token.
        - Signature expired. Please log in again.
        - Invalid token. Please log in again.
    :statuscode 403: You do not have permissions.
    :statuscode 500: Error on updating configuration.
    """
    config_data = request.get_json()
    if not config_data:
        return InvalidPayloadErrorResponse()

    ret = verify_app_config(config_data)
    if ret:
        return InvalidPayloadErrorResponse(message=ret)

    try:
        config = AppConfig.query.one()
        if 'federation_enabled' in config_data:
            config.federation_enabled = config_data.get('federation_enabled')
        if 'gpx_limit_import' in config_data:
            config.gpx_limit_import = config_data.get('gpx_limit_import')
        if 'max_single_file_size' in config_data:
            config.max_single_file_size = config_data.get(
                'max_single_file_size'
            )
        if 'max_zip_file_size' in config_data:
            config.max_zip_file_size = config_data.get('max_zip_file_size')
        if 'max_users' in config_data:
            config.max_users = config_data.get('max_users')

        if config.max_zip_file_size < config.max_single_file_size:
            return InvalidPayloadErrorResponse(
                'Max. size of zip archive must be equal or greater than '
                'max. size of uploaded files'
            )
        db.session.commit()
        update_app_config_from_database(current_app, config)
        return {'status': 'success', 'data': config.serialize()}

    except Exception as e:
        return handle_error_and_return_response(
            e, message='Error on updating configuration.'
        )


@config_blueprint.route('/ping', methods=['GET'])
def health_check() -> Union[Dict, HttpResponse]:
    """health check endpoint

    **Example request**:

    .. sourcecode:: http

      GET /api/ping HTTP/1.1
      Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "message": "pong!",
        "status": "success"
      }

    :statuscode 200: success

    """
    return {'status': 'success', 'message': 'pong!'}
