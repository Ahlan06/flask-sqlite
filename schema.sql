DROP TABLE IF EXISTS commandes;
DROP TABLE IF EXISTS clients;
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    adresse TEXT NOT NULL,
    telephone TEXT
);

CREATE TABLE IF NOT EXISTS commandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients (id),
    produit TEXT NOT NULL,
    montant REAL NOT NULL CHECK (montant >= 0),
    date_commande TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS commandes_client_id ON commandes (client_id);

CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    mot_de_passe_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
    actif INTEGER NOT NULL DEFAULT 1 CHECK (actif IN (0, 1))
);
CREATE TABLE IF NOT EXISTS configuration (
    nom TEXT PRIMARY KEY,
    valeur TEXT NOT NULL
);
INSERT OR IGNORE INTO configuration VALUES ('secret_session', lower(hex(randomblob(32))));
BEGIN IMMEDIATE;
INSERT OR IGNORE INTO utilisateurs (login, mot_de_passe_hash, role) SELECT 'admin', 'scrypt:32768:8:1$pADAt7KNAzE9Rp7G$79d2bc5f9b42caf964e97092659c9e76998169de825caed4a09a482decd748c4a0da454d97ba95a5a643cfd924fb5fd57551aa842e4434bb83516e73efc54245', 'admin' WHERE NOT EXISTS (SELECT 1 FROM configuration WHERE nom = 'comptes_initialises');
INSERT OR IGNORE INTO utilisateurs (login, mot_de_passe_hash, role) SELECT 'user', 'scrypt:32768:8:1$hWgALiUqN5r5tgfb$bf92e07969f3bc64b06553e03ce5bd3c27a011b5fc5a191e3521c93bb1736e1a7ee42f746e2f3842de74394df944c954cfb605dc212d25b9fc2b17f8e00f58f8', 'user' WHERE NOT EXISTS (SELECT 1 FROM configuration WHERE nom = 'comptes_initialises');
INSERT OR IGNORE INTO utilisateurs (login, mot_de_passe_hash, role) SELECT 'user2', 'scrypt:32768:8:1$ulg6Bxrf5E7dDhk5$5e04c635698947db387fbb4ca6e4fb7864079b30e97ee3002dd332c1eda014b0f38d7196cde2a86af7aa2b0703671eee6efece32051073addf2123b17e460d9b', 'user' WHERE NOT EXISTS (SELECT 1 FROM configuration WHERE nom = 'comptes_initialises');
INSERT OR IGNORE INTO configuration VALUES ('comptes_initialises', '1');
COMMIT;

CREATE TABLE IF NOT EXISTS livres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    isbn TEXT,
    annee INTEGER,
    genre TEXT,
    nb_exemplaires INTEGER NOT NULL CHECK (nb_exemplaires >= 0),
    actif INTEGER NOT NULL DEFAULT 1 CHECK (actif IN (0, 1))
);
CREATE TABLE IF NOT EXISTS emprunts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livre_id INTEGER NOT NULL REFERENCES livres (id),
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs (id),
    date_emprunt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_retour_prevue DATE NOT NULL,
    date_retour TIMESTAMP
);
CREATE INDEX IF NOT EXISTS emprunts_livre ON emprunts (livre_id, date_retour);
CREATE INDEX IF NOT EXISTS emprunts_utilisateur ON emprunts (utilisateur_id, date_retour);

BEGIN IMMEDIATE;
INSERT INTO livres (titre, auteur, nb_exemplaires)
SELECT titre, auteur, exemplaires FROM (
    SELECT 'Le Petit Prince' AS titre, 'Antoine de Saint-Exupéry' AS auteur, 2 AS exemplaires
    UNION ALL SELECT 'Les Misérables', 'Victor Hugo', 3
    UNION ALL SELECT 'L’Étranger', 'Albert Camus', 2
    UNION ALL SELECT 'Germinal', 'Émile Zola', 2
    UNION ALL SELECT 'Le Comte de Monte-Cristo', 'Alexandre Dumas', 1
    UNION ALL SELECT 'Madame Bovary', 'Gustave Flaubert', 2
    UNION ALL SELECT 'L’Odyssée', 'Homère', 1
    UNION ALL SELECT 'Orgueil et Préjugés', 'Jane Austen', 2
    UNION ALL SELECT 'Frankenstein', 'Mary Shelley', 1
    UNION ALL SELECT 'Les Fleurs du mal', 'Charles Baudelaire', 2
)
WHERE NOT EXISTS (SELECT 1 FROM configuration WHERE nom = 'catalogue_initialise');
INSERT OR IGNORE INTO configuration VALUES ('catalogue_initialise', '1');
COMMIT;
