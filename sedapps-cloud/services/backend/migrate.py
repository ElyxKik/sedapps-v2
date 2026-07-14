#!/usr/bin/env python
"""
Migration script to create tables in Supabase or local PostgreSQL.
Run this before starting the backend for the first time.
"""

from sqlalchemy import inspect, text

from app.database import Base, engine
from app.models import AiJob, Article, Comment, FormSubmission, MediaAsset, Project, User

def migrate():
    """Create all tables in the database."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    project_columns = [column["name"] for column in inspector.get_columns("projects")]
    if "generated_files" not in project_columns:
        print("Adding projects.generated_files column...")
        with engine.begin() as connection:
            if engine.url.get_backend_name().startswith("sqlite"):
                connection.execute(text("ALTER TABLE projects ADD COLUMN generated_files JSON DEFAULT '[]'"))
            else:
                connection.execute(text("ALTER TABLE projects ADD COLUMN generated_files JSONB DEFAULT '[]'::jsonb"))
    print("✓ Tables created successfully!")

if __name__ == "__main__":
    migrate()
