# -*- coding: utf-8 -*-
"""Script à lancer UNE FOIS pour initialiser la base SQLite."""

from utils.database import init_database
from utils.auth import creer_admin_par_defaut

if __name__ == "__main__":
    print("=" * 60)
    print("INITIALISATION DE LA BASE DataAnalyzer")
    print("=" * 60)

    init_database()
    print("✅ Tables créées (users, analyses, configs).")

    cree, msg = creer_admin_par_defaut()
    if cree:
        print(f"✅ {msg}")
        print("\n⚠️  Pensez à changer le mot de passe admin après la 1re connexion !")
    else:
        print("ℹ️  Des utilisateurs existent déjà, aucun admin par défaut créé.")

    print("\nInitialisation terminée.")