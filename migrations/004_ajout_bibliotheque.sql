CREATE TABLE IF NOT EXISTS livres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    isbn TEXT,
    annee INTEGER,
    genre TEXT,
    nb_exemplaires INTEGER NOT NULL CHECK (nb_exemplaires >= 0)
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
