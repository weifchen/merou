import hashlib
import hmac
import os
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from grouper.models.base.model_base import Model
from grouper.models.user import User


def _make_secret():
    return os.urandom(20).encode("hex")


class UserToken(Model):
    """Simple bearer tokens used by third parties to verify user identity"""

    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(length=16), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    disabled_at = Column(DateTime, default=None, nullable=True)

    hashed_secret = Column(String(length=64), unique=True, nullable=False)

    user = relationship("User", backref="tokens")

    __table_args__ = (UniqueConstraint("user_id", "name"),)

    @staticmethod
    def get_by_value(session, username, name):
        return (
            session.query(UserToken)
            .join(UserToken.user)
            .filter(User.username == username, UserToken.name == name)
            .scalar()
        )

    @staticmethod
    def get(session, user, name=None, id=None):
        """Retrieves a single UserToken.

        Args:
            session (Session): Session object
            user (User): Owner of the token
            name (str): Name of the token
            id (int): Primary key of the token

        Returns:
            UserToken: UserToken matching the specified constraints

        """
        assert name is None or id is None

        if name is not None:
            return session.query(UserToken).filter_by(name=name, user=user).scalar()
        return session.query(UserToken).filter_by(id=id, user=user).scalar()

    def _set_secret(self):
        secret = _make_secret()
        self.hashed_secret = hashlib.sha256(secret).hexdigest()
        return secret

    def check_secret(self, secret):
        # The length of self.hashed_secret is not secret
        return self.enabled and hmac.compare_digest(
            hashlib.sha256(secret).hexdigest(), self.hashed_secret.encode("utf-8")
        )

    @property
    def enabled(self):
        return self.disabled_at is None and self.user.enabled

    def __str__(self):
        return "/".join(
            (
                self.user.username if self.user is not None else "unspecified",
                self.name if self.name is not None else "unspecified",
            )
        )
