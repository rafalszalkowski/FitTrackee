from datetime import timedelta

import gpxpy.gpx

from .utils_weather import get_weather


class ActivityGPXException(Exception):
    def __init__(self, status, message, e):
        self.status = status
        self.message = message
        self.e = e


def open_gpx_file(gpx_file):
    gpx_file = open(gpx_file, 'r')
    gpx = gpxpy.parse(gpx_file)
    if len(gpx.tracks) == 0:
        return None
    return gpx


def get_gpx_data(parsed_gpx, max_speed, start, stopped_time_btwn_seg):
    gpx_data = {'max_speed': (max_speed / 1000) * 3600, 'start': start}

    duration = parsed_gpx.get_duration()
    gpx_data['duration'] = timedelta(seconds=duration) + stopped_time_btwn_seg

    ele = parsed_gpx.get_elevation_extremes()
    gpx_data['elevation_max'] = ele.maximum
    gpx_data['elevation_min'] = ele.minimum

    hill = parsed_gpx.get_uphill_downhill()
    gpx_data['uphill'] = hill.uphill
    gpx_data['downhill'] = hill.downhill

    mv = parsed_gpx.get_moving_data()
    gpx_data['moving_time'] = timedelta(seconds=mv.moving_time)
    gpx_data['stop_time'] = (timedelta(seconds=mv.stopped_time)
                             + stopped_time_btwn_seg)
    distance = mv.moving_distance + mv.stopped_distance
    gpx_data['distance'] = distance / 1000

    average_speed = distance / mv.moving_time if mv.moving_time > 0 else 0
    gpx_data['average_speed'] = (average_speed / 1000) * 3600

    return gpx_data


def get_gpx_info(gpx_file, update_map_data=True, update_weather_data=True):
    gpx = open_gpx_file(gpx_file)
    if gpx is None:
        return None

    gpx_data = {
        'name': gpx.tracks[0].name,
        'segments': []
    }
    max_speed = 0
    start = 0
    map_data = []
    weather_data = []
    segments_nb = len(gpx.tracks[0].segments)
    prev_seg_last_point = None
    no_stopped_time = timedelta(seconds=0)
    stopped_time_btwn_seg = no_stopped_time

    for segment_idx, segment in enumerate(gpx.tracks[0].segments):
        segment_start = 0
        segment_points_nb = len(segment.points)
        for point_idx, point in enumerate(segment.points):
            if point_idx == 0:
                # first gpx point => get weather
                if start == 0:
                    start = point.time
                    if update_weather_data:
                        weather_data.append(get_weather(point))

                # if a previous segment exists, calculate stopped time between
                # the two segments
                if prev_seg_last_point:
                    stopped_time_btwn_seg = point.time - prev_seg_last_point

            # last segment point
            if point_idx == (segment_points_nb - 1):
                prev_seg_last_point = point.time

                # last gpx point => get weather
                if segment_idx == (segments_nb - 1) and update_weather_data:
                    weather_data.append(get_weather(point))

            if update_map_data:
                map_data.append([
                    point.longitude, point.latitude
                ])
        segment_max_speed = (segment.get_moving_data().max_speed
                             if segment.get_moving_data().max_speed
                             else 0)

        if segment_max_speed > max_speed:
            max_speed = segment_max_speed

        segment_data = get_gpx_data(
            segment, segment_max_speed, segment_start, no_stopped_time
        )
        segment_data['idx'] = segment_idx
        gpx_data['segments'].append(segment_data)

    full_gpx_data = get_gpx_data(gpx, max_speed, start, stopped_time_btwn_seg)
    gpx_data = {**gpx_data, **full_gpx_data}

    if update_map_data:
        bounds = gpx.get_bounds()
        gpx_data['bounds'] = [
            bounds.min_latitude,
            bounds.min_longitude,
            bounds.max_latitude,
            bounds.max_longitude
        ]

    return gpx_data, map_data, weather_data


def get_chart_data(gpx_file):
    gpx = open_gpx_file(gpx_file)
    if gpx is None:
        return None

    chart_data = []
    first_point = None
    previous_point = None
    previous_distance = 0

    for segment_idx, segment in enumerate(gpx.tracks[0].segments):
        for point_idx, point in enumerate(segment.points):
            if segment_idx == 0 and point_idx == 0:
                first_point = point
            distance = (point.distance_3d(previous_point)
                        if (point.elevation
                            and previous_point
                            and previous_point.elevation)
                        else point.distance_2d(previous_point)
                        )
            distance = 0 if distance is None else distance
            distance += previous_distance
            speed = (round((segment.get_speed(point_idx) / 1000)*3600, 2)
                     if segment.get_speed(point_idx) is not None
                     else 0)
            chart_data.append({
                'distance': (round(distance / 1000, 2)
                             if distance is not None else 0),
                'duration': point.time_difference(first_point),
                'elevation': (round(point.elevation, 1)
                              if point.elevation is not None else 0),
                'latitude': point.latitude,
                'longitude': point.longitude,
                'speed': speed,
                'time': point.time,
            })
            previous_point = point
            previous_distance = distance

    return chart_data