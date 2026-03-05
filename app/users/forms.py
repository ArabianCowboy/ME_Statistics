"""WTForms used by admin user management and settings pages."""

from __future__ import annotations

from typing import Optional as TypingOptional

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, PasswordField, SelectField
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from wtforms.validators import ValidationError

from app.models import LanguageCode, User, UserRole


class UserCreateForm(FlaskForm):
    """Form used by admins to create a new user account."""

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
    role = SelectField(
        "Role",
        choices=[
            (UserRole.USER.value, "Staff"),
            (UserRole.ADMIN.value, "Admin"),
        ],
        validators=[DataRequired()],
    )
    monthly_target = IntegerField(
        "Monthly target",
        default=0,
        validators=[DataRequired(), NumberRange(min=0, max=100000)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    is_approved = BooleanField("Approved", default=True)
    goal_approval_required = BooleanField("Goal approval required", default=True)
    report_approval_required = BooleanField("Report approval required", default=False)
    can_create_goals = BooleanField("Can create goals", default=True)
    submit = SubmitField("Create user")

    def validate_username(self, field: StringField) -> None:
        """Validate username uniqueness for new users.

        Args:
            field: Username field submitted by the user.

        Returns:
            None.

        Side Effects:
            Executes a database query.

        Raises:
            ValidationError: When username already exists.
        """

        username = str(field.data or "").strip()
        existing = User.query.filter_by(username=username).first()
        if existing is not None:
            raise ValidationError("Username is already taken.")

    def validate_email(self, field: StringField) -> None:
        """Validate email uniqueness for new users.

        Args:
            field: Email field submitted by the user.

        Returns:
            None.

        Side Effects:
            Executes a database query.

        Raises:
            ValidationError: When email already exists.
        """

        email = str(field.data or "").strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing is not None:
            raise ValidationError("Email is already registered.")


class UserEditForm(FlaskForm):
    """Form used by admins to edit existing user profiles."""

    user_id = HiddenField("User ID", validators=[Optional()])
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
    role = SelectField(
        "Role",
        choices=[
            (UserRole.USER.value, "Staff"),
            (UserRole.ADMIN.value, "Admin"),
        ],
        validators=[DataRequired()],
    )
    preferred_lang = SelectField(
        "Preferred language",
        choices=[
            (LanguageCode.EN.value, "English"),
            (LanguageCode.AR.value, "Arabic"),
        ],
        validators=[DataRequired()],
    )
    monthly_target = IntegerField(
        "Monthly target",
        default=0,
        validators=[DataRequired(), NumberRange(min=0, max=100000)],
    )
    is_approved = BooleanField("Approved")
    goal_approval_required = BooleanField("Goal approval required")
    report_approval_required = BooleanField("Report approval required")
    can_create_goals = BooleanField("Can create goals")
    new_password = PasswordField(
        "New password",
        validators=[Optional(), Length(min=8, max=128)],
    )
    submit = SubmitField("Save changes")

    def _current_user_id(self) -> TypingOptional[int]:
        """Resolve the currently edited user ID from hidden field.

        Args:
            None.

        Returns:
            TypingOptional[int]: Parsed user ID or `None` when unavailable.

        Side Effects:
            None.

        Raises:
            None.
        """

        raw_value = str(self.user_id.data or "").strip()
        if not raw_value:
            return None

        try:
            return int(raw_value)
        except ValueError:
            return None

    def validate_username(self, field: StringField) -> None:
        """Validate username uniqueness while excluding current user.

        Args:
            field: Username field submitted by the user.

        Returns:
            None.

        Side Effects:
            Executes a database query.

        Raises:
            ValidationError: When username belongs to another account.
        """

        username = str(field.data or "").strip()
        existing = User.query.filter_by(username=username).first()
        current_id = self._current_user_id()
        if existing is not None and existing.id != current_id:
            raise ValidationError("Username is already taken.")

    def validate_email(self, field: StringField) -> None:
        """Validate email uniqueness while excluding current user.

        Args:
            field: Email field submitted by the user.

        Returns:
            None.

        Side Effects:
            Executes a database query.

        Raises:
            ValidationError: When email belongs to another account.
        """

        email = str(field.data or "").strip().lower()
        existing = User.query.filter_by(email=email).first()
        current_id = self._current_user_id()
        if existing is not None and existing.id != current_id:
            raise ValidationError("Email is already registered.")


class ResetPasswordForm(FlaskForm):
    """Form used by admins to reset a user password."""

    password = PasswordField(
        "New password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    submit = SubmitField("Reset password")


class SystemSettingsForm(FlaskForm):
    """Form for editing key system configuration values."""

    fiscal_year_start = SelectField(
        "Fiscal year start month",
        choices=[(str(index), str(index)) for index in range(1, 13)],
        validators=[DataRequired()],
    )
    default_language = SelectField(
        "Default language",
        choices=[
            (LanguageCode.EN.value, "English"),
            (LanguageCode.AR.value, "Arabic"),
        ],
        validators=[DataRequired()],
    )
    allow_self_registration = BooleanField("Allow self registration")
    leaderboard_visible = BooleanField("Show leaderboard to staff")
    default_monthly_target = IntegerField(
        "Default monthly target",
        default=0,
        validators=[DataRequired(), NumberRange(min=0, max=100000)],
    )
    department_name = StringField(
        "Department name",
        validators=[DataRequired(), Length(min=3, max=100)],
    )
    submit = SubmitField("Save settings")
