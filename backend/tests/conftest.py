import os
import pytest

from app import create_app

@pytest.fixture
def app():
    # Ensure test API key is set so gemini service initializes without error
    os.environ.setdefault('GEMINI_API_KEY', 'testkey')

    app = create_app()
    app.config['TESTING'] = True
    yield app

@pytest.fixture
def client(app):
    return app.test_client()