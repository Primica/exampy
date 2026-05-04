DROP DATABASE IF EXISTS jdr;
CREATE DATABASE jdr;
USE jdr;

CREATE TABLE campagne (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    maitre_du_jeu VARCHAR(255) NOT NULL,
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_campagne_nom_mj (nom, maitre_du_jeu)
);

CREATE TABLE personnage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    classe VARCHAR(100) NOT NULL,
    niveau INT NOT NULL,
    points_de_vie INT NOT NULL,
    id_campagne INT NOT NULL,
    UNIQUE KEY uq_personnage_nom_classe_campagne (nom, classe, id_campagne),
    FOREIGN KEY (id_campagne) REFERENCES campagne(id)
);

CREATE TABLE quete (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titre VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    statut VARCHAR(100) NOT NULL,
    id_campagne INT NOT NULL,
    UNIQUE KEY uq_quete_titre_campagne (titre, id_campagne),
    FOREIGN KEY (id_campagne) REFERENCES campagne(id)
);

CREATE TABLE participation (
    id_personnage INT NOT NULL,
    id_quete INT NOT NULL,
    PRIMARY KEY (id_personnage, id_quete),
    FOREIGN KEY (id_personnage) REFERENCES personnage(id),
    FOREIGN KEY (id_quete) REFERENCES quete(id)
);

