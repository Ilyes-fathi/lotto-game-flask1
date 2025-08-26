# tests/test_routes.py

import unittest
from app import create_app
from models import db, Participant, Settings
from config import TestConfig

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app.testing = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Ajouter des réglages par défaut
        settings = Settings(
            max_participants=100,
            jackpot_amount=3000000,
            max_numeros=49,
            max_etoiles=9,
            selection_numeros=5,
            selection_etoiles=2,
            max_gagnants=10
        )
        db.session.add(settings)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bienvenue sur le Jeu du LOTO', response.data)

    def test_inscription_get(self):
        response = self.client.get('/inscription')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ajouter un participant manuellement', response.data)

    def test_inscription_post(self):
        # Envoi d'un formulaire d'inscription valide
        response = self.client.post('/inscription', data={
            'nom': 'TestUser',
            'numeros': ['1', '2', '3', '4', '5'],
            'etoiles': ['1', '2']
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Participant ajout\xc3\xa9 avec succ\xc3\xa8s', response.data)

        # Vérifier que le participant a été ajouté
        participant = Participant.query.filter_by(nom='TestUser').first()
        self.assertIsNotNone(participant)
        self.assertEqual(participant.numeros, [1,2,3,4,5])
        self.assertEqual(participant.etoiles, [1,2])

    def test_tirage_without_participants(self):
        response = self.client.get('/tirage')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Aucun participant disponible pour le tirage.', response.data)

    def test_tirage_with_participants(self):
        # Ajouter un participant
        participant = Participant(nom='TestUser', numeros=[1,2,3,4,5], etoiles=[1,2])
        db.session.add(participant)
        db.session.commit()

        response = self.client.post('/tirage', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'R\xc3\xa9sultats du Tirage', response.data)

    def test_settings_get(self):
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Modifier les R\xc3\xa9glages du Jeu', response.data)

    def test_settings_post(self):
        response = self.client.post('/settings', data={
            'max_participants': '200',
            'jackpot_amount': '5000000',
            'max_numeros': '60',
            'max_etoiles': '12',
            'selection_numeros': '6',
            'selection_etoiles': '3',
            'max_gagnants': '5'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Les r\xc3\xa9glages ont \xc3\xa9t\xc3\xa9 mis \xc3\xa0 jour avec succ\xc3\xa8s', response.data)

        # Vérifier que les réglages ont été mis à jour
        settings = Settings.query.first()
        self.assertEqual(settings.max_participants, 200)
        self.assertEqual(settings.jackpot_amount, 5000000)
        self.assertEqual(settings.max_numeros, 60)
        self.assertEqual(settings.max_etoiles, 12)
        self.assertEqual(settings.selection_numeros, 6)
        self.assertEqual(settings.selection_etoiles, 3)
        self.assertEqual(settings.max_gagnants, 5)

