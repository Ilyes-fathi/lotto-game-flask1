# tests/test_models.py

import unittest
from app import create_app
from models import db, Participant, Settings
from config import TestConfig

class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app.testing = True
        self.client = self.app.test_client()

        # Établit le contexte de l'application
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Crée les tables de la base de données
        db.create_all()

    def tearDown(self):
        # Nettoie la base de données après chaque test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_participant_model(self):
        participant = Participant(nom='TestUser', numeros=[1,2,3,4,5], etoiles=[1,2])
        db.session.add(participant)
        db.session.commit()

        retrieved = Participant.query.filter_by(nom='TestUser').first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.numeros, [1,2,3,4,5])
        self.assertEqual(retrieved.etoiles, [1,2])

    def test_settings_model(self):
        settings = Settings(
            max_participants=50,
            jackpot_amount=5000000,
            max_numeros=50,
            max_etoiles=12,
            selection_numeros=6,
            selection_etoiles=2,
            max_gagnants=5
        )
        db.session.add(settings)
        db.session.commit()

        retrieved = Settings.query.first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.max_participants, 50)
        self.assertEqual(retrieved.jackpot_amount, 5000000)
        self.assertEqual(retrieved.max_numeros, 50)
        self.assertEqual(retrieved.max_etoiles, 12)
        self.assertEqual(retrieved.selection_numeros, 6)
        self.assertEqual(retrieved.selection_etoiles, 2)
        self.assertEqual(retrieved.max_gagnants, 5)
