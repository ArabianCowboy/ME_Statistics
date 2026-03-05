"""
ME Statistics — Settings Forms
=================================
WTForms for system-wide configuration.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length


class SystemSettingsForm(FlaskForm):
    """Form for admin system-wide settings."""

    department_name = StringField(
        'Department Name',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'placeholder': 'e.g. Medication Error'}
    )

    default_monthly_target = IntegerField(
        'Default Monthly Target',
        validators=[NumberRange(min=0, max=999)],
        default=0,
        render_kw={'placeholder': '0'}
    )

    fiscal_year_start = SelectField(
        'Fiscal Year Start Month',
        choices=[
            ('1', 'January'), ('2', 'February'), ('3', 'March'),
            ('4', 'April'), ('5', 'May'), ('6', 'June'),
            ('7', 'July'), ('8', 'August'), ('9', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ],
        default='1'
    )

    default_language = SelectField(
        'Default Language',
        choices=[('en', 'English'), ('ar', 'Arabic')],
        default='en'
    )

    allow_self_registration = BooleanField(
        'Allow Self-Registration',
        default=True
    )

    leaderboard_visible = BooleanField(
        'Show Leaderboard to Staff',
        default=True
    )

    submit = SubmitField('Save Settings')
