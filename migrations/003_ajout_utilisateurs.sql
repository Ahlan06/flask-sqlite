CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    mot_de_passe_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user'))
);
CREATE TABLE IF NOT EXISTS configuration (
    nom TEXT PRIMARY KEY,
    valeur TEXT NOT NULL
);
INSERT OR IGNORE INTO configuration VALUES ('secret_session', lower(hex(randomblob(32))));
INSERT OR IGNORE INTO utilisateurs (login, mot_de_passe_hash, role) VALUES ('admin', 'scrypt:32768:8:1$pADAt7KNAzE9Rp7G$79d2bc5f9b42caf964e97092659c9e76998169de825caed4a09a482decd748c4a0da454d97ba95a5a643cfd924fb5fd57551aa842e4434bb83516e73efc54245', 'admin');
INSERT OR IGNORE INTO utilisateurs (login, mot_de_passe_hash, role) VALUES ('user', 'scrypt:32768:8:1$hWgALiUqN5r5tgfb$bf92e07969f3bc64b06553e03ce5bd3c27a011b5fc5a191e3521c93bb1736e1a7ee42f746e2f3842de74394df944c954cfb605dc212d25b9fc2b17f8e00f58f8', 'user');
