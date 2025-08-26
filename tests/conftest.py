# tests/conftest.py

import pytest
from app import create_app, db
from config_test import TestConfig
from models import Participant

@pytest.fixture(scope='module')
def test_client():
    # Crée une instance de l'application avec la configuration de test
    flask_app = create_app(config_class=TestConfig)

    # Crée un client de test
    testing_client = flask_app.test_client()

    # Établit le contexte de l'application
    ctx = flask_app.app_context()
    ctx.push()

    # Crée les tables de la base de données
    db.create_all()

    yield testing_client  # Les tests seront exécutés ici

    # Nettoie après les tests
    db.session.remove()
    db.drop_all()
    ctx.pop()
