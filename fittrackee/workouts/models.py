import datetime
import os
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.base import Connection
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.session import Session, object_session
from sqlalchemy.types import JSON, Enum

from fittrackee import BaseModel, db

from .utils_files import get_absolute_file_path
from .utils_format import convert_in_duration, convert_value_to_integer
from .utils_id import encode_uuid

record_types = [
    'AS',  # 'Best Average Speed'
    'FD',  # 'Farthest Distance'
    'LD',  # 'Longest Duration'
    'MS',  # 'Max speed'
]


def update_records(
    user_id: int, sport_id: int, connection: Connection, session: Session
) -> None:
    record_table = Record.__table__
    new_records = Workout.get_user_workout_records(user_id, sport_id)
    for record_type, record_data in new_records.items():
        if record_data['record_value']:
            record = Record.query.filter_by(
                user_id=user_id, sport_id=sport_id, record_type=record_type
            ).first()
            if record:
                value = convert_value_to_integer(
                    record_type, record_data['record_value']
                )
                connection.execute(
                    record_table.update()
                    .where(record_table.c.id == record.id)
                    .values(
                        value=value,
                        workout_id=record_data['workout'].id,
                        workout_uuid=record_data['workout'].uuid,
                        workout_date=record_data['workout'].workout_date,
                    )
                )
            else:
                new_record = Record(
                    workout=record_data['workout'], record_type=record_type
                )
                new_record.value = record_data['record_value']  # type: ignore
                session.add(new_record)
        else:
            connection.execute(
                record_table.delete()
                .where(record_table.c.user_id == user_id)
                .where(record_table.c.sport_id == sport_id)
                .where(record_table.c.record_type == record_type)
            )


class Sport(BaseModel):
    __tablename__ = 'sports'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(50), unique=True, nullable=False)
    img = db.Column(db.String(255), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    workouts = db.relationship(
        'Workout', lazy=True, backref=db.backref('sports', lazy='joined')
    )
    records = db.relationship(
        'Record', lazy=True, backref=db.backref('sports', lazy='joined')
    )

    def __repr__(self) -> str:
        return f'<Sport {self.label!r}>'

    def __init__(self, label: str) -> None:
        self.label = label

    def serialize(self, is_admin: Optional[bool] = False) -> Dict:
        serialized_sport = {
            'id': self.id,
            'label': self.label,
            'img': self.img,
            'is_active': self.is_active,
        }
        if is_admin:
            serialized_sport['has_workouts'] = len(self.workouts) > 0
        return serialized_sport


class Workout(BaseModel):
    __tablename__ = 'workouts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(
        postgresql.UUID(as_uuid=True),
        default=uuid4,
        unique=True,
        nullable=False,
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sport_id = db.Column(
        db.Integer, db.ForeignKey('sports.id'), nullable=False
    )
    title = db.Column(db.String(255), nullable=True)
    gpx = db.Column(db.String(255), nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modification_date = db.Column(
        db.DateTime, onupdate=datetime.datetime.utcnow
    )
    workout_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Interval, nullable=False)
    pauses = db.Column(db.Interval, nullable=True)
    moving = db.Column(db.Interval, nullable=True)
    distance = db.Column(db.Numeric(6, 3), nullable=True)  # kilometers
    min_alt = db.Column(db.Numeric(6, 2), nullable=True)  # meters
    max_alt = db.Column(db.Numeric(6, 2), nullable=True)  # meters
    descent = db.Column(db.Numeric(7, 2), nullable=True)  # meters
    ascent = db.Column(db.Numeric(7, 2), nullable=True)  # meters
    max_speed = db.Column(db.Numeric(6, 2), nullable=True)  # km/h
    ave_speed = db.Column(db.Numeric(6, 2), nullable=True)  # km/h
    bounds = db.Column(postgresql.ARRAY(db.Float), nullable=True)
    map = db.Column(db.String(255), nullable=True)
    map_id = db.Column(db.String(50), nullable=True)
    weather_start = db.Column(JSON, nullable=True)
    weather_end = db.Column(JSON, nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    segments = db.relationship(
        'WorkoutSegment',
        lazy=True,
        cascade='all, delete',
        backref=db.backref('workouts', lazy='joined', single_parent=True),
    )
    records = db.relationship(
        'Record',
        lazy=True,
        cascade='all, delete',
        backref=db.backref('workouts', lazy='joined', single_parent=True),
    )

    def __str__(self) -> str:
        return f'<Workout \'{self.sports.label}\' - {self.workout_date}>'

    def __init__(
        self,
        user_id: int,
        sport_id: int,
        workout_date: datetime.datetime,
        distance: float,
        duration: datetime.timedelta,
    ) -> None:
        self.user_id = user_id
        self.sport_id = sport_id
        self.workout_date = workout_date
        self.distance = distance
        self.duration = duration

    @property
    def short_id(self) -> str:
        return encode_uuid(self.uuid)

    def serialize(self, params: Optional[Dict] = None) -> Dict:
        date_from = params.get('from') if params else None
        date_to = params.get('to') if params else None
        distance_from = params.get('distance_from') if params else None
        distance_to = params.get('distance_to') if params else None
        duration_from = params.get('duration_from') if params else None
        duration_to = params.get('duration_to') if params else None
        ave_speed_from = params.get('ave_speed_from') if params else None
        ave_speed_to = params.get('ave_speed_to') if params else None
        max_speed_from = params.get('max_speed_from') if params else None
        max_speed_to = params.get('max_speed_to') if params else None
        sport_id = params.get('sport_id') if params else None
        previous_workout = (
            Workout.query.filter(
                Workout.id != self.id,
                Workout.user_id == self.user_id,
                Workout.sport_id == sport_id if sport_id else True,
                Workout.workout_date <= self.workout_date,
                Workout.workout_date
                >= datetime.datetime.strptime(date_from, '%Y-%m-%d')
                if date_from
                else True,
                Workout.workout_date
                <= datetime.datetime.strptime(date_to, '%Y-%m-%d')
                if date_to
                else True,
                Workout.distance >= int(distance_from)
                if distance_from
                else True,
                Workout.distance <= int(distance_to) if distance_to else True,
                Workout.duration >= convert_in_duration(duration_from)
                if duration_from
                else True,
                Workout.duration <= convert_in_duration(duration_to)
                if duration_to
                else True,
                Workout.ave_speed >= float(ave_speed_from)
                if ave_speed_from
                else True,
                Workout.ave_speed <= float(ave_speed_to)
                if ave_speed_to
                else True,
                Workout.max_speed >= float(max_speed_from)
                if max_speed_from
                else True,
                Workout.max_speed <= float(max_speed_to)
                if max_speed_to
                else True,
            )
            .order_by(Workout.workout_date.desc())
            .first()
        )
        next_workout = (
            Workout.query.filter(
                Workout.id != self.id,
                Workout.user_id == self.user_id,
                Workout.sport_id == sport_id if sport_id else True,
                Workout.workout_date >= self.workout_date,
                Workout.workout_date
                >= datetime.datetime.strptime(date_from, '%Y-%m-%d')
                if date_from
                else True,
                Workout.workout_date
                <= datetime.datetime.strptime(date_to, '%Y-%m-%d')
                if date_to
                else True,
                Workout.distance >= int(distance_from)
                if distance_from
                else True,
                Workout.distance <= int(distance_to) if distance_to else True,
                Workout.duration >= convert_in_duration(duration_from)
                if duration_from
                else True,
                Workout.duration <= convert_in_duration(duration_to)
                if duration_to
                else True,
                Workout.ave_speed >= float(ave_speed_from)
                if ave_speed_from
                else True,
                Workout.ave_speed <= float(ave_speed_to)
                if ave_speed_to
                else True,
            )
            .order_by(Workout.workout_date.asc())
            .first()
        )
        return {
            'id': self.short_id,  # WARNING: client use uuid as id
            'user': self.user.username,
            'sport_id': self.sport_id,
            'title': self.title,
            'creation_date': self.creation_date,
            'modification_date': self.modification_date,
            'workout_date': self.workout_date,
            'duration': str(self.duration) if self.duration else None,
            'pauses': str(self.pauses) if self.pauses else None,
            'moving': str(self.moving) if self.moving else None,
            'distance': float(self.distance) if self.distance else None,
            'min_alt': float(self.min_alt) if self.min_alt else None,
            'max_alt': float(self.max_alt) if self.max_alt else None,
            'descent': float(self.descent) if self.descent else None,
            'ascent': float(self.ascent) if self.ascent else None,
            'max_speed': float(self.max_speed) if self.max_speed else None,
            'ave_speed': float(self.ave_speed) if self.ave_speed else None,
            'with_gpx': self.gpx is not None,
            'bounds': [float(bound) for bound in self.bounds]
            if self.bounds
            else [],  # noqa
            'previous_workout': previous_workout.short_id
            if previous_workout
            else None,  # noqa
            'next_workout': next_workout.short_id if next_workout else None,
            'segments': [segment.serialize() for segment in self.segments],
            'records': [record.serialize() for record in self.records],
            'map': self.map_id if self.map else None,
            'weather_start': self.weather_start,
            'weather_end': self.weather_end,
            'notes': self.notes,
        }

    @classmethod
    def get_user_workout_records(
        cls, user_id: int, sport_id: int, as_integer: Optional[bool] = False
    ) -> Dict:
        record_types_columns = {
            'AS': 'ave_speed',  # 'Average speed'
            'FD': 'distance',  # 'Farthest Distance'
            'LD': 'moving',  # 'Longest Duration'
            'MS': 'max_speed',  # 'Max speed'
        }
        records = {}
        for record_type, column in record_types_columns.items():
            column_sorted = getattr(getattr(Workout, column), 'desc')()
            record_workout = (
                Workout.query.filter_by(user_id=user_id, sport_id=sport_id)
                .order_by(column_sorted, Workout.workout_date)
                .first()
            )
            records[record_type] = dict(
                record_value=(
                    getattr(record_workout, column) if record_workout else None
                ),
                workout=record_workout,
            )
        return records


@listens_for(Workout, 'after_insert')
def on_workout_insert(
    mapper: Mapper, connection: Connection, workout: Workout
) -> None:
    @listens_for(db.Session, 'after_flush', once=True)
    def receive_after_flush(session: Session, context: Any) -> None:
        update_records(
            workout.user_id, workout.sport_id, connection, session
        )  # noqa


@listens_for(Workout, 'after_update')
def on_workout_update(
    mapper: Mapper, connection: Connection, workout: Workout
) -> None:
    if object_session(workout).is_modified(
        workout, include_collections=True
    ):  # noqa

        @listens_for(db.Session, 'after_flush', once=True)
        def receive_after_flush(session: Session, context: Any) -> None:
            sports_list = [workout.sport_id]
            records = Record.query.filter_by(workout_id=workout.id).all()
            for rec in records:
                if rec.sport_id not in sports_list:
                    sports_list.append(rec.sport_id)
            for sport_id in sports_list:
                update_records(workout.user_id, sport_id, connection, session)


@listens_for(Workout, 'after_delete')
def on_workout_delete(
    mapper: Mapper, connection: Connection, old_record: 'Record'
) -> None:
    @listens_for(db.Session, 'after_flush', once=True)
    def receive_after_flush(session: Session, context: Any) -> None:
        if old_record.map:
            os.remove(get_absolute_file_path(old_record.map))
        if old_record.gpx:
            os.remove(get_absolute_file_path(old_record.gpx))


class WorkoutSegment(BaseModel):
    __tablename__ = 'workout_segments'
    workout_id = db.Column(
        db.Integer, db.ForeignKey('workouts.id'), primary_key=True
    )
    workout_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)
    segment_id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Interval, nullable=False)
    pauses = db.Column(db.Interval, nullable=True)
    moving = db.Column(db.Interval, nullable=True)
    distance = db.Column(db.Numeric(6, 3), nullable=True)  # kilometers
    min_alt = db.Column(db.Numeric(6, 2), nullable=True)  # meters
    max_alt = db.Column(db.Numeric(6, 2), nullable=True)  # meters
    descent = db.Column(db.Numeric(7, 2), nullable=True)  # meters
    ascent = db.Column(db.Numeric(7, 2), nullable=True)  # meters
    max_speed = db.Column(db.Numeric(6, 2), nullable=True)  # km/h
    ave_speed = db.Column(db.Numeric(6, 2), nullable=True)  # km/h

    def __str__(self) -> str:
        return (
            f'<Segment \'{self.segment_id}\' '
            f'for workout \'{encode_uuid(self.workout_uuid)}\'>'
        )

    def __init__(
        self, segment_id: int, workout_id: int, workout_uuid: UUID
    ) -> None:
        self.segment_id = segment_id
        self.workout_id = workout_id
        self.workout_uuid = workout_uuid

    def serialize(self) -> Dict:
        return {
            'workout_id': encode_uuid(self.workout_uuid),
            'segment_id': self.segment_id,
            'duration': str(self.duration) if self.duration else None,
            'pauses': str(self.pauses) if self.pauses else None,
            'moving': str(self.moving) if self.moving else None,
            'distance': float(self.distance) if self.distance else None,
            'min_alt': float(self.min_alt) if self.min_alt else None,
            'max_alt': float(self.max_alt) if self.max_alt else None,
            'descent': float(self.descent) if self.descent else None,
            'ascent': float(self.ascent) if self.ascent else None,
            'max_speed': float(self.max_speed) if self.max_speed else None,
            'ave_speed': float(self.ave_speed) if self.ave_speed else None,
        }


class Record(BaseModel):
    __tablename__ = "records"
    __table_args__ = (
        db.UniqueConstraint(
            'user_id', 'sport_id', 'record_type', name='user_sports_records'
        ),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sport_id = db.Column(
        db.Integer, db.ForeignKey('sports.id'), nullable=False
    )
    workout_id = db.Column(
        db.Integer, db.ForeignKey('workouts.id'), nullable=False
    )
    workout_uuid = db.Column(postgresql.UUID(as_uuid=True), nullable=False)
    record_type = db.Column(Enum(*record_types, name="record_types"))
    workout_date = db.Column(db.DateTime, nullable=False)
    _value = db.Column("value", db.Integer, nullable=True)

    def __str__(self) -> str:
        return (
            f'<Record {self.sports.label} - '
            f'{self.record_type} - '
            f"{self.workout_date.strftime('%Y-%m-%d')}>"
        )

    def __init__(self, workout: Workout, record_type: str) -> None:
        self.user_id = workout.user_id
        self.sport_id = workout.sport_id
        self.workout_id = workout.id
        self.workout_uuid = workout.uuid
        self.record_type = record_type
        self.workout_date = workout.workout_date

    @hybrid_property
    def value(self) -> Optional[Union[datetime.timedelta, float]]:
        if self._value is None:
            return None
        if self.record_type == 'LD':
            return datetime.timedelta(seconds=self._value)
        elif self.record_type in ['AS', 'MS']:
            return float(self._value / 100)
        else:  # 'FD'
            return float(self._value / 1000)

    @value.setter  # type: ignore
    def value(self, val: Union[str, float]) -> None:
        self._value = convert_value_to_integer(self.record_type, val)

    def serialize(self) -> Dict:
        if self.value is None:
            value = None
        elif self.record_type in ['AS', 'FD', 'MS']:
            value = float(self.value)  # type: ignore
        else:  # 'LD'
            value = str(self.value)  # type: ignore

        return {
            'id': self.id,
            'user': self.user.username,
            'sport_id': self.sport_id,
            'workout_id': encode_uuid(self.workout_uuid),
            'record_type': self.record_type,
            'workout_date': self.workout_date,
            'value': value,
        }


@listens_for(Record, 'after_delete')
def on_record_delete(
    mapper: Mapper, connection: Connection, old_record: Record
) -> None:
    @listens_for(db.Session, 'after_flush', once=True)
    def receive_after_flush(session: Session, context: Any) -> None:
        workout = old_record.workouts
        new_records = Workout.get_user_workout_records(
            workout.user_id, workout.sport_id
        )
        for record_type, record_data in new_records.items():
            if (
                record_data['record_value']
                and record_type == old_record.record_type
            ):
                new_record = Record(
                    workout=record_data['workout'], record_type=record_type
                )
                new_record.value = record_data['record_value']  # type: ignore
                session.add(new_record)
