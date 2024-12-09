from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import sys
import os

# Add the app directory to sys.path so Alembic can find the models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import your SQLAlchemy models
from models.camera import Base  # Adjust the import path to your project structure
from config import settings
from sqlalchemy import create_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Set the target metadata for Alembic migrations
target_metadata = Base.metadata

# Update the SQLAlchemy URL from your app's database config
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()