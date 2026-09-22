# -*- coding: utf-8 -*-
"""Tests statistiques."""

import pandas as pd
from scipy import stats


def test_mann_whitney(df, var_quanti, var_groupe):
    """Compare une variable quantitative entre 2 groupes."""
    groupes = df[var_groupe].dropna().unique()
    if len(groupes) != 2:
        return {"erreur": "La variable groupe doit avoir exactement 2 modalités."}
    g1 = df[df[var_groupe] == groupes[0]][var_quanti].dropna()
    g2 = df[df[var_groupe] == groupes[1]][var_quanti].dropna()
    stat, p = stats.mannwhitneyu(g1, g2, alternative="two-sided")
    return {
        "Test": "Mann-Whitney",
        "Groupe 1": f"{groupes[0]} (n={len(g1)})",
        "Groupe 2": f"{groupes[1]} (n={len(g2)})",
        "Statistique U": round(stat, 2),
        "p-value": round(p, 4),
        "Significatif (p<0.05)": "Oui" if p < 0.05 else "Non",
    }


def test_kruskal_wallis(df, var_quanti, var_groupe):
    """Compare une variable quantitative entre 3 groupes ou plus."""
    groupes = [g[var_quanti].dropna() for _, g in df.groupby(var_groupe)]
    groupes = [g for g in groupes if len(g) > 0]
    if len(groupes) < 3:
        return {"erreur": "La variable groupe doit avoir au moins 3 modalités."}
    stat, p = stats.kruskal(*groupes)
    return {
        "Test": "Kruskal-Wallis",
        "Nombre de groupes": len(groupes),
        "Statistique H": round(stat, 2),
        "p-value": round(p, 4),
        "Significatif (p<0.05)": "Oui" if p < 0.05 else "Non",
    }


def test_khi2(df, var1, var2):
    """Test du khi² d'indépendance."""
    tab = pd.crosstab(df[var1], df[var2])
    if tab.size == 0:
        return {"erreur": "Tableau vide."}
    chi2, p, dof, expected = stats.chi2_contingency(tab)
    return {
        "Test": "Khi² d'indépendance",
        "Statistique chi2": round(chi2, 2),
        "Degrés de liberté": dof,
        "p-value": round(p, 4),
        "Significatif (p<0.05)": "Oui" if p < 0.05 else "Non",
    }


def test_fisher(df, var1, var2):
    """Test exact de Fisher (tableaux 2x2)."""
    tab = pd.crosstab(df[var1], df[var2])
    if tab.shape != (2, 2):
        return {"erreur": "Fisher nécessite un tableau 2x2."}
    odds, p = stats.fisher_exact(tab)
    return {
        "Test": "Fisher exact",
        "Odds ratio": round(odds, 2),
        "p-value": round(p, 4),
        "Significatif (p<0.05)": "Oui" if p < 0.05 else "Non",
    }