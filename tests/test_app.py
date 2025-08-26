# tests/test_app.py

import unittest
from app import create_app
from config import TestConfig

class TestAppInitialization(unittest.TestCase):

    def setUp(self):
        # Configure l'application pour les tests
        self.app = create_app(config_class=TestConfig)
        self.app.testing = True
        self.client = self.app.test_client()

        # Établit le contexte de l'application
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Initialise la base de données
        from models import db
        db.create_all()

    def tearDown(self):
        # Nettoie la base de données après chaque test
        from models import db
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.config['TESTING'])
