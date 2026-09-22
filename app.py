# -*- coding: utf-8 -*-
"""
DataAnalyzer V6.1
Analyse + Audit + Évolution + Historique + Auth + MDP
Thème sombre forcé nativement via config.toml
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from datetime import datetime

from utils.analyse import (
    stats_descriptives,
    tableau_frequences,
    tableau_croise,
    detecter_types_colonnes,
)
from utils.stats import (
    test_mann_whitney,
    test_kruskal_wallis,
    test_khi2,
    test_fisher,
)
from utils.evolution import (
    detecter_colonnes_evolution,
    frequences_par_position,
    frequences_statuts,
)
from utils.qualite import rapport_qualite
from utils.export import (
    exporter_word_complet,
    exporter_excel_enrichi,
)
from utils.auth import (
    connecter,
    inscrire,
    creer_admin_par_defaut,
    changer_mot_de_passe,
    forcer_changement_mot_de_passe,
)
from utils.database import (
    init_database,
    enregistrer_analyse,
    lister_analyses,
    lister_utilisateurs,
    supprimer_utilisateur,
    sauvegarder_config,
    lister_configs,
    supprimer_config,
)

# ==============================================================================
# CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="DataAnalyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("exports", exist_ok=True)

init_database()
creer_admin_par_defaut()

# ==============================================================================
# SESSION STATE
# ==============================================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "df" not in st.session_state:
    st.session_state.df = None
if "df_filename" not in st.session_state:
    st.session_state.df_filename = None
if "df_sheet" not in st.session_state:
    st.session_state.df_sheet = None


# ==============================================================================
# PAGE DE LOGIN / INSCRIPTION
# ==============================================================================
def page_login():
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0;">
            <h1>📊 DataAnalyzer</h1>
            <p style="color:#999;">Plateforme d'analyse de données Excel</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        onglet_login, onglet_inscription = st.tabs(["🔐 Connexion", "📝 Inscription"])

        with onglet_login:
            with st.form("form_login"):
                username = st.text_input("Nom d'utilisateur")
                password = st.text_input("Mot de passe", type="password")
                submit = st.form_submit_button("Se connecter", use_container_width=True)

                if submit:
                    succes, resultat = connecter(username, password)
                    if succes:
                        st.session_state.user = resultat
                        st.success(f"Bienvenue, {resultat['username']} !")
                        st.rerun()
                    else:
                        st.error(resultat)

        with onglet_inscription:
            with st.form("form_inscription"):
                new_username = st.text_input("Choisissez un nom d'utilisateur")
                new_password = st.text_input(
                    "Choisissez un mot de passe (min. 6 caractères)",
                    type="password",
                )
                new_password2 = st.text_input(
                    "Confirmez le mot de passe", type="password"
                )
                submit2 = st.form_submit_button("Créer le compte", use_container_width=True)

                if submit2:
                    if new_password != new_password2:
                        st.error("Les deux mots de passe ne correspondent pas.")
                    else:
                        succes, msg = inscrire(new_username, new_password)
                        if succes:
                            st.success(msg + " Vous pouvez maintenant vous connecter.")
                        else:
                            st.error(msg)


# ==============================================================================
# HEADER UTILISATEUR CONNECTÉ
# ==============================================================================
def header_utilisateur():
    user = st.session_state.user
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f"### 📊 DataAnalyzer — Connecté : **{user['username']}** "
            f"(`{user['role']}`)"
        )
    with c2:
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.user = None
            st.session_state.df = None
            st.rerun()

    with st.expander("🔑 Changer mon mot de passe"):
        with st.form("form_change_pwd"):
            ancien = st.text_input("Ancien mot de passe", type="password")
            nouveau = st.text_input("Nouveau mot de passe (min. 6 caractères)", type="password")
            confirme = st.text_input("Confirmer le nouveau mot de passe", type="password")
            submit_pwd = st.form_submit_button("Valider le changement")

            if submit_pwd:
                if nouveau != confirme:
                    st.error("Les deux mots de passe ne correspondent pas.")
                elif not ancien or not nouveau:
                    st.error("Veuillez remplir tous les champs.")
                else:
                    succes, msg = changer_mot_de_passe(
                        user["username"], ancien, nouveau,
                    )
                    if succes:
                        st.success(msg)
                    else:
                        st.error(msg)

    st.markdown("---")


# ==============================================================================
# BARRE LATÉRALE
# ==============================================================================
def barre_laterale():
    st.sidebar.header("1️⃣ Import des données")
    fichier = st.sidebar.file_uploader("Fichier Excel", type=["xlsx", "xls"])

    if fichier is not None:
        try:
            excel_file = pd.ExcelFile(fichier)
            feuille = st.sidebar.selectbox("Feuille", excel_file.sheet_names)
            df = pd.read_excel(fichier, sheet_name=feuille)

            st.session_state.df = df
            st.session_state.df_filename = fichier.name
            st.session_state.df_sheet = feuille

            st.sidebar.success(f"✅ {df.shape[0]} lignes × {df.shape[1]} colonnes")

            if st.sidebar.button("💾 Enregistrer cette analyse", use_container_width=True):
                rapport = rapport_qualite(df)
                enregistrer_analyse(
                    user_id=st.session_state.user["id"],
                    filename=fichier.name,
                    sheet_name=feuille,
                    nb_lignes=df.shape[0],
                    nb_colonnes=df.shape[1],
                    taux_completude=float(rapport["synthese"].iloc[4]["Valeur"]),
                    nb_doublons=int(df.duplicated().sum()),
                    notes="Analyse importée",
                )
                st.sidebar.success("Analyse enregistrée dans l'historique !")
        except Exception as e:
            st.sidebar.error(f"Erreur : {e}")

    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ À propos")
    st.sidebar.caption("DataAnalyzer v6.1")
    st.sidebar.caption("Python + Streamlit + SQLite")
    st.sidebar.caption("Thème sombre natif")


# ==============================================================================
# PAGE PRINCIPALE — ONGLETS
# ==============================================================================
def page_principale():
    header_utilisateur()
    barre_laterale()

    df = st.session_state.df
    if df is None:
        st.info("👈 Importez un fichier Excel pour commencer.")
        return

    types = detecter_types_colonnes(df)

    onglets = [
        "📋 Aperçu",
        "🔍 Audit Qualité",
        "📈 Descriptif",
        "📊 Fréquences",
        "🔀 Croisés",
        "🧪 Tests",
        "🔬 Évolution",
        "📚 Historique",
    ]
    if st.session_state.user["role"] == "admin":
        onglets.append("👥 Utilisateurs")

    tabs = st.tabs(onglets)

    # ---------------- 0. APERÇU ----------------
    with tabs[0]:
        st.header("Aperçu des données")
        st.caption(
            f"Fichier : **{st.session_state.df_filename}** — "
            f"Feuille : **{st.session_state.df_sheet}**"
        )
        st.dataframe(df.head(50), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Lignes", df.shape[0])
        c2.metric("Colonnes", df.shape[1])
        c3.metric("Valeurs manquantes", int(df.isna().sum().sum()))

        with st.expander("Types de colonnes détectés"):
            st.write(f"**Numériques** ({len(types['numeriques'])}) :", types["numeriques"])
            st.write(f"**Catégorielles** ({len(types['categorielles'])}) :", types["categorielles"])
            st.write(f"**Dates** ({len(types['dates'])}) :", types["dates"])

    # ---------------- 1. AUDIT QUALITÉ ----------------
    with tabs[1]:
        st.header("🔍 Audit qualité des données")
        st.markdown("Vérification automatique de la propreté de votre base avant analyse.")

        rapport = rapport_qualite(df)

        st.subheader("Synthèse générale")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Lignes", df.shape[0])
        col2.metric("Colonnes", df.shape[1])
        taux_complet = round(
            (1 - df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100, 1
        ) if df.shape[0] * df.shape[1] > 0 else 0
        col3.metric("Complétude", f"{taux_complet} %")
        col4.metric("Doublons", int(df.duplicated().sum()))

        st.dataframe(rapport["synthese"], use_container_width=True, hide_index=True)

        st.subheader("Diagnostic")
        taux_manquant_global = (
            df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100
        ) if df.shape[0] * df.shape[1] > 0 else 0
        doublons_total = int(df.duplicated().sum())

        if taux_manquant_global < 5 and doublons_total == 0:
            st.success("✅ Base de bonne qualité. Analyse possible sans réserve.")
        elif taux_manquant_global < 20:
            st.warning(
                f"⚠️ Base globalement exploitable, mais "
                f"{round(taux_manquant_global, 1)} % de valeurs manquantes et "
                f"{doublons_total} doublon(s) à examiner."
            )
        else:
            st.error(
                f"❌ Base à nettoyer en priorité : "
                f"{round(taux_manquant_global, 1)} % de valeurs manquantes."
            )

        st.subheader("Analyse colonne par colonne")
        st.dataframe(rapport["colonnes"], use_container_width=True, hide_index=True)

        if not rapport["manquants"].empty:
            st.subheader("Valeurs manquantes par colonne")
            st.dataframe(rapport["manquants"], use_container_width=True, hide_index=True)
            fig_manquants = px.bar(
                rapport["manquants"].head(20),
                x="Manquants", y="Colonne", orientation="h",
                title="Top 20 des colonnes avec valeurs manquantes",
                color="Pourcentage (%)",
                color_continuous_scale="Reds",
            )
            fig_manquants.update_layout(
                yaxis=dict(autorange="reversed"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
            )
            st.plotly_chart(fig_manquants, use_container_width=True)
        else:
            st.success("✅ Aucune valeur manquante détectée.")

        st.subheader("Doublons")
        if not rapport["doublons"].empty:
            st.warning(f"{len(rapport['doublons'])} lignes dupliquées détectées.")
            st.dataframe(rapport["doublons"].head(50), use_container_width=True)
        else:
            st.success("✅ Aucun doublon détecté.")

        if rapport["constantes"]:
            st.subheader("Colonnes constantes (à supprimer)")
            for col in rapport["constantes"]:
                st.write(f"- `{col}`")

        if not rapport["cardinalite"].empty:
            st.subheader("Colonnes à très forte cardinalité")
            st.dataframe(rapport["cardinalite"], use_container_width=True, hide_index=True)

        st.subheader("📄 Export du rapport qualité")
        if st.button("Générer le rapport qualité Excel"):
            try:
                feuilles = {
                    "Synthèse": rapport["synthese"],
                    "Analyse_colonnes": rapport["colonnes"],
                }
                if not rapport["manquants"].empty:
                    feuilles["Manquants"] = rapport["manquants"]
                if not rapport["doublons"].empty:
                    feuilles["Doublons"] = rapport["doublons"]
                chemin = "exports/rapport_qualite.xlsx"
                exporter_excel_enrichi(feuilles, chemin)
                with open(chemin, "rb") as f:
                    st.download_button(
                        "⬇️ Télécharger le rapport Excel",
                        f,
                        file_name="rapport_qualite.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                st.success("Rapport généré !")
            except Exception as e:
                st.error(f"Erreur : {e}")

    # ---------------- 2. DESCRIPTIF ----------------
    with tabs[2]:
        st.header("Statistiques descriptives")
        if not types["numeriques"]:
            st.warning("Aucune colonne numérique détectée.")
        else:
            variables = st.multiselect(
                "Variables à analyser", types["numeriques"],
                default=types["numeriques"][:5],
            )
            if variables:
                resultats = []
                for var in variables:
                    s = stats_descriptives(df[var])
                    s["Variable"] = var
                    resultats.append(s)
                tableau = pd.DataFrame(resultats).set_index("Variable")
                st.dataframe(tableau, use_container_width=True)

                var_graph = st.selectbox("Variable à visualiser", variables)
                fig = px.histogram(
                    df, x=var_graph, nbins=20,
                    title=f"Distribution de {var_graph}",
                    color_discrete_sequence=["#4A90D9"],
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#FAFAFA"),
                )
                st.plotly_chart(fig, use_container_width=True)

    # ---------------- 3. FRÉQUENCES ----------------
    with tabs[3]:
        st.header("Tableaux de fréquences")
        if not types["categorielles"]:
            st.warning("Aucune colonne catégorielle détectée.")
        else:
            var_cat = st.selectbox("Variable catégorielle", types["categorielles"])
            tab = tableau_frequences(df[var_cat])
            st.dataframe(tab, use_container_width=True)
            fig = px.bar(
                tab, x="Modalité", y="Effectif",
                title=f"Répartition de {var_cat}",
                color_discrete_sequence=["#4A90D9"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ---------------- 4. CROISÉS ----------------
    with tabs[4]:
        st.header("Tableaux croisés")
        if len(types["categorielles"]) < 2:
            st.warning("Il faut au moins 2 colonnes catégorielles.")
        else:
            c1, c2 = st.columns(2)
            var1 = c1.selectbox("Variable 1 (lignes)", types["categorielles"])
            var2 = c2.selectbox("Variable 2 (colonnes)", types["categorielles"])
            if var1 != var2:
                tab, tab_pct = tableau_croise(df, var1, var2)
                st.subheader("Effectifs")
                st.dataframe(tab, use_container_width=True)
                st.subheader("Pourcentages en ligne (%)")
                st.dataframe(tab_pct, use_container_width=True)
                fig = px.imshow(
                    tab_pct.values, x=tab_pct.columns, y=tab_pct.index,
                    text_auto=True, aspect="auto",
                    color_continuous_scale="Blues",
                    title=f"{var1} × {var2}",
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#FAFAFA"),
                )
                st.plotly_chart(fig, use_container_width=True)

    # ---------------- 5. TESTS ----------------
    with tabs[5]:
        st.header("Tests statistiques")
        type_test = st.selectbox(
            "Test à réaliser",
            ["Mann-Whitney", "Kruskal-Wallis", "Khi²", "Fisher exact"],
        )
        if type_test == "Mann-Whitney":
            vq = st.selectbox("Variable quantitative", types["numeriques"])
            vg = st.selectbox("Variable de groupe (2 modalités)", types["categorielles"])
            if st.button("Lancer"):
                st.json(test_mann_whitney(df, vq, vg))
        elif type_test == "Kruskal-Wallis":
            vq = st.selectbox("Variable quantitative", types["numeriques"])
            vg = st.selectbox("Variable de groupe (3+ modalités)", types["categorielles"])
            if st.button("Lancer"):
                st.json(test_kruskal_wallis(df, vq, vg))
        elif type_test == "Khi²":
            v1 = st.selectbox("Variable 1", types["categorielles"])
            v2 = st.selectbox("Variable 2", types["categorielles"])
            if st.button("Lancer"):
                st.json(test_khi2(df, v1, v2))
        elif type_test == "Fisher exact":
            v1 = st.selectbox("Variable 1", types["categorielles"])
            v2 = st.selectbox("Variable 2", types["categorielles"])
            if st.button("Lancer"):
                st.json(test_fisher(df, v1, v2))

    # ---------------- 6. ÉVOLUTION ----------------
    with tabs[6]:
        st.header("🔬 Module d'évolution")
        st.markdown(
            "Comparez **deux temps de mesure** (avant/après). "
            "Détection automatique des colonnes `_T1` / `_T2` ou sélection manuelle."
        )

        cols_evol = detecter_colonnes_evolution(df)

        mode = st.radio(
            "Mode de détection",
            [
                "Automatique (colonnes _T1 / _T2)",
                "Manuel (je choisis les colonnes)",
            ],
            horizontal=True,
        )

        if mode.startswith("Automatique"):
            if not cols_evol["disponible"]:
                st.error(
                    "Aucune colonne terminant par `_T1` et `_T2` n'a été détectée. "
                    "Utilisez le mode manuel."
                )
                st.stop()
            cols = cols_evol
            st.success(f"{len(cols['t1'])} paires de colonnes détectées.")
        else:
            toutes = list(df.columns)
            st.info(
                "Sélectionnez les colonnes dans le même ordre : "
                "la 1re de T1 correspond à la 1re de T2, etc."
            )
            c1, c2 = st.columns(2)
            t1_manuel = c1.multiselect("Colonnes T1 (avant)", toutes)
            t2_manuel = c2.multiselect("Colonnes T2 (après)", toutes)
            if len(t1_manuel) == 0 or len(t1_manuel) != len(t2_manuel):
                st.warning("Sélectionnez le même nombre de colonnes en T1 et T2.")
                st.stop()
            cols = {"t1": t1_manuel, "t2": t2_manuel,
                    "statut": [], "ecart": [], "disponible": True}

        st.markdown("---")
        st.subheader("Configuration des valeurs")
        c1, c2 = st.columns(2)
        valeur_present = c1.text_input("Valeur = présent / positif", value="Oui")
        valeur_absent = c2.text_input("Valeur = absent / négatif", value="Non")

        df_temp = df.copy()
        df_temp["ET1"] = (df_temp[cols["t1"]] == valeur_present).sum(axis=1)
        df_temp["ET2"] = (df_temp[cols["t2"]] == valeur_present).sum(axis=1)

        resolus = 0
        persistants = 0
        nouveaux = 0
        for c1_, c2_ in zip(cols["t1"], cols["t2"]):
            resolus += ((df_temp[c1_] == valeur_present) & (df_temp[c2_] == valeur_absent)).astype(int)
            persistants += ((df_temp[c1_] == valeur_present) & (df_temp[c2_] == valeur_present)).astype(int)
            nouveaux += ((df_temp[c1_] == valeur_absent) & (df_temp[c2_] == valeur_present)).astype(int)

        df_temp["Resolus"] = resolus
        df_temp["Persistants"] = persistants
        df_temp["Nouveaux"] = nouveaux
        df_temp["Variation_Nette"] = df_temp["ET1"] - df_temp["ET2"]
        df_temp["Taux_Resolution"] = df_temp.apply(
            lambda r: round(r["Resolus"] / r["ET1"] * 100, 2) if r["ET1"] > 0 else 0,
            axis=1,
        )

        def juger(row):
            if row["ET1"] == 0:
                return "Non évaluable"
            if row["Variation_Nette"] > 0 and row["Taux_Resolution"] >= 75:
                return "Amélioration nette"
            elif row["Variation_Nette"] > 0:
                return "Amélioration partielle"
            elif row["Variation_Nette"] == 0:
                return "Stagnation"
            else:
                return "Dégradation"

        df_temp["Jugement"] = df_temp.apply(juger, axis=1)

        st.markdown("---")
        st.subheader("Indicateurs clés")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("T1 moyen", f"{df_temp['ET1'].mean():.1f}")
        c2.metric("T2 moyen", f"{df_temp['ET2'].mean():.1f}")
        c3.metric("Taux de résolution moyen", f"{df_temp['Taux_Resolution'].mean():.1f} %")
        c4.metric("Variation nette moyenne", f"{df_temp['Variation_Nette'].mean():+.1f}")

        st.subheader("Jugement global")
        jugement_counts = df_temp["Jugement"].value_counts().reset_index()
        jugement_counts.columns = ["Jugement", "Effectif"]
        jugement_counts["Pourcentage (%)"] = (
            jugement_counts["Effectif"] / len(df_temp) * 100
        ).round(1)
        st.dataframe(jugement_counts, use_container_width=True, hide_index=True)

        fig_jug = px.bar(
            jugement_counts, x="Jugement", y="Effectif",
            color="Jugement", text="Effectif",
            color_discrete_map={
                "Amélioration nette": "#2E8B57",
                "Amélioration partielle": "#8FBC8F",
                "Stagnation": "#FFA500",
                "Dégradation": "#DC143C",
                "Non évaluable": "#808080",
            },
        )
        fig_jug.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
        )
        st.plotly_chart(fig_jug, use_container_width=True)

        st.subheader("Comparaison T1 vs T2")
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(name="T1", x=df_temp.index, y=df_temp["ET1"], marker_color="#4A90D9"))
        fig_comp.add_trace(go.Bar(name="T2", x=df_temp.index, y=df_temp["ET2"], marker_color="#2E8B57"))
        fig_comp.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.subheader("Fréquences par position")
        temps = st.radio("Temps", ["T1", "T2"], horizontal=True, key="temps_radio")
        freq = frequences_par_position(df_temp, cols, temps=temps, valeur_present=valeur_present)
        st.dataframe(freq, use_container_width=True, hide_index=True)

        st.subheader("Statuts par position")
        statuts_df = frequences_statuts(
            df_temp, cols, valeur_present=valeur_present, valeur_absent=valeur_absent,
        )
        st.dataframe(statuts_df, use_container_width=True, hide_index=True)

        st.subheader("📄 Exports")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Générer le rapport Word"):
                try:
                    sections = [
                        {"titre": "1. Indicateurs clés", "tableau": jugement_counts, "graphique": fig_jug},
                        {"titre": "2. Comparaison T1 vs T2", "graphique": fig_comp},
                    ]
                    chemin = "exports/rapport_evolution.docx"
                    exporter_word_complet(chemin, "Rapport d'analyse — Évolution", sections)
                    with open(chemin, "rb") as f:
                        st.download_button(
                            "⬇️ Télécharger Word", f,
                            file_name="rapport_evolution.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                except Exception as e:
                    st.error(f"Erreur : {e}")
        with c2:
            if st.button("Générer le rapport Excel"):
                try:
                    feuilles = {
                        "Indicateurs": jugement_counts,
                        "Détail": df_temp[["ET1", "ET2", "Resolus", "Persistants",
                                            "Nouveaux", "Variation_Nette",
                                            "Taux_Resolution", "Jugement"]],
                        "Statuts": statuts_df,
                    }
                    chemin = "exports/rapport_evolution.xlsx"
                    exporter_excel_enrichi(feuilles, chemin)
                    with open(chemin, "rb") as f:
                        st.download_button(
                            "⬇️ Télécharger Excel", f,
                            file_name="rapport_evolution.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                except Exception as e:
                    st.error(f"Erreur : {e}")

    # ---------------- 7. HISTORIQUE ----------------
    with tabs[7]:
        st.header("📚 Historique des analyses")

        user = st.session_state.user
        if user["role"] == "admin":
            st.info("Mode administrateur : vous voyez l'historique de tous les utilisateurs.")
            analyses = lister_analyses()
        else:
            analyses = lister_analyses(user_id=user["id"])

        if not analyses:
            st.info("Aucune analyse enregistrée pour le moment.")
        else:
            df_hist = pd.DataFrame(analyses)
            df_hist = df_hist[[
                "id", "username", "filename", "sheet_name",
                "nb_lignes", "nb_colonnes", "taux_completude",
                "nb_doublons", "created_at",
            ]]
            df_hist.columns = [
                "ID", "Utilisateur", "Fichier", "Feuille",
                "Lignes", "Colonnes", "Complétude (%)",
                "Doublons", "Date",
            ]
            st.dataframe(df_hist, use_container_width=True, hide_index=True)

            fig = px.bar(
                df_hist.groupby("Utilisateur").size().reset_index(name="Analyses"),
                x="Utilisateur", y="Analyses",
                title="Nombre d'analyses par utilisateur",
                color_discrete_sequence=["#4A90D9"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("💾 Configurations sauvegardées")
        configs = lister_configs(user["id"])
        if not configs:
            st.info("Aucune configuration sauvegardée.")
        else:
            for cfg in configs:
                with st.expander(f"⚙️ {cfg['nom']} — {cfg['created_at'][:19]}"):
                    st.json(json.loads(cfg["data_json"]))
                    if st.button("🗑 Supprimer", key=f"del_cfg_{cfg['id']}"):
                        supprimer_config(cfg["id"])
                        st.rerun()

    # ---------------- 8. UTILISATEURS (ADMIN) ----------------
    if st.session_state.user["role"] == "admin":
        with tabs[8]:
            st.header("👥 Gestion des utilisateurs")

            utilisateurs = lister_utilisateurs()
            df_users = pd.DataFrame(utilisateurs)
            st.dataframe(df_users, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("➕ Créer un nouvel utilisateur")
            with st.form("form_admin_creer_user"):
                c1, c2, c3 = st.columns(3)
                new_u = c1.text_input("Nom d'utilisateur")
                new_p = c2.text_input("Mot de passe", type="password")
                new_r = c3.selectbox("Rôle", ["user", "admin"])
                if st.form_submit_button("Créer"):
                    succes, msg = inscrire(new_u, new_p, role=new_r)
                    if succes:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            st.subheader("🔑 Changer le mot de passe d'un utilisateur")
            autres_users = [
                u for u in utilisateurs
                if u["username"] != st.session_state.user["username"]
            ]
            if not autres_users:
                st.info("Aucun autre utilisateur à modifier.")
            else:
                user_a_modifier = st.selectbox(
                    "Choisir l'utilisateur",
                    autres_users,
                    format_func=lambda u: f"{u['username']} ({u['role']})",
                    key="select_user_change_pwd",
                )
                nouveau_pwd = st.text_input(
                    "Nouveau mot de passe (min. 6 caractères)",
                    type="password",
                    key="new_pwd_admin",
                )
                confirme_pwd = st.text_input(
                    "Confirmer le nouveau mot de passe",
                    type="password",
                    key="confirm_pwd_admin",
                )
                if st.button("Changer le mot de passe", type="primary", key="btn_change_pwd"):
                    if not nouveau_pwd or not confirme_pwd:
                        st.error("Veuillez remplir tous les champs.")
                    elif nouveau_pwd != confirme_pwd:
                        st.error("Les deux mots de passe ne correspondent pas.")
                    else:
                        succes, msg = forcer_changement_mot_de_passe(
                            user_a_modifier["id"], nouveau_pwd,
                        )
                        if succes:
                            st.success(
                                f"Mot de passe de **{user_a_modifier['username']}** modifié."
                            )
                        else:
                            st.error(msg)

            st.markdown("---")
            st.subheader("🗑 Supprimer un utilisateur")
            if not autres_users:
                st.info("Aucun autre utilisateur à supprimer.")
            else:
                user_a_supprimer = st.selectbox(
                    "Choisir l'utilisateur à supprimer",
                    autres_users,
                    format_func=lambda u: f"{u['username']} ({u['role']})",
                    key="select_user_delete",
                )
                confirmation = st.checkbox(
                    f"Je confirme vouloir supprimer **{user_a_supprimer['username']}** "
                    "et toutes ses analyses."
                )
                if st.button(
                    "🗑 Supprimer définitivement",
                    type="primary",
                    disabled=not confirmation,
                    key="btn_delete_user",
                ):
                    supprimer_utilisateur(user_a_supprimer["id"])
                    st.success(f"Utilisateur {user_a_supprimer['username']} supprimé.")
                    st.rerun()


# ==============================================================================
# ROUTAGE
# ==============================================================================
if st.session_state.user is None:
    page_login()
else:
    page_principale()