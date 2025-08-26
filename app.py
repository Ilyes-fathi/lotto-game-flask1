# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Participant, Tirage, Settings, init_db
import random
import itertools
from config import Config

def create_app(config_class=Config):
    print("Création de l'application Flask")
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = app.config['SECRET_KEY']

    print("Initialisation de la base de données")
    db.init_app(app)

    with app.app_context():
        print("Initialisation de la base de données avec init_db")
        init_db()

        # 👇 garanti qu'on a une ligne Settings
        ensure_default_settings()

        # Définition des filtres personnalisés
        register_filters(app)

        # Enregistrement des routes
        register_routes(app)

    return app

def register_filters(app):
    # Filtre pour formater les gains avec le symbole €
    @app.template_filter('format_gain')
    def format_gain(gain):
        try:
            if gain is None or gain == "":
                return "0 €"
            g = float(gain)
            return f"{int(g)} €" if g.is_integer() else f"{g:.2f} €"
        except Exception:
            return "0 €"

    # Filtre pour formater les nombres sans le symbole €
    @app.template_filter('format_number')
    def format_number(number):
        try:
            if number is None or number == "":
                return "0"
            n = float(number)
            return f"{int(n)}" if n.is_integer() else f"{n:.2f}"
        except Exception:
            return "0"


def ensure_default_settings():
    s = Settings.query.first()
    if not s:
        s = Settings(
            max_participants=100,
            jackpot_amount=3000000,
            max_numeros=49,
            max_etoiles=9,
            selection_numeros=5,
            selection_etoiles=2,
            max_gagnants=10
        )
        db.session.add(s)
        db.session.commit()


def register_routes(app):
    # Route pour la page d'accueil
    @app.route('/')
    def index():
        print("Accès à la route /")
        settings = Settings.query.first()
        if not settings:
            ensure_default_settings()
            settings = Settings.query.first()
        return render_template('index.html', settings=settings)


    # Route pour la page des règles du jeu
    @app.route('/rules')
    def rules():
        print("Accès à la route /rules")
        settings = Settings.query.first()
        return render_template('rules.html', settings=settings)

    # Route pour effectuer un tirage
    @app.route('/tirage', methods=['GET', 'POST'])
    def tirage():
        print("Accès à la route /tirage")
        participants = Participant.query.all()

        if len(participants) == 0:
            error = "Aucun participant disponible pour le tirage."
            return render_template('tirage.html', error=error)

        if request.method == 'POST':
            settings = Settings.query.first()
            numeros = random.sample(range(1, settings.max_numeros + 1), settings.selection_numeros)
            etoiles = random.sample(range(1, settings.max_etoiles + 1), settings.selection_etoiles)
            nouveau_tirage = Tirage(numeros=numeros, etoiles=etoiles)
            db.session.add(nouveau_tirage)
            db.session.commit()
            return redirect(url_for('resultats'))

        return render_template('tirage.html')

    # Route pour générer automatiquement des participants
    @app.route('/generer_participants', methods=['POST'])
    def generer_participants():
        print("Accès à la route /generer_participants")
        nombre_demande = int(request.form['nombre'])
        settings = Settings.query.first()
        participants_existants = Participant.query.count()
        nombre_disponible = settings.max_participants - participants_existants

        if nombre_disponible <= 0:
            participants = Participant.query.all()
            erreur = f"Le nombre maximum de {settings.max_participants} participants a été atteint."
            return render_template('inscription.html', participants=participants, erreur=erreur, settings=settings)

        nombre_a_generer = min(nombre_demande, nombre_disponible)
        for i in range(nombre_a_generer):
            numeros = random.sample(range(1, settings.max_numeros + 1), settings.selection_numeros)
            etoiles = random.sample(range(1, settings.max_etoiles + 1), settings.selection_etoiles)
            nom_fictif = f'Participant_{participants_existants + i + 1}'
            participant = Participant(nom=nom_fictif, numeros=numeros, etoiles=etoiles)
            db.session.add(participant)

        db.session.commit()

        return redirect(url_for('inscription', success=f"{nombre_a_generer} participants générés avec succès !"))

    # Route pour supprimer tous les participants
    @app.route('/supprimer_participants', methods=['POST'])
    def supprimer_participants():
        print("Accès à la route /supprimer_participants")
        Participant.query.delete()
        db.session.commit()

        nom = request.form.get('nom', '')
        numeros = request.form.get('numeros', '')
        etoiles = request.form.get('etoiles', '')

        return redirect(url_for('inscription', success="Tous les participants ont été supprimés.", nom=nom, numeros=numeros, etoiles=etoiles))

    # Route pour afficher la liste des participants
    @app.route('/participants', methods=['GET'])
    def participants_route():
        print("Accès à la route /participants")
        participants = Participant.query.all()
        return render_template('participants.html', participants=participants)

    # Route pour afficher les résultats du dernier tirage
    @app.route('/resultats')
    def resultats():
        print("Accès à la route /resultats")
        participants = Participant.query.all()
        tirage = Tirage.query.order_by(Tirage.id.desc()).first()

        if not participants:
            return redirect(url_for('tirage', error="Aucun participant trouvé pour les résultats."))

        if not tirage:
            # Pas de tirage encore -> redirige vers la page de tirage
            return redirect(url_for('tirage', error="Aucun tirage n'a encore été effectué."))

        sorted_participants = calculer_gains(participants, tirage)
        settings = Settings.query.first()
        return render_template('resultats.html', participants=sorted_participants, tirage=tirage, settings=settings)


    # Route pour afficher et modifier les réglages du jeu
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        print("Accès à la route /settings")
        settings = Settings.query.first()

        if not settings:
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

        if request.method == 'POST':
            max_gagnants = int(request.form['max_gagnants'])
            if max_gagnants > 10:
                max_gagnants = 10

            settings.max_participants = int(request.form['max_participants'])
            settings.jackpot_amount = float(request.form['jackpot_amount'])
            settings.max_numeros = int(request.form['max_numeros'])
            settings.max_etoiles = int(request.form['max_etoiles'])
            settings.selection_numeros = int(request.form['selection_numeros'])
            settings.selection_etoiles = int(request.form['selection_etoiles'])
            settings.max_gagnants = max_gagnants

            db.session.commit()
            return redirect(url_for('settings', success="Les réglages ont été mis à jour avec succès !"))

        success = request.args.get('success')
        return render_template('settings.html', settings=settings, success=success)

    # Route pour réinitialiser les réglages aux valeurs par défaut
    @app.route('/reset_settings', methods=['POST'])
    def reset_settings():
        print("Accès à la route /reset_settings")
        settings = Settings.query.first()

        if settings:
            settings.max_participants = 100
            settings.jackpot_amount = 3000000
            settings.max_numeros = 49
            settings.max_etoiles = 9
            settings.selection_numeros = 5
            settings.selection_etoiles = 2
            settings.max_gagnants = 10

            db.session.commit()

        return redirect(url_for('settings', success="Les réglages ont été réinitialisés avec succès !"))

    # Route pour l'inscription des participants
    @app.route('/inscription', methods=['GET', 'POST'])
    def inscription():
        print("Accès à la route /inscription")
        success = request.args.get('success')
        erreur = None

        settings = Settings.query.first()
        nombre_participants = Participant.query.count()

        nom = request.args.get('nom', '')
        numeros = [int(n) for n in request.args.get('numeros', '').split(',') if n] if request.args.get('numeros') else []
        etoiles = [int(e) for e in request.args.get('etoiles', '').split(',') if e] if request.args.get('etoiles') else []

        if request.method == 'POST':
            nom = request.form['nom']
            numeros = [int(n) for n in request.form.getlist('numeros')]
            etoiles = [int(e) for e in request.form.getlist('etoiles')]

            if nombre_participants >= settings.max_participants:
                erreur = f"Le nombre maximum de {settings.max_participants} participants a été atteint. Vous ne pouvez pas ajouter d'autres participants."
            else:
                if Participant.query.filter_by(nom=nom).first():
                    erreur = "Ce nom est déjà pris, veuillez en choisir un autre."
                elif not nom:
                    erreur = "Veuillez entrer votre nom."
                elif len(numeros) != settings.selection_numeros or len(set(numeros)) != settings.selection_numeros or not all(1 <= n <= settings.max_numeros for n in numeros):
                    erreur = f"Veuillez sélectionner {settings.selection_numeros} numéros uniques entre 1 et {settings.max_numeros}."
                elif len(etoiles) != settings.selection_etoiles or len(set(etoiles)) != settings.selection_etoiles or not all(1 <= e <= settings.max_etoiles for e in etoiles):
                    erreur = f"Veuillez sélectionner {settings.selection_etoiles} étoiles uniques entre 1 et {settings.max_etoiles}."

            if not erreur:
                participant = Participant(nom=nom, numeros=numeros, etoiles=etoiles)
                db.session.add(participant)
                db.session.commit()

                return redirect(url_for('inscription', success="Participant ajouté avec succès !"))

        participants = Participant.query.all()

        return render_template('inscription.html', participants=participants, success=success, erreur=erreur, nom=nom, numeros=numeros, etoiles=etoiles, settings=settings)

    # Fonction pour calculer la proximité des numéros entre le participant et le tirage
    def calculate_numbers_proximity(numeros_participant, numeros_tirage):
        matched_numbers = set(numeros_participant).intersection(numeros_tirage)
        unmatched_drawn_numbers = list(set(numeros_tirage).difference(matched_numbers))
        unmatched_participant_numbers = list(set(numeros_participant).difference(matched_numbers))

        if not unmatched_drawn_numbers or not unmatched_participant_numbers:
            return 0

        permutations = itertools.permutations(unmatched_participant_numbers)

        min_total_proximity = None
        for perm in permutations:
            total_proximity = sum(abs(num_draw - num_part) for num_draw, num_part in zip(unmatched_drawn_numbers, perm))
            if min_total_proximity is None or total_proximity < min_total_proximity:
                min_total_proximity = total_proximity

        return min_total_proximity

    # Fonction pour calculer la proximité des étoiles entre le participant et le tirage
    def calculate_stars_proximity(etoiles_participant, etoiles_tirage):
        matched_stars = set(etoiles_participant).intersection(etoiles_tirage)
        unmatched_drawn_stars = list(set(etoiles_tirage).difference(matched_stars))
        unmatched_participant_stars = list(set(etoiles_participant).difference(matched_stars))

        if not unmatched_drawn_stars or not unmatched_participant_stars:
            return 0

        permutations = itertools.permutations(unmatched_participant_stars)

        min_total_proximity = None
        for perm in permutations:
            total_proximity = sum(abs(star_draw - star_part) for star_draw, star_part in zip(unmatched_drawn_stars, perm))
            if min_total_proximity is None or total_proximity < min_total_proximity:
                min_total_proximity = total_proximity

        return min_total_proximity

    # Fonction pour calculer les gains des participants en fonction du tirage
    def calculer_gains(participants, tirage):
        settings = Settings.query.first()
        total_gains = settings.jackpot_amount
        max_gagnants = min(settings.max_gagnants, 10)

        pourcentages_fixes = [40, 20, 12, 7, 6, 5, 4, 3, 2, 1]

        for participant in participants:
            participant.match_numeros = len(set(participant.numeros).intersection(tirage.numeros))
            participant.match_etoiles = len(set(participant.etoiles).intersection(tirage.etoiles))
            participant.numbers_proximity = calculate_numbers_proximity(participant.numeros, tirage.numeros)
            participant.stars_proximity = calculate_stars_proximity(participant.etoiles, tirage.etoiles)

        sorted_participants = sorted(
            participants,
            key=lambda p: (
                -p.match_numeros,
                -p.match_etoiles,
                p.numbers_proximity,
                p.stars_proximity
            )
        )

        nb_gagnants = min(len(sorted_participants), max_gagnants)
        pourcentages = pourcentages_fixes[:nb_gagnants]

        if nb_gagnants < 10:
            somme_pourcentages = sum(pourcentages)
            pourcentages_normalises = [(p / somme_pourcentages) * 100 for p in pourcentages]
        else:
            pourcentages_normalises = pourcentages

        position = 0
        while position < nb_gagnants:
            same_rank_participants = [sorted_participants[position]]
            current_match = (
                sorted_participants[position].match_numeros,
                sorted_participants[position].match_etoiles,
                sorted_participants[position].numbers_proximity,
                sorted_participants[position].stars_proximity
            )

            while (position + 1 < nb_gagnants and
                   (sorted_participants[position + 1].match_numeros,
                    sorted_participants[position + 1].match_etoiles,
                    sorted_participants[position + 1].numbers_proximity,
                    sorted_participants[position + 1].stars_proximity) == current_match):
                same_rank_participants.append(sorted_participants[position + 1])
                position += 1

            start_rank = position - len(same_rank_participants) + 1
            end_rank = position + 1

            total_pourcentage = sum(pourcentages_normalises[start_rank:end_rank])
            gain_par_participant = (total_gains * (total_pourcentage / 100)) / len(same_rank_participants)

            for p in same_rank_participants:
                p.gain = gain_par_participant
            position += 1

        for p in sorted_participants[nb_gagnants:]:
            p.gain = 0

        db.session.commit()

        return sorted_participants

if __name__ == '__main__':
    print("Démarrage de l'application Flask")
    app = create_app()
    print("Exécution de l'application Flask")
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )

