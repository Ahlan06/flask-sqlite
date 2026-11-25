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

from flask import Flask, render_template, request, redirect, url_for, session, abort

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour signer les sessions (à cacher par la suite)

# Chemin ABSOLU vers la base de données.
# Sur PythonAnywhere, le serveur ne démarre pas forcément dans le dossier
# du projet : un simple 'database.db' créerait une base vide ailleurs !
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')


def get_db():
    """Ouvre une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Fonction pour savoir si l'utilisateur s'est authentifié
def est_authentifie():
    return session.get('authentifie')


@app.route('/')
def hello_world():
    return render_template('hello.html')


@app.route('/lecture')
def lecture():
    if not est_authentifie():
        # Rediriger vers la page d'authentification si l'utilisateur n'est pas authentifié
        return redirect(url_for('authentification'))

    # Si l'utilisateur est authentifié
    return "<h2>Bravo, vous êtes authentifié</h2>"


@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        # Vérifier les identifiants
        if request.form['username'] == 'admin' and request.form['password'] == 'password':  # password à cacher par la suite
            session['authentifie'] = True
            # Rediriger vers la route lecture après une authentification réussie
            return redirect(url_for('lecture'))
        else:
            # Afficher un message d'erreur si les identifiants sont incorrects
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)


@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    data = cursor.fetchone()
    conn.close()
    if not data:
        return "<h2>Client introuvable</h2>", 404
    return render_template('fiche_client.html', client=data)


@app.route('/consultation/')
def ReadBDD():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients ORDER BY nom;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/fiche_nom/<nom>')
def fiche_nom(nom):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE nom = ?', (nom,))
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/recherche')
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
def formulaire_client():
    return render_template('formulaire.html')  # afficher le formulaire


@app.route('/enregistrer_client', methods=['POST'])
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
def supprimer_client(client_id):
    with closing(get_db()) as conn, conn:
        resultat = conn.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        if not resultat.rowcount:
            abort(404, description='Client introuvable')
    return redirect(url_for('ReadBDD'))


# ---------------------------------------------------------------
#  Ajoutez vos nouvelles routes ci-dessous 👇
# ---------------------------------------------------------------



# ---------------------------------------------------------------
#  Ne pas modifier : utile seulement pour lancer le site
#  sur votre propre ordinateur (python flask_app.py)
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
