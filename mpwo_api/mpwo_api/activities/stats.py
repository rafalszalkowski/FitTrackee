from datetime import datetime

from flask import Blueprint, jsonify, request
from mpwo_api import appLog

from ..users.models import User
from ..users.utils import authenticate
from .models import Activity, Sport, convert_timedelta_to_integer

stats_blueprint = Blueprint('stats', __name__)


def get_activities(user_id, type):
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            response_object = {
                'status': 'not found',
                'message': 'User does not exist.'
            }
            return jsonify(response_object), 404

        params = request.args.copy()
        date_from = params.get('from')
        date_to = params.get('to')
        sport_id = params.get('sport_id')
        time = params.get('time')

        if type == 'by_sport':
            sport_id = params.get('sport_id')
            if sport_id:
                sport = Sport.query.filter_by(id=sport_id).first()
                if not sport:
                    print('not sport')
                    response_object = {
                        'status': 'not found',
                        'message': 'Sport does not exist.'
                    }
                    return jsonify(response_object), 404

        activities = Activity.query.filter(
            Activity.user_id == user_id,
            Activity.activity_date >= datetime.strptime(date_from, '%Y-%m-%d')
            if date_from else True,
            Activity.activity_date <= datetime.strptime(date_to, '%Y-%m-%d')
            if date_to else True,
            Activity.sport_id == sport_id if sport_id else True,
        ).order_by(
            Activity.activity_date.asc()
        ).all()

        activities_list = {}
        for activity in activities:
            if type == 'by_sport':
                sport_id = activity.sport_id
                if sport_id not in activities_list:
                    activities_list[sport_id] = {
                        'nb_activities': 0,
                        'total_distance': 0.,
                        'total_duration': 0,
                    }
                activities_list[sport_id]['nb_activities'] += 1
                activities_list[sport_id]['total_distance'] += \
                    float(activity.distance)
                activities_list[sport_id]['total_duration'] += \
                    convert_timedelta_to_integer(activity.duration)

            else:
                if time == 'week':
                    time_period = datetime.strftime(activity.activity_date, "%Y-W%U")  # noqa
                elif time == 'weekm':  # week start Monday
                    time_period = datetime.strftime(activity.activity_date, "%Y-W%W")  # noqa
                elif time == 'month':
                    time_period = datetime.strftime(activity.activity_date, "%Y-%m")  # noqa
                elif time == 'year' or not time:
                    time_period = datetime.strftime(activity.activity_date, "%Y")  # noqa
                else:
                    response_object = {
                        'status': 'fail',
                        'message': 'Invalid time period.'
                    }
                    return jsonify(response_object), 400
                sport_id = activity.sport_id
                if time_period not in activities_list:
                    activities_list[time_period] = {}
                if sport_id not in activities_list[time_period]:
                    activities_list[time_period][sport_id] = {
                        'nb_activities': 0,
                        'total_distance': 0.,
                        'total_duration': 0,
                    }
                activities_list[time_period][sport_id]['nb_activities'] += 1
                activities_list[time_period][sport_id]['total_distance'] += \
                    float(activity.distance)
                activities_list[time_period][sport_id]['total_duration'] += \
                    convert_timedelta_to_integer(activity.duration)

        response_object = {
            'status': 'success',
            'data': {
                'statistics': activities_list
            }
        }
        code = 200
    except Exception as e:
        appLog.error(e)
        response_object = {
            'status': 'error',
            'message': 'Error. Please try again or contact the administrator.'
        }
        code = 500
    return jsonify(response_object), code


@stats_blueprint.route('/stats/<int:user_id>/by_time', methods=['GET'])
@authenticate
def get_activities_by_time(auth_user_id, user_id):
    """Get activities statistics for a user"""
    return get_activities(user_id, 'by_time')


@stats_blueprint.route('/stats/<int:user_id>/by_sport', methods=['GET'])
@authenticate
def get_activities_by_sport(auth_user_id, user_id):
    return get_activities(user_id, 'by_sport')
