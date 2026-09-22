# -*- coding: utf-8 -*-
"""Module d'audit qualité des données."""

import pandas as pd
import numpy as np


def rapport_qualite(df):
    """
    Génère un rapport complet de qualité des données.
    Retourne un dict avec plusieurs DataFrames.
    """
    rapport = {}

    # ---------- 1. Vue d'ensemble ----------
    nb_lignes = df.shape[0]
    nb_colonnes = df.shape[1]
    cellules_totales = nb_lignes * nb_colonnes
    cellules_manquantes = int(df.isna().sum().sum())
    taux_completude = (
        round((1 - cellules_manquantes / cellules_totales) * 100, 2)
        if cellules_totales > 0 else 0
    )

    synthese = pd.DataFrame({
        "Indicateur": [
            "Nombre de lignes",
            "Nombre de colonnes",
            "Cellules totales",
            "Cellules manquantes",
            "Taux de complétude (%)",
            "Doublons exacts (lignes)",
            "Colonnes avec valeurs manquantes",
        ],
        "Valeur": [
            nb_lignes,
            nb_colonnes,
            cellules_totales,
            cellules_manquantes,
            taux_completude,
            int(df.duplicated().sum()),
            int((df.isna().sum() > 0).sum()),
        ],
    })
    rapport["synthese"] = synthese

    # ---------- 2. Analyse colonne par colonne ----------
    lignes = []
    for col in df.columns:
        serie = df[col]
        manquants = int(serie.isna().sum())
        taux_manquant = round(manquants / len(df) * 100, 2) if len(df) > 0 else 0
        uniques = int(serie.nunique(dropna=True))
        type_detecte = str(serie.dtype)

        # Détection de valeurs aberrantes pour les numériques
        aberrants = 0
        if pd.api.types.is_numeric_dtype(serie):
            serie_num = pd.to_numeric(serie, errors="coerce").dropna()
            if len(serie_num) > 3:
                q1 = serie_num.quantile(0.25)
                q3 = serie_num.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    borne_basse = q1 - 1.5 * iqr
                    borne_haute = q3 + 1.5 * iqr
                    aberrants = int(
                        ((serie_num < borne_basse) | (serie_num > borne_haute)).sum()
                    )

        lignes.append({
            "Colonne": col,
            "Type": type_detecte,
            "Manquants": manquants,
            "Taux manquant (%)": taux_manquant,
            "Valeurs uniques": uniques,
            "Valeurs aberrantes": aberrants,
            "Statut": "⚠ À vérifier" if taux_manquant > 20 else "✅ OK",
        })

    rapport["colonnes"] = pd.DataFrame(lignes)

    # ---------- 3. Colonnes avec valeurs manquantes ----------
    manquants_df = df.isna().sum().reset_index()
    manquants_df.columns = ["Colonne", "Manquants"]
    manquants_df["Pourcentage (%)"] = (
        manquants_df["Manquants"] / len(df) * 100
    ).round(2) if len(df) > 0 else 0
    manquants_df = manquants_df[manquants_df["Manquants"] > 0]
    manquants_df = manquants_df.sort_values(
        "Manquants", ascending=False
    ).reset_index(drop=True)
    rapport["manquants"] = manquants_df

    # ---------- 4. Doublons ----------
    doublons = df[df.duplicated(keep=False)]
    rapport["doublons"] = doublons

    # ---------- 5. Colonnes constantes ----------
    constantes = [col for col in df.columns if df[col].nunique(dropna=True) <= 1]
    rapport["constantes"] = constantes

    # ---------- 6. Colonnes à très forte cardinalité ----------
    cardinalite = []
    for col in df.columns:
        nunique = df[col].nunique(dropna=True)
        if len(df) > 0 and nunique > 0.8 * len(df) and not pd.api.types.is_numeric_dtype(df[col]):
            cardinalite.append({"Colonne": col, "Valeurs uniques": nunique})
    rapport["cardinalite"] = pd.DataFrame(cardinalite)

    return rapport


def detecter_valeurs_incoherentes(df, colonne, regle):
    """
    Détecte les valeurs qui ne respectent pas une règle.
    regle : fonction lambda appliquée à chaque valeur.
    """
    masque = df[colonne].apply(
        lambda x: not regle(x) if pd.notna(x) else False
    )
    return df[masque]