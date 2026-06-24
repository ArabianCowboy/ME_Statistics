"""
Logs Blueprint — Reports, Goals, and Tasks CRUD
"""
from flask import Blueprint

logs_bp = Blueprint('logs', __name__, template_folder='../templates/logs')

from app.logs import routes
