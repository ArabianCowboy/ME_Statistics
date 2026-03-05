"""
ME Statistics — User Management Forms
========================================
Forms for creating and editing users (admin only).
"""

from wtforms import (
    StringField, PasswordField, IntegerField, SelectField,
    BooleanField, validators
)
from flask_wtf import FlaskForm
from app.models import User


class CreateUserForm(FlaskForm):
    """Admin form to create a new user directly (pre-approved)."""
    username = StringField('Username', validators=[
        validators.DataRequired('Username is required.'),
        validators.Length(min=3, max=80),
        validators.Regexp('^[a-zA-Z0-9_]+$', message='Only letters, numbers, and underscores.')
    ])
    email = StringField('Email', validators=[
        validators.DataRequired('Email is required.'),
        validators.Email('Enter a valid email address.')
    ])
    full_name = StringField('Full Name', validators=[
        validators.DataRequired('Full name is required.'),
        validators.Length(min=2, max=120)
    ])
    password = PasswordField('Password', validators=[
        validators.DataRequired('Password is required.'),
        validators.Length(min=6, max=128, message='Password must be at least 6 characters.')
    ])
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Admin'),
    ], default='user')
    monthly_target = IntegerField('Monthly Target', validators=[
        validators.NumberRange(min=0, message='Target must be ≥ 0.')
    ], default=0)
    preferred_lang = SelectField('Language', choices=[
        ('en', 'English'),
        ('ar', 'العربية'),
    ], default='en')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise validators.ValidationError('Username already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise validators.ValidationError('Email already registered.')


class EditUserForm(FlaskForm):
    """Admin form to edit an existing user's profile and toggles."""
    full_name = StringField('Full Name', validators=[
        validators.DataRequired('Full name is required.'),
        validators.Length(min=2, max=120)
    ])
    email = StringField('Email', validators=[
        validators.DataRequired('Email is required.'),
        validators.Email('Enter a valid email address.')
    ])
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Admin'),
    ])
    monthly_target = IntegerField('Monthly Target', validators=[
        validators.NumberRange(min=0, message='Target must be ≥ 0.')
    ], default=0)
    preferred_lang = SelectField('Language', choices=[
        ('en', 'English'),
        ('ar', 'العربية'),
    ])

    # Per-user workflow toggles
    goal_approval_required = BooleanField('Goal Approval Required')
    report_approval_required = BooleanField('Report Approval Required')
    can_create_goals = BooleanField('Can Create Goals')

    def __init__(self, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_email = original_email

    def validate_email(self, field):
        if field.data.lower() != self._original_email:
            if User.query.filter_by(email=field.data.lower()).first():
                raise validators.ValidationError('Email already registered.')


class ResetPasswordForm(FlaskForm):
    """Admin form to reset a user's password."""
    new_password = PasswordField('New Password', validators=[
        validators.DataRequired('Password is required.'),
        validators.Length(min=6, max=128, message='Must be at least 6 characters.')
    ])
