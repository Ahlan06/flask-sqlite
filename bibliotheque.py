import sqlite3
from contextlib import closing

from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash


CATALOGUE = """
    SELECT livres.*, livres.nb_exemplaires - COUNT(emprunts.id) AS nb_disponibles
    FROM livres
    LEFT JOIN emprunts ON emprunts.livre_id = livres.id AND emprunts.date_retour IS NULL
"""


def creer_bibliotheque(get_db, acces, est_authentifie):
    bp = Blueprint('bibliotheque', __name__)

    def chercher_livres(q):
        motif = '%' + q + '%'
        with closing(get_db()) as conn:
            return conn.execute(
                CATALOGUE + ' WHERE livres.actif = 1 AND (titre LIKE ? OR auteur LIKE ?) GROUP BY livres.id ORDER BY titre, livres.id',
                (motif, motif),
            ).fetchall()

    @bp.get('/livres')
    @acces('admin', 'user')
    def livres():
        q = request.args.get('q', '').strip()
        return render_template('livres.html', livres=chercher_livres(q), q=q)

    @bp.route('/admin/livres/nouveau', methods=['GET', 'POST'])
    @bp.route('/admin/livres/<int:livre_id>/modifier', methods=['GET', 'POST'])
    @acces('admin')
    def modifier_livre(livre_id=None):
        with closing(get_db()) as conn, conn:
            if request.method == 'POST':
                conn.execute('BEGIN IMMEDIATE')
            livre = {}
            if livre_id is not None:
                ligne = conn.execute(CATALOGUE + ' WHERE livres.id = ? AND livres.actif = 1 GROUP BY livres.id', (livre_id,)).fetchone()
                if ligne is None:
                    abort(404, description='Livre introuvable.')
                livre = dict(ligne)
            if request.method == 'GET':
                return render_template('livre_formulaire.html', livre=livre, livre_id=livre_id)

            champs = ('titre', 'auteur', 'isbn', 'annee', 'genre', 'nb_exemplaires')
            valeurs = {champ: request.form.get(champ, '').strip() for champ in champs}
            try:
                stock = int(valeurs['nb_exemplaires'])
                annee = int(valeurs['annee']) if valeurs['annee'] else None
            except ValueError:
                abort(400, description='Indiquez une année et un stock valides.')
            if not valeurs['titre'] or not valeurs['auteur']:
                abort(400, description='Le titre et l’auteur sont obligatoires.')
            if not 0 <= stock <= 1_000_000 or (annee is not None and not 1 <= annee <= 9999):
                abort(400, description='Indiquez une année et un stock valides.')
            if livre_id is not None and stock < livre['nb_exemplaires'] - livre['nb_disponibles']:
                abort(409, description='Le stock doit couvrir les emprunts en cours.')
            params = (valeurs['titre'], valeurs['auteur'], valeurs['isbn'], annee, valeurs['genre'], stock)
            if livre_id is None:
                conn.execute(
                    'INSERT INTO livres (titre, auteur, isbn, annee, genre, nb_exemplaires) VALUES (?, ?, ?, ?, ?, ?)',
                    params,
                )
            else:
                conn.execute(
                    'UPDATE livres SET titre=?, auteur=?, isbn=?, annee=?, genre=?, nb_exemplaires=? WHERE id=?',
                    (*params, livre_id),
                )
        return redirect(url_for('.livres'))

    @bp.post('/admin/livres/<int:livre_id>/supprimer')
    @acces('admin')
    def supprimer_livre(livre_id):
        with closing(get_db()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            livre = conn.execute(CATALOGUE + ' WHERE livres.id = ? AND livres.actif = 1 GROUP BY livres.id', (livre_id,)).fetchone()
            if livre is None:
                abort(404, description='Livre introuvable.')
            if livre['nb_exemplaires'] != livre['nb_disponibles']:
                abort(409, description='Ce livre a des exemplaires en cours d’emprunt.')
            historique = conn.execute('SELECT 1 FROM emprunts WHERE livre_id = ? LIMIT 1', (livre_id,)).fetchone()
            if historique:
                conn.execute('UPDATE livres SET actif = 0 WHERE id = ?', (livre_id,))
            else:
                conn.execute('DELETE FROM livres WHERE id = ?', (livre_id,))
        return redirect(url_for('.livres'))

    @bp.post('/livres/<int:livre_id>/emprunter')
    @acces('user')
    def emprunter(livre_id):
        utilisateur_id = session['utilisateur_id']
        with closing(get_db()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            livre = conn.execute(CATALOGUE + ' WHERE livres.id = ? AND livres.actif = 1 GROUP BY livres.id', (livre_id,)).fetchone()
            if livre is None:
                abort(404, description='Livre introuvable.')
            if livre['nb_disponibles'] <= 0:
                abort(409, description='Tous les exemplaires de ce livre sont empruntés.')
            nombre = conn.execute(
                'SELECT COUNT(*) FROM emprunts WHERE utilisateur_id = ? AND date_retour IS NULL',
                (utilisateur_id,),
            ).fetchone()[0]
            if nombre >= 3:
                abort(409, description='Vous avez déjà trois emprunts en cours.')
            conn.execute(
                "INSERT INTO emprunts (livre_id, utilisateur_id, date_retour_prevue) VALUES (?, ?, date('now', '+21 days'))",
                (livre_id, utilisateur_id),
            )
        return redirect(url_for('.mes_emprunts'))

    @bp.get('/emprunts')
    @acces('admin', 'user')
    def mes_emprunts():
        with closing(get_db()) as conn:
            lignes = conn.execute(
                """SELECT emprunts.*, livres.titre, utilisateurs.login FROM emprunts
                   JOIN livres ON livres.id = emprunts.livre_id
                   JOIN utilisateurs ON utilisateurs.id = emprunts.utilisateur_id
                   WHERE date_retour IS NULL AND (utilisateur_id = ? OR ? = 'admin')
                   ORDER BY emprunts.date_retour_prevue, emprunts.id""",
                (session['utilisateur_id'], session['role']),
            ).fetchall()
        return render_template('emprunts.html', emprunts=lignes)

    @bp.post('/emprunts/<int:emprunt_id>/rendre')
    @acces('admin', 'user')
    def rendre(emprunt_id):
        with closing(get_db()) as conn, conn:
            resultat = conn.execute(
                """UPDATE emprunts SET date_retour = CURRENT_TIMESTAMP
                   WHERE id = ? AND date_retour IS NULL AND (utilisateur_id = ? OR ? = 'admin')""",
                (emprunt_id, session['utilisateur_id'], session['role']),
            )
            if not resultat.rowcount:
                abort(404, description='Emprunt en cours introuvable.')
        return redirect(url_for('.mes_emprunts'))

    @bp.route('/admin/utilisateurs', methods=['GET', 'POST'])
    @acces('admin')
    def utilisateurs():
        with closing(get_db()) as conn, conn:
            if request.method == 'POST':
                login = request.form.get('login', '').strip()
                password = request.form.get('password', '')
                role = request.form.get('role', 'user')
                if not login or len(password) < 12 or role not in ('admin', 'user'):
                    abort(400, description='Renseignez un identifiant, un rôle et un mot de passe d’au moins 12 caractères.')
                try:
                    conn.execute(
                        'INSERT INTO utilisateurs (login, mot_de_passe_hash, role) VALUES (?, ?, ?)',
                        (login, generate_password_hash(password), role),
                    )
                except sqlite3.IntegrityError:
                    abort(409, description='Cet identifiant existe déjà.')
                return redirect(url_for('.utilisateurs'))
            lignes = conn.execute('SELECT id, login, role FROM utilisateurs WHERE actif = 1 ORDER BY login').fetchall()
        return render_template('utilisateurs.html', utilisateurs=lignes)

    @bp.post('/admin/utilisateurs/<int:utilisateur_id>/supprimer')
    @acces('admin')
    def supprimer_utilisateur(utilisateur_id):
        if utilisateur_id == session['utilisateur_id']:
            abort(409, description='Vous utilisez actuellement ce compte.')
        with closing(get_db()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            compte = conn.execute('SELECT 1 FROM utilisateurs WHERE id = ? AND actif = 1', (utilisateur_id,)).fetchone()
            if compte is None:
                abort(404, description='Compte introuvable.')
            emprunts = conn.execute('SELECT date_retour FROM emprunts WHERE utilisateur_id = ?', (utilisateur_id,)).fetchall()
            if any(emprunt['date_retour'] is None for emprunt in emprunts):
                abort(409, description='Ce compte a des emprunts en cours.')
            if emprunts:
                conn.execute('UPDATE utilisateurs SET actif = 0 WHERE id = ?', (utilisateur_id,))
            else:
                conn.execute('DELETE FROM utilisateurs WHERE id = ?', (utilisateur_id,))
        return redirect(url_for('.utilisateurs'))

    @bp.get('/api/livres')
    def api_livres():
        if not est_authentifie():
            return jsonify(erreur='Authentification requise'), 401
        return jsonify([dict(livre) for livre in chercher_livres(request.args.get('q', '').strip())])

    @bp.get('/api/livres/<int:livre_id>')
    def api_livre(livre_id):
        if not est_authentifie():
            return jsonify(erreur='Authentification requise'), 401
        with closing(get_db()) as conn:
            livre = conn.execute(CATALOGUE + ' WHERE livres.id = ? AND livres.actif = 1 GROUP BY livres.id', (livre_id,)).fetchone()
        if livre is None:
            return jsonify(erreur='Livre introuvable'), 404
        return jsonify(dict(livre))

    return bp
