
# Flask-Migrate Commands Guide

Flask-Migrate is an extension that handles SQLAlchemy database migrations for Flask applications. It integrates with Alembic, a database migration tool for SQLAlchemy. Below are the common commands you'll need to manage database migrations in a Flask project.

---

## Step-by-Step Guide for Flask-Migrate Commands

### 1. **Install Flask-Migrate**

Before using Flask-Migrate, ensure it's installed:

```bash
pip install Flask-Migrate
```

### 2. **Initialize Flask-Migrate**

In your main Flask application file (e.g., `app.py` or `run.py`), initialize Flask-Migrate:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize the app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Example database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
```

### 3. **Create Migration Folder**

To create a folder where migration scripts will be stored:

```bash
flask db init
```

- **Explanation**: This command initializes the `migrations/` directory. This folder will contain the migration scripts.

#### Example output:

```
$ flask db init
  Creating directory migrations...  done
  Creating directory migrations/versions...  done
  Creating file migrations/alembic.ini...  done
  Creating file migrations/env.py...  done
  Creating file migrations/README...  done
  Creating file migrations/script.py.mako...  done
```

### 4. **Generate Migration Script**

To generate a migration script based on changes in your SQLAlchemy models:

```bash
flask db migrate -m "Initial migration"
```

- **Explanation**: This command detects changes to your models (compared to the database) and generates a migration script that will create or modify database tables. The `-m` flag is used to provide a description for the migration (e.g., "Initial migration").

#### Example output:

```
$ flask db migrate -m "Initial migration"
  Generating migrations/versions/xxxxxx_initial_migration.py...  done
```

- The script will be stored in the `migrations/versions/` directory.

### 5. **Apply Migration (Upgrade Database)**

To apply the migration and update the database schema:

```bash
flask db upgrade
```

- **Explanation**: This command applies the migration scripts and modifies the database according to the generated migration.

#### Example output:

```
$ flask db upgrade
  Upgrading to xxxxxx_revision_id... done
```

### 6. **Downgrade Migration (Rollback)**

To roll back (undo) a migration, you can use the `flask db downgrade` command. This will revert the database schema to a previous state.

```bash
flask db downgrade
```

- **Explanation**: This command reverts the database schema by undoing the last applied migration.

#### Example output:

```
$ flask db downgrade
  Downgrading to previous_revision_id... done
```

### 7. **Show Current Migration Version**

To check the current version of the database schema:

```bash
flask db current
```

- **Explanation**: This command shows the current migration version applied to the database. It helps track which migrations have been applied.

#### Example output:

```
$ flask db current
  Current revision for /your/database/path: xxxxxx_revision_id
```

### 8. **Show Migration History**

To show the migration history, including all revisions:

```bash
flask db history
```

- **Explanation**: This command lists all migrations that have been created, including the revision identifiers and their descriptions.

#### Example output:

```
$ flask db history
  ---+--------------------------------+----------------------
  Rev   | Message                     | Date
  ----+--------------------------------+----------------------
  xxxxxx_revision_id | Initial migration      | 2024-12-12 14:00:00
```

### 9. **Stamp the Database with a Revision**

To mark the database with a specific revision without actually applying migrations:

```bash
flask db stamp head
```

- **Explanation**: This command is useful if you have manually modified the database and want to align it with the migration history. `head` refers to the most recent revision.

#### Example output:

```
$ flask db stamp head
  Stamping the database with revision xxxxxx_revision_id... done
```

### 10. **Autogenerate Migration Script for Changes**

If you made changes to your models and want to generate a new migration, you can run:

```bash
flask db migrate -m "Added new field to User model"
```

- **Explanation**: This will generate a migration script for any new changes made to your SQLAlchemy models since the last migration.

#### Example output:

```
$ flask db migrate -m "Added new field to User model"
  Generating migrations/versions/yyyyyy_added_new_field.py...  done
```

### 11. **Manual Script Generation (Optional)**

Sometimes, you may want to manually create a migration script instead of relying on auto-generation. You can create an empty script using:

```bash
flask db revision -m "Manual migration"
```

- **Explanation**: This creates an empty migration script in the `migrations/versions/` directory. You can then edit the script to add specific migration logic.

#### Example output:

```
$ flask db revision -m "Manual migration"
  Generating migrations/versions/zzzzzz_manual_migration.py...  done
```

### 12. **Revert All Migrations (Remove All Migrations)**

If you need to reset your database (use with caution), you can run the following to remove all migrations and start fresh:

```bash
flask db reset
```

- **Explanation**: This command will drop all tables and revert the schema back to the initial state. Use carefully as this removes data.

#### Example output:

```
$ flask db reset
  Dropping all tables... done
  Resetting database to initial state... done
```

---

## Example Workflow for Initial Setup

### 1. **Initialize Database and Migrations**
```bash
flask db init
```

### 2. **Generate the First Migration Script**
```bash
flask db migrate -m "Initial migration"
```

### 3. **Apply the Migration to the Database**
```bash
flask db upgrade
```

### 4. **Make Changes to Your Models** (e.g., add a new field to `User` model)

### 5. **Generate a New Migration Script**
```bash
flask db migrate -m "Added new field to User model"
```

### 6. **Apply the New Migration**
```bash
flask db upgrade
```

---

## Final Notes

- **Flask-Migrate** provides a set of commands to manage your database migrations, making it easier to handle changes to your database schema as your application grows.
- Always make sure to run `flask db migrate` whenever you make changes to your models to keep the migration scripts up to date.
- Be cautious with `flask db downgrade` and `flask db reset`, especially in production environments, as they can result in data loss.

Let me know if you need further explanations or assistance!

---
