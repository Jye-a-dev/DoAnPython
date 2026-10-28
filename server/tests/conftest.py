"""
conftest.py — Pytest fixtures for server test suites.
"""

from __future__ import annotations

import pytest
from app.main import create_app
from app.core.database import db


@pytest.fixture
def app():
    app_instance = create_app()
    app_instance.config["TESTING"] = True
    app_instance.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app_instance.app_context():
        db.create_all()
        yield app_instance
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

