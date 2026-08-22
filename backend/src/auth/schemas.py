from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=32,
        max_length=256,
    )
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )


class PasswordResetMessage(BaseModel):
    message: str