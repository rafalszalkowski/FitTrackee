import os
from pathlib import Path
from typing import Generator, Optional, Union

import pytest

from fittrackee import create_app, db
from fittrackee.application.models import AppConfig
from fittrackee.application.utils import update_app_config_from_database
from fittrackee.federation.models import Domain


def get_app_config(
    with_config: Optional[bool] = False,
    max_workouts: Optional[int] = None,
    max_single_file_size: Optional[Union[int, float]] = None,
    max_zip_file_size: Optional[Union[int, float]] = None,
    max_users: Optional[int] = None,
    with_federation: Optional[bool] = False,
) -> Optional[AppConfig]:
    if with_config:
        config = AppConfig()
        config.federation_enabled = with_federation
        config.gpx_limit_import = 10 if max_workouts is None else max_workouts
        config.max_single_file_size = (
            (1 if max_single_file_size is None else max_single_file_size)
            * 1024
            * 1024
        )
        config.max_zip_file_size = (
            (10 if max_zip_file_size is None else max_zip_file_size)
            * 1024
            * 1024
        )
        config.max_users = 100 if max_users is None else max_users
        db.session.add(config)
        db.session.commit()
        return config
    return None


def get_app(
    with_config: Optional[bool] = False,
    max_workouts: Optional[int] = None,
    max_single_file_size: Optional[Union[int, float]] = None,
    max_zip_file_size: Optional[Union[int, float]] = None,
    max_users: Optional[int] = None,
    with_federation: Optional[bool] = False,
    with_domain: Optional[bool] = True,
) -> Generator:
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            app_db_config = get_app_config(
                with_config,
                max_workouts,
                max_single_file_size,
                max_zip_file_size,
                max_users,
                with_federation,
            )
            if app_db_config:
                update_app_config_from_database(app, app_db_config)
                if with_domain:
                    domain = Domain(name=app.config['AP_DOMAIN'])
                    db.session.add(domain)
                    db.session.commit()
            yield app
        except Exception as e:
            print(f'Error with app configuration: {e}')
        finally:
            db.session.remove()
            db.drop_all()
            # close unused idle connections => avoid the following error:
            # FATAL: remaining connection slots are reserved for
            # non-replication superuser connections
            db.engine.dispose()
            return app


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025')
    if os.getenv('TILE_SERVER_URL'):
        monkeypatch.delenv('TILE_SERVER_URL')
    if os.getenv('MAP_ATTRIBUTION'):
        monkeypatch.delenv('MAP_ATTRIBUTION')
    yield from get_app(with_config=True)


@pytest.fixture
def app_with_max_workouts(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025')
    yield from get_app(with_config=True, max_workouts=2)


@pytest.fixture
def app_with_max_file_size_equals_0(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025')
    yield from get_app(with_config=True, max_single_file_size=0)


@pytest.fixture
def app_with_max_file_size(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025')
    yield from get_app(with_config=True, max_single_file_size=0.001)


@pytest.fixture
def app_with_max_zip_file_size(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025')
    yield from get_app(with_config=True, max_zip_file_size=0.001)


@pytest.fixture
def app_with_3_users_max(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025')
    yield from get_app(with_config=True, max_users=3)


@pytest.fixture
def app_no_config() -> Generator:
    yield from get_app(with_config=False)


@pytest.fixture
def app_ssl(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025?ssl=True')
    yield from get_app(with_config=True)


@pytest.fixture
def app_tls(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv('EMAIL_URL', 'smtp://none:none@0.0.0.0:1025?tls=True')
    yield from get_app(with_config=True)


@pytest.fixture
def app_with_federation() -> Generator:
    yield from get_app(with_config=True, with_federation=True)


@pytest.fixture
def app_wo_domain() -> Generator:
    yield from get_app(
        with_config=True, with_federation=True, with_domain=False
    )


@pytest.fixture()
def app_config() -> AppConfig:
    config = AppConfig()
    config.federation_enabled = False
    config.gpx_limit_import = 10
    config.max_single_file_size = 1048576
    config.max_zip_file_size = 10485760
    config.max_users = 0
    db.session.add(config)
    db.session.commit()
    return config


@pytest.fixture()
def app_version() -> str:
    return (
        (Path(__file__).parent.parent.parent / 'VERSION').read_text().strip()
    )
