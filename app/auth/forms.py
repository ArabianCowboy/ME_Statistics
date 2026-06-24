"""
ME Statistics — Auth Forms
===========================
WTForms classes for login and registration with server-side validation.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    """Login form — username + password."""
    username = StringField('Username or Email', validators=[
        DataRequired(message='Username or email is required.'),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
    """Registration form — full details with password confirmation."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=80, message='Username must be 3–80 characters.'),
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=120, message='Full name must be 2–120 characters.'),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.'),
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords do not match.'),
    ])
    submit = SubmitField('Register')

    def validate_username(self, field):
        from sqlalchemy import func
        if User.query.filter(func.lower(User.username) == field.data.strip().lower()).first():
            raise ValidationError('This username is already taken.')

    def validate_email(self, field):
        from sqlalchemy import func
        if User.query.filter(func.lower(User.email) == field.data.strip().lower()).first():
            raise ValidationError('This email is already registered.')
