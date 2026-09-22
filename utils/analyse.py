# -*- coding: utf-8 -*-
"""Fonctions d'analyse descriptive."""

import pandas as pd
import numpy as np


def stats_descriptives(serie):
    """Retourne moyenne, écart-type, médiane, Q1, Q3, min, max."""
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    if len(serie) == 0:
        return {}
    return {
        "Effectif (n)": len(serie),
        "Moyenne": round(serie.mean(), 2),
        "Écart-type": round(serie.std(), 2),
        "Médiane": round(serie.median(), 2),
        "Q1": round(serie.quantile(0.25), 2),
        "Q3": round(serie.quantile(0.75), 2),
        "Minimum": round(serie.min(), 2),
        "Maximum": round(serie.max(), 2),
    }


def tableau_frequences(serie, pourcentage=True):
    """Retourne un tableau d'effectifs et pourcentages."""
    tab = serie.value_counts(dropna=False).reset_index()
    tab.columns = ["Modalité", "Effectif"]
    if pourcentage:
        tab["Pourcentage (%)"] = (tab["Effectif"] / tab["Effectif"].sum() * 100).round(1)
    return tab


def tableau_croise(df, var1, var2, pourcentage="ligne"):
    """Tableau croisé avec pourcentages."""
    tab = pd.crosstab(df[var1], df[var2], margins=True, margins_name="Total")
    if pourcentage == "ligne":
        tab_pct = pd.crosstab(df[var1], df[var2], normalize="index") * 100
    elif pourcentage == "colonne":
        tab_pct = pd.crosstab(df[var1], df[var2], normalize="columns") * 100
    else:
        tab_pct = pd.crosstab(df[var1], df[var2], normalize="all") * 100
    return tab, tab_pct.round(1)


def detecter_types_colonnes(df):
    """Détecte les colonnes numériques, catégorielles et dates."""
    numeriques, categorielles, dates = [], [], []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeriques.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            dates.append(col)
        else:
            categorielles.append(col)
    return {
        "numeriques": numeriques,
        "categorielles": categorielles,
        "dates": dates,
    }