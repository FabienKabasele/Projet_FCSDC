import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="Dashboard TIFA TBCI - Lomami",
    page_icon="🫁",
    layout="wide"
)

st.markdown("""
    <style>
    .main-header {
        background-color: #1f77b4;
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🫁 Tableau de Bord TIFA TBCI - Lomami</h1><p>Suivi des activités de lutte contre la tuberculose</p></div>', unsafe_allow_html=True)

# ============================================================
# DONNÉES DE RÉFÉRENCE - LOMAMI
# ============================================================
LOMAMI_ZS = {
    "lm Kabinda": 8,
    "lm Kalambayi Kabanga": 6,
    "lm Kalenda": 7,
    "lm Kalonda Est": 6,
    "lm Kamana": 7,
    "lm Kamiji": 6,
    "lm Kanda Kanda": 7,
    "lm Lubao": 6,
    "lm Ludimbi Lukula": 6,
    "lm Luputa": 10,
    "lm Makota": 7,
    "lm Mulumba": 6,
    "lm Mweneditu": 6,
    "lm Ngandajika": 6,
    "lm Tshofa": 6,
    "lm Wikong": 5,
    "sk Bagira": 1
}

TOTAL_ESS = sum(LOMAMI_ZS.values())
TOTAL_ZS = len(LOMAMI_ZS)

MOIS_FR = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================
@st.cache_data
def load_data(file_path="drc_posaf_tifa_tbci_WIDE.csv"):
    """Charge et prépare les données Lomami"""
    try:
        df = pd.read_csv(
            file_path,
            encoding='utf-8',
            sep=None,
            engine='python',
            on_bad_lines='skip'
        )
        df.columns = df.columns.str.strip()

        if df.empty:
            st.warning("⚠️ Le fichier est vide ou n'a pas pu être lu.")
            return create_empty_dataframe()

        # Filtrer Lomami
        if 'q010a' in df.columns:
            df['province_code'] = df['q010a'].astype(str).str.strip()
        else:
            df['province_code'] = df['siteid'].str.split('-').str[0].str.strip() if 'siteid' in df.columns else ''

        if 'q010b' in df.columns:
            df['province_name'] = df['q010b'].astype(str).str.strip()
        else:
            df['province_name'] = ''

        mask_lomami = (df['province_code'] == '6') | (df['province_name'].str.contains('Lomami', case=False, na=False))
        df_lomami = df[mask_lomami].copy()

        if df_lomami.empty:
            st.warning("⚠️ Aucune donnée trouvée pour la province de Lomami.")
            return create_empty_dataframe()

        # Noms géographiques
        df_lomami['healthzone_name'] = df_lomami.get('q011b', 'Non spécifié').fillna('Non spécifié')
        df_lomami['facility_name'] = df_lomami.get('q012b', 'Non spécifié').fillna('Non spécifié')

        # ============================================================
        # DATES ET PÉRIODES - Utilisation de qmois et qannee (fiable)
        # ============================================================
        if 'qmois' in df_lomami.columns and 'qannee' in df_lomami.columns:
            df_lomami['mois'] = df_lomami['qmois'].str.extract('(\d+)')[0].astype(float)
            df_lomami['annee'] = df_lomami['qannee'].str.extract('(\d+)')[0].astype(float)
            df_lomami['date_saisie'] = pd.to_datetime(
                df_lomami['annee'].astype(str) + '-' + df_lomami['mois'].astype(str) + '-01',
                errors='coerce'
            )
            df_lomami['trimestre'] = np.ceil(df_lomami['mois'] / 3)
            df_lomami['mois_nom'] = df_lomami['mois'].map(MOIS_FR)
        else:
            # Fallback : essayer de parser q001a
            if 'q001a' in df_lomami.columns:
                import re
                mois_fr_to_num = {
                    'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
                    'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
                    'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12,
                    'janv': 1, 'févr': 2, 'mars': 3, 'avr': 4, 'mai': 5, 'juin': 6,
                    'juil': 7, 'août': 8, 'sept': 9, 'oct': 10, 'nov': 11, 'déc': 12
                }
                def parse_date_fr(date_str):
                    if pd.isna(date_str):
                        return pd.NaT
                    match = re.match(r'(\d+)\s+([a-zéû.]+)\s+(\d{4})', str(date_str).lower())
                    if match:
                        jour = int(match.group(1))
                        mois = mois_fr_to_num.get(match.group(2), 0)
                        annee = int(match.group(3))
                        if mois > 0:
                            return pd.Timestamp(year=annee, month=mois, day=jour)
                    return pd.NaT

                df_lomami['date_saisie'] = df_lomami['q001a'].apply(parse_date_fr)
                df_lomami['mois'] = df_lomami['date_saisie'].dt.month
                df_lomami['annee'] = df_lomami['date_saisie'].dt.year
                df_lomami['trimestre'] = df_lomami['date_saisie'].dt.quarter
                df_lomami['mois_nom'] = df_lomami['mois'].map(MOIS_FR)
            else:
                df_lomami['date_saisie'] = pd.NaT
                df_lomami['mois'] = pd.NA
                df_lomami['trimestre'] = pd.NA
                df_lomami['annee'] = pd.NA
                df_lomami['mois_nom'] = pd.NA

        # Colonnes numériques
        numeric_cols = [
            'index_0_4ans_h', 'index_0_4ans_f', 'index_5_14ans_h', 'index_5_14ans_f',
            'index_15plus_h', 'index_15plus_f', 'index_investigue_h', 'index_investigue_f',
            'cf_rep_0_4ans_h', 'cf_rep_0_4ans_f', 'cf_rep_5_14ans_h', 'cf_rep_5_14ans_f',
            'cf_rep_15plus_h', 'cf_rep_15plus_f',
            'cf_inv_0_4ans_h', 'cf_inv_0_4ans_f', 'cf_inv_5_14ans_h', 'cf_inv_5_14ans_f',
            'cf_inv_15plus_h', 'cf_inv_15plus_f',
            'cf_vih_pos_h', 'cf_vih_pos_f', 'cf_vih_neg_h', 'cf_vih_neg_f',
            'tb_presume_0_4ans_h', 'tb_presume_0_4ans_f', 'tb_presume_5_14ans_h', 'tb_presume_5_14ans_f',
            'tb_presume_15plus_h', 'tb_presume_15plus_f',
            'tb_oriente_cdt_0_4ans_h', 'tb_oriente_cdt_0_4ans_f', 'tb_oriente_cdt_5_14ans_h', 'tb_oriente_cdt_5_14ans_f',
            'tb_oriente_cdt_15plus_h', 'tb_oriente_cdt_15plus_f',
            'cf_conf_tb_0_4ans_h', 'cf_conf_tb_0_4ans_f', 'cf_conf_tb_5_14ans_h', 'cf_conf_tb_5_14ans_f',
            'cf_conf_tb_15plus_h', 'cf_conf_tb_15plus_f',
            'cf_conf_trait_0_4ans_h', 'cf_conf_trait_0_4ans_f', 'cf_conf_trait_5_14ans_h', 'cf_conf_trait_5_14ans_f',
            'cf_conf_trait_15plus_h', 'cf_conf_trait_15plus_f',
            'cf_tpt_elig_0_4ans_h', 'cf_tpt_elig_0_4ans_f', 'cf_tpt_elig_5_14ans_h', 'cf_tpt_elig_5_14ans_f',
            'cf_tpt_elig_15plus_h', 'cf_tpt_elig_15plus_f',
            'cf_tpt_init_0_4ans_h', 'cf_tpt_init_0_4ans_f', 'cf_tpt_init_5_14ans_h', 'cf_tpt_init_5_14ans_f',
            'cf_tpt_init_15plus_h', 'cf_tpt_init_15plus_f',
            'tpt_3m_0_4ans_h', 'tpt_3m_0_4ans_f', 'tpt_3m_5_14ans_h', 'tpt_3m_5_14ans_f',
            'tpt_3m_15plus_h', 'tpt_3m_15plus_f',
            'tpt_termine_0_4ans_h', 'tpt_termine_0_4ans_f', 'tpt_termine_5_14ans_h', 'tpt_termine_5_14ans_f',
            'tpt_termine_15plus_h', 'tpt_termine_15plus_f',
            'tb_conf_trait6m_0_4ans_h', 'tb_conf_trait6m_0_4ans_f', 'tb_conf_trait6m_5_14ans_h', 'tb_conf_trait6m_5_14ans_f',
            'tb_conf_trait6m_15plus_h', 'tb_conf_trait6m_15plus_f',
            'tb_gueris_0_4ans_h', 'tb_gueris_0_4ans_f', 'tb_gueris_5_14ans_h', 'tb_gueris_5_14ans_f',
            'tb_gueris_15plus_h', 'tb_gueris_15plus_f'
        ]
        for col in numeric_cols:
            if col in df_lomami.columns:
                df_lomami[col] = pd.to_numeric(df_lomami[col], errors='coerce').fillna(0)
            else:
                df_lomami[col] = 0

        df_lomami = calculate_indicators(df_lomami)
        return df_lomami

    except FileNotFoundError:
        st.warning("⚠️ Fichier non trouvé. Assurez-vous que 'drc_posaf_tifa_tbci_WIDE (1).csv' est présent.")
        return create_empty_dataframe()
    except Exception as e:
        st.warning(f"⚠️ Erreur lors du chargement : {e}")
        return create_empty_dataframe()

def create_empty_dataframe():
    df = pd.DataFrame()
    df['healthzone_name'] = 'Non spécifié'
    df['facility_name'] = 'Non spécifié'
    df['date_saisie'] = pd.NaT
    df['mois'] = pd.NA
    df['trimestre'] = pd.NA
    df['annee'] = pd.NA
    df['mois_nom'] = pd.NA
    calcul_cols = [
        'cf_rep_total', 'cf_inv_total', 'cf_conf_tb_total',
        'cf_tpt_elig_total', 'cf_tpt_init_total', 'tpt_3m_total',
        'tpt_termine_total', 'tb_gueris_total', 'cf_vih_pos_total',
        'cf_vih_neg_total', 'tb_conf_trait6m_total', 'index_total',
        'index_total_investigue', 'tb_presume_total', 'tb_oriente_cdt_total'
    ]
    for col in calcul_cols:
        df[col] = 0
    return df

def calculate_indicators(df):
    df['cf_rep_total'] = (df.get('cf_rep_0_4ans_h', 0) + df.get('cf_rep_0_4ans_f', 0) +
                          df.get('cf_rep_5_14ans_h', 0) + df.get('cf_rep_5_14ans_f', 0) +
                          df.get('cf_rep_15plus_h', 0) + df.get('cf_rep_15plus_f', 0))

    df['cf_inv_total'] = (df.get('cf_inv_0_4ans_h', 0) + df.get('cf_inv_0_4ans_f', 0) +
                          df.get('cf_inv_5_14ans_h', 0) + df.get('cf_inv_5_14ans_f', 0) +
                          df.get('cf_inv_15plus_h', 0) + df.get('cf_inv_15plus_f', 0))

    df['cf_conf_tb_total'] = (df.get('cf_conf_tb_0_4ans_h', 0) + df.get('cf_conf_tb_0_4ans_f', 0) +
                              df.get('cf_conf_tb_5_14ans_h', 0) + df.get('cf_conf_tb_5_14ans_f', 0) +
                              df.get('cf_conf_tb_15plus_h', 0) + df.get('cf_conf_tb_15plus_f', 0))

    df['cf_tpt_elig_total'] = (df.get('cf_tpt_elig_0_4ans_h', 0) + df.get('cf_tpt_elig_0_4ans_f', 0) +
                               df.get('cf_tpt_elig_5_14ans_h', 0) + df.get('cf_tpt_elig_5_14ans_f', 0) +
                               df.get('cf_tpt_elig_15plus_h', 0) + df.get('cf_tpt_elig_15plus_f', 0))

    df['cf_tpt_init_total'] = (df.get('cf_tpt_init_0_4ans_h', 0) + df.get('cf_tpt_init_0_4ans_f', 0) +
                               df.get('cf_tpt_init_5_14ans_h', 0) + df.get('cf_tpt_init_5_14ans_f', 0) +
                               df.get('cf_tpt_init_15plus_h', 0) + df.get('cf_tpt_init_15plus_f', 0))

    df['tpt_3m_total'] = (df.get('tpt_3m_0_4ans_h', 0) + df.get('tpt_3m_0_4ans_f', 0) +
                          df.get('tpt_3m_5_14ans_h', 0) + df.get('tpt_3m_5_14ans_f', 0) +
                          df.get('tpt_3m_15plus_h', 0) + df.get('tpt_3m_15plus_f', 0))

    df['tpt_termine_total'] = (df.get('tpt_termine_0_4ans_h', 0) + df.get('tpt_termine_0_4ans_f', 0) +
                               df.get('tpt_termine_5_14ans_h', 0) + df.get('tpt_termine_5_14ans_f', 0) +
                               df.get('tpt_termine_15plus_h', 0) + df.get('tpt_termine_15plus_f', 0))

    df['tb_gueris_total'] = (df.get('tb_gueris_0_4ans_h', 0) + df.get('tb_gueris_0_4ans_f', 0) +
                             df.get('tb_gueris_5_14ans_h', 0) + df.get('tb_gueris_5_14ans_f', 0) +
                             df.get('tb_gueris_15plus_h', 0) + df.get('tb_gueris_15plus_f', 0))

    df['cf_vih_pos_total'] = df.get('cf_vih_pos_h', 0) + df.get('cf_vih_pos_f', 0)
    df['cf_vih_neg_total'] = df.get('cf_vih_neg_h', 0) + df.get('cf_vih_neg_f', 0)

    df['tb_conf_trait6m_total'] = (df.get('tb_conf_trait6m_0_4ans_h', 0) + df.get('tb_conf_trait6m_0_4ans_f', 0) +
                                   df.get('tb_conf_trait6m_5_14ans_h', 0) + df.get('tb_conf_trait6m_5_14ans_f', 0) +
                                   df.get('tb_conf_trait6m_15plus_h', 0) + df.get('tb_conf_trait6m_15plus_f', 0))

    df['index_total'] = (df.get('index_0_4ans_h', 0) + df.get('index_0_4ans_f', 0) +
                         df.get('index_5_14ans_h', 0) + df.get('index_5_14ans_f', 0) +
                         df.get('index_15plus_h', 0) + df.get('index_15plus_f', 0))
    df['index_total_investigue'] = df.get('index_investigue_h', 0) + df.get('index_investigue_f', 0)
    df['tb_presume_total'] = (df.get('tb_presume_0_4ans_h', 0) + df.get('tb_presume_0_4ans_f', 0) +
                              df.get('tb_presume_5_14ans_h', 0) + df.get('tb_presume_5_14ans_f', 0) +
                              df.get('tb_presume_15plus_h', 0) + df.get('tb_presume_15plus_f', 0))
    df['tb_oriente_cdt_total'] = (df.get('tb_oriente_cdt_0_4ans_h', 0) + df.get('tb_oriente_cdt_0_4ans_f', 0) +
                                  df.get('tb_oriente_cdt_5_14ans_h', 0) + df.get('tb_oriente_cdt_5_14ans_f', 0) +
                                  df.get('tb_oriente_cdt_15plus_h', 0) + df.get('tb_oriente_cdt_15plus_f', 0))
    return df

# ============================================================
# CHARGEMENT
# ============================================================
df = load_data()

if df.empty:
    st.stop()

# ============================================================
# BARRE LATÉRALE
# ============================================================
st.sidebar.header("🔍 Filtres")

# ---- BOUTON DE NAVIGATION VERS FC SDC ----
st.sidebar.link_button(
    "🔗 Basculer vers FC SDC",
    "https://posafcsdc.streamlit.app/",
    use_container_width=True
)

st.sidebar.info("🏛️ Province: **Lomami**")

st.sidebar.subheader("📅 Période")

# Années disponibles (depuis qannee)
annees_disponibles = sorted(df['annee'].dropna().unique().astype(int).tolist()) if 'annee' in df.columns else [2026]
annee_filter = st.sidebar.selectbox("Année", annees_disponibles, index=len(annees_disponibles)-1 if annees_disponibles else 0)

# Mois disponibles pour l'année sélectionnée
mois_disponibles = sorted(df[df['annee'] == annee_filter]['mois'].dropna().unique().astype(int).tolist()) if 'annee' in df.columns else []
mois_options = ['Tous les mois'] + [MOIS_FR[m] for m in mois_disponibles] if mois_disponibles else ['Tous les mois']
mois_selection = st.sidebar.selectbox("Mois", mois_options)
mois_filter = None if mois_selection == 'Tous les mois' else [m for m, nom in MOIS_FR.items() if nom == mois_selection][0]

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Ou par Trimestre")
trimestres_disponibles = sorted(df[df['annee'] == annee_filter]['trimestre'].dropna().unique().astype(int).tolist()) if 'annee' in df.columns else []
trimestre_options = ['Tous les trimestres'] + [f"T{int(t)}" for t in trimestres_disponibles] if trimestres_disponibles else ['Tous les trimestres']
trimestre_selection = st.sidebar.selectbox("Trimestre", trimestre_options)
trimestre_filter = None if trimestre_selection == 'Tous les trimestres' else int(trimestre_selection.replace('T', ''))

st.sidebar.markdown("---")
zones = sorted(df['healthzone_name'].dropna().unique().tolist())
zone_options = ['Toutes les zones'] + zones
zone_filter = st.sidebar.selectbox("🏥 Zone de Santé", zone_options)

if zone_filter != 'Toutes les zones':
    facilities = sorted(df[df['healthzone_name'] == zone_filter]['facility_name'].dropna().unique().tolist())
else:
    facilities = sorted(df['facility_name'].dropna().unique().tolist())
facility_options = ['Tous les établissements'] + facilities
facility_filter = st.sidebar.selectbox("🏪 Établissement", facility_options)

# Application des filtres
df_filtered = df.copy()
if 'annee' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['annee'] == annee_filter]
if mois_filter is not None and 'mois' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['mois'] == mois_filter]
elif trimestre_filter is not None and 'trimestre' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['trimestre'] == trimestre_filter]
if zone_filter != 'Toutes les zones':
    df_filtered = df_filtered[df_filtered['healthzone_name'] == zone_filter]
if facility_filter != 'Tous les établissements':
    df_filtered = df_filtered[df_filtered['facility_name'] == facility_filter]

periode_texte = f"Année {annee_filter}"
if mois_filter is not None:
    periode_texte += f" - {MOIS_FR[mois_filter]}"
elif trimestre_filter is not None:
    periode_texte += f" - T{trimestre_filter}"

st.sidebar.markdown("---")
st.sidebar.info(f"📊 Période: **{periode_texte}**")

# ============================================================
# INDICATEURS CLÉS
# ============================================================
total_contacts = int(df_filtered['cf_rep_total'].sum()) if not df_filtered.empty else 0
total_invest = int(df_filtered['cf_inv_total'].sum()) if not df_filtered.empty else 0
pct_invest = (total_invest / total_contacts * 100) if total_contacts > 0 else 0
total_tb = int(df_filtered['cf_conf_tb_total'].sum()) if not df_filtered.empty else 0
total_tpt_elig = int(df_filtered['cf_tpt_elig_total'].sum()) if not df_filtered.empty else 0
total_tpt_init = int(df_filtered['cf_tpt_init_total'].sum()) if not df_filtered.empty else 0
pct_tpt = (total_tpt_init / total_tpt_elig * 100) if total_tpt_elig > 0 else 0
nb_ess_ayant_soumis = df_filtered['facility_name'].nunique() if not df_filtered.empty else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("📋 ESS ayant soumis", f"{nb_ess_ayant_soumis}/{TOTAL_ESS}")
col2.metric("📋 Contacts répertoriés", f"{total_contacts:,}")
col3.metric("🔍 Contacts investigués", f"{total_invest:,}")
col4.metric("📊 Taux investigation", f"{pct_invest:.1f}%")
col5.metric("🦠 TB confirmées", f"{total_tb:,}")
col6.metric("💉 Taux initiation TPT", f"{pct_tpt:.1f}%")

st.markdown("---")

# ============================================================
# ONGLETS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🩺 Dépistage des Contacts",
    "🔬 Diagnostic TB",
    "🦠 Co-infection VIH/TB",
    "💊 Prise en charge",
    "💉 Traitement Préventif (TPT)",
    "📊 Performance par Zone",
    "📋 Tableau personnalisé",
    "📈 Complétude"
])

# ============================================================
# TAB 1 à 7 : inchangés (repris intégralement)
# ============================================================
with tab1:
    st.header(f"📋 Cascade de Dépistage des Contacts - {periode_texte}")

    cascade_data = {
        "Étape": [
            "Cas index répertoriés",
            "Cas index investigués",
            "Contacts familiaux répertoriés",
            "Contacts familiaux investigués",
            "Cas présumés TB identifiés",
            "TB présumée orientée vers CDT"
        ],
        "Nombre": [
            int(df_filtered['index_total'].sum()) if not df_filtered.empty and 'index_total' in df_filtered.columns else 0,
            int(df_filtered['index_total_investigue'].sum()) if not df_filtered.empty and 'index_total_investigue' in df_filtered.columns else 0,
            int(df_filtered['cf_rep_total'].sum()) if not df_filtered.empty else 0,
            int(df_filtered['cf_inv_total'].sum()) if not df_filtered.empty else 0,
            int(df_filtered['tb_presume_total'].sum()) if not df_filtered.empty and 'tb_presume_total' in df_filtered.columns else 0,
            int(df_filtered['tb_oriente_cdt_total'].sum()) if not df_filtered.empty and 'tb_oriente_cdt_total' in df_filtered.columns else 0
        ]
    }
    df_cascade = pd.DataFrame(cascade_data)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.bar(df_cascade, x="Étape", y="Nombre",
                     title="Cascade de Dépistage des Contacts TB",
                     color="Nombre", color_continuous_scale="Blues",
                     text="Nombre")
        fig.update_traces(textposition="outside")
        fig.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("Total contacts répertoriés", f"{total_contacts:,}")
        st.metric("Total contacts investigués", f"{total_invest:,}")
        st.metric("Taux d'investigation", f"{pct_invest:.1f}%")
        st.metric("Cas présumés TB", f"{df_cascade['Nombre'].iloc[4]:,}")

    st.subheader("📊 Entonnoir de la cascade")
    fig_funnel = go.Figure(go.Funnel(
        y=cascade_data["Étape"],
        x=cascade_data["Nombre"],
        textposition="inside",
        textinfo="value+percent initial",
        marker={"color": px.colors.sequential.Blues_r}
    ))
    fig_funnel.update_layout(height=500)
    st.plotly_chart(fig_funnel, use_container_width=True)

with tab2:
    st.header(f"🔬 Diagnostic de la Tuberculose - {periode_texte}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TB Confirmée", f"{total_tb:,}")
    col2.metric("TB RR (résistante)", "N/A")
    col3.metric("TP+ Microscopie", "N/A")
    col4.metric("Testés GeneXpert", "N/A")

    st.subheader("👥 Répartition des TB confirmées par âge et sexe")

    if not df_filtered.empty:
        age_data = {
            "Groupe d'âge": ["0-4 ans", "5-14 ans", "15+ ans", "0-4 ans", "5-14 ans", "15+ ans"],
            "Sexe": ["Hommes", "Hommes", "Hommes", "Femmes", "Femmes", "Femmes"],
            "Nombre": [
                int(df_filtered['cf_conf_tb_0_4ans_h'].sum()),
                int(df_filtered['cf_conf_tb_5_14ans_h'].sum()),
                int(df_filtered['cf_conf_tb_15plus_h'].sum()),
                int(df_filtered['cf_conf_tb_0_4ans_f'].sum()),
                int(df_filtered['cf_conf_tb_5_14ans_f'].sum()),
                int(df_filtered['cf_conf_tb_15plus_f'].sum())
            ]
        }
    else:
        age_data = {
            "Groupe d'âge": ["0-4 ans", "5-14 ans", "15+ ans", "0-4 ans", "5-14 ans", "15+ ans"],
            "Sexe": ["Hommes", "Hommes", "Hommes", "Femmes", "Femmes", "Femmes"],
            "Nombre": [0, 0, 0, 0, 0, 0]
        }

    df_age = pd.DataFrame(age_data)
    fig = px.bar(df_age, x="Groupe d'âge", y="Nombre", color="Sexe",
                 barmode="group", title="TB confirmées par âge et sexe")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header(f"🦠 Co-infection VIH/TB - {periode_texte}")

    total_vih_pos = int(df_filtered['cf_vih_pos_total'].sum()) if not df_filtered.empty else 0
    total_vih_neg = int(df_filtered['cf_vih_neg_total'].sum()) if not df_filtered.empty else 0
    total_vih_connu = total_vih_pos + total_vih_neg

    col1, col2 = st.columns(2)
    with col1:
        if total_vih_connu > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['VIH+', 'VIH-'],
                values=[total_vih_pos, total_vih_neg],
                hole=0.4,
                marker_colors=['#ff6b6b', '#4ecdc4']
            )])
        else:
            fig = go.Figure(data=[go.Pie(labels=['VIH+', 'VIH-'], values=[0, 1], hole=0.4)])
        fig.update_layout(title="Statut VIH des contacts investigués")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("Contacts VIH+", f"{total_vih_pos:,}")
        st.metric("Contacts VIH-", f"{total_vih_neg:,}")
        if total_vih_connu > 0:
            st.metric("Prévalence VIH", f"{(total_vih_pos / total_vih_connu * 100):.1f}%")
        else:
            st.metric("Prévalence VIH", "0%")

with tab4:
    st.header(f"💊 Prise en charge des cas TB - {periode_texte}")

    total_tb = int(df_filtered['cf_conf_tb_total'].sum()) if not df_filtered.empty else 0
    total_tb_traitement = int(df_filtered['cf_conf_trait_total'].sum()) if not df_filtered.empty and 'cf_conf_trait_total' in df_filtered.columns else 0
    total_tb_6m = int(df_filtered['tb_conf_trait6m_total'].sum()) if not df_filtered.empty else 0
    total_gueris = int(df_filtered['tb_gueris_total'].sum()) if not df_filtered.empty else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confirmés TB", f"{total_tb:,}")
        st.metric("Sous traitement", f"{total_tb_traitement:,}")
    with col2:
        st.metric("Traitement 6 mois", f"{total_tb_6m:,}")
        st.metric("TB guéris", f"{total_gueris:,}")
    with col3:
        pct_guerison = (total_gueris / total_tb * 100) if total_tb > 0 else 0
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pct_guerison,
            title={'text': "Taux de guérison (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#2ecc71"},
                   'steps': [
                       {'range': [0, 50], 'color': "#e74c3c"},
                       {'range': [50, 80], 'color': "#f39c12"},
                       {'range': [80, 100], 'color': "#2ecc71"}]}))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header(f"💉 Cascade du Traitement Préventif (TPT) - {periode_texte}")

    tpt_cascade = {
        "Étape": ["Éligibles TPT", "Initiés TPT", "TPT à 3 mois", "TPT terminé"],
        "Nombre": [
            int(df_filtered['cf_tpt_elig_total'].sum()) if not df_filtered.empty else 0,
            int(df_filtered['cf_tpt_init_total'].sum()) if not df_filtered.empty else 0,
            int(df_filtered['tpt_3m_total'].sum()) if not df_filtered.empty else 0,
            int(df_filtered['tpt_termine_total'].sum()) if not df_filtered.empty else 0
        ]
    }
    df_tpt = pd.DataFrame(tpt_cascade)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_tpt, x="Étape", y="Nombre",
                     title="Cascade TPT", color="Nombre",
                     color_continuous_scale="Tealgrn", text="Nombre")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        elig = df_tpt['Nombre'].iloc[0]
        init = df_tpt['Nombre'].iloc[1]
        pct_init = (init / elig * 100) if elig > 0 else 0
        st.metric("Éligibles TPT", f"{elig:,}")
        st.metric("Initiés TPT", f"{init:,}")
        st.metric("Taux d'initiation", f"{pct_init:.1f}%")
        st.metric("TPT terminé", f"{df_tpt['Nombre'].iloc[3]:,}")

    fig_funnel = go.Figure(go.Funnel(
        y=tpt_cascade["Étape"],
        x=tpt_cascade["Nombre"],
        textposition="inside",
        textinfo="value+percent initial",
        marker={"color": px.colors.sequential.Tealgrn}
    ))
    fig_funnel.update_layout(height=400)
    st.plotly_chart(fig_funnel, use_container_width=True)

with tab6:
    st.header(f"📊 Performance par Zone de Santé - {periode_texte}")

    if not df_filtered.empty:
        perf_zs = df_filtered.groupby('healthzone_name').agg({
            'cf_rep_total': 'sum',
            'cf_inv_total': 'sum',
            'cf_conf_tb_total': 'sum',
            'cf_tpt_elig_total': 'sum',
            'cf_tpt_init_total': 'sum'
        }).reset_index()

        perf_zs['pct_investigation'] = (perf_zs['cf_inv_total'] / perf_zs['cf_rep_total'].replace(0, 1) * 100).round(1)
        perf_zs['pct_tpt_init'] = (perf_zs['cf_tpt_init_total'] / perf_zs['cf_tpt_elig_total'].replace(0, 1) * 100).round(1)
        perf_zs['ess_attendu'] = perf_zs['healthzone_name'].map(LOMAMI_ZS)

        metric_choice = st.selectbox(
            "Choisir la métrique",
            ["Taux d'investigation (%)", "Taux d'initiation TPT (%)", "Nombre de TB confirmées"]
        )

        if metric_choice == "Taux d'investigation (%)":
            fig = px.bar(perf_zs.sort_values('pct_investigation', ascending=False),
                         x='healthzone_name', y='pct_investigation',
                         title="Taux d'investigation des contacts par ZS",
                         color='pct_investigation', color_continuous_scale='Blues',
                         text='pct_investigation')
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        elif metric_choice == "Taux d'initiation TPT (%)":
            fig = px.bar(perf_zs.sort_values('pct_tpt_init', ascending=False),
                         x='healthzone_name', y='pct_tpt_init',
                         title="Taux d'initiation TPT par ZS",
                         color='pct_tpt_init', color_continuous_scale='Tealgrn',
                         text='pct_tpt_init')
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        else:
            fig = px.bar(perf_zs.sort_values('cf_conf_tb_total', ascending=False),
                         x='healthzone_name', y='cf_conf_tb_total',
                         title="Nombre de TB confirmées par ZS",
                         color='cf_conf_tb_total', color_continuous_scale='Reds',
                         text='cf_conf_tb_total')

        fig.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🏆 Classement des Zones de Santé")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Meilleur taux d'investigation**")
            st.dataframe(perf_zs.nlargest(5, 'pct_investigation')[['healthzone_name', 'pct_investigation']])
        with col2:
            st.write("**Meilleur taux d'initiation TPT**")
            st.dataframe(perf_zs.nlargest(5, 'pct_tpt_init')[['healthzone_name', 'pct_tpt_init']])
    else:
        st.info("Aucune donnée disponible")

with tab7:
    st.header(f"📋 Tableau personnalisé - {periode_texte}")

    indicateurs = {
        "Contacts répertoriés": "cf_rep_total",
        "Contacts investigués": "cf_inv_total",
        "Taux investigation contacts (%)": "cf_pct_total",
        "TB confirmées": "cf_conf_tb_total",
        "Éligibles TPT": "cf_tpt_elig_total",
        "Initiés TPT": "cf_tpt_init_total",
        "Taux initiation TPT (%)": "cf_tpt_pct_total",
        "TPT terminé": "tpt_termine_total",
        "TB guéris": "tb_gueris_total"
    }

    selected = st.multiselect(
        "Choisir les indicateurs",
        options=list(indicateurs.keys()),
        default=["Contacts répertoriés", "Contacts investigués", "Taux investigation contacts (%)", "TB confirmées"]
    )

    if selected and not df_filtered.empty:
        cols_to_show = [indicateurs[i] for i in selected if indicateurs[i] in df_filtered.columns]
        if cols_to_show:
            table_data = df_filtered.groupby('healthzone_name')[cols_to_show].sum().reset_index()
            table_data['ESS Attendus'] = table_data['healthzone_name'].map(LOMAMI_ZS)
            st.dataframe(table_data, use_container_width=True)
            csv = table_data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger CSV", csv, "tableau.csv", "text/csv")
    else:
        st.info("Sélectionnez des indicateurs pour afficher le tableau")

# ============================================================
# TAB 8 : COMPLÉTUDE (synthèse filtrée par zone)
# ============================================================
with tab8:
    df_comp = df_filtered  # déjà filtré par zone, établissement, période

    if zone_filter != 'Toutes les zones':
        ess_attendus_zone = LOMAMI_ZS.get(zone_filter, 0)
        ess_ayant_soumis = df_comp['facility_name'].nunique() if not df_comp.empty else 0
        zs_ayant_soumis = df_comp['healthzone_name'].nunique() if not df_comp.empty else 0
        zs_attendues = 1
    else:
        ess_ayant_soumis = df_comp['facility_name'].nunique() if not df_comp.empty else 0
        zs_ayant_soumis = df_comp['healthzone_name'].nunique() if not df_comp.empty else 0
        ess_attendus_zone = TOTAL_ESS
        zs_attendues = TOTAL_ZS

    taux_global = (ess_ayant_soumis / ess_attendus_zone * 100) if ess_attendus_zone > 0 else 0

    st.header(f"📊 Synthèse de la Complétude - Lomami - {periode_texte}")
    st.markdown(f"**{zs_attendues} Zone(s) de Santé** | **{ess_attendus_zone} Établissement(s) de Santé attendus**")
    st.markdown("---")
    
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("🏥 ESS ayant soumis", f"{ess_ayant_soumis}/{ess_attendus_zone}")
    col_s2.metric("🏛️ ZS ayant soumis", f"{zs_ayant_soumis}/{zs_attendues}")
    col_s3.metric("📊 Taux de couverture", f"{taux_global:.1f}%")
    col_s4.metric("📋 Enquêtes dans la sélection", f"{len(df_comp):,}")

    if zone_filter != 'Toutes les zones':
        st.subheader(f"📋 Détail par Établissement pour la zone {zone_filter}")
        etab_stats = df_comp.groupby('facility_name').agg({
            'cf_rep_total': 'sum',
            'cf_inv_total': 'sum',
            'cf_conf_tb_total': 'sum'
        }).reset_index()
        etab_stats.rename(columns={
            'cf_rep_total': 'Contacts répertoriés',
            'cf_inv_total': 'Contacts investigués',
            'cf_conf_tb_total': 'TB confirmées'
        }, inplace=True)
        st.dataframe(etab_stats, use_container_width=True)
        csv_etab = etab_stats.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger les données des établissements (CSV)", csv_etab, "etablissements.csv", "text/csv")
    else:
        zs_stats = df_comp.groupby('healthzone_name')['facility_name'].nunique().reset_index()
        zs_stats.columns = ['Zone de Santé', 'ESS ayant soumis']
        zs_stats['ESS attendus'] = zs_stats['Zone de Santé'].map(LOMAMI_ZS)
        zs_stats['Taux'] = (zs_stats['ESS ayant soumis'] / zs_stats['ESS attendus'] * 100).round(1)
        zs_stats = zs_stats.sort_values('Taux', ascending=False)

        st.subheader("🏆 Classement des Zones de Santé par taux de couverture")
        col_class1, col_class2 = st.columns(2)
        with col_class1:
            st.write("**Meilleures ZS**")
            st.dataframe(zs_stats.head(5))
        with col_class2:
            st.write("**ZS à renforcer**")
            st.dataframe(zs_stats.tail(5))

        fig_zs = px.bar(zs_stats, x='Zone de Santé', y='Taux',
                        title="Taux de couverture par Zone de Santé",
                        color='Taux', color_continuous_scale='RdYlGn',
                        range_color=[0, 100], text='Taux')
        fig_zs.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_zs.update_layout(xaxis_tickangle=-45, height=500, yaxis_range=[0, 110])
        st.plotly_chart(fig_zs, use_container_width=True)

        csv_zs = zs_stats.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger les données des ZS (CSV)", csv_zs, "zs_stats.csv", "text/csv")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(f"📅 Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | Lomami - {TOTAL_ZS} ZS, {TOTAL_ESS} ESS | {len(df)} enquête(s) | Période: {periode_texte}")