"""init federation with ActivityPub Actor

Revision ID: 8842c351a2d8
Revises: 4e8597c50064
Create Date: 2021-01-10 16:02:43.811023

"""
import os
from datetime import datetime

import sqlalchemy as sa
from alembic import op

from fittrackee.federation.utils import get_ap_url


# revision identifiers, used by Alembic.
revision = '8842c351a2d8'
down_revision = '4e8597c50064'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'app_config',
        sa.Column(
            'federation_enabled', sa.Boolean(), nullable=True, default=False
        ),
    )
    op.execute('UPDATE app_config SET federation_enabled = false')
    op.alter_column('app_config', 'federation_enabled', nullable=False)

    domain_table = op.create_table(
        'domains',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=1000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_allowed', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    domain = os.environ['UI_URL']
    created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    op.execute(
        "INSERT INTO domains (name, created_at, is_allowed)"
        f"VALUES ('{domain}', '{created_at}'::timestamp, True)"
    )

    actors_table = op.create_table(
        'actors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('activitypub_id', sa.String(length=255), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column(
            'type',
            sa.Enum('APPLICATION', 'GROUP', 'PERSON', name='actor_types'),
            server_default='PERSON',
            nullable=True,
        ),
        sa.Column('preferred_username', sa.String(length=255), nullable=False),
        sa.Column('public_key', sa.String(length=5000), nullable=True),
        sa.Column('private_key', sa.String(length=5000), nullable=True),
        sa.Column('inbox_url', sa.String(length=255), nullable=False),
        sa.Column('outbox_url', sa.String(length=255), nullable=False),
        sa.Column('followers_url', sa.String(length=255), nullable=False),
        sa.Column('following_url', sa.String(length=255), nullable=False),
        sa.Column('shared_inbox_url', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('manually_approves_followers', sa.Boolean(), nullable=False),
        sa.Column('last_fetch_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['domain_id'],
            ['domains.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('activitypub_id'),
        sa.UniqueConstraint(
            'domain_id', 'preferred_username', name='domain_username_unique'
        ),
    )

    op.add_column('users', sa.Column('actor_id', sa.Integer(), nullable=True))
    op.create_unique_constraint('users_actor_id_key', 'users', ['actor_id'])
    op.create_foreign_key(
        'users_actor_id_fkey', 'users', 'actors', ['actor_id'], ['id']
    )

    # create local actors
    user_helper = sa.Table(
        'users',
        sa.MetaData(),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=20), nullable=False),
    )
    connection = op.get_bind()
    domain = connection.execute(domain_table.select()).fetchone()
    for user in connection.execute(user_helper.select()):
        created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        op.execute(
            "INSERT INTO actors ("
            "activitypub_id, domain_id, preferred_username, followers_url, "
            "following_url, inbox_url, outbox_url, shared_inbox_url, "
            "created_at, manually_approves_followers) "
            "VALUES ("
            f"'{get_ap_url(user.username, 'user_url')}', "
            f"{domain.id}, '{user.username}', "
            f"'{get_ap_url(user.username, 'followers')}', "
            f"'{get_ap_url(user.username, 'following')}', "
            f"'{get_ap_url(user.username, 'inbox')}', "
            f"'{get_ap_url(user.username, 'outbox')}', "
            f"'{get_ap_url(user.username, 'shared_inbox')}', "
            f"'{created_at}'::timestamp, {True}) RETURNING id"
        )
        actor = connection.execute(
            actors_table.select().where(
                actors_table.c.preferred_username == user.username
            )
        ).fetchone()
        op.execute(
            f'UPDATE users SET actor_id = {actor.id} WHERE users.id = {user.id}'
        )

    op.create_table(
        'follow_requests',
        sa.Column('follower_actor_id', sa.Integer(), nullable=False),
        sa.Column('followed_actor_id', sa.Integer(), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['followed_actor_id'],
            ['actors.id'],
        ),
        sa.ForeignKeyConstraint(
            ['follower_actor_id'],
            ['actors.id'],
        ),
        sa.PrimaryKeyConstraint('follower_actor_id', 'followed_actor_id'),
    )


def downgrade():
    op.drop_table('follow_requests')

    op.drop_constraint('users_actor_id_fkey', 'users', type_='foreignkey')
    op.drop_constraint('users_actor_id_key', 'users', type_='unique')
    op.drop_column('users', 'actor_id')

    op.drop_table('actors')
    op.execute('DROP TYPE actor_types')

    op.drop_table('domains')

    op.drop_column('app_config', 'federation_enabled')
