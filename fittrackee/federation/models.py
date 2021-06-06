from datetime import datetime
from typing import Dict, Optional

from flask import current_app
from sqlalchemy.types import Enum

from fittrackee import BaseModel, db

from .utils import ACTOR_TYPES, AP_CTX, generate_keys, get_ap_url


class Domain(BaseModel):
    """ ActivityPub Domain """

    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(1000), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    is_allowed = db.Column(db.Boolean, default=True, nullable=False)

    actors = db.relationship('Actor', back_populates='domain')

    def __str__(self) -> str:
        return f'<Domain \'{self.name}\'>'

    def __init__(
        self, name: str, created_at: Optional[datetime] = datetime.utcnow()
    ) -> None:
        self.name = name
        self.created_at = created_at

    @property
    def is_remote(self) -> bool:
        return self.name != current_app.config['AP_DOMAIN']

    def serialize(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'is_remote': self.is_remote,
            'is_allowed': self.is_allowed,
        }


class Actor(BaseModel):
    """ ActivityPub Actor """

    __tablename__ = 'actors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ap_id = db.Column(db.String(255), unique=True, nullable=False)
    domain_id = db.Column(
        db.Integer, db.ForeignKey('domains.id'), nullable=False
    )
    type = db.Column(
        Enum(*ACTOR_TYPES, name='actor_types'), server_default='Person'
    )
    name = db.Column(db.String(255), nullable=False)
    preferred_username = db.Column(db.String(255), nullable=False)
    public_key = db.Column(db.String(5000), nullable=True)
    private_key = db.Column(db.String(5000), nullable=True)
    inbox_url = db.Column(db.String(255), nullable=False)
    outbox_url = db.Column(db.String(255), nullable=False)
    followers_url = db.Column(db.String(255), nullable=False)
    following_url = db.Column(db.String(255), nullable=False)
    shared_inbox_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    manually_approves_followers = db.Column(
        db.Boolean, default=True, nullable=False
    )
    last_fetch_date = db.Column(db.DateTime, nullable=True)

    domain = db.relationship('Domain', back_populates='actors')
    user = db.relationship('User', uselist=False, back_populates='actor')

    def __str__(self) -> str:
        return f'<Actor \'{self.name}\'>'

    def __init__(
        self,
        username: str,
        domain_id: int,
        created_at: Optional[datetime] = datetime.utcnow(),
    ) -> None:
        self.ap_id = get_ap_url(username, 'user_url')
        self.created_at = created_at
        self.domain_id = domain_id
        self.followers_url = get_ap_url(username, 'followers')
        self.following_url = get_ap_url(username, 'following')
        self.inbox_url = get_ap_url(username, 'inbox')
        self.name = username
        self.outbox_url = get_ap_url(username, 'outbox')
        self.preferred_username = username
        self.shared_inbox_url = get_ap_url(username, 'shared_inbox')

    def generate_keys(self) -> None:
        self.public_key, self.private_key = generate_keys()

    @property
    def is_remote(self) -> bool:
        return self.domain.is_remote

    def serialize(self) -> Dict:
        return {
            '@context': AP_CTX,
            'id': self.ap_id,
            'type': self.type,
            'preferredUsername': self.preferred_username,
            'name': self.name,
            'inbox': self.inbox_url,
            'outbox': self.outbox_url,
            'followers': self.followers_url,
            'following': self.following_url,
            'manuallyApprovesFollowers': self.manually_approves_followers,
            'publicKey': {
                'id': f'{self.ap_id}#main-key',
                'owner': self.ap_id,
                'publicKeyPem': self.public_key,
            },
            'endpoints': {'sharedInbox': self.shared_inbox_url},
        }
