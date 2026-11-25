CREATE TABLE IF NOT EXISTS commandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients (id),
    produit TEXT NOT NULL,
    montant REAL NOT NULL CHECK (montant >= 0),
    date_commande TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS commandes_client_id ON commandes (client_id);
