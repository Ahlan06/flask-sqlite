# 📒 Mon carnet de bord

**Nom : MIRA** 

**Prénom : Ahlan** 

**Adresse de mon site :** https://ahlan06.pythonanywhere.com

**Adresse de mon dépôt GitHub :** https://github.com/ahlan06/flask-sqlite

> Modifiez ce fichier directement sur GitHub (icône crayon ✏️) pour répondre aux questions de chaque exercice.
> Écrivez avec vos propres mots : une réponse courte et juste vaut mieux qu'un long copier-coller ! 🙂

---

## 🟢 Exercice 1 — Explorer la base en SQL

1. Expliquez avec vos mots la différence entre une **table**, une **colonne** et une **ligne**.

   > _Ma réponse :_ Une table rassemble les données du même type, ici les clients. Une colonne représente une catégorie d'information, comme `nom` ou `adresse`. Une ligne représente un client précis et contient une valeur pour chacune des colonnes.

2. À quoi sert la clé primaire `id` ? Pourquoi ne pas simplement identifier un client par son nom ?

   > _Ma réponse :_ La clé primaire `id` identifie chaque ligne de manière unique. Plusieurs clients peuvent avoir le même nom ou prénom, et un nom peut changer : il ne permet donc pas un identifiant fiable.

3. Pourquoi votre client ajouté en console est-il apparu sur le site ?

   > _Ma réponse :_ La console SQLite et le site utilisent le même fichier `database.db`. La route `/consultation/` relit cette base à chaque affichage, donc l'insertion effectuée en console est immédiatement visible sans modifier GitHub.

4. Que signifie `NOT NULL` dans `schema.sql` ? Quelle erreur avez-vous obtenue avec `INSERT INTO clients (nom) VALUES ('TEST');` ?

   > _Ma réponse :_ `NOT NULL` signifie que la colonne doit obligatoirement recevoir une valeur. L'insertion de `TEST` échoue car `prenom` et/ou `adresse` sont obligatoires : SQLite renvoie une erreur de contrainte du type `NOT NULL constraint failed`.

### 🧩 Défi

```sql
-- Les 3 derniers clients enregistrés
SELECT * FROM clients ORDER BY id DESC LIMIT 3;

-- Les clients dont le prénom commence par la lettre A
SELECT * FROM clients WHERE prenom LIKE 'A%';

-- Le nombre de clients qui habitent à Paris
SELECT COUNT(*) FROM clients WHERE adresse LIKE '%Paris%';
```

---

## 🟢 Exercice 2 — Afficher les données proprement

1. Décrivez avec vos mots le trajet d'une requête, du navigateur jusqu'à la base de données, puis le retour.

   > _Ma réponse :_ Le navigateur envoie une requête à Flask. La route correspondante interroge SQLite, récupère les lignes, puis Flask les insère dans le template avec Jinja. Le navigateur reçoit et affiche le HTML généré, pas le SQL ni le code Python.

2. Pourquoi faut-il **fermer** la connexion (`conn.close()`) après chaque requête ?

   > _Ma réponse :_ Pour libérer les ressources utilisées par la connexion et éviter de garder inutilement la base ouverte, ce qui pourrait finir par gêner d'autres opérations.

3. Quel est l'avantage d'écrire `row['nom']` plutôt que `row[2]` ? (Pensez à ce qui arriverait si on ajoutait une colonne au milieu de la table.)

   > _Ma réponse :_ Le nom de colonne indique clairement quelle donnée on lit. Si une colonne est ajoutée ou si l'ordre change, `row['nom']` continue de désigner le nom, tandis que `row[2]` pourrait désigner une autre donnée.

4. Pourquoi est-il préférable de trier avec `ORDER BY` dans la requête SQL plutôt qu'en Python ?

   > _Ma réponse :_ SQLite peut trier les données directement avant de les renvoyer. C'est plus efficace pour de grandes tables et évite de refaire le tri côté Python après avoir récupéré toutes les lignes.

---

## 🟢 Exercice 3 — Rechercher un client

1. Quelle est la différence entre `WHERE nom = 'DUPONT'` et `WHERE nom LIKE '%DUP%'` ?

   > _Ma réponse :_ `=` cherche le nom exact. `LIKE '%DUP%'` exige seulement que le nom contienne DUP, où que ce soit.

2. Expliquez avec vos mots ce qu'est une **injection SQL**. Qu'est-ce qu'un pirate pourrait faire de pire qu'afficher tous les clients ?

   > _Ma réponse :_ Une injection SQL se produit quand une saisie est interprétée comme une partie de la requête. Selon les droits de l’application, cela peut exposer des informations privées, modifier ou effacer des données.

3. Pourquoi la version avec `?` est-elle protégée contre l'injection ?

   > _Ma réponse :_ SQLite reçoit la requête et ses paramètres séparément. La saisie est donc traitée comme une valeur.

4. Pour la recherche, on a utilisé `method="get"`. Quel avantage pour l'utilisateur ? (Indice : favoris, partage de lien.)

   > _Ma réponse :_ La recherche et le tri apparaissent dans l’URL. On peut mettre le résultat en favori ou partager le lien.

### 🧩 Défi

> Le menu propose trois tris. Python associe chaque choix à un ordre SQL prédéfini et utilise le tri par nom si le choix est inconnu.

---

## 🔵 Exercice 4 — Enregistrer un client

1. Quelles étaient les deux anomalies du formulaire d'origine, et d'où venaient-elles ?

   > _Ma réponse :_ L’adresse valait toujours `ICI` parce que le formulaire ne la demandait pas et que le code imposait cette valeur. La date était incorrecte parce que l’INSERT imposait la valeur `1002938`.

2. Pourquoi la validation côté **navigateur** (`required`) ne suffit-elle pas ? Pourquoi la garder quand même ?

   > _Ma réponse :_ Le navigateur peut être contourné, par exemple en envoyant le formulaire directement au serveur. `required` reste utile pour signaler tout de suite un champ oublié.

3. À quoi sert `conn.commit()` ? Que se passe-t-il sans lui ?

   > _Ma réponse :_ `conn.commit()` valide la transaction. Si on ferme la connexion sans valider, SQLite annule l’insertion. Ici, le bloc `with conn` valide automatiquement si tout réussit.

4. Pourquoi redirige-t-on vers `/consultation/` après l'enregistrement, au lieu d'afficher directement une page ? (Indice : essayez d'appuyer sur F5 après l'envoi.)

   > _Ma réponse :_ La redirection transforme l’affichage suivant en requête GET. Actualiser la page recharge la liste ou la fiche sans renvoyer le formulaire.

### 🧩 Défi

> Après l’insertion, je récupère `cursor.lastrowid` pour rediriger vers la fiche du nouveau client.

---

## 🔵 Exercice 5 — Modifier et supprimer

1. Que signifie CRUD ? Donnez la requête SQL correspondant à chaque lettre.

   > _Ma réponse :_ CRUD signifie créer (`INSERT`), lire (`SELECT`), modifier (`UPDATE`) et supprimer (`DELETE`).

2. Que se passe-t-il si l'on oublie le `WHERE` dans un `UPDATE` ou un `DELETE` ? À quoi servent `BEGIN` et `ROLLBACK` ?

   > _Ma réponse :_ Sans `WHERE`, la requête s’applique à toutes les lignes de la table. `BEGIN` ouvre une transaction et `ROLLBACK` annule ses changements avant validation.

3. Pourquoi ne faut-il **jamais** supprimer des données avec une requête GET (un simple lien) ? (Indice : les moteurs de recherche et certains navigateurs « visitent » les liens à l'avance.)

   > _Ma réponse :_ Un lien GET peut être ouvert automatiquement par un navigateur ou un moteur de recherche. Un formulaire POST envoie une demande de suppression lors de sa soumission.

4. Une fois un `id` supprimé, pourquoi est-il préférable qu'il ne soit jamais réattribué à un autre client ?

   > _Ma réponse :_ Des liens ou des données liées peuvent encore faire référence à l’ancien identifiant. Le réutiliser pointerait alors vers un autre client.

### 🧩 Défi

> La suppression logique permet de restaurer un client, de garder son historique et de conserver ses liens avec d’autres données. Les listes courantes filtrent les clients actifs.

---

## 🟣 Exercice 6 — Faire évoluer la base

1. Quelle est la différence entre le **schéma** d'une base et ses **données** ? Où se trouve chacun ?

   > _Ma réponse :_ Le schéma décrit les tables, les colonnes et leurs contraintes. Il est documenté dans `schema.sql` et appliqué dans `database.db`, qui contient aussi les lignes des clients.

2. Pourquoi ne faut-il pas relancer `create_db.py` sur une application en production ?

   > _Ma réponse :_ `create_db.py` exécute le script de création qui supprime d’abord la table. Les données saisies en production seraient perdues.

3. Pourquoi est-il important de garder `schema.sql` à jour, même si on a modifié la base avec `ALTER TABLE` ?

   > _Ma réponse :_ Une nouvelle installation doit créer une base avec les mêmes colonnes que le serveur existant, où la migration a déjà été appliquée.

4. Pour ajouter **une** information, combien de fichiers avez-vous dû modifier ? Lesquels ?

   > _Ma réponse :_ Cinq fichiers servent à la modification : `schema.sql`, `flask_app.py`, `formulaire.html`, `modifier_client.html` et `read_data.html`. La migration ajoute un sixième fichier.

### 🧩 Défi

> Le fichier `migrations/001_ajout_telephone.sql` conserve la commande exacte à appliquer. Les numéros indiquent l’ordre des changements pour faire évoluer la base de la même façon sur chaque serveur.

---

## 🟣 Exercice 7 — Relier deux tables

1. Qu'est-ce qu'une **clé étrangère** ? Dans quelle table se trouve-t-elle ici, et pourquoi pas dans l'autre ?

   > _Ma réponse :_ Une clé étrangère pointe vers une ligne d’une autre table. Ici, chaque commande a un seul client, donc `commandes.client_id` pointe vers `clients.id`.

2. Pourquoi est-ce une mauvaise idée de créer des colonnes `commande1`, `commande2`… dans la table `clients` ?

   > _Ma réponse :_ Un client peut avoir autant de commandes que nécessaire. Une ligne par commande évite d’ajouter des colonnes et facilite les recherches et les totaux.

3. À quoi sert un `JOIN` ? Et un `GROUP BY` ?

   > _Ma réponse :_ `JOIN` associe les lignes de plusieurs tables. `GROUP BY` rassemble les lignes d’un même client pour calculer son nombre de commandes et le montant total.

4. Pour la bibliothèque, quelles tables imaginez-vous ? Lesquelles contiendront des clés étrangères ?

   > _Ma réponse :_ Je prévois les tables `livres`, `utilisateurs` et `emprunts`. La table `emprunts` contient les clés étrangères du livre et de l’utilisateur.

### 🧩 Défi

> La fiche permet d’ajouter une commande. Si le client a des commandes, la suppression affiche leur nombre et un lien vers sa fiche.

---

## 🔴 Exercice 8 — Contrôle d'accès

1. Quelle est la différence entre **authentification** et **autorisation** ?

   > _Ma réponse :_ L’authentification vérifie mon identité. L’autorisation vérifie les actions que mon rôle permet.

2. Où est stockée la session ? Comment le serveur sait-il qui vous êtes à chaque nouvelle requête ?

   > _Ma réponse :_ Flask stocke la session dans un cookie signé. Le navigateur le renvoie et Flask vérifie la signature avant de lire l’identifiant et le rôle.

3. Pourquoi masquer un bouton dans le HTML ne suffit-il pas à protéger une action ?

   > _Ma réponse :_ Une personne peut ouvrir l’URL directement. La route doit vérifier le rôle avant d’exécuter l’action.

4. Que signifient les codes `302` et `403` ? Dans quel cas votre application renvoie-t-elle chacun d'eux ?

   > _Ma réponse :_ Le code 302 redirige un visiteur vers la connexion. Le code 403 refuse une action à un utilisateur connecté dont le rôle ne suffit pas.

5. Le mot de passe `password` est écrit en clair dans `flask_app.py`, sur un dépôt **public**. Quel est le risque ? Quelle solution avez-vous déjà rencontrée dans cet atelier pour cacher une information sensible ?

   > _Ma réponse :_ Un mot de passe écrit en clair dans GitHub est lisible par les visiteurs. Les secrets GitHub peuvent protéger les informations de déploiement. Les mots de passe des comptes sont stockés sous forme de hachage.

### 🧩 Défi

> Les comptes et leurs rôles sont dans la table `utilisateurs`. Werkzeug vérifie le mot de passe à partir du hachage.

---

## 🔴 Exercice 9 — Créer une API

1. Quelle est la différence entre une page HTML et une réponse JSON ? À qui chacune est-elle destinée ?

   > _Ma réponse :_ Le HTML est destiné à l’affichage dans le navigateur. Le JSON représente des données structurées qu’un programme peut lire.

2. Que signifient les codes `200`, `201`, `400`, `401` et `404` renvoyés par votre API ?

   > _Ma réponse :_ 200 indique une lecture réussie, 201 une création, 400 une requête invalide, 401 une authentification requise et 404 une ressource introuvable.

3. Pourquoi une API renvoie-t-elle une erreur JSON plutôt qu'une redirection vers la page de connexion ?

   > _Ma réponse :_ Le programme qui appelle une API doit pouvoir lire l’erreur et décider de la suite à partir du code et du JSON.

4. Citez une application de votre téléphone qui, selon vous, utilise une API. Quelles données échange-t-elle ?

   > _Ma réponse :_ Une application météo envoie un lieu et reçoit des données telles que les températures et les prévisions.

### 🧩 Défi

> L’API permet la suppression par un administrateur et le filtrage avec `q`. La page de recherche appelle l’API sans recharger la page.

---

## 📚 Projet bibliothèque

1. Pourquoi ne supprime-t-on pas un emprunt quand le livre est rendu ?

   > _Ma réponse :_ 

2. Pourquoi calculer la disponibilité d'un livre plutôt que de la stocker dans une colonne ?

   > _Ma réponse :_ 

3. Quelle a été la plus grande difficulté rencontrée pendant le projet, et comment l'avez-vous surmontée ?

   > _Ma réponse :_ 

4. Quelles fonctionnalités n'avez-vous pas eu le temps de réaliser ? Comment vous y prendriez-vous ?

   > _Ma réponse :_ 

---

## 🏁 Pour conclure

En quelques phrases, expliquez à un ami ce qui se passe entre le moment où il clique sur « Enregistrer » dans un formulaire et celui où l'information s'affiche dans une liste :

> _Ma réponse :_ 
