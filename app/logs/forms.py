"""
ME Statistics — Logs Forms
=============================
WTForms for Monthly Reports, Goals, and Tasks.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional


class MonthlyReportForm(FlaskForm):
    """Form to submit or edit a Monthly Report."""
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    month = SelectField('Month', choices=[
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], validators=[DataRequired()])
    report_count = IntegerField('Report Count', validators=[DataRequired(), NumberRange(min=0, max=100000)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Report')


class GoalForm(FlaskForm):
    """Form to submit or edit a Goal."""
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    kpi = StringField('KPI', validators=[Optional(), Length(max=255)])
    priority = SelectField('Priority', choices=[
        ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')
    ], default='medium', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed')
    ], default='not_started', validators=[DataRequired()])
    progress = IntegerField('Progress (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    comments = TextAreaField('Comments', validators=[Optional()])
    submit = SubmitField('Save Goal')


class TaskForm(FlaskForm):
    """Form to submit or edit a Task."""
    description = StringField('Description', validators=[DataRequired(), Length(max=500)])
    priority = SelectField('Priority', choices=[
        ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')
    ], default='medium', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed')
    ], default='not_started', validators=[DataRequired()])
    progress = IntegerField('Progress (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    comments = TextAreaField('Comments', validators=[Optional()])
    submit = SubmitField('Save Task')
