"""WTForms used by the authentication blueprint."""

from __future__ import annotations

from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms.validators import ValidationError

from flask_wtf import FlaskForm

from app.models import User


class LoginForm(FlaskForm):
    """Credentials form used by the login route."""

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    """Self-registration form for new staff accounts."""

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Create account")

    def validate_username(self, field: StringField) -> None:
        """Reject usernames already used by another account.

        Args:
            field: Username field to validate.

        Returns:
            None.

        Side Effects:
            Performs a database lookup through SQLAlchemy.

        Raises:
            ValidationError: Triggered by WTForms when username exists.
        """

        username = str(field.data or "").strip()
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is not None:
            raise ValidationError("Username is already taken.")

    def validate_email(self, field: StringField) -> None:
        """Reject emails already used by another account.

        Args:
            field: Email field to validate.

        Returns:
            None.

        Side Effects:
            Performs a database lookup through SQLAlchemy.

        Raises:
            ValidationError: Triggered by WTForms when email exists.
        """

        email = str(field.data or "").strip().lower()
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is not None:
            raise ValidationError("Email is already registered.")
