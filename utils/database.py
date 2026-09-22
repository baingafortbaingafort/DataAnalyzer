# -*- coding: utf-8 -*-
"""Gestion de la base SQLite : utilisateurs, analyses, configurations."""

import sqlite3
import os
from datetime import datetime

DB_PATH = "dataanalyzer.db"


def get_connexion():
    """Retourne une connexion SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Crée les tables si elles n'existent pas."""
    conn = get_connexion()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            sheet_name TEXT,
            nb_lignes INTEGER,
            nb_colonnes INTEGER,
            taux_completude REAL,
            nb_doublons INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ==============================================================================
# UTILISATEURS
# ==============================================================================
def creer_utilisateur(username, password_hash, role="user"):
    conn = get_connexion()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?)",
            (username, password_hash, role, datetime.now().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_utilisateur(username):
    conn = get_connexion()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_utilisateur_par_id(user_id):
    conn = get_connexion()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def lister_utilisateurs():
    conn = get_connexion()
    rows = conn.execute(
        "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def supprimer_utilisateur(user_id):
    conn = get_connexion()
    conn.execute("DELETE FROM analyses WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM configs WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def mettre_a_jour_password(user_id, nouveau_hash):
    """Met à jour le mot de passe d'un utilisateur."""
    conn = get_connexion()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (nouveau_hash, user_id),
    )
    conn.commit()
    conn.close()


# ==============================================================================
# ANALYSES
# ==============================================================================
def enregistrer_analyse(
    user_id, filename, sheet_name, nb_lignes, nb_colonnes,
    taux_completude, nb_doublons, notes="",
):
    conn = get_connexion()
    conn.execute("""
        INSERT INTO analyses (
            user_id, filename, sheet_name, nb_lignes, nb_colonnes,
            taux_completude, nb_doublons, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, filename, sheet_name, nb_lignes, nb_colonnes,
        taux_completude, nb_doublons, notes, datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def lister_analyses(user_id=None, limite=100):
    conn = get_connexion()
    if user_id:
        rows = conn.execute("""
            SELECT a.*, u.username
            FROM analyses a
            JOIN users u ON u.id = a.user_id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
            LIMIT ?
        """, (user_id, limite)).fetchall()
    else:
        rows = conn.execute("""
            SELECT a.*, u.username
            FROM analyses a
            JOIN users u ON u.id = a.user_id
            ORDER BY a.created_at DESC
            LIMIT ?
        """, (limite,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==============================================================================
# CONFIGURATIONS
# ==============================================================================
def sauvegarder_config(user_id, nom, data_json):
    conn = get_connexion()
    conn.execute("""
        INSERT INTO configs (user_id, nom, data_json, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, nom, data_json, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def lister_configs(user_id):
    conn = get_connexion()
    rows = conn.execute("""
        SELECT * FROM configs WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def supprimer_config(config_id):
    conn = get_connexion()
    conn.execute("DELETE FROM configs WHERE id = ?", (config_id,))
    conn.commit()
    conn.close()