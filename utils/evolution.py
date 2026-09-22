# -*- coding: utf-8 -*-
"""Module d'analyse de l'évolution entre deux temps de mesure."""

import pandas as pd
import numpy as np


def detecter_colonnes_evolution(df):
    """Détecte les colonnes Lx_T1, Lx_T2, Lx_Statut, Lx_Ecart."""
    t1_cols = sorted([c for c in df.columns if c.endswith("_T1")])
    t2_cols = sorted([c for c in df.columns if c.endswith("_T2")])
    statut_cols = sorted([c for c in df.columns if c.endswith("_Statut")])
    ecart_cols = sorted([c for c in df.columns if c.endswith("_Ecart")])
    return {
        "t1": t1_cols,
        "t2": t2_cols,
        "statut": statut_cols,
        "ecart": ecart_cols,
        "disponible": len(t1_cols) > 0 and len(t2_cols) > 0,
    }


def frequences_par_position(df, cols, temps="T1", valeur_present="Oui"):
    """Retourne le nombre d'individus ayant chaque écart à T1 ou T2."""
    colonnes = cols["t1"] if temps == "T1" else cols["t2"]
    resultats = []
    for c in colonnes:
        position = c.replace("_T1", "").replace("_T2", "")
        n = (df[c] == valeur_present).sum()
        resultats.append({
            "Position": position,
            "Effectif": n,
            "Pourcentage (%)": round(n / len(df) * 100, 1) if len(df) > 0 else 0,
        })
    return pd.DataFrame(resultats).sort_values("Effectif", ascending=False).reset_index(drop=True)


def frequences_statuts(df, cols, valeur_present="Oui", valeur_absent="Non"):
    """Fréquences des écarts résolus, persistants, nouveaux par position."""
    resultats = []
    for c1, c2 in zip(cols["t1"], cols["t2"]):
        position = c1.replace("_T1", "")
        resolus = ((df[c1] == valeur_present) & (df[c2] == valeur_absent)).sum()
        persistants = ((df[c1] == valeur_present) & (df[c2] == valeur_present)).sum()
        nouveaux = ((df[c1] == valeur_absent) & (df[c2] == valeur_present)).sum()
        resultats.append({
            "Position": position,
            "Résolus": resolus,
            "Persistants": persistants,
            "Nouveaux": nouveaux,
        })
    return pd.DataFrame(resultats)