import hashlib
import secrets
import uuid

from redis.asyncio import Redis

from src.auth.exceptions import (
    InvalidPasswordResetTokenError,
)
from src.auth.password import hash_password
from src.tasks.email_tasks import (
    send_password_reset_email,
)
from src.users.repository import UserRepository


class PasswordResetService:
    RESET_TOKEN_TTL_SECONDS = 15 * 60

    def __init__(
        self,
        user_repository: UserRepository,
        redis_client: Redis,
    ) -> None:
        self.user_repository = user_repository
        self.redis = redis_client

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def _hash_token(
        token: str,
    ) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _reset_token_key(
        self,
        token_hash: str,
    ) -> str:
        return f"password_reset:{token_hash}"

    async def _store_token(
        self,
        token: str,
        user_id: uuid.UUID,
    ) -> None:
        token_hash = self._hash_token(token)

        await self.redis.set(
            self._reset_token_key(token_hash),
            str(user_id),
            ex=self.RESET_TOKEN_TTL_SECONDS,
        )

    async def request_password_reset(
        self,
        email: str,
    ) -> str | None:
        normalized_email = email.strip().lower()

        user = await self.user_repository.get_by_email(normalized_email)

        if user is None or not user.is_active:
            return None

        token = self._generate_token()

        await self._store_token(
            token=token,
            user_id=user.id,
        )

        send_password_reset_email.delay(
            user.email,
            token,
        )

        return token

    async def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> None:
        token_hash = self._hash_token(token)

        cache_key = self._reset_token_key(token_hash)

        user_id = await self.redis.get(cache_key)

        if user_id is None:
            raise InvalidPasswordResetTokenError

        user = await self.user_repository.get_by_id(uuid.UUID(user_id))

        if user is None:
            raise InvalidPasswordResetTokenError

        user.hashed_password = hash_password(new_password)

        await self.user_repository.update(user)

        await self.redis.delete(cache_key)
