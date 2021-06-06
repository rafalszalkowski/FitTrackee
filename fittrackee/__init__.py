import logging
import os
import re
from importlib import import_module, reload
from typing import Any

from flask import Flask, Response, render_template, send_file
from flask_bcrypt import Bcrypt
from flask_dramatiq import Dramatiq
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import DeclarativeMeta

from fittrackee.emails.email import Email

db = SQLAlchemy()
BaseModel: DeclarativeMeta = db.Model
bcrypt = Bcrypt()
migrate = Migrate()
email_service = Email()
dramatiq = Dramatiq()
log_file = os.getenv('APP_LOG')
logging.basicConfig(
    filename=log_file,
    format='%(asctime)s - %(name)s - %(levelname)s - ' '%(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
)
appLog = logging.getLogger('fittrackee')


def create_app() -> Flask:
    # instantiate the app
    app = Flask(__name__, static_folder='dist/static', template_folder='dist')

    # set config
    with app.app_context():
        app_settings = os.getenv(
            'APP_SETTINGS', 'fittrackee.config.ProductionConfig'
        )
        if app_settings == 'fittrackee.config.TestingConfig':
            # reload config on tests
            config = import_module('fittrackee.config')
            reload(config)
        app.config.from_object(app_settings)

    # set up extensions
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    dramatiq.init_app(app)

    # set up email
    email_service.init_email(app)

    # get configuration from database
    from .application.models import AppConfig
    from .application.utils import init_config, update_app_config_from_database

    with app.app_context():
        # Note: check if "app_config" table exist to avoid errors when
        # dropping tables on dev environments
        try:
            if db.engine.dialect.has_table(db.engine.connect(), 'app_config'):
                db_app_config = AppConfig.query.one_or_none()
                if not db_app_config:
                    _, db_app_config = init_config()
                update_app_config_from_database(app, db_app_config)
        except ProgrammingError as e:
            # avoid error on AppConfig migration
            if re.match(
                r'psycopg2.errors.UndefinedColumn(.*)app_config.', str(e)
            ):
                pass

    from .application.app_config import config_blueprint  # noqa
    from .users.auth import auth_blueprint  # noqa
    from .users.users import users_blueprint  # noqa
    from .workouts.records import records_blueprint  # noqa
    from .workouts.sports import sports_blueprint  # noqa
    from .workouts.stats import stats_blueprint  # noqa
    from .workouts.workouts import workouts_blueprint  # noqa

    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(config_blueprint, url_prefix='/api')
    app.register_blueprint(records_blueprint, url_prefix='/api')
    app.register_blueprint(sports_blueprint, url_prefix='/api')
    app.register_blueprint(stats_blueprint, url_prefix='/api')
    app.register_blueprint(users_blueprint, url_prefix='/api')
    app.register_blueprint(workouts_blueprint, url_prefix='/api')

    # ActivityPub federation
    from .federation.federation import ap_federation_blueprint  # noqa
    from .federation.nodeinfo import ap_nodeinfo_blueprint  # noqa
    from .federation.webfinger import ap_webfinger_blueprint  # noqa

    app.register_blueprint(ap_federation_blueprint, url_prefix='/federation')
    app.register_blueprint(ap_nodeinfo_blueprint)
    app.register_blueprint(ap_webfinger_blueprint, url_prefix='/.well-known')

    if app.debug:
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy').handlers = logging.getLogger(
            'werkzeug'
        ).handlers
        logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
        logging.getLogger('flake8').propagate = False
        appLog.setLevel(logging.DEBUG)

        # Enable CORS
        @app.after_request
        def after_request(response: Response) -> Response:
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add(
                'Access-Control-Allow-Headers', 'Content-Type,Authorization'
            )
            response.headers.add(
                'Access-Control-Allow-Methods',
                'GET,PUT,POST,DELETE,PATCH,OPTIONS',
            )
            return response

    @app.route('/favicon.ico')
    def favicon() -> Any:
        return send_file(
            os.path.join(app.root_path, 'dist/favicon.ico')  # type: ignore
        )

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path: str) -> Any:
        # workaround to serve images (not in static directory)
        if path.startswith('img/'):
            return send_file(
                os.path.join(
                    app.root_path,  # type: ignore
                    'dist',
                    path,
                )
            )
        else:
            return render_template('index.html')

    return app
