# ---------------------------------------------------------------
#  Atelier Flask + SQLite
# ---------------------------------------------------------------
#  Ce fichier est le "cerveau" de votre application : il reçoit
#  les demandes des navigateurs, interroge la base de données
#  et fabrique les réponses.
#
#  Vous allez le compléter petit à petit, exercice après exercice.
#  Les consignes sont dans le dossier "exercices/".
# ---------------------------------------------------------------

import os
import sqlite3
from contextlib import closing
from decimal import Decimal, InvalidOperation
from pathlib import Path
from functools import wraps

from werkzeug.security import check_password_hash

from bibliotheque import creer_bibliotheque

from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify

app = Flask(__name__)
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax')

# Chemin ABSOLU vers la base de données.
# Sur PythonAnywhere, le serveur ne démarre pas forcément dans le dossier
# du projet : un simple 'database.db' créerait une base vide ailleurs !
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')


def get_db():
    """Ouvre une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.row_factory = sqlite3.Row
    return conn


def initialiser_application():
    if Path(DATABASE).is_file():
        with closing(get_db()) as conn:
            for fichier in ('002_ajout_commandes.sql', '003_ajout_utilisateurs.sql', '004_ajout_bibliotheque.sql'):
                migration = Path(BASE_DIR, 'migrations', fichier)
                conn.executescript(migration.read_text(encoding='utf-8'))
            with conn:
                conn.execute('BEGIN IMMEDIATE')
                for table in ('livres', 'utilisateurs'):
                    colonnes = conn.execute(f'PRAGMA table_info({table})').fetchall()
                    if not any(colonne['name'] == 'actif' for colonne in colonnes):
                        conn.execute(f'ALTER TABLE {table} ADD COLUMN actif INTEGER NOT NULL DEFAULT 1 CHECK (actif IN (0, 1))')
            app.secret_key = conn.execute(
                "SELECT valeur FROM configuration WHERE nom = 'secret_session'"
            ).fetchone()[0]


initialiser_application()


def est_authentifie():
    return a_le_role('admin', 'user')


def a_le_role(*roles):
    if session.get('role') not in roles:
        return False
    with closing(get_db()) as conn:
        compte = conn.execute('SELECT role FROM utilisateurs WHERE id = ? AND actif = 1', (session.get('utilisateur_id'),)).fetchone()
    return compte is not None and compte['role'] == session.get('role')


def acces(*roles):
    def decorateur(route):
        @wraps(route)
        def verifier(*args, **kwargs):
            if not est_authentifie():
                if request.method == 'GET':
                    destination = request.full_path.removesuffix('?')
                    if not destination.startswith('//') and chr(92) not in destination:
                        session['destination'] = destination
                return redirect(url_for('authentification'))
            if not a_le_role(*roles):
                abort(403)
            return route(*args, **kwargs)
        return verifier
    return decorateur


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(409)
def afficher_erreur(erreur):
    if request.path.startswith('/api/'):
        return jsonify(erreur=erreur.description), erreur.code
    return render_template('erreur.html', erreur=erreur), erreur.code


@app.route('/')
def hello_world():
    return render_template('hello.html')


@app.route('/lecture')
@acces('admin', 'user')
def lecture():
    return render_template('lecture.html')


@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        login = request.form.get('username', '').strip()
        with closing(get_db()) as conn:
            compte = conn.execute('SELECT * FROM utilisateurs WHERE login = ? AND actif = 1', (login,)).fetchone()
        if compte and check_password_hash(compte['mot_de_passe_hash'], request.form.get('password', '')):
            destination = session.get('destination') or url_for('ReadBDD')
            session.clear()
            session.update(utilisateur_id=compte['id'], role=compte['role'])
            return redirect(destination)
        return render_template('formulaire_authentification.html', error=True), 401

    return render_template('formulaire_authentification.html', error=False)


@app.post('/deconnexion')
def deconnexion():
    session.clear()
    return redirect(url_for('authentification'))


@app.route('/fiche_client/<int:post_id>')
@acces('admin', 'user')
def Readfiche(post_id):
    with closing(get_db()) as conn:
        client = conn.execute('SELECT * FROM clients WHERE id = ?', (post_id,)).fetchone()
        if client is None:
            abort(404, description='Client introuvable')
        commandes = conn.execute(
            'SELECT * FROM commandes WHERE client_id = ? ORDER BY id DESC', (post_id,),
        ).fetchall()
    return render_template('fiche_client.html', client=client, commandes=commandes)



@app.route('/consultation/')
@acces('admin', 'user')
def ReadBDD():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients ORDER BY nom;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/fiche_nom/<nom>')
@acces('admin', 'user')
def fiche_nom(nom):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE nom = ?', (nom,))
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/recherche')
@acces('admin', 'user')
def recherche():
    q = request.args.get('q', '').strip()
    tris = {'nom': 'nom, prenom, id', 'prenom': 'prenom, nom, id', 'created': 'created DESC, id DESC'}
    tri = request.args.get('tri', 'nom')
    if tri not in tris:
        tri = 'nom'
    data = []
    if q:
        motif = '%' + q + '%'
        with closing(get_db()) as conn:
            data = conn.execute(
                'SELECT * FROM clients WHERE nom LIKE ? OR prenom LIKE ? ORDER BY ' + tris[tri],
                (motif, motif),
            ).fetchall()
    return render_template('recherche.html', q=q, tri=tri, data=data)


@app.route('/enregistrer_client', methods=['GET'])
@acces('admin')
def formulaire_client():
    return render_template('formulaire.html')  # afficher le formulaire


@app.route('/enregistrer_client', methods=['POST'])
@acces('admin')
def enregistrer_client():
    champs_obligatoires = ('nom', 'prenom', 'adresse')
    valeurs = {champ: request.form.get(champ, '').strip() for champ in (*champs_obligatoires, 'telephone')}
    if not all(valeurs[champ] for champ in champs_obligatoires):
        return render_template('formulaire.html', valeurs=valeurs, erreur='Le nom, le prénom et l’adresse sont obligatoires.'), 400

    with closing(get_db()) as conn, conn:
        cursor = conn.execute(
            'INSERT INTO clients (nom, prenom, adresse, telephone) VALUES (?, ?, ?, ?)',
            (valeurs['nom'], valeurs['prenom'], valeurs['adresse'], valeurs['telephone'] or None),
        )
        client_id = cursor.lastrowid
    return redirect(url_for('Readfiche', post_id=client_id))


@app.route('/modifier_client/<int:client_id>', methods=['GET', 'POST'])
@acces('admin')
def modifier_client(client_id):
    champs_obligatoires = ('nom', 'prenom', 'adresse')
    with closing(get_db()) as conn:
        if request.method == 'GET':
            client = conn.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
            if client is None:
                abort(404, description='Client introuvable')
            return render_template('modifier_client.html', client_id=client_id, valeurs=dict(client))

        valeurs = {champ: request.form.get(champ, '').strip() for champ in (*champs_obligatoires, 'telephone')}
        if not all(valeurs[champ] for champ in champs_obligatoires):
            return render_template(
                'modifier_client.html', client_id=client_id, valeurs=valeurs,
                erreur='Le nom, le prénom et l’adresse sont obligatoires.',
            ), 400

        with conn:
            resultat = conn.execute(
                'UPDATE clients SET nom = ?, prenom = ?, adresse = ?, telephone = ? WHERE id = ?',
                (valeurs['nom'], valeurs['prenom'], valeurs['adresse'], valeurs['telephone'] or None, client_id),
            )
            if not resultat.rowcount:
                abort(404, description='Client introuvable')
    return redirect(url_for('ReadBDD'))


@app.post('/supprimer_client/<int:client_id>')
@acces('admin')
def supprimer_client(client_id):
    with closing(get_db()) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        nombre = conn.execute(
            'SELECT COUNT(*) FROM commandes WHERE client_id = ?', (client_id,),
        ).fetchone()[0]
        if nombre:
            return render_template('suppression_refusee.html', nombre=nombre, client_id=client_id), 409
        resultat = conn.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        if not resultat.rowcount:
            abort(404, description='Client introuvable')
    return redirect(url_for('ReadBDD'))


@app.get('/commandes/')
@acces('admin', 'user')
def commandes():
    with closing(get_db()) as conn:
        lignes = conn.execute(
            """SELECT commandes.*, clients.nom, clients.prenom
               FROM commandes JOIN clients ON commandes.client_id = clients.id
               ORDER BY commandes.id DESC"""
        ).fetchall()
    return render_template('commandes.html', commandes=lignes)


@app.get('/statistiques/')
@acces('admin', 'user')
def statistiques():
    with closing(get_db()) as conn:
        lignes = conn.execute(
            """SELECT clients.id, clients.nom, clients.prenom, COUNT(commandes.id) AS nombre,
                      COALESCE(SUM(commandes.montant), 0) AS total
               FROM clients LEFT JOIN commandes ON commandes.client_id = clients.id
               GROUP BY clients.id ORDER BY total DESC, clients.nom, clients.id"""
        ).fetchall()
    return render_template('statistiques.html', clients=lignes)


@app.post('/fiche_client/<int:client_id>/commandes')
@acces('admin')
def ajouter_commande(client_id):
    produit = request.form.get('produit', '').strip()
    try:
        montant = Decimal(request.form.get('montant', '').strip().replace(',', '.'))
    except InvalidOperation:
        abort(400, description='Indiquez un montant valide.')
    if not produit or not montant.is_finite() or not 0 <= montant <= Decimal('999999999.99'):
        abort(400, description='Indiquez un produit et un montant valide.')
    if montant != montant.quantize(Decimal('0.01')):
        abort(400, description='Le montant doit avoir au maximum deux décimales.')

    with closing(get_db()) as conn, conn:
        cursor = conn.execute(
            """INSERT INTO commandes (client_id, produit, montant)
               SELECT id, ?, ? FROM clients WHERE id = ?""",
            (produit, float(montant), client_id),
        )
        if not cursor.rowcount:
            abort(404, description='Client introuvable')
    return redirect(url_for('Readfiche', post_id=client_id))


@app.get('/api/clients')
def api_liste_clients():
    if not est_authentifie():
        return jsonify(erreur='Authentification requise'), 401
    motif = '%' + request.args.get('q', '').strip() + '%'
    with closing(get_db()) as conn:
        rows = conn.execute(
            'SELECT * FROM clients WHERE nom LIKE ? OR prenom LIKE ? ORDER BY nom, id',
            (motif, motif),
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get('/api/clients/<int:client_id>')
def api_un_client(client_id):
    if not est_authentifie():
        return jsonify(erreur='Authentification requise'), 401
    with closing(get_db()) as conn:
        row = conn.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
    if row is None:
        return jsonify(erreur='Client introuvable'), 404
    return jsonify(dict(row))


@app.post('/api/clients')
def api_creer_client():
    if not a_le_role('admin'):
        return jsonify(erreur='Authentification administrateur requise'), 401
    data = request.get_json(silent=True)
    champs = ('nom', 'prenom', 'adresse')
    if not isinstance(data, dict) or not all(
        isinstance(data.get(champ), str) and data[champ].strip() for champ in champs
    ):
        return jsonify(erreur='Les champs nom, prenom et adresse sont obligatoires'), 400
    nom, prenom, adresse = (data[champ].strip() for champ in champs)
    with closing(get_db()) as conn, conn:
        row = conn.execute(
            'INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)', (nom, prenom, adresse),
        )
        client_id = row.lastrowid
    return jsonify(id=client_id, nom=nom, prenom=prenom, adresse=adresse), 201


@app.delete('/api/clients/<int:client_id>')
def api_supprimer_client(client_id):
    if not a_le_role('admin'):
        return jsonify(erreur='Authentification administrateur requise'), 401
    try:
        with closing(get_db()) as conn, conn:
            row = conn.execute('DELETE FROM clients WHERE id = ?', (client_id,))
            if not row.rowcount:
                return jsonify(erreur='Client introuvable'), 404
    except sqlite3.IntegrityError:
        return jsonify(erreur='Ce client a des commandes'), 409
    return '', 204


@app.get('/clients-api')
@acces('admin', 'user')
def clients_api():
    return render_template('clients_api.html')


# ---------------------------------------------------------------
#  Ajoutez vos nouvelles routes ci-dessous 👇
# ---------------------------------------------------------------



# ---------------------------------------------------------------
#  Ne pas modifier : utile seulement pour lancer le site
#  sur votre propre ordinateur (python flask_app.py)
# ---------------------------------------------------------------
app.register_blueprint(creer_bibliotheque(get_db, acces, est_authentifie))


if __name__ == "__main__":
    app.run(debug=True)
