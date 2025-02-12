Installation
############

This application is written in Python (API) and Javascript (client):

- API:
    - Flask
    - `gpxpy <https://github.com/tkrajina/gpxpy>`_ to parse gpx files
    - `staticmap <https://github.com/komoot/staticmap>`_ to generate a static map image from gpx coordinates
    - `python-forecast.io <https://github.com/ZeevG/python-forecast.io>`_ to fetch weather data from `Dark Sky <https://darksky.net>`__ (former forecast.io)
    - `dramatiq <https://flask-dramatiq.readthedocs.io/en/latest/>`_ for task queue
- Client:
    - React/Redux
    - `Leaflet <https://leafletjs.com/>`__ to display map
    - `Recharts <https://github.com/recharts/recharts>`__ to display charts with elevation and speed

Sports and weather icons are made by `Freepik <https://www.freepik.com/>`__ from `www.flaticon.com <https://www.flaticon.com/>`__.

Prerequisites
~~~~~~~~~~~~~

-  PostgreSQL database (10+)
-  Redis for task queue
-  Python 3.7+
-  `Poetry <https://poetry.eustace.io>`__ (for installation from sources only)
-  API key from `Dark Sky <https://darksky.net/dev>`__ [not mandatory]
-  SMTP provider
-  `Yarn <https://yarnpkg.com>`__ (for development only)
-  Docker (for development only, to start `MailHog <https://github.com/mailhog/MailHog>`__ or evaluation purposes)

.. note::
    | The following steps describe an installation on Linux systems (tested
      on Debian and Arch).
    | On other OS, some issues can be encountered and adaptations may be
      necessary.


Environment variables
~~~~~~~~~~~~~~~~~~~~~

.. warning::
    | Since FitTrackee 0.4.0, ``Makefile.custom.config`` is replaced by ``.env``

The following environment variables are used by **FitTrackee** web application
or the task processing library. They are not all mandatory depending on
deployment method.

.. envvar:: FLASK_APP

    | Name of the module to import at flask run.
    | ``FLASK_APP`` should contain ``$(PWD)/fittrackee/__main__.py`` with installation from sources, else ``fittrackee``.


.. envvar:: HOST

    **FitTrackee** host.

    :default: 0.0.0.0


.. envvar:: PORT

    **FitTrackee** port.

    :default: 5000


.. envvar:: APP_SETTINGS

    **FitTrackee** configuration.

    :default: fittrackee.config.ProductionConfig


.. envvar:: APP_SECRET_KEY

    **FitTrackee** secret key, must be initialized in production environment.


.. envvar:: APP_WORKERS

    Number of workers spawned by **Gunicorn**.

    :default: 1


.. envvar:: APP_LOG 🆕

    .. versionadded:: 0.4.0

    Path to log file


.. envvar:: UPLOAD_FOLDER 🆕

    .. versionadded:: 0.4.0

    Directory containing uploaded files.

    :default: `fittrackee/uploads/`

    .. danger::
        | With installation from PyPI, the directory will be located in
          **virtualenv** directory if the variable is not initialized.

.. envvar:: DATABASE_URL

    | Database URL with username and password, must be initialized in production environment.
    | For example in dev environment : ``postgresql://fittrackee:fittrackee@localhost:5432/fittrackee``

    .. danger::
        | Since `SQLAlchemy update (1.4+) <https://docs.sqlalchemy.org/en/14/changelog/changelog_14.html#change-3687655465c25a39b968b4f5f6e9170b>`__,
          engine URL should begin with `postgresql://`.

.. envvar:: DATABASE_DISABLE_POOLING 🆕

    .. versionadded:: 0.4.0

    Disable pooling if needed (when starting application with **FitTrackee** entry point and not directly with **Gunicorn**),
    see `SqlAlchemy documentation <https://docs.sqlalchemy.org/en/13/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork>`__.

    :default: false

.. envvar:: UI_URL

    **FitTrackee** URL, needed for links in emails.


.. envvar:: EMAIL_URL

    .. versionadded:: 0.3.0

    Email URL with credentials, see `Emails <installation.html#emails>`__.


.. envvar:: SENDER_EMAIL

    .. versionadded:: 0.3.0

    **FitTrackee** sender email address.


.. envvar:: REDIS_URL

    .. versionadded:: 0.3.0

    Redis instance used by **Dramatiq**.

    :default: local Redis instance (``redis://``)


.. envvar:: WORKERS_PROCESSES

    .. versionadded:: 0.3.0

    Number of processes used by **Dramatiq**.


.. envvar:: TILE_SERVER_URL 🆕

    .. versionadded:: 0.4.0

    Tile server URL (with api key if needed), see `Map tile server <installation.html#map-tile-server>`__.

    :default: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`


.. envvar:: MAP_ATTRIBUTION 🆕

    .. versionadded:: 0.4.0

    Map attribution (if using another tile server), see `Map tile server <installation.html#map-tile-server>`__.

    :default: `&copy; <a href="http://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors`


.. envvar:: WEATHER_API_KEY

    .. versionchanged:: 0.4.0 ⚠️ replaces ``WEATHER_API``

    **Dark Sky** API key for weather data (not mandatory).


.. envvar:: REACT_APP_API_URL

    **FitTrackee** API URL, only needed in dev environment.



Deprecated variables
^^^^^^^^^^^^^^^^^^^^

.. envvar:: REACT_APP_GPX_LIMIT_IMPORT

    .. deprecated:: 0.3.0 now stored in database

    Maximum number of gpx file in zip archive.

    :default: 10


.. envvar:: REACT_APP_MAX_SINGLE_FILE_SIZE

    .. deprecated:: 0.3.0 now stored in database

    Maximum size of a gpx or picture file.

    :default: 1MB


.. envvar:: REACT_APP_MAX_ZIP_FILE_SIZE

    .. deprecated:: 0.3.0 now stored in database

    Maximum size of a zip archive.

    :default: 10MB


.. envvar:: REACT_APP_ALLOW_REGISTRATION

    .. deprecated:: 0.3.0 now stored in database

    Allows users to register.

    :default: true


.. envvar:: REACT_APP_THUNDERFOREST_API_KEY

    .. deprecated:: 0.4.0 see `TILE_SERVER_URL <installation.html#envvar-TILE_SERVER_URL>`__

    ThunderForest API key.

.. warning::
    | Since FitTrackee 0.3.0, some applications parameters are now stored in database.
    | Related environment variables are needed to initialize database when upgrading from version prior 0.3.0.


Emails
^^^^^^
.. versionadded:: 0.3.0

To send emails, a valid ``EMAIL_URL`` must be provided:

- with an unencrypted SMTP server: ``smtp://username:password@smtp.example.com:25``
- with SSL: ``smtp://username:password@smtp.example.com:465/?ssl=True``
- with STARTTLS: ``smtp://username:password@smtp.example.com:587/?tls=True``


Map tile server
^^^^^^^^^^^^^^^
.. versionadded:: 0.4.0

Default tile server is now **OpenStreetMap**'s standard tile layer (if environment variables are not initialized).
The tile server can be changed by updating ``TILE_SERVER_URL`` and ``MAP_ATTRIBUTION`` variables (`list of tile servers <https://wiki.openstreetmap.org/wiki/Tile_servers>`__).

To keep using **ThunderForest Outdoors**, the configuration is:

- ``TILE_SERVER_URL=https://{s}.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=XXXX`` where **XXXX** is **ThunderForest** API key
- ``MAP_ATTRIBUTION=&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors``

.. note::
    | Check the terms of service of tile provider for map attribution

From PyPI
~~~~~~~~~

.. note::
    | Recommended way on production.

.. warning::
    | Note that FitTrackee is under heavy development, some features may be unstable.

Installation
^^^^^^^^^^^^

- Create and activate a virtualenv

- Install **FitTrackee** with pip

.. code-block:: bash

    $ pip install fittrackee

- Create ``fittrackee`` database

Example :

.. code-block:: sql

    CREATE DATABASE fittrackee;
    CREATE USER fittrackee WITH PASSWORD '<PASSWORD>';
    GRANT ALL PRIVILEGES ON DATABASE fittrackee TO fittrackee;

- Initialize environment variables, see `Environment variables <installation.html#environment-variables>`__

For instance, copy and update ``.env`` file from ``.env.example`` and source the file.

.. code-block:: bash

    $ nano .env
    $ source .env


- Upgrade database schema

.. code-block:: bash

    $ fittrackee_upgrade_db

- Initialize database

.. code-block:: bash

    $ fittrackee_init_data

- Start the application

.. code-block:: bash

    $ fittrackee

- Start task queue workers

.. code-block:: bash

    $ fittrackee_worker --processes 2

.. note::
    | To start application and workers with **systemd** service, see `Deployment <installation.html#deployment>`__


Upgrade
^^^^^^^

.. warning::
    | Before upgrading, make a backup of all data:
    | - database (with `pg_dump <https://www.postgresql.org/docs/11/app-pgdump.html>`__ for instance)
    | - upload directory (see `Environment variables <installation.html#environment-variables>`__)

- Activate the virtualenv

- Upgrade with pip

.. code-block:: bash

    $ pip install -U fittrackee

- Update environment variables if needed and source environment variables file

.. code-block:: bash

    $ nano .env
    $ source .env

- Upgrade database if needed

.. code-block:: bash

    $ fittrackee_upgrade_db


- Restart the application and task queue workers.


From sources
~~~~~~~~~~~~~

.. warning::
    | Since FitTrackee 0.2.1, Python packages installation needs Poetry.
    | To install it on ArchLinux:

    .. code-block:: bash

        $ yay poetry
        $ poetry --version
        Poetry 1.0.10

        # optional
        $ poetry config virtualenvs.in-project true

    For other OS, see `Poetry Documentation <https://python-poetry.org/docs/#installation>`__


Installation
^^^^^^^^^^^^

Dev environment
"""""""""""""""

-  Clone this repo:

.. code:: bash

   $ git clone https://github.com/SamR1/FitTrackee.git
   $ cd FitTrackee

-  Create **Makefile.custom.config** from example and update it
   (see `Environment variables <installation.html#environment-variables>`__).

-  Install Python virtualenv, React and all related packages and
   initialize the database:

.. code:: bash

   $ make install-dev
   $ make install-db

-  Start the server and the client:

.. code:: bash

   $ make serve

-  Run dramatiq workers:

.. code:: bash

   $ make run-workers

Open http://localhost:3000 and log in (the email is ``admin@example.com``
and the password ``mpwoadmin``) or register


Production environment
""""""""""""""""""""""

.. warning::
    | Note that FitTrackee is under heavy development, some features may be unstable.

-  Download the last release (for now, it is the release v0.4.0):

.. code:: bash

   $ wget https://github.com/SamR1/FitTrackee/archive/v0.4.0.tar.gz
   $ tar -xzf v0.4.0.tar.gz
   $ mv FitTrackee-0.4.0 FitTrackee
   $ cd FitTrackee

-  Create **Makefile.custom.config** from example and update it
   (see `Environment variables <installation.html#environment-variables>`__).

-  Install Python virtualenv and all related packages:

.. code:: bash

   $ make install-python

-  Initialize the database (**after updating** ``db/create.sql`` **to change
   database credentials**):

.. code:: bash

   $ make install-db

-  Start the server and dramatiq workers:

.. code:: bash

   $ make run

Open http://localhost:5000, log in as admin (the email is
``admin@example.com`` and the password ``mpwoadmin``) and change the
password

Upgrade
^^^^^^^

.. warning::
    | Before upgrading, make a backup of all data:
    | - database (with `pg_dump <https://www.postgresql.org/docs/11/app-pgdump.html>`__ for instance)
    | - upload directory (see `Environment variables <installation.html#environment-variables>`__)


Dev environment
"""""""""""""""

- Stop the application and pull the repository:

.. code:: bash

   $ git pull

- Update **.env** if needed

- Upgrade packages and database:

.. code:: bash

   $ make install-dev
   $ make upgrade-db

- Restart the server:

.. code:: bash

   $ make serve

-  Run dramatiq workers:

.. code:: bash

   $ make run-workers

Prod environment
""""""""""""""""

- Stop the application and pull the repository:

.. code:: bash

   $ git pull

- Update **Makefile.custom.config** if needed

- Upgrade packages and database:

.. code:: bash

   $ make install
   $ make upgrade-db

- Restart the server and dramatiq workers:

.. code:: bash

   $ make run


Deployment
~~~~~~~~~~~~~

There are several ways to start **FitTrackee** web application and task queue
library.
One way is to use a **systemd** services and **Nginx** to proxy pass to **Gunicorn**.

Examples (to update depending on your application configuration and given distribution):

- for application: ``fittrackee.service``

.. code-block::

    [Unit]
    Description=FitTrackee service
    After=network.target
    After=postgresql.service
    After=redis.service
    StartLimitIntervalSec=0

    [Service]
    Type=simple
    Restart=always
    RestartSec=1
    User=<USER>
    StandardOutput=syslog
    StandardError=syslog
    SyslogIdentifier=fittrackee
    Environment="APP_SECRET_KEY="
    Environment="APP_LOG="
    Environment="UPLOAD_FOLDER="
    Environment="DATABASE_URL="
    Environment="UI_URL="
    Environment="EMAIL_URL="
    Environment="SENDER_EMAIL="
    Environment="REDIS_URL="
    Environment="TILE_SERVER_URL="
    Environment="MAP_ATTRIBUTION="
    Environment="WEATHER_API_KEY="
    WorkingDirectory=/home/<USER>/<FITTRACKEE DIRECTORY>
    ExecStart=/home/<USER>/<FITTRACKEE DIRECTORY>/.venv/bin/gunicorn -b 127.0.0.1:5000 "fittrackee:create_app()" --error-logfile /home/<USER>/<FITTRACKEE DIRECTORY>/gunicorn.log
    Restart=always

    [Install]
    WantedBy=multi-user.target

.. note::
    More information on `Gunicorn documentation <https://docs.gunicorn.org/en/stable/deploy.html>`__

- for task queue workers: ``fittrackee_workers.service``

.. code-block::

    [Unit]
    Description=FitTrackee task queue service
    After=network.target
    After=postgresql.service
    After=redis.service
    StartLimitIntervalSec=0

    [Service]
    Type=simple
    Restart=always
    RestartSec=1
    User=<USER>
    StandardOutput=syslog
    StandardError=syslog
    SyslogIdentifier=fittrackee_workers
    Environment="FLASK_APP=fittrackee"
    Environment="APP_SECRET_KEY="
    Environment="APP_LOG="
    Environment="UPLOAD_FOLDER="
    Environment="DATABASE_URL="
    Environment="UI_URL="
    Environment="EMAIL_URL="
    Environment="SENDER_EMAIL="
    Environment="REDIS_URL="
    WorkingDirectory=/home/<USER>/<FITTRACKEE DIRECTORY>
    ExecStart=/home/<USER>/<FITTRACKEE DIRECTORY>/.venv/bin/flask worker --processes <NUMBER OF PROCESSES>
    Restart=always

    [Install]
    WantedBy=multi-user.target

- **Nginx** configuration:

.. code-block::

    server {
        listen 443 ssl;
        server_name example.com;
        ssl_certificate fullchain.pem;
        ssl_certificate_key privkey.pem;

        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_redirect    default;
            proxy_set_header  Host $host;
            proxy_set_header  X-Real-IP $remote_addr;
            proxy_set_header  X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header  X-Forwarded-Host $server_name;
        }
    }

    server {
        listen 80;
        server_name example.com;
        location / {
            return 301 https://example.com$request_uri;
        }
    }

.. note::
    If needed, update configuration to handle larger files (see `client_max_body_size <https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size>`_).


Docker
~~~~~~

.. versionadded:: 0.4.4

For evaluation purposes (at least for now), docker files are available,
installing **FitTrackee** from **sources**.

- To install **FitTrackee** with database initialisation and run the application and dramatiq workers:

.. code-block:: bash

    $ git clone https://github.com/SamR1/FitTrackee.git
    $ cd FitTrackee
    $ make docker-build docker-run docker-init

Open http://localhost:5000, log in as admin (the email is `admin@example.com` and the password `mpwoadmin`) or register.

Open http://localhost:8025 to access `MailHog interface <https://github.com/mailhog/MailHog>`_ (email testing tool)

- To stop **Fittrackee**:

.. code-block:: bash

    $ make docker-stop

- To start **Fittrackee** (application and dramatiq workers):

.. code-block:: bash

    $ make docker-run-all


- To run shell inside **Fittrackee** container:

.. code-block:: bash

    $ make docker-shell