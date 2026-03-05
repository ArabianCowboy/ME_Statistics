# Test Credentials

> **⚠️ WARNING**: This file contains test credentials for local development only.
> Never commit real credentials or use these in production!

## Admin Account

Created during initial database setup:

- **Username**: `admin`
- **Email**: `admin@mestatistics.local`
- **Password**: `Admin123!`
- **Role**: Administrator
- **Status**: Active & Approved

## Access URLs

- **Local Development**: http://localhost:5000
- **Login Page**: http://localhost:5000/auth/login
- **Admin Dashboard**: http://localhost:5000/dashboard/admin (after login)

## Running the Application

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Start the development server
python run.py
```

## Creating Additional Test Users

You can create additional users through:
1. The registration page (requires admin approval)
2. Admin user management interface (after logging in as admin)
3. Using the create_admin.py script:

```powershell
python scripts/create_admin.py --username testuser --email test@example.com --full-name "Test User"
```

## Database Location

- **SQLite Database**: `instance/me_statistics.db`
- **Migrations**: `migrations/versions/`

## Resetting the Database

If you need to start fresh:

```powershell
# Remove the database
Remove-Item instance/me_statistics.db

# Rerun migrations
flask --app run.py db upgrade

# Reinitialize system config
flask --app run.py init-db

# Recreate admin
python scripts/create_admin.py --username admin --email admin@mestatistics.local --full-name "System Administrator" --password Admin123!
```
