"""
ME Statistics — Admin Seeder Script
=====================================
Creates the initial admin account.

Usage:
    python -m scripts.create_admin

Or from the project root:
    python scripts/create_admin.py
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from app import create_app
from app.extensions import db
from app.models import User, SystemConfig


def create_admin():
    """Create the initial admin account and seed system config defaults."""
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()

        # Seed system config defaults
        SystemConfig.seed_defaults()
        print('[✓] System config defaults seeded.')

        # Check if admin already exists
        existing = User.query.filter_by(role='admin').first()
        if existing:
            print(f'[!] Admin already exists: {existing.username}')
            return

        # Create admin user
        password = 'admin123'  # Change this immediately after first login!
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        admin = User(
            username='admin',
            email='admin@mestatistics.local',
            full_name='System Administrator',
            password_hash=password_hash,
            role='admin',
            is_active=True,
            is_approved=True,
            monthly_target=0,
        )
        db.session.add(admin)
        db.session.commit()

        print('[✓] Admin account created:')
        print(f'    Username: admin')
        print(f'    Password: {password}')
        print(f'    ⚠  Change this password immediately!')


if __name__ == '__main__':
    create_admin()
