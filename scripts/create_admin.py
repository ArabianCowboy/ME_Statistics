"""Create or update the initial administrator account."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.models import LanguageCode, User, UserRole, seed_default_system_config


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for admin seeding.

    Args:
        None.

    Returns:
        argparse.Namespace: Parsed user-provided options.

    Side Effects:
        Reads command-line arguments from process state.

    Raises:
        SystemExit: Raised by argparse on invalid arguments.
    """

    parser = argparse.ArgumentParser(description="Create or update admin account.")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument(
        "--email",
        default="admin@example.com",
        help="Admin email",
    )
    parser.add_argument(
        "--full-name",
        default="System Administrator",
        help="Admin display name",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Admin password. Prompts securely when omitted.",
    )
    return parser.parse_args()


def _resolve_password(cli_password: Optional[str]) -> str:
    """Resolve the password from CLI input or secure prompt.

    Args:
        cli_password: Password passed via command line, if any.

    Returns:
        str: Password string accepted for account creation.

    Side Effects:
        May prompt in terminal when no password is provided.

    Raises:
        ValueError: When password is shorter than 8 characters.
    """

    password = cli_password
    if not password:
        password = getpass.getpass("Admin password: ")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    return password


def _get_conflicting_user(username: str, email: str) -> Optional[Tuple[User, User]]:
    """Return conflicting users when username and email point to different rows.

    Args:
        username: Desired admin username.
        email: Desired admin email.

    Returns:
        Optional[Tuple[User, User]]: Conflicting users when both exist separately.

    Side Effects:
        Performs database read queries.

    Raises:
        None.
    """

    username_user = User.query.filter_by(username=username).first()
    email_user = User.query.filter_by(email=email).first()

    if username_user and email_user and username_user.id != email_user.id:
        return username_user, email_user

    return None


def create_or_update_admin(
    username: str,
    email: str,
    full_name: str,
    password: str,
) -> Tuple[User, bool]:
    """Create a new admin account or promote/update an existing account.

    Args:
        username: Admin username.
        email: Admin email.
        full_name: Admin display name.
        password: Plain-text password to hash and store.

    Returns:
        Tuple[User, bool]: Updated user object and `True` when newly created.

    Side Effects:
        Writes and commits user records in the database.

    Raises:
        RuntimeError: When username and email map to different existing users.
        SQLAlchemyError: When persistence operations fail.
    """

    conflicts = _get_conflicting_user(username=username, email=email)
    if conflicts is not None:
        raise RuntimeError(
            "Username and email belong to different accounts; resolve manually first."
        )

    user = User.query.filter_by(username=username).first()
    was_created = False

    if user is None:
        user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            preferred_lang=LanguageCode.EN,
        )
        was_created = True
        db.session.add(user)

    user.username = username
    user.email = email
    user.full_name = full_name
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_approved = True
    user.set_password(password)

    db.session.commit()
    return user, was_created


def main() -> int:
    """Run the admin seeding workflow from the command line.

    Args:
        None.

    Returns:
        int: POSIX-style process exit code.

    Side Effects:
        Creates database tables when missing and writes admin/system records.

    Raises:
        None. Errors are handled and converted to return codes.
    """

    args = parse_args()

    try:
        password = _resolve_password(args.password)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    app = create_app()
    with app.app_context():
        db.create_all()
        seed_default_system_config()

        try:
            user, was_created = create_or_update_admin(
                username=args.username.strip(),
                email=args.email.strip().lower(),
                full_name=args.full_name.strip(),
                password=password,
            )
        except (RuntimeError, SQLAlchemyError) as error:
            db.session.rollback()
            print(f"Failed to seed admin account: {error}")
            return 1

        username = user.username
        email = user.email

    action = "Created" if was_created else "Updated"
    print(f"{action} admin account: {username} ({email})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
