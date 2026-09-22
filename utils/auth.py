# -*- coding: utf-8 -*-
"""Authentification locale avec hash PBKDF2 (stdlib)."""

import hashlib
import os
import binascii
from datetime import datetime

from utils.database import (
    get_utilisateur,
    creer_utilisateur,
    lister_utilisateurs,
    mettre_a_jour_password,
)


# ==============================================================================
# HASH DE MOT DE PASSE
# ==============================================================================
def _hash_password(password, salt=None):
    """Hash un mot de passe avec PBKDF2-SHA256 + salt aléatoire."""
    if salt is None:
        salt = binascii.hexlify(os.urandom(16)).decode()
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    hash_hex = binascii.hexlify(dk).decode()
    return f"pbkdf2_sha256${iterations}${salt}${hash_hex}"


def verifier_password(password, hash_stocke):
    """Vérifie qu'un mot de passe correspond au hash."""
    try:
        algo, iterations, salt, _ = hash_stocke.split("$")
        if algo != "pbkdf2_sha256":
            return False
        nouveau = _hash_password(password, salt=salt)
        return nouveau == hash_stocke
    except Exception:
        return False


# ==============================================================================
# INSCRIPTION / CONNEXION
# ==============================================================================
def inscrire(username, password, role="user"):
    """Crée un utilisateur. Retourne (succes, message)."""
    if not username or len(username) < 3:
        return False, "Le nom d'utilisateur doit contenir au moins 3 caractères."
    if not password or len(password) < 6:
        return False, "Le mot de passe doit contenir au moins 6 caractères."
    if get_utilisateur(username):
        return False, "Ce nom d'utilisateur existe déjà."

    hash_pwd = _hash_password(password)
    succes = creer_utilisateur(username, hash_pwd, role=role)
    if succes:
        return True, "Utilisateur créé avec succès."
    return False, "Erreur lors de la création."


def connecter(username, password):
    """Vérifie les identifiants. Retourne (succes, user_dict ou message)."""
    user = get_utilisateur(username)
    if not user:
        return False, "Utilisateur inconnu."
    if not verifier_password(password, user["password_hash"]):
        return False, "Mot de passe incorrect."
    return True, {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }


# ==============================================================================
# CHANGEMENT DE MOT DE PASSE
# ==============================================================================
def changer_mot_de_passe(username, ancien_password, nouveau_password):
    """
    Permet à un utilisateur de changer son propre mot de passe.
    Vérifie l'ancien mot de passe avant modification.
    """
    user = get_utilisateur(username)
    if not user:
        return False, "Utilisateur introuvable."
    if not verifier_password(ancien_password, user["password_hash"]):
        return False, "L'ancien mot de passe est incorrect."
    if len(nouveau_password) < 6:
        return False, "Le nouveau mot de passe doit contenir au moins 6 caractères."

    nouveau_hash = _hash_password(nouveau_password)
    mettre_a_jour_password(user["id"], nouveau_hash)
    return True, "Mot de passe modifié avec succès."


def forcer_changement_mot_de_passe(user_id, nouveau_password):
    """
    Permet à un admin de changer le mot de passe d'un autre utilisateur.
    Aucune vérification de l'ancien mot de passe.
    """
    if len(nouveau_password) < 6:
        return False, "Le mot de passe doit contenir au moins 6 caractères."
    nouveau_hash = _hash_password(nouveau_password)
    mettre_a_jour_password(user_id, nouveau_hash)
    return True, "Mot de passe modifié avec succès."


# ==============================================================================
# ADMIN PAR DÉFAUT
# ==============================================================================
def creer_admin_par_defaut():
    """Crée un admin par défaut si aucun utilisateur n'existe."""
    utilisateurs = lister_utilisateurs()
    if not utilisateurs:
        succes, msg = inscrire("admin", "admin123", role="admin")
        if succes:
            return True, "Admin par défaut créé : admin / admin123"
    return False, ""