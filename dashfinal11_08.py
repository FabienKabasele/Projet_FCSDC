import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import calendar
import io
import re

# Configuration de la page
st.set_page_config(
    page_title="Stop TB - Tableau de Bord FCSDS",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    .main-header {
        background-color: #1f77b4;
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .national-badge {
        background-color: #1f77b4;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .provincial-badge {
        background-color: #ff7f0e;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .zs-badge {
        background-color: #9467bd;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .facility-badge {
        background-color: #2ca02c;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .status-ok {
        background-color: #d4edda;
        color: #155724;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-danger {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<div class="main-header"><h1>🩺 Stop TB - Tableau de Bord FCSDS</h1><p>Suivi des activités de lutte contre la tuberculose</p></div>', unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION DU PROJET (FINANCES)
# ============================================================================

PROJET_CONFIG = {
    'budget_total': 500000,
    'date_debut': '2026-06-01',
    'date_fin': '2027-03-31',
    'nom_projet': 'Stop TB - FCSDS'
}

# ============================================================================
# DICTIONNAIRE DE RENOMMAGE DES COLONNES POUR L'EXPORT
# ============================================================================

COLUMN_RENAME_MAP = {
    'province_name': 'Province', 'healthzone_name': 'Zone_de_Sante',
    'facility_name': 'Etablissement', 'facility_id': 'ID_Etablissement',
    'mois_nom': 'Mois', 'qannee': 'Annee', 'trimestre': 'Trimestre',
    'date_saisie': 'Date_de_saisie', 'jour_soumission': 'Jour_soumission',
    'mois_soumission': 'Mois_soumission', 'annee_soumission': 'Annee_soumission',
    'est_prompt': 'Soumission_a_temps', 'statut_promptitude': 'Statut_promptitude',
    'q1_0_h': 'Depistage_Hommes', 'q1_0_f': 'Depistage_Femmes',
    'q1_0_hf_total': 'Depistage_Total', 'q1_0_age15m': 'Depistage_0_15_ans',
    'q1_0_age15p': 'Depistage_plus_15_ans', 'q1_0_age_total': 'Depistage_Tous_ages',
    'q1_0_niv_sante': 'Depistage_Niveau_sante', 'q1_0_niv_com': 'Depistage_Niveau_communautaire',
    'q1_0_niv_total': 'Depistage_Niveau_total', 'q1_1_h': 'Symptomatiques_Hommes',
    'q1_1_f': 'Symptomatiques_Femmes', 'q1_1_hf_total': 'Symptomatiques_Total',
    'q1_1_age15m': 'Symptomatiques_0_15_ans', 'q1_1_age15p': 'Symptomatiques_plus_15_ans',
    'q1_1_age_total': 'Symptomatiques_Tous_ages', 'q1_1_niv_sante': 'Symptomatiques_Niveau_sante',
    'q1_1_niv_com': 'Symptomatiques_Niveau_communautaire', 'q1_1_niv_total': 'Symptomatiques_Niveau_total',
    'q1_2_h': 'Cas_presumes_Hommes', 'q1_2_f': 'Cas_presumes_Femmes',
    'q1_2_hf_total': 'Cas_presumes_Total', 'q1_2_age15m': 'Cas_presumes_0_15_ans',
    'q1_2_age15p': 'Cas_presumes_plus_15_ans', 'q1_2_age_total': 'Cas_presumes_Tous_ages',
    'q1_2_niv_sante': 'Cas_presumes_Niveau_sante', 'q1_2_niv_com': 'Cas_presumes_Niveau_communautaire',
    'q1_2_niv_total': 'Cas_presumes_Niveau_total', 'q1_3_h': 'Examens_realises_Hommes',
    'q1_3_f': 'Examens_realises_Femmes', 'q1_3_hf_total': 'Examens_realises_Total',
    'q1_3_age15m': 'Examens_realises_0_15_ans', 'q1_3_age15p': 'Examens_realises_plus_15_ans',
    'q1_3_age_total': 'Examens_realises_Tous_ages', 'q1_3_niv_sante': 'Examens_realises_Niveau_sante',
    'q1_3_niv_com': 'Examens_realises_Niveau_communautaire', 'q1_3_niv_total': 'Examens_realises_Niveau_total',
    'q1_4_h': 'Eligibles_Xpert_Hommes', 'q1_4_f': 'Eligibles_Xpert_Femmes',
    'q1_4_hf_total': 'Eligibles_Xpert_Total', 'q1_4_age15m': 'Eligibles_Xpert_0_15_ans',
    'q1_4_age15p': 'Eligibles_Xpert_plus_15_ans', 'q1_4_age_total': 'Eligibles_Xpert_Tous_ages',
    'q1_5_h': 'Testes_Xpert_Hommes', 'q1_5_f': 'Testes_Xpert_Femmes',
    'q1_5_hf_total': 'Testes_Xpert_Total', 'q1_5_age15m': 'Testes_Xpert_0_15_ans',
    'q1_5_age15p': 'Testes_Xpert_plus_15_ans', 'q1_5_age_total': 'Testes_Xpert_Tous_ages',
    'q2_0_h': 'TB_detectee_Hommes', 'q2_0_f': 'TB_detectee_Femmes',
    'q2_0_hf_total': 'TB_detectee_Total', 'q2_0_age15m': 'TB_detectee_0_15_ans',
    'q2_0_age15p': 'TB_detectee_plus_15_ans', 'q2_0_age_total': 'TB_detectee_Tous_ages',
    'q2_1_h': 'TB_confirmee_bacterio_Hommes', 'q2_1_f': 'TB_confirmee_bacterio_Femmes',
    'q2_1_hf_total': 'TB_confirmee_bacterio_Total', 'q2_1_age15m': 'TB_confirmee_bacterio_0_15_ans',
    'q2_1_age15p': 'TB_confirmee_bacterio_plus_15_ans', 'q2_1_age_total': 'TB_confirmee_bacterio_Tous_ages',
    'q2_2_h': 'TB_confirmee_clinique_Hommes', 'q2_2_f': 'TB_confirmee_clinique_Femmes',
    'q2_2_hf_total': 'TB_confirmee_clinique_Total', 'q2_2_age15m': 'TB_confirmee_clinique_0_15_ans',
    'q2_2_age15p': 'TB_confirmee_clinique_plus_15_ans', 'q2_2_age_total': 'TB_confirmee_clinique_Tous_ages',
    'q3_0_h': 'Traitement_DS_debute_Hommes', 'q3_0_f': 'Traitement_DS_debute_Femmes',
    'q3_0_hf_total': 'Traitement_DS_debute_Total', 'q3_0_age15m': 'Traitement_DS_debute_0_15_ans',
    'q3_0_age15p': 'Traitement_DS_debute_plus_15_ans', 'q3_0_age_total': 'Traitement_DS_debute_Tous_ages',
    'q3_4_g04': 'Nouveaux_cas_0_4_ans_Hommes', 'q3_4_g514': 'Nouveaux_cas_5_14_ans_Hommes',
    'q3_4_h1524': 'Nouveaux_cas_15_24_ans_Hommes', 'q3_4_h2534': 'Nouveaux_cas_25_34_ans_Hommes',
    'q3_4_h3544': 'Nouveaux_cas_35_44_ans_Hommes', 'q3_4_h4554': 'Nouveaux_cas_45_54_ans_Hommes',
    'q3_4_h5564': 'Nouveaux_cas_55_64_ans_Hommes', 'q3_4_h65p': 'Nouveaux_cas_plus_65_ans_Hommes',
    'q3_4_f04': 'Nouveaux_cas_0_4_ans_Femmes', 'q3_4_f514': 'Nouveaux_cas_5_14_ans_Femmes',
    'q3_4_f1524': 'Nouveaux_cas_15_24_ans_Femmes', 'q3_4_f2534': 'Nouveaux_cas_25_34_ans_Femmes',
    'q3_4_f3544': 'Nouveaux_cas_35_44_ans_Femmes', 'q3_4_f4554': 'Nouveaux_cas_45_54_ans_Femmes',
    'q3_4_f5564': 'Nouveaux_cas_55_64_ans_Femmes', 'q3_4_f65p': 'Nouveaux_cas_plus_65_ans_Femmes',
    'q3_4_h_total': 'Nouveaux_cas_Total_Hommes', 'q3_4_f_total': 'Nouveaux_cas_Total_Femmes',
    'q3_4_hf_total': 'Nouveaux_cas_Total_General', 'q4_0_h': 'Testes_resistance_Hommes',
    'q4_0_f': 'Testes_resistance_Femmes', 'q4_0_hf_total': 'Testes_resistance_Total',
    'q4_0_age15m': 'Testes_resistance_0_15_ans', 'q4_0_age15p': 'Testes_resistance_plus_15_ans',
    'q4_0_age_total': 'Testes_resistance_Tous_ages', 'q4_1_h': 'Diagnostiques_RRMDR_Hommes',
    'q4_1_f': 'Diagnostiques_RRMDR_Femmes', 'q4_1_hf_total': 'Diagnostiques_RRMDR_Total',
    'q4_1_age15m': 'Diagnostiques_RRMDR_0_15_ans', 'q4_1_age15p': 'Diagnostiques_RRMDR_plus_15_ans',
    'q4_1_age_total': 'Diagnostiques_RRMDR_Tous_ages', 'q5_0_h': 'Traitement_RRMDR_debute_Hommes',
    'q5_0_f': 'Traitement_RRMDR_debute_Femmes', 'q5_0_hf_total': 'Traitement_RRMDR_debute_Total',
    'q5_0_age15m': 'Traitement_RRMDR_debute_0_15_ans', 'q5_0_age15p': 'Traitement_RRMDR_debute_plus_15_ans',
    'q5_0_age_total': 'Traitement_RRMDR_debute_Tous_ages', 'q6_0_h': 'Traitement_DS_reussi_Hommes',
    'q6_0_f': 'Traitement_DS_reussi_Femmes', 'q6_0_hf_total': 'Traitement_DS_reussi_Total',
    'q6_0_age15m': 'Traitement_DS_reussi_0_15_ans', 'q6_0_age15p': 'Traitement_DS_reussi_plus_15_ans',
    'q6_0_age_total': 'Traitement_DS_reussi_Tous_ages', 'q7_0_h': 'Traitement_RRMDR_reussi_Hommes',
    'q7_0_f': 'Traitement_RRMDR_reussi_Femmes', 'q7_0_hf_total': 'Traitement_RRMDR_reussi_Total',
    'q7_0_age15m': 'Traitement_RRMDR_reussi_0_15_ans', 'q7_0_age15p': 'Traitement_RRMDR_reussi_plus_15_ans',
    'q7_0_age_total': 'Traitement_RRMDR_reussi_Tous_ages', 'q8_0_h': 'TPT_depistage_Hommes',
    'q8_0_f': 'TPT_depistage_Femmes', 'q8_0_hf_total': 'TPT_depistage_Total',
    'q8_0_age5m': 'TPT_depistage_0_5_ans', 'q8_0_age5p': 'TPT_depistage_plus_5_ans',
    'q8_0_age_total': 'TPT_depistage_Tous_ages', 'q8_1_h': 'TPT_contacts_Hommes',
    'q8_1_f': 'TPT_contacts_Femmes', 'q8_1_hf_total': 'TPT_contacts_Total',
    'q8_1_age5m': 'TPT_contacts_0_5_ans', 'q8_1_age5p': 'TPT_contacts_plus_5_ans',
    'q8_1_age_total': 'TPT_contacts_Tous_ages', 'q8_2_h': 'TPT_PVVIH_Hommes',
    'q8_2_f': 'TPT_PVVIH_Femmes', 'q8_2_hf_total': 'TPT_PVVIH_Total',
    'q8_2_age5m': 'TPT_PVVIH_0_5_ans', 'q8_2_age5p': 'TPT_PVVIH_plus_5_ans',
    'q8_2_age_total': 'TPT_PVVIH_Tous_ages', 'q8_3_h': 'TPT_autres_groupes_Hommes',
    'q8_3_f': 'TPT_autres_groupes_Femmes', 'q8_3_hf_total': 'TPT_autres_groupes_Total',
    'q8_3_age5m': 'TPT_autres_groupes_0_5_ans', 'q8_3_age5p': 'TPT_autres_groupes_plus_5_ans',
    'q8_3_age_total': 'TPT_autres_groupes_Tous_ages', 'q8_4_h': 'TPT_eligibles_contacts_Hommes',
    'q8_4_f': 'TPT_eligibles_contacts_Femmes', 'q8_4_hf_total': 'TPT_eligibles_contacts_Total',
    'q8_4_age5m': 'TPT_eligibles_contacts_0_5_ans', 'q8_4_age5p': 'TPT_eligibles_contacts_plus_5_ans',
    'q8_4_age_total': 'TPT_eligibles_contacts_Tous_ages', 'q8_5_h': 'TPT_eligibles_PVVIH_Hommes',
    'q8_5_f': 'TPT_eligibles_PVVIH_Femmes', 'q8_5_hf_total': 'TPT_eligibles_PVVIH_Total',
    'q8_5_age15m': 'TPT_eligibles_PVVIH_0_15_ans', 'q8_5_age15p': 'TPT_eligibles_PVVIH_plus_15_ans',
    'q8_5_age_total': 'TPT_eligibles_PVVIH_Tous_ages', 'q8_6_h': 'TPT_eligibles_autres_Hommes',
    'q8_6_f': 'TPT_eligibles_autres_Femmes', 'q8_6_hf_total': 'TPT_eligibles_autres_Total',
    'q8_6_age5m': 'TPT_eligibles_autres_0_5_ans', 'q8_6_age5p': 'TPT_eligibles_autres_plus_5_ans',
    'q8_6_age_total': 'TPT_eligibles_autres_Tous_ages', 'q9_0': 'TPT_commence_contacts',
    'q9_1_h': 'TPT_commence_contacts_Hommes', 'q9_1_f': 'TPT_commence_contacts_Femmes',
    'q9_1_hf_total': 'TPT_commence_contacts_Total', 'q9_1_age5m': 'TPT_commence_contacts_0_5_ans',
    'q9_1_age5p': 'TPT_commence_contacts_plus_5_ans', 'q9_1_age_total': 'TPT_commence_contacts_Tous_ages',
    'q9_2_h': 'TPT_commence_PVVIH_Hommes', 'q9_2_f': 'TPT_commence_PVVIH_Femmes',
    'q9_2_hf_total': 'TPT_commence_PVVIH_Total', 'q9_2_age15m': 'TPT_commence_PVVIH_0_15_ans',
    'q9_2_age15p': 'TPT_commence_PVVIH_plus_15_ans', 'q9_2_age_total': 'TPT_commence_PVVIH_Tous_ages',
    'q9_3_h': 'TPT_commence_autres_Hommes', 'q9_3_f': 'TPT_commence_autres_Femmes',
    'q9_3_hf_total': 'TPT_commence_autres_Total', 'q9_3_age5m': 'TPT_commence_autres_0_5_ans',
    'q9_3_age5p': 'TPT_commence_autres_plus_5_ans', 'q9_3_age_total': 'TPT_commence_autres_Tous_ages',
    'q10_0_h': 'TPT_termine_contacts_Hommes', 'q10_0_f': 'TPT_termine_contacts_Femmes',
    'q10_0_hf_total': 'TPT_termine_contacts_Total', 'q10_0_age5m': 'TPT_termine_contacts_0_5_ans',
    'q10_0_age5p': 'TPT_termine_contacts_plus_5_ans', 'q10_0_age_total': 'TPT_termine_contacts_Tous_ages',
    'q10_1_h': 'TPT_termine_PVVIH_Hommes', 'q10_1_f': 'TPT_termine_PVVIH_Femmes',
    'q10_1_hf_total': 'TPT_termine_PVVIH_Total', 'q10_1_age5m': 'TPT_termine_PVVIH_0_5_ans',
    'q10_1_age5p': 'TPT_termine_PVVIH_plus_5_ans', 'q10_1_age_total': 'TPT_termine_PVVIH_Tous_ages',
    'q10_2_h': 'TPT_termine_autres_Hommes', 'q10_2_f': 'TPT_termine_autres_Femmes',
    'q10_2_hf_total': 'TPT_termine_autres_Total', 'q10_2_age5m': 'TPT_termine_autres_0_5_ans',
    'q10_2_age5p': 'TPT_termine_autres_plus_5_ans', 'q10_2_age_total': 'TPT_termine_autres_Tous_ages',
    'xpert_test_rate': 'Taux_test_Xpert', 'rrmdr_detection_rate': 'Taux_detection_RRMDR',
    'tpt_coverage': 'Couverture_TPT', 'tpt_completion_rate': "Taux_achevement_TPT",
    'tpt_eligible_total': 'TPT_Eligibles_Total', 'tpt_started_total': 'TPT_Commence_Total',
    'tpt_completed_total': 'TPT_Termine_Total', 'enfants_moins_5_depistes': 'Enfants_moins_5_ans_depistes',
    'enfants_moins_5_eligibles': 'Enfants_moins_5_ans_eligibles',
    'enfants_moins_5_commences': 'Enfants_moins_5_ans_TPT_commence',
    'enfants_moins_5_termines': 'Enfants_moins_5_ans_TPT_termine',
}

def get_readable_column_name(col):
    return COLUMN_RENAME_MAP.get(col, col)

def get_readable_columns(df):
    return df.rename(columns=COLUMN_RENAME_MAP)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Donnees')
    return output.getvalue()

# ============================================================================
# DICTIONNAIRE DES MÉDICAMENTS
# ============================================================================

MEDICAMENTS = {
    'RHZE adulte': {'prefix': 'rhze', 'nom': 'RHZE adulte (R=150mg, H=75mg, Z=400mg, E=275mg)', 'couleur': '#1f77b4'},
    'RH adulte': {'prefix': 'rh', 'nom': 'RH adulte (R=150mg, H=75mg)', 'couleur': '#ff7f0e'},
    'Rifapentine/Isoniazide': {'prefix': 'rifiso', 'nom': 'Rifapentine/Isoniazide (H=300mg, P=300mg)', 'couleur': '#2ca02c'},
    'RHZ enfant': {'prefix': 'rhz', 'nom': 'RHZ enfant (R=75mg, H=50mg, Z=150mg)', 'couleur': '#d62728'},
    'Bédaquilline': {'prefix': 'beda', 'nom': 'Bédaquilline (100mg)', 'couleur': '#9467bd'},
    'Lévofloxacine': {'prefix': 'levo', 'nom': 'Lévofloxacine (250mg)', 'couleur': '#8c564b'},
    'Prothionamide': {'prefix': 'prothio', 'nom': 'Prothionamide (250mg)', 'couleur': '#e377c2'},
    'Isoniazide': {'prefix': 'inh', 'nom': 'Isoniazide (300mg)', 'couleur': '#7f7f7f'},
    'Clofazimine 50mg': {'prefix': 'clofa50', 'nom': 'Clofazimine (50mg)', 'couleur': '#bcbd22'},
    'Clofazimine 100mg': {'prefix': 'clofa100', 'nom': 'Clofazimine (100mg)', 'couleur': '#17becf'},
    'Ethambutol': {'prefix': 'etham', 'nom': 'Ethambutol (400mg)', 'couleur': '#aec7e8'},
    'Pyrazinamide': {'prefix': 'pyra', 'nom': 'Pyrazinamide (400mg)', 'couleur': '#ffbb78'}
}

COLONNES_MEDICAMENTS = ['stock_initial', 'quantite_recue', 'stock_disponible', 
                        'quantite_consomme', 'stock_theorique', 'stock_physique',
                        'pertes_exp', 'jours_rupture', 'date_expiration']

# Types de niveaux pour la distribution
TYPES_NIVEAUX = ['National', 'CDR', 'Zone de Santé']

# ============================================================================
# DONNÉES DE RÉFÉRENCE POUR LA COMPLÉTUDE
# ============================================================================

ZS_CDT_REFERENCE = pd.DataFrame({
    'Province': [
        'Haut Katanga', 'Haut Lomami', 'Kasai Oriental', 'Kasai Central',
        'Lualaba', 'Lomami', 'Sud Kivu', 'Sankuru', 'Tanganyika'
    ],
    'ZS_attendues': [27, 16, 19, 26, 14, 16, 34, 16, 11],
    'CDT_attendus': [107, 74, 132, 109, 75, 106, 135, 93, 68]
})

DATE_LIMITE_JOUR = 7

# ============================================================================
# FONCTIONS DE TRAITEMENT DES DONNÉES
# ============================================================================

def clean_province_name(name):
    if pd.isna(name):
        return None
    name = str(name).strip()
    mapping = {
        'haut katanga': 'Haut Katanga', 'hautkatanga': 'Haut Katanga', 'katanga': 'Haut Katanga',
        'haut lomami': 'Haut Lomami', 'hautlomami': 'Haut Lomami', 'lomami': 'Lomami',
        'kasai oriental': 'Kasai Oriental', 'kasaioriental': 'Kasai Oriental',
        'kasai central': 'Kasai Central', 'kasaicentral': 'Kasai Central',
        'lualaba': 'Lualaba', 'sud kivu': 'Sud Kivu', 'sudkivu': 'Sud Kivu',
        'sankuru': 'Sankuru', 'tanganyika': 'Tanganyika'
    }
    name_clean = name.lower().strip()
    if name_clean in mapping:
        return mapping[name_clean]
    if ' ' in name:
        parts = name.split(' ', 1)
        if len(parts) == 2:
            code, nom = parts
            nom_clean = nom.lower().strip()
            if nom_clean in mapping:
                return mapping[nom_clean]
    if name in mapping.values():
        return name
    return name

def extraire_annee_num(annee):
    if pd.isna(annee):
        return None
    annee_str = str(annee).strip()
    match = re.search(r'(\d{4})', annee_str)
    if match:
        return int(match.group(1))
    return None

def safe_int_convert(value):
    try:
        if pd.isna(value) or np.isinf(value) or np.isnan(value):
            return 0
        return int(value)
    except (ValueError, TypeError):
        return 0

@st.cache_data
def load_and_process_data():
    df = pd.read_csv('drc_stop_tb_data.csv')
    
    if 'qannee' in df.columns:
        df['qannee_num'] = df['qannee'].apply(extraire_annee_num)
    
    if 'q010b' in df.columns:
        df['province_name_raw'] = df['q010b']
        df['province_name'] = df['q010b'].apply(clean_province_name)
    
    if 'q011b' in df.columns:
        df['healthzone_name'] = df['q011b']
    
    if 'q012b' in df.columns:
        df['facility_name'] = df['q012b']
    
    if 'q012a' in df.columns:
        df['facility_id'] = df['q012a']
    
    if 'q001a' in df.columns:
        df['date_saisie'] = pd.to_datetime(df['q001a'], format='%d/%m/%Y', errors='coerce')
        df['jour_soumission'] = df['date_saisie'].dt.day
        df['mois_soumission'] = df['date_saisie'].dt.month
        df['annee_soumission'] = df['date_saisie'].dt.year
        df['est_prompt'] = df['jour_soumission'] <= DATE_LIMITE_JOUR
        df['statut_promptitude'] = df['est_prompt'].map({True: 'À temps', False: 'En retard'})
    
    if 'qmois' in df.columns:
        mois_num = df['qmois'].str.extract(r'(\d+)')[0].astype(float)
        mois_num = mois_num.fillna(0)
        trimestre_calc = np.ceil(mois_num / 3)
        trimestre_calc = trimestre_calc.replace(0, np.nan)
        df['trimestre'] = trimestre_calc.astype('Int64')
        df['trimestre'] = df['trimestre'].map({1: 'T1', 2: 'T2', 3: 'T3', 4: 'T4'})
    
    colonnes_q = ['q1_0_h', 'q1_0_f', 'q1_0_age15m', 'q1_0_age15p', 'q1_0_niv_sante', 'q1_0_niv_com',
                  'q1_1_h', 'q1_1_f', 'q1_1_age15m', 'q1_1_age15p', 'q1_1_niv_sante', 'q1_1_niv_com',
                  'q1_2_h', 'q1_2_f', 'q1_2_age15m', 'q1_2_age15p', 'q1_2_niv_sante', 'q1_2_niv_com',
                  'q1_3_h', 'q1_3_f', 'q1_3_age15m', 'q1_3_age15p', 'q1_3_niv_sante', 'q1_3_niv_com',
                  'q1_4_h', 'q1_4_f', 'q1_4_age15m', 'q1_4_age15p',
                  'q1_5_h', 'q1_5_f', 'q1_5_age15m', 'q1_5_age15p',
                  'q2_0_h', 'q2_0_f', 'q2_0_age15m', 'q2_0_age15p',
                  'q2_1_h', 'q2_1_f', 'q2_1_age15m', 'q2_1_age15p',
                  'q2_2_h', 'q2_2_f', 'q2_2_age15m', 'q2_2_age15p',
                  'q3_0_h', 'q3_0_f', 'q3_0_age15m', 'q3_0_age15p',
                  'q3_4_g04', 'q3_4_g514', 'q3_4_h1524', 'q3_4_h2534', 'q3_4_h3544', 'q3_4_h4554', 'q3_4_h5564', 'q3_4_h65p',
                  'q3_4_f04', 'q3_4_f514', 'q3_4_f1524', 'q3_4_f2534', 'q3_4_f3544', 'q3_4_f4554', 'q3_4_f5564', 'q3_4_f65p',
                  'q4_0_h', 'q4_0_f', 'q4_0_age15m', 'q4_0_age15p',
                  'q4_1_h', 'q4_1_f', 'q4_1_age15m', 'q4_1_age15p',
                  'q5_0_h', 'q5_0_f', 'q5_0_age15m', 'q5_0_age15p',
                  'q6_0_h', 'q6_0_f', 'q6_0_age15m', 'q6_0_age15p',
                  'q7_0_h', 'q7_0_f', 'q7_0_age15m', 'q7_0_age15p',
                  'q8_0_h', 'q8_0_f', 'q8_0_age5m', 'q8_0_age5p',
                  'q8_1_h', 'q8_1_f', 'q8_1_age5m', 'q8_1_age5p',
                  'q8_2_h', 'q8_2_f', 'q8_2_age5m', 'q8_2_age5p',
                  'q8_3_h', 'q8_3_f', 'q8_3_age5m', 'q8_3_age5p',
                  'q8_4_h', 'q8_4_f', 'q8_4_age5m', 'q8_4_age5p',
                  'q8_5_h', 'q8_5_f', 'q8_5_age15m', 'q8_5_age15p',
                  'q8_6_h', 'q8_6_f', 'q8_6_age5m', 'q8_6_age5p',
                  'q9_1_h', 'q9_1_f', 'q9_1_age5m', 'q9_1_age5p',
                  'q9_2_h', 'q9_2_f', 'q9_2_age15m', 'q9_2_age15p',
                  'q9_3_h', 'q9_3_f', 'q9_3_age5m', 'q9_3_age5p',
                  'q10_0_h', 'q10_0_f', 'q10_0_age5m', 'q10_0_age5p',
                  'q10_1_h', 'q10_1_f', 'q10_1_age5m', 'q10_1_age5p',
                  'q10_2_h', 'q10_2_f', 'q10_2_age5m', 'q10_2_age5p']
    
    for col in colonnes_q:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    df['q1_0_hf_total'] = df['q1_0_h'] + df['q1_0_f']
    df['q1_0_age_total'] = df['q1_0_age15m'] + df['q1_0_age15p']
    df['q1_0_niv_total'] = df['q1_0_niv_sante'] + df['q1_0_niv_com']
    df['q1_1_hf_total'] = df['q1_1_h'] + df['q1_1_f']
    df['q1_1_age_total'] = df['q1_1_age15m'] + df['q1_1_age15p']
    df['q1_1_niv_total'] = df['q1_1_niv_sante'] + df['q1_1_niv_com']
    df['q1_2_hf_total'] = df['q1_2_h'] + df['q1_2_f']
    df['q1_2_age_total'] = df['q1_2_age15m'] + df['q1_2_age15p']
    df['q1_2_niv_total'] = df['q1_2_niv_sante'] + df['q1_2_niv_com']
    df['q1_3_hf_total'] = df['q1_3_h'] + df['q1_3_f']
    df['q1_3_age_total'] = df['q1_3_age15m'] + df['q1_3_age15p']
    df['q1_3_niv_total'] = df['q1_3_niv_sante'] + df['q1_3_niv_com']
    df['q1_4_hf_total'] = df['q1_4_h'] + df['q1_4_f']
    df['q1_4_age_total'] = df['q1_4_age15m'] + df['q1_4_age15p']
    df['q1_5_hf_total'] = df['q1_5_h'] + df['q1_5_f']
    df['q1_5_age_total'] = df['q1_5_age15m'] + df['q1_5_age15p']
    df['q2_0_hf_total'] = df['q2_0_h'] + df['q2_0_f']
    df['q2_0_age_total'] = df['q2_0_age15m'] + df['q2_0_age15p']
    df['q2_1_hf_total'] = df['q2_1_h'] + df['q2_1_f']
    df['q2_1_age_total'] = df['q2_1_age15m'] + df['q2_1_age15p']
    df['q2_2_hf_total'] = df['q2_2_h'] + df['q2_2_f']
    df['q2_2_age_total'] = df['q2_2_age15m'] + df['q2_2_age15p']
    df['q3_0_hf_total'] = df['q3_0_h'] + df['q3_0_f']
    df['q3_0_age_total'] = df['q3_0_age15m'] + df['q3_0_age15p']
    
    df['q3_4_h_total'] = (df['q3_4_g04'] + df['q3_4_g514'] + df['q3_4_h1524'] + 
                          df['q3_4_h2534'] + df['q3_4_h3544'] + df['q3_4_h4554'] + 
                          df['q3_4_h5564'] + df['q3_4_h65p'])
    df['q3_4_f_total'] = (df['q3_4_f04'] + df['q3_4_f514'] + df['q3_4_f1524'] + 
                          df['q3_4_f2534'] + df['q3_4_f3544'] + df['q3_4_f4554'] + 
                          df['q3_4_f5564'] + df['q3_4_f65p'])
    df['q3_4_hf_total'] = df['q3_4_h_total'] + df['q3_4_f_total']
    
    df['q4_0_hf_total'] = df['q4_0_h'] + df['q4_0_f']
    df['q4_0_age_total'] = df['q4_0_age15m'] + df['q4_0_age15p']
    df['q4_1_hf_total'] = df['q4_1_h'] + df['q4_1_f']
    df['q4_1_age_total'] = df['q4_1_age15m'] + df['q4_1_age15p']
    df['q5_0_hf_total'] = df['q5_0_h'] + df['q5_0_f']
    df['q5_0_age_total'] = df['q5_0_age15m'] + df['q5_0_age15p']
    df['q6_0_hf_total'] = df['q6_0_h'] + df['q6_0_f']
    df['q6_0_age_total'] = df['q6_0_age15m'] + df['q6_0_age15p']
    df['q7_0_hf_total'] = df['q7_0_h'] + df['q7_0_f']
    df['q7_0_age_total'] = df['q7_0_age15m'] + df['q7_0_age15p']
    df['q8_0_hf_total'] = df['q8_0_h'] + df['q8_0_f']
    df['q8_0_age_total'] = df['q8_0_age5m'] + df['q8_0_age5p']
    df['q8_1_hf_total'] = df['q8_1_h'] + df['q8_1_f']
    df['q8_1_age_total'] = df['q8_1_age5m'] + df['q8_1_age5p']
    df['q8_2_hf_total'] = df['q8_2_h'] + df['q8_2_f']
    df['q8_2_age_total'] = df['q8_2_age5m'] + df['q8_2_age5p']
    df['q8_3_hf_total'] = df['q8_3_h'] + df['q8_3_f']
    df['q8_3_age_total'] = df['q8_3_age5m'] + df['q8_3_age5p']
    df['q8_4_hf_total'] = df['q8_4_h'] + df['q8_4_f']
    df['q8_4_age_total'] = df['q8_4_age5m'] + df['q8_4_age5p']
    df['q8_5_hf_total'] = df['q8_5_h'] + df['q8_5_f']
    df['q8_5_age_total'] = df['q8_5_age15m'] + df['q8_5_age15p']
    df['q8_6_hf_total'] = df['q8_6_h'] + df['q8_6_f']
    df['q8_6_age_total'] = df['q8_6_age5m'] + df['q8_6_age5p']
    df['q9_1_hf_total'] = df['q9_1_h'] + df['q9_1_f']
    df['q9_1_age_total'] = df['q9_1_age5m'] + df['q9_1_age5p']
    df['q9_2_hf_total'] = df['q9_2_h'] + df['q9_2_f']
    df['q9_2_age_total'] = df['q9_2_age15m'] + df['q9_2_age15p']
    df['q9_3_hf_total'] = df['q9_3_h'] + df['q9_3_f']
    df['q9_3_age_total'] = df['q9_3_age5m'] + df['q9_3_age5p']
    df['q10_0_hf_total'] = df['q10_0_h'] + df['q10_0_f']
    df['q10_0_age_total'] = df['q10_0_age5m'] + df['q10_0_age5p']
    df['q10_1_hf_total'] = df['q10_1_h'] + df['q10_1_f']
    df['q10_1_age_total'] = df['q10_1_age5m'] + df['q10_1_age5p']
    df['q10_2_hf_total'] = df['q10_2_h'] + df['q10_2_f']
    df['q10_2_age_total'] = df['q10_2_age5m'] + df['q10_2_age5p']
    
    df['tpt_eligible_total'] = df['q8_4_hf_total'] + df['q8_5_hf_total'] + df['q8_6_hf_total']
    df['tpt_started_total'] = df['q9_1_hf_total'] + df['q9_2_hf_total'] + df['q9_3_hf_total']
    df['tpt_completed_total'] = df['q10_0_hf_total'] + df['q10_1_hf_total'] + df['q10_2_hf_total']
    
    df['enfants_moins_5_depistes'] = df['q8_0_age5m']
    df['enfants_moins_5_eligibles'] = df['q8_4_age5m']
    df['enfants_moins_5_commences'] = df['q9_1_age5m']
    df['enfants_moins_5_termines'] = df['q10_0_age5m']
    
    df['xpert_test_rate'] = np.where(df['q1_4_hf_total'] > 0, 
                                      df['q1_5_hf_total'] / df['q1_4_hf_total'] * 100, 0)
    df['rrmdr_detection_rate'] = np.where(df['q4_0_hf_total'] > 0,
                                           df['q4_1_hf_total'] / df['q4_0_hf_total'] * 100, 0)
    df['tpt_coverage'] = np.where(df['tpt_eligible_total'] > 0,
                                  df['tpt_started_total'] / df['tpt_eligible_total'] * 100, 0)
    df['tpt_completion_rate'] = np.where(df['tpt_started_total'] > 0,
                                         df['tpt_completed_total'] / df['tpt_started_total'] * 100, 0)
    
    mois_map = {
        'mois_1': 'Janvier', 'mois_2': 'Février', 'mois_3': 'Mars',
        'mois_4': 'Avril', 'mois_5': 'Mai', 'mois_6': 'Juin',
        'mois_7': 'Juillet', 'mois_8': 'Août', 'mois_9': 'Septembre',
        'mois_10': 'Octobre', 'mois_11': 'Novembre', 'mois_12': 'Décembre'
    }
    if 'qmois' in df.columns:
        df['mois_nom'] = df['qmois'].map(mois_map)
    
    df = df[df['province_name'].notna()]
    
    for medicament, info in MEDICAMENTS.items():
        prefix = info['prefix']
        for col in COLONNES_MEDICAMENTS:
            nom_col = f"{prefix}_{col}"
            if nom_col in df.columns:
                df[nom_col] = pd.to_numeric(df[nom_col], errors='coerce').fillna(0)
                if 'date' in col:
                    df[nom_col] = pd.to_datetime(df[nom_col], errors='coerce')
    
    return df

def filter_by_hierarchy(df, niveau, province=None, facility=None, zone_sante=None):
    if niveau == 'National':
        return df
    elif niveau == 'Provincial' and province and province != 'Toutes':
        return df[df['province_name'] == province]
    elif niveau == 'Provincial' and province == 'Toutes':
        return df
    elif niveau == 'Zone Sante' and zone_sante and zone_sante != 'Toutes':
        return df[df['healthzone_name'] == zone_sante]
    elif niveau == 'Zone Sante' and zone_sante == 'Toutes':
        return df
    elif niveau == 'Etablissement' and facility and facility != 'Tous':
        return df[df['facility_name'] == facility]
    elif niveau == 'Etablissement' and facility == 'Tous':
        return df
    return df

def get_previous_period_df(df, type_periode, mois_selectionne=None, annee_selectionne=None, 
                            trimestre_selectionne=None):
    df_previous = df.copy()
    annee_num = extraire_annee_num(annee_selectionne)
    
    if annee_num is None:
        return pd.DataFrame()
    
    if 'qannee_num' not in df_previous.columns:
        df_previous['qannee_num'] = df_previous['qannee'].apply(extraire_annee_num)
    
    if type_periode == 'Mois' and mois_selectionne:
        mois_map = {
            'Janvier': 1, 'Février': 2, 'Mars': 3, 'Avril': 4, 'Mai': 5, 'Juin': 6,
            'Juillet': 7, 'Août': 8, 'Septembre': 9, 'Octobre': 10, 'Novembre': 11, 'Décembre': 12
        }
        mois_inverse = {v: k for k, v in mois_map.items()}
        mois_num = mois_map.get(mois_selectionne, 1)
        
        if mois_num == 1:
            mois_precedent_num = 12
            annee_precedente = annee_num - 1
        else:
            mois_precedent_num = mois_num - 1
            annee_precedente = annee_num
        
        mois_precedent_nom = mois_inverse.get(mois_precedent_num, 'Janvier')
        
        df_previous = df_previous[
            (df_previous['mois_nom'] == mois_precedent_nom) & 
            (df_previous['qannee_num'] == annee_precedente)
        ]
    
    elif type_periode == 'Trimestre' and trimestre_selectionne:
        trimestre_num = int(trimestre_selectionne.replace('T', ''))
        
        if trimestre_num == 1:
            trimestre_precedent = 4
            annee_precedente = annee_num - 1
        else:
            trimestre_precedent = trimestre_num - 1
            annee_precedente = annee_num
        
        df_previous = df_previous[
            (df_previous['trimestre'] == f'T{trimestre_precedent}') & 
            (df_previous['qannee_num'] == annee_precedente)
        ]
    
    return df_previous

# ============================================================================
# FONCTIONS DE VISUALISATION
# ============================================================================

def show_kpi_cards(df_filtered, niveau, df_previous=None, type_periode=None):
    if niveau == 'National':
        st.markdown('<div class="national-badge">🌍 NIVEAU NATIONAL</div>', unsafe_allow_html=True)
    elif niveau == 'Provincial':
        st.markdown('<div class="provincial-badge">📍 NIVEAU PROVINCIAL</div>', unsafe_allow_html=True)
    elif niveau == 'Zone Sante':
        st.markdown('<div class="zs-badge">🏥 NIVEAU ZONE DE SANTÉ</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="facility-badge">🏥 NIVEAU ÉTABLISSEMENT</div>', unsafe_allow_html=True)
    
    if df_previous is None:
        df_previous = pd.DataFrame()
    
    if type_periode == 'Mois':
        label_precedent = "vs mois précédent"
    elif type_periode == 'Trimestre':
        label_precedent = "vs trimestre précédent"
    else:
        label_precedent = "vs période précédente"
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        val_actuelle = df_filtered['q1_0_hf_total'].sum()
        val_precedente = df_previous['q1_0_hf_total'].sum() if len(df_previous) > 0 and 'q1_0_hf_total' in df_previous.columns else 0
        if val_precedente > 0:
            pct = ((val_actuelle - val_precedente) / val_precedente) * 100
            delta_text = f"{pct:+.1f}% {label_precedent}"
        elif val_actuelle > 0:
            delta_text = "Nouveau (0 avant)"
        else:
            delta_text = "Aucune donnée"
        st.metric("👥 Personnes dépistées", f"{val_actuelle:,.0f}", delta=delta_text)
        st.caption(f"📅 Préc. : **{val_precedente:,.0f}**")
    
    with col2:
        val_actuelle = df_filtered['q1_2_hf_total'].sum()
        val_precedente = df_previous['q1_2_hf_total'].sum() if len(df_previous) > 0 and 'q1_2_hf_total' in df_previous.columns else 0
        if val_precedente > 0:
            pct = ((val_actuelle - val_precedente) / val_precedente) * 100
            delta_text = f"{pct:+.1f}% {label_precedent}"
        elif val_actuelle > 0:
            delta_text = "Nouveau (0 avant)"
        else:
            delta_text = "Aucune donnée"
        st.metric("🔬 Cas présumés", f"{val_actuelle:,.0f}", delta=delta_text)
        st.caption(f"📅 Préc. : **{val_precedente:,.0f}**")
    
    with col3:
        val_actuelle = df_filtered['q1_5_hf_total'].sum()
        val_precedente = df_previous['q1_5_hf_total'].sum() if len(df_previous) > 0 and 'q1_5_hf_total' in df_previous.columns else 0
        if val_precedente > 0:
            pct = ((val_actuelle - val_precedente) / val_precedente) * 100
            delta_text = f"{pct:+.1f}% {label_precedent}"
        elif val_actuelle > 0:
            delta_text = "Nouveau (0 avant)"
        else:
            delta_text = "Aucune donnée"
        st.metric("🧪 Testés Xpert", f"{val_actuelle:,.0f}", delta=delta_text)
        st.caption(f"📅 Préc. : **{val_precedente:,.0f}**")
    
    with col4:
        val_actuelle = df_filtered['q2_0_hf_total'].sum()
        val_precedente = df_previous['q2_0_hf_total'].sum() if len(df_previous) > 0 and 'q2_0_hf_total' in df_previous.columns else 0
        if val_precedente > 0:
            pct = ((val_actuelle - val_precedente) / val_precedente) * 100
            delta_text = f"{pct:+.1f}% {label_precedent}"
        elif val_actuelle > 0:
            delta_text = "Nouveau (0 avant)"
        else:
            delta_text = "Aucune donnée"
        st.metric("🦠 TB détectée", f"{val_actuelle:,.0f}", delta=delta_text, delta_color="inverse")
        st.caption(f"📅 Préc. : **{val_precedente:,.0f}**")
    
    with col5:
        val_actuelle = df_filtered['q3_0_hf_total'].sum()
        val_precedente = df_previous['q3_0_hf_total'].sum() if len(df_previous) > 0 and 'q3_0_hf_total' in df_previous.columns else 0
        if val_precedente > 0:
            pct = ((val_actuelle - val_precedente) / val_precedente) * 100
            delta_text = f"{pct:+.1f}% {label_precedent}"
        elif val_actuelle > 0:
            delta_text = "Nouveau (0 avant)"
        else:
            delta_text = "Aucune donnée"
        st.metric("💊 Traitements DS débutés", f"{val_actuelle:,.0f}", delta=delta_text)
        st.caption(f"📅 Préc. : **{val_precedente:,.0f}**")
    
    with col6:
        val_actuelle = df_filtered['tpt_coverage'].mean() if len(df_filtered) > 0 else 0
        val_precedente = df_previous['tpt_coverage'].mean() if len(df_previous) > 0 and 'tpt_coverage' in df_previous.columns else 0
        if val_precedente > 0:
            pct = ((val_actuelle - val_precedente) / val_precedente) * 100
            delta_text = f"{pct:+.1f}% {label_precedent}"
        elif val_actuelle > 0:
            delta_text = "Nouveau (0 avant)"
        else:
            delta_text = "Aucune donnée"
        st.metric("🛡️ Couverture TPT", f"{val_actuelle:.1f}%", delta=delta_text)
        st.caption(f"📅 Préc. : **{val_precedente:.1f}%**")


def show_depistage_tab(df_filtered):
    st.subheader("📈 Cascade de dépistage et diagnostic")
    
    cascade_data = pd.DataFrame({
        'Étape': ['Personnes dépistées', 'Cas présumés TB', 'Testés (Xpert)', 'TB détectée', 'TB confirmée bactério'],
        'Nombre': [
            df_filtered['q1_0_hf_total'].sum(),
            df_filtered['q1_2_hf_total'].sum(),
            df_filtered['q1_5_hf_total'].sum(),
            df_filtered['q2_0_hf_total'].sum(),
            df_filtered['q2_2_hf_total'].sum()
        ]
    })
    
    fig_cascade = px.funnel(cascade_data, x='Nombre', y='Étape', 
                             title="Cascade des patients TB",
                             color_discrete_sequence=['#1f77b4'])
    fig_cascade.update_traces(textposition="inside", textinfo="value+percent previous")
    st.plotly_chart(fig_cascade, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Répartition par sexe - Dépistage")
        sexe_data = pd.DataFrame({
            'Sexe': ['Hommes', 'Femmes'],
            'Dépistés': [df_filtered['q1_0_h'].sum(), df_filtered['q1_0_f'].sum()],
            'Présumés': [df_filtered['q1_2_h'].sum(), df_filtered['q1_2_f'].sum()],
            'Détectés': [df_filtered['q2_0_h'].sum(), df_filtered['q2_0_f'].sum()]
        })
        sexe_melted = sexe_data.melt(id_vars=['Sexe'], var_name='Catégorie', value_name='Nombre')
        fig_sexe = px.bar(sexe_melted, x='Catégorie', y='Nombre', color='Sexe', 
                          barmode='group', title="Distribution par sexe")
        st.plotly_chart(fig_sexe, use_container_width=True)
    
    with col2:
        st.subheader("Répartition par âge")
        age_data = pd.DataFrame({
            'Âge': ['≤ 15 ans', '> 15 ans'],
            'Dépistés': [df_filtered['q1_0_age15m'].sum(), df_filtered['q1_0_age15p'].sum()],
            'Présumés': [df_filtered['q1_2_age15m'].sum(), df_filtered['q1_2_age15p'].sum()],
            'Détectés': [df_filtered['q2_0_age15m'].sum(), df_filtered['q2_0_age15p'].sum()]
        })
        age_melted = age_data.melt(id_vars=['Âge'], var_name='Catégorie', value_name='Nombre')
        fig_age = px.bar(age_melted, x='Catégorie', y='Nombre', color='Âge', 
                         barmode='group', title="Distribution par âge")
        st.plotly_chart(fig_age, use_container_width=True)
    
    st.subheader("🧬 Détection de la tuberculose résistante (RR/MDR)")
    col3, col4 = st.columns(2)
    
    with col3:
        rr_data = pd.DataFrame({
            'Indicateur': ['Testés pour résistance', 'Diagnostiqués RR/MDR'],
            'Nombre': [df_filtered['q4_0_hf_total'].sum(), df_filtered['q4_1_hf_total'].sum()]
        })
        fig_rr = px.bar(rr_data, x='Indicateur', y='Nombre', 
                        color='Indicateur', title="Test de résistance à la Rifampicine")
        st.plotly_chart(fig_rr, use_container_width=True)
    
    with col4:
        taux_rr = df_filtered['rrmdr_detection_rate'].mean()
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_rr,
            title={'text': "Taux de détection RR/MDR (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#1f77b4"},
                   'steps': [
                       {'range': [0, 50], 'color': "lightgray"},
                       {'range': [50, 80], 'color': "gray"},
                       {'range': [80, 100], 'color': "darkgray"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                                 'thickness': 0.75, 'value': 90}}))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)


def show_traitement_tab(df_filtered):
    st.subheader("💊 Résultats du traitement")
    st.info("ℹ️ **Note importante :** Les taux de succès des traitements DS-TB et RR/MDR nécessitent un suivi de cohorte respectivement sur 12 et 24 mois.")
    
    st.markdown("### Tuberculose sensible (DS-TB)")
    col1, col2 = st.columns(2)
    
    with col1:
        ds_data = pd.DataFrame({
            'Statut': ['Traitement débuté', 'Traitement réussi'],
            'Hommes': [df_filtered['q3_0_h'].sum(), df_filtered['q6_0_h'].sum()],
            'Femmes': [df_filtered['q3_0_f'].sum(), df_filtered['q6_0_f'].sum()]
        })
        ds_melted = ds_data.melt(id_vars=['Statut'], var_name='Sexe', value_name='Nombre')
        fig_ds = px.bar(ds_melted, x='Statut', y='Nombre', color='Sexe', 
                        barmode='group', title="Traitement DS-TB par sexe")
        st.plotly_chart(fig_ds, use_container_width=True)
    
    with col2:
        total_debutes = df_filtered['q3_0_hf_total'].sum()
        total_reussis = df_filtered['q6_0_hf_total'].sum()
        st.metric("📊 Total traitements DS-TB débutés", f"{int(total_debutes):,}")
        st.metric("✅ Traitements DS-TB réussis", f"{int(total_reussis):,}")
        st.caption("💡 Le taux de succès DS-TB se calcule sur une cohorte suivie 12 mois.")
    
    st.markdown("### Tuberculose résistante (RR/MDR)")
    col3, col4 = st.columns(2)
    
    with col3:
        rr_data_tx = pd.DataFrame({
            'Statut': ['Traitement débuté', 'Traitement réussi'],
            'Hommes': [df_filtered['q5_0_h'].sum(), df_filtered['q7_0_h'].sum()],
            'Femmes': [df_filtered['q5_0_f'].sum(), df_filtered['q7_0_f'].sum()]
        })
        rr_melted = rr_data_tx.melt(id_vars=['Statut'], var_name='Sexe', value_name='Nombre')
        fig_rr_tx = px.bar(rr_melted, x='Statut', y='Nombre', color='Sexe', 
                           barmode='group', title="Traitement RR/MDR par sexe")
        st.plotly_chart(fig_rr_tx, use_container_width=True)
    
    with col4:
        total_debutes_rr = df_filtered['q5_0_hf_total'].sum()
        total_reussis_rr = df_filtered['q7_0_hf_total'].sum()
        st.metric("📊 Total traitements RR/MDR débutés", f"{int(total_debutes_rr):,}")
        st.metric("✅ Traitements RR/MDR réussis", f"{int(total_reussis_rr):,}")
        st.caption("💡 Le taux de succès RR/MDR se calcule sur une cohorte suivie 24 mois.")
    
    st.subheader("📊 Nouveaux cas et rechutes par âge et sexe")
    
    age_categories = ['0-4', '5-14', '15-24', '25-34', '35-44', '45-54', '55-64', '≥65']
    
    hommes_data = [
        df_filtered['q3_4_g04'].sum(), df_filtered['q3_4_g514'].sum(),
        df_filtered['q3_4_h1524'].sum(), df_filtered['q3_4_h2534'].sum(),
        df_filtered['q3_4_h3544'].sum(), df_filtered['q3_4_h4554'].sum(),
        df_filtered['q3_4_h5564'].sum(), df_filtered['q3_4_h65p'].sum()
    ]
    
    femmes_data = [
        df_filtered['q3_4_f04'].sum(), df_filtered['q3_4_f514'].sum(),
        df_filtered['q3_4_f1524'].sum(), df_filtered['q3_4_f2534'].sum(),
        df_filtered['q3_4_f3544'].sum(), df_filtered['q3_4_f4554'].sum(),
        df_filtered['q3_4_f5564'].sum(), df_filtered['q3_4_f65p'].sum()
    ]
    
    age_df = pd.DataFrame({
        'Tranche d\'âge': age_categories,
        'Hommes': hommes_data,
        'Femmes': femmes_data
    })
    
    fig_age_detailed = px.bar(age_df, x='Tranche d\'âge', y=['Hommes', 'Femmes'],
                               barmode='group', title="Distribution détaillée par âge et sexe",
                               color_discrete_sequence=['#1f77b4', '#ff7f0e'])
    st.plotly_chart(fig_age_detailed, use_container_width=True)


def show_prevention_tab(df_filtered):
    st.subheader("🛡️ Traitement Préventif à la Tuberculose (TPT)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Dépistés TPT", f"{df_filtered['q8_0_hf_total'].sum():,.0f}")
    with col2:
        st.metric("Éligibles TPT", f"{df_filtered['tpt_eligible_total'].sum():,.0f}")
    with col3:
        st.metric("Ont commencé", f"{df_filtered['tpt_started_total'].sum():,.0f}")
    with col4:
        st.metric("Ont terminé", f"{df_filtered['tpt_completed_total'].sum():,.0f}")
    with col5:
        tpt_cov = df_filtered['tpt_coverage'].mean()
        st.metric("Couverture", f"{tpt_cov:.1f}%")
    
    st.markdown("### 👶 Focus : Enfants de moins de 5 ans")
    
    enfants_data = {
        'Dépistés': df_filtered['enfants_moins_5_depistes'].sum(),
        'Éligibles': df_filtered['enfants_moins_5_eligibles'].sum(),
        'TPT commencé': df_filtered['enfants_moins_5_commences'].sum(),
        'TPT terminé': df_filtered['enfants_moins_5_termines'].sum()
    }
    
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
        st.metric("👶 Enfants <5 ans dépistés", f"{enfants_data['Dépistés']:,.0f}")
    with col_e2:
        st.metric("✅ Enfants <5 ans éligibles", f"{enfants_data['Éligibles']:,.0f}")
    with col_e3:
        st.metric("💊 Enfants <5 ans ont commencé", f"{enfants_data['TPT commencé']:,.0f}")
    with col_e4:
        st.metric("🏁 Enfants <5 ans ont terminé", f"{enfants_data['TPT terminé']:,.0f}")
    
    enfants_df = pd.DataFrame({
        'Étape': ['Dépistés', 'Éligibles', 'TPT commencé', 'TPT terminé'],
        'Nombre': list(enfants_data.values())
    })
    fig_enfants = px.bar(enfants_df, x='Étape', y='Nombre', 
                         title="Cascade TPT pour les enfants de moins de 5 ans",
                         color='Étape', text='Nombre')
    fig_enfants.update_traces(textposition='outside')
    st.plotly_chart(fig_enfants, use_container_width=True)
    
    st.subheader("📊 TPT par groupe cible")
    
    tpt_flow = pd.DataFrame({
        'Groupe cible': ['Contacts (dont <5 ans)', 'PVVIH', 'Autres groupes'],
        'Dépistés': [
            df_filtered['q8_0_hf_total'].sum(),
            df_filtered['q8_2_hf_total'].sum(),
            df_filtered['q8_3_hf_total'].sum()
        ],
        'Éligibles': [
            df_filtered['q8_4_hf_total'].sum(),
            df_filtered['q8_5_hf_total'].sum(),
            df_filtered['q8_6_hf_total'].sum()
        ],
        'Ont commencé': [
            df_filtered['q9_1_hf_total'].sum(),
            df_filtered['q9_2_hf_total'].sum(),
            df_filtered['q9_3_hf_total'].sum()
        ],
        'Ont terminé': [
            df_filtered['q10_0_hf_total'].sum(),
            df_filtered['q10_1_hf_total'].sum(),
            df_filtered['q10_2_hf_total'].sum()
        ]
    })
    
    tpt_flow_melted = tpt_flow.melt(id_vars=['Groupe cible'], var_name='Étape', value_name='Nombre')
    fig_tpt_flow = px.bar(tpt_flow_melted, x='Groupe cible', y='Nombre', color='Étape',
                          barmode='group', title="Cascade TPT par groupe cible")
    st.plotly_chart(fig_tpt_flow, use_container_width=True)
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        fig_tpt_cov = go.Figure(go.Indicator(
            mode="gauge+number",
            value=df_filtered['tpt_coverage'].mean(),
            title={'text': "Couverture TPT (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#17becf"}}))
        fig_tpt_cov.update_layout(height=300)
        st.plotly_chart(fig_tpt_cov, use_container_width=True)
    
    with col_c2:
        fig_tpt_comp = go.Figure(go.Indicator(
            mode="gauge+number",
            value=df_filtered['tpt_completion_rate'].mean(),
            title={'text': "Taux d'achèvement TPT (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#2ca02c"}}))
        fig_tpt_comp.update_layout(height=300)
        st.plotly_chart(fig_tpt_comp, use_container_width=True)


# ============================================================================
# FONCTIONS DISTRIBUTION MÉDICAMENTS
# ============================================================================

def get_semaines_annee(annee):
    """Génère les semaines d'une année"""
    semaines = []
    for i in range(1, 53):
        try:
            # Semaine ISO
            lundi = pd.Timestamp.fromisocalendar(annee, i, 1)
            dimanche = lundi + pd.Timedelta(days=6)
            semaines.append({
                'numero': i,
                'debut': lundi,
                'fin': dimanche,
                'label': f"S{i:02d} ({lundi.strftime('%d/%m')} - {dimanche.strftime('%d/%m')})"
            })
        except:
            pass
    return semaines


def load_distribution_data():
    """Charge les données de distribution des médicaments"""
    try:
        df_dist = pd.read_csv('distribution_medicaments.csv')
        df_dist['date_saisie'] = pd.to_datetime(df_dist['date_saisie'], errors='coerce')
        df_dist['semaine_num'] = df_dist['date_saisie'].dt.isocalendar().week
        df_dist['annee'] = df_dist['date_saisie'].dt.isocalendar().year
        df_dist['mois_annee'] = df_dist['date_saisie'].dt.strftime('%Y-%m')
        
        for col in ['quantite_prevue', 'quantite_expediee', 'quantite_recue']:
            if col in df_dist.columns:
                df_dist[col] = pd.to_numeric(df_dist[col], errors='coerce').fillna(0)
        
        return df_dist
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'date_saisie', 'semaine', 'type_niveau', 'medicament', 'code_entite',
            'nom_entite', 'quantite_prevue', 'quantite_expediee', 'quantite_recue',
            'observations', 'semaine_num', 'annee', 'mois_annee'
        ])


def save_distribution_data(df_dist):
    """Sauvegarde les données de distribution"""
    df_to_save = df_dist.drop(columns=['semaine_num', 'annee', 'mois_annee'], errors='ignore')
    df_to_save.to_csv('distribution_medicaments.csv', index=False)


def show_medicaments_tab(df_filtered):
    """Onglet Gestion des Médicaments - Version avec suivi de distribution"""
    st.subheader("💊 Gestion des stocks de médicaments")
    
    medicaments_presents = []
    for medicament, info in MEDICAMENTS.items():
        prefix = info['prefix']
        if f"{prefix}_stock_disponible" in df_filtered.columns:
            medicaments_presents.append(medicament)
    
    if not medicaments_presents:
        st.warning("⚠️ Aucune donnée de médicaments trouvée dans le fichier.")
        return
    
    # ===== TABLEAU DES STOCKS (KPI et alertes supprimés) =====
    st.markdown("### 📋 État des stocks par médicament")
    
    data_stocks = []
    total_cdts = len(df_filtered)
    
    for medicament in medicaments_presents:
        prefix = MEDICAMENTS[medicament]['prefix']
        row = {'Médicament': medicament}
        
        col_mapping = {
            'stock_initial': 'Stock Initial',
            'quantite_recue': 'Quantité Reçue',
            'stock_disponible': 'Stock Disponible',
            'quantite_consomme': 'Quantité Consommée',
            'stock_theorique': 'Stock Théorique',
            'stock_physique': 'Stock Physique',
            'pertes_exp': 'Pertes Exp',
            'jours_rupture': 'Jours Rupture (moyenne)',
            'date_expiration': 'Date Expiration'
        }
        
        for col_key, col_display in col_mapping.items():
            nom_col = f"{prefix}_{col_key}"
            if nom_col in df_filtered.columns:
                if 'date' in col_key:
                    dates = df_filtered[nom_col].dropna()
                    if len(dates) > 0:
                        row[col_display] = dates.max().strftime('%d/%m/%Y')
                    else:
                        row[col_display] = '-'
                elif 'jours_rupture' in col_key:
                    valeurs = df_filtered[nom_col]
                    valeurs_positives = valeurs[valeurs > 0]
                    if len(valeurs_positives) > 0:
                        moyenne = valeurs_positives.mean()
                        row[col_display] = round(moyenne, 1) if moyenne > 0 else 0
                    else:
                        row[col_display] = 0
                else:
                    val = df_filtered[nom_col].sum()
                    row[col_display] = int(val) if val > 0 else 0
            else:
                row[col_display] = '-'
        
        jours_rupture_col = f"{prefix}_jours_rupture"
        nb_cdt_rupture = 0
        if jours_rupture_col in df_filtered.columns:
            nb_cdt_rupture = (df_filtered[jours_rupture_col] > 0).sum()
        
        row['Nb CDT en rupture'] = nb_cdt_rupture
        
        if total_cdts > 0:
            taux_rupture = (nb_cdt_rupture / total_cdts) * 100
            row['Taux de rupture (%)'] = round(taux_rupture, 1)
        else:
            row['Taux de rupture (%)'] = 0
        
        if nb_cdt_rupture > 0:
            if nb_cdt_rupture > total_cdts * 0.5:
                row['Statut'] = '🔴 Crise'
            elif nb_cdt_rupture > total_cdts * 0.2:
                row['Statut'] = '🟠 Risque élevé'
            else:
                row['Statut'] = '🟡 Rupture partielle'
        else:
            row['Statut'] = '🟢 Stock OK'
        
        date_exp = row.get('Date Expiration', '-')
        if date_exp != '-' and date_exp != 0:
            try:
                date_obj = pd.to_datetime(date_exp, format='%d/%m/%Y')
                jours_restants = (date_obj - pd.Timestamp.now()).days
                if 0 < jours_restants < 180:
                    row['Statut'] = '🔵 Expiration proche'
                elif jours_restants <= 0:
                    row['Statut'] = '🔴 Expiré'
            except:
                pass
        
        data_stocks.append(row)
    
    df_stocks = pd.DataFrame(data_stocks)
    
    colonnes_ordre = ['Médicament', 'Stock Initial', 'Quantité Reçue', 'Stock Disponible', 
                      'Quantité Consommée', 'Stock Théorique', 'Stock Physique', 
                      'Pertes Exp', 'Jours Rupture (moyenne)', 'Nb CDT en rupture', 
                      'Taux de rupture (%)', 'Date Expiration', 'Statut']
    colonnes_existantes = [col for col in colonnes_ordre if col in df_stocks.columns]
    df_stocks_display = df_stocks[colonnes_existantes]
    
    st.dataframe(df_stocks_display, use_container_width=True, height=400)
    
    col_export1, col_export2 = st.columns(2)
    with col_export1:
        st.download_button(
            label="📥 Télécharger les stocks (CSV)",
            data=df_stocks_display.to_csv(index=False).encode('utf-8'),
            file_name=f"stocks_medicaments_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with col_export2:
        st.download_button(
            label="📥 Télécharger les stocks (Excel)",
            data=to_excel(df_stocks_display),
            file_name=f"stocks_medicaments_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    st.subheader("📊 Visualisation des stocks")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        df_graph = df_stocks[df_stocks['Stock Disponible'] != '-'].copy()
        if len(df_graph) > 0:
            df_graph['Stock Disponible'] = pd.to_numeric(df_graph['Stock Disponible'], errors='coerce')
            df_graph = df_graph[df_graph['Stock Disponible'] > 0]
            
            if len(df_graph) > 0:
                fig_stock = px.bar(
                    df_graph, x='Médicament', y='Stock Disponible',
                    title='Stock disponible par médicament',
                    color='Stock Disponible', color_continuous_scale='Blues',
                    text='Stock Disponible'
                )
                fig_stock.update_traces(textposition='outside')
                fig_stock.update_layout(xaxis_tickangle=45, height=400)
                st.plotly_chart(fig_stock, use_container_width=True)
            else:
                st.info("Aucun stock disponible à afficher")
    
    with col_g2:
        if 'Nb CDT en rupture' in df_stocks.columns:
            df_rupture_cdt = df_stocks[df_stocks['Nb CDT en rupture'] > 0].copy()
            if len(df_rupture_cdt) > 0:
                fig_rupture_cdt = px.bar(
                    df_rupture_cdt, x='Médicament', y='Nb CDT en rupture',
                    title='Nombre de CDT avec rupture de stock',
                    color='Nb CDT en rupture', color_continuous_scale='Reds',
                    text='Nb CDT en rupture'
                )
                fig_rupture_cdt.update_traces(textposition='outside')
                fig_rupture_cdt.update_layout(xaxis_tickangle=45, height=400)
                st.plotly_chart(fig_rupture_cdt, use_container_width=True)
            else:
                st.success("✅ Aucun CDT en rupture de stock")
    
    # ============================================================
    # SECTION DISTRIBUTION (remplace les Alertes stock)
    # ============================================================
    st.markdown("---")
    st.subheader("📤 Suivi de distribution des médicaments")
    st.markdown("**Suivi hebdomadaire** de la distribution : National → CDR → Zone de Santé")
    
    df_dist = load_distribution_data()
    
    # ===== FORMULAIRE DE SAISIE =====
    with st.expander("📝 **Ajouter / Modifier une entrée de distribution**", expanded=False):
        with st.form("form_distribution", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélection de l'année
                annee_courante = datetime.now().year
                annee_options = [annee_courante - 1, annee_courante, annee_courante + 1]
                annee_dist = st.selectbox("📅 Année", options=annee_options, index=1, key="annee_dist")
                
                # Générer les semaines pour l'année
                semaines = get_semaines_annee(annee_dist)
                semaine_options = [s['label'] for s in semaines]
                
                # Sélectionner la semaine actuelle par défaut
                semaine_actuelle = datetime.now().isocalendar()[1]
                index_defaut = min(semaine_actuelle - 1, len(semaine_options) - 1) if semaine_actuelle > 0 else 0
                
                semaine_label = st.selectbox("📆 Semaine", options=semaine_options, index=index_defaut, key="semaine_dist")
                semaine_idx = semaine_options.index(semaine_label)
                semaine_selectionnee = semaines[semaine_idx]
                
                date_saisie = semaine_selectionnee['fin']
                
                type_niveau = st.selectbox(
                    "🏢 Niveau de distribution",
                    options=TYPES_NIVEAUX,
                    help="National : envoi vers CDR | CDR : réception ou redistribution vers ZS | Zone de Santé : réception"
                )
                
                medicament_dist = st.selectbox(
                    "💊 Médicament",
                    options=list(MEDICAMENTS.keys()),
                    key="med_dist"
                )
            
            with col2:
                code_entite = st.text_input(
                    "🔢 Code entité",
                    value="",
                    placeholder="Ex: CDR-001, ZS-012, NAT",
                    help="Code unique de l'entité (optionnel)"
                )
                
                nom_entite = st.text_input(
                    "🏥 Nom de l'entité",
                    value="",
                    placeholder="Ex: CDR Kinshasa, ZS Bandalungwa, National",
                    help="Nom de l'entité concernée"
                )
                
                quantite_prevue = st.number_input(
                    "📋 Quantité prévue",
                    min_value=0,
                    value=0,
                    step=100,
                    help="Quantité prévue à expédier/recevoir"
                )
                
                quantite_expediee = st.number_input(
                    "📤 Quantité expédiée",
                    min_value=0,
                    value=0,
                    step=100,
                    help="Quantité réellement expédiée"
                )
                
                quantite_recue = st.number_input(
                    "📥 Quantité reçue",
                    min_value=0,
                    value=0,
                    step=100,
                    help="Quantité réellement reçue"
                )
            
            observations = st.text_area("📝 Observations", value="", height=80)
            
            submitted = st.form_submit_button("✅ Enregistrer l'entrée", use_container_width=True)
            
            if submitted:
                if not nom_entite:
                    st.error("⚠️ Veuillez renseigner le nom de l'entité.")
                else:
                    nouvelle_entree = {
                        'date_saisie': pd.to_datetime(date_saisie),
                        'semaine': semaine_label,
                        'type_niveau': type_niveau,
                        'medicament': medicament_dist,
                        'code_entite': code_entite if code_entite else '-',
                        'nom_entite': nom_entite,
                        'quantite_prevue': quantite_prevue,
                        'quantite_expediee': quantite_expediee,
                        'quantite_recue': quantite_recue,
                        'observations': observations
                    }
                    
                    df_dist = pd.concat([df_dist, pd.DataFrame([nouvelle_entree])], ignore_index=True)
                    df_dist['date_saisie'] = pd.to_datetime(df_dist['date_saisie'], errors='coerce')
                    df_dist['semaine_num'] = df_dist['date_saisie'].dt.isocalendar().week
                    df_dist['annee'] = df_dist['date_saisie'].dt.isocalendar().year
                    df_dist['mois_annee'] = df_dist['date_saisie'].dt.strftime('%Y-%m')
                    df_dist = df_dist.sort_values('date_saisie').reset_index(drop=True)
                    
                    save_distribution_data(df_dist)
                    st.success(f"✅ Entrée de distribution ajoutée pour {nom_entite} ({semaine_label}) !")
                    st.rerun()
    
    if len(df_dist) == 0:
        st.info("📋 Aucune donnée de distribution n'est encore enregistrée. Utilisez le formulaire ci-dessus pour ajouter la première entrée.")
        return
    
    # ===== KPI DE DISTRIBUTION =====
    st.markdown("---")
    st.markdown("### 📊 Indicateurs de distribution")
    
    # Calculs globaux
    total_prevu = df_dist['quantite_prevue'].sum()
    total_expedie = df_dist['quantite_expediee'].sum()
    total_recu = df_dist['quantite_recue'].sum()
    
    taux_expedition = (total_expedie / total_prevu * 100) if total_prevu > 0 else 0
    taux_reception = (total_recu / total_expedie * 100) if total_expedie > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Quantité totale prévue", f"{int(total_prevu):,}")
    with col2:
        st.metric("📤 Quantité totale expédiée", f"{int(total_expedie):,}",
                 delta=f"{taux_expedition:.1f}% du prévu" if total_prevu > 0 else None)
    with col3:
        st.metric("📥 Quantité totale reçue", f"{int(total_recu):,}",
                 delta=f"{taux_reception:.1f}% de l'expédié" if total_expedie > 0 else None)
    with col4:
        ecart_global = total_expedie - total_recu
        if ecart_global > 0:
            delta_ecart = f"⚠️ {int(ecart_global):,} en transit"
            color_ecart = "off"
        elif ecart_global < 0:
            delta_ecart = f"⚠️ Sur-réception"
            color_ecart = "inverse"
        else:
            delta_ecart = "✅ Concordance parfaite"
            color_ecart = "normal"
        
        st.metric("⚖️ Écart Expédié/Reçu", f"{int(abs(ecart_global)):,}",
                 delta=delta_ecart, delta_color=color_ecart)
    
    # ===== TABLEAU PAR NIVEAU =====
    st.markdown("---")
    st.markdown("### 📋 Suivi par niveau de distribution")
    
    tab_nat, tab_cdr, tab_zs = st.tabs(["🌍 National → CDR", "🏭 CDR → ZS", "🏥 Zones de Santé"])
    
    with tab_nat:
        df_nat = df_dist[df_dist['type_niveau'] == 'National'].copy()
        if len(df_nat) > 0:
            # Grouper par CDR destinataire
            df_nat_grouped = df_nat.groupby(['nom_entite', 'medicament']).agg({
                'quantite_prevue': 'sum',
                'quantite_expediee': 'sum',
                'quantite_recue': 'sum'
            }).reset_index()
            
            df_nat_grouped['Taux expédition (%)'] = np.where(
                df_nat_grouped['quantite_prevue'] > 0,
                (df_nat_grouped['quantite_expediee'] / df_nat_grouped['quantite_prevue'] * 100).round(1),
                0
            )
            
            df_nat_grouped['Statut'] = df_nat_grouped['Taux expédition (%)'].apply(
                lambda x: '🟢 OK' if x >= 90 else '🟡 Partiel' if x >= 50 else '🔴 Faible'
            )
            
            df_nat_display = df_nat_grouped.rename(columns={
                'nom_entite': 'CDR destinataire',
                'medicament': 'Médicament',
                'quantite_prevue': 'Qté prévue',
                'quantite_expediee': 'Qté expédiée',
                'quantite_recue': 'Qté reçue'
            })
            
            st.dataframe(df_nat_display, use_container_width=True, height=300)
        else:
            st.info("Aucune donnée d'expédition nationale pour le moment.")
    
    with tab_cdr:
        df_cdr = df_dist[df_dist['type_niveau'] == 'CDR'].copy()
        if len(df_cdr) > 0:
            df_cdr_grouped = df_cdr.groupby(['nom_entite', 'medicament']).agg({
                'quantite_prevue': 'sum',
                'quantite_expediee': 'sum',
                'quantite_recue': 'sum'
            }).reset_index()
            
            df_cdr_grouped['Taux réception (%)'] = np.where(
                df_cdr_grouped['quantite_expediee'] > 0,
                (df_cdr_grouped['quantite_recue'] / df_cdr_grouped['quantite_expediee'] * 100).round(1),
                0
            )
            
            df_cdr_grouped['Statut'] = df_cdr_grouped['Taux réception (%)'].apply(
                lambda x: '🟢 OK' if x >= 90 else '🟡 Partiel' if x >= 50 else '🔴 Faible'
            )
            
            df_cdr_display = df_cdr_grouped.rename(columns={
                'nom_entite': 'CDR',
                'medicament': 'Médicament',
                'quantite_prevue': 'Qté prévue',
                'quantite_expediee': 'Qté expédiée',
                'quantite_recue': 'Qté reçue'
            })
            
            st.dataframe(df_cdr_display, use_container_width=True, height=300)
        else:
            st.info("Aucune donnée de réception/redistribution CDR pour le moment.")
    
    with tab_zs:
        df_zs = df_dist[df_dist['type_niveau'] == 'Zone de Santé'].copy()
        if len(df_zs) > 0:
            df_zs_grouped = df_zs.groupby(['nom_entite', 'medicament']).agg({
                'quantite_prevue': 'sum',
                'quantite_expediee': 'sum',
                'quantite_recue': 'sum'
            }).reset_index()
            
            df_zs_grouped['Taux réception (%)'] = np.where(
                df_zs_grouped['quantite_prevue'] > 0,
                (df_zs_grouped['quantite_recue'] / df_zs_grouped['quantite_prevue'] * 100).round(1),
                0
            )
            
            df_zs_grouped['Statut'] = df_zs_grouped['Taux réception (%)'].apply(
                lambda x: '🟢 OK' if x >= 90 else '🟡 Partiel' if x >= 50 else '🔴 Faible'
            )
            
            df_zs_display = df_zs_grouped.rename(columns={
                'nom_entite': 'Zone de Santé',
                'medicament': 'Médicament',
                'quantite_prevue': 'Qté prévue',
                'quantite_expediee': 'Qté expédiée',
                'quantite_recue': 'Qté reçue'
            })
            
            st.dataframe(df_zs_display, use_container_width=True, height=300)
        else:
            st.info("Aucune donnée de réception Zone de Santé pour le moment.")
    
    # ===== EXPORT =====
    st.markdown("---")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.download_button(
            label="📥 Télécharger les données de distribution (CSV)",
            data=df_dist.to_csv(index=False).encode('utf-8'),
            file_name=f"distribution_medicaments_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with col_exp2:
        st.download_button(
            label="📥 Télécharger les données de distribution (Excel)",
            data=to_excel(df_dist),
            file_name=f"distribution_medicaments_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # ===== GRAPHIQUES =====
    st.markdown("---")
    st.markdown("### 📊 Visualisation de la distribution")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Graphique : Prévision vs Expédié vs Reçu par médicament
        df_med = df_dist.groupby('medicament').agg({
            'quantite_prevue': 'sum',
            'quantite_expediee': 'sum',
            'quantite_recue': 'sum'
        }).reset_index()
        
        fig_med = go.Figure()
        fig_med.add_trace(go.Bar(x=df_med['medicament'], y=df_med['quantite_prevue'],
                                  name='Prévu', marker_color='#1f77b4'))
        fig_med.add_trace(go.Bar(x=df_med['medicament'], y=df_med['quantite_expediee'],
                                  name='Expédié', marker_color='#ff7f0e'))
        fig_med.add_trace(go.Bar(x=df_med['medicament'], y=df_med['quantite_recue'],
                                  name='Reçu', marker_color='#2ca02c'))
        fig_med.update_layout(
            title='Distribution par médicament (tous niveaux)',
            xaxis_title='Médicament',
            yaxis_title='Quantité',
            barmode='group',
            height=400,
            xaxis_tickangle=45
        )
        st.plotly_chart(fig_med, use_container_width=True)
    
    with col_g2:
        # Graphique : Évolution temporelle
        if 'semaine' in df_dist.columns:
            df_time = df_dist.groupby('semaine').agg({
                'quantite_prevue': 'sum',
                'quantite_expediee': 'sum',
                'quantite_recue': 'sum'
            }).reset_index()
            
            df_time = df_time.sort_values('semaine')
            
            fig_time = go.Figure()
            fig_time.add_trace(go.Scatter(x=df_time['semaine'], y=df_time['quantite_prevue'],
                                            mode='lines+markers', name='Prévu',
                                            line=dict(color='#1f77b4', width=2)))
            fig_time.add_trace(go.Scatter(x=df_time['semaine'], y=df_time['quantite_expediee'],
                                            mode='lines+markers', name='Expédié',
                                            line=dict(color='#ff7f0e', width=2)))
            fig_time.add_trace(go.Scatter(x=df_time['semaine'], y=df_time['quantite_recue'],
                                            mode='lines+markers', name='Reçu',
                                            line=dict(color='#2ca02c', width=2)))
            fig_time.update_layout(
                title='Évolution hebdomadaire de la distribution',
                xaxis_title='Semaine',
                yaxis_title='Quantité',
                height=400,
                xaxis_tickangle=45
            )
            st.plotly_chart(fig_time, use_container_width=True)
    
    # ===== TABLEAU DÉTAILLÉ =====
    st.markdown("---")
    with st.expander("📜 **Voir le détail de toutes les entrées**", expanded=False):
        df_detail = df_dist.copy()
        df_detail['date_saisie'] = pd.to_datetime(df_detail['date_saisie']).dt.strftime('%d/%m/%Y')
        
        cols_affichage = ['date_saisie', 'semaine', 'type_niveau', 'medicament', 
                          'code_entite', 'nom_entite', 'quantite_prevue', 
                          'quantite_expediee', 'quantite_recue', 'observations']
        cols_affichage = [c for c in cols_affichage if c in df_detail.columns]
        
        df_detail_display = df_detail[cols_affichage].rename(columns={
            'date_saisie': 'Date',
            'semaine': 'Semaine',
            'type_niveau': 'Niveau',
            'medicament': 'Médicament',
            'code_entite': 'Code',
            'nom_entite': 'Entité',
            'quantite_prevue': 'Qté prévue',
            'quantite_expediee': 'Qté expédiée',
            'quantite_recue': 'Qté reçue',
            'observations': 'Observations'
        })
        
        st.dataframe(df_detail_display, use_container_width=True, height=400)


# ============================================================================
# FONCTIONS DE COMPLÉTUDE ET PROMPTITUDE
# ============================================================================

def colorer_taux(val):
    try:
        if isinstance(val, str):
            val_num = float(val.replace('%', '').strip())
        else:
            val_num = float(val)
        
        if val_num < 50:
            return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
        elif val_num < 80:
            return 'background-color: #fff3cd; color: #856404; font-weight: bold;'
        elif val_num < 90:
            return 'background-color: #d1ecf1; color: #0c5460; font-weight: bold;'
        else:
            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    except:
        return ''


def show_completude_promptitude_tab(df, niveau=None, province_selectionne=None, zone_sante_selectionne=None):
    st.subheader("📊 Complétude et Promptitude des rapports")
    st.markdown(f"**Date limite de soumission :** Le {DATE_LIMITE_JOUR} de chaque mois")
    
    if 'date_saisie' in df.columns:
        total_soumissions = len(df)
        soumissions_a_temps = df['est_prompt'].sum() if 'est_prompt' in df.columns else 0
        taux_promptitude_global = (soumissions_a_temps / total_soumissions * 100) if total_soumissions > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total soumissions", f"{total_soumissions}")
        with col2:
            st.metric("Soumissions à temps", f"{soumissions_a_temps}")
        with col3:
            st.metric("Taux promptitude global", f"{taux_promptitude_global:.1f}%")
    
    st.markdown("---")
    
    if niveau == 'Zone Sante' and zone_sante_selectionne and zone_sante_selectionne != 'Toutes':
        st.subheader(f"📋 Détail par Établissement - {zone_sante_selectionne}")
        show_detail_etablissement(df, zone_sante_selectionne)
    elif niveau == 'Provincial' and province_selectionne and province_selectionne != 'Toutes':
        st.subheader(f"📋 Détail par Zone de Santé - {province_selectionne}")
        show_detail_zs(df, province_selectionne)
    else:
        st.subheader("📋 Tableau récapitulatif par province")
        show_summary_province(df)


def show_summary_province(df):
    if 'province_name' in df.columns:
        completeness = df.groupby('province_name').agg({
            'healthzone_name': 'nunique',
            'facility_name': 'nunique',
            'q1_0_hf_total': 'sum', 'q1_2_hf_total': 'sum', 'q2_0_hf_total': 'sum',
            'q3_0_hf_total': 'sum', 'q4_0_hf_total': 'sum', 'q5_0_hf_total': 'sum',
            'q8_0_hf_total': 'sum', 'tpt_started_total': 'sum'
        }).reset_index()
        
        completeness.columns = ['Province', 'ZS_soumises', 'CDT_soumis', 
                                'Dépistages', 'Cas_présumés', 'TB_détectée',
                                'Traitement_DS', 'Test_RR', 'Traitement_RR',
                                'Dépistés_TPT', 'TPT_commencé']
        
        completeness = completeness.merge(ZS_CDT_REFERENCE, on='Province', how='outer')
        completeness = completeness.fillna(0)
        
        completeness['Taux_ZS'] = (completeness['ZS_soumises'] / completeness['ZS_attendues'] * 100).round(1)
        completeness['Taux_CDT'] = (completeness['CDT_soumis'] / completeness['CDT_attendus'] * 100).round(1)
        
        completeness['Performance'] = completeness.apply(
            lambda row: '✅ Bonne' if row['Taux_ZS'] >= 100 and row['Taux_CDT'] >= 100
            else '⚠️ Moyenne' if row['Taux_ZS'] >= 80 and row['Taux_CDT'] >= 80
            else '🔴 Faible', axis=1
        )
        
        cols_affichage = ['Province', 'ZS_attendues', 'ZS_soumises', 'Taux_ZS',
                         'CDT_attendus', 'CDT_soumis', 'Taux_CDT',
                         'Dépistages', 'Cas_présumés', 'TB_détectée',
                         'Traitement_DS', 'Test_RR', 'Traitement_RR',
                         'Dépistés_TPT', 'TPT_commencé', 'Performance']
        
        cols_affichage = [col for col in cols_affichage if col in completeness.columns]
        df_affichage = completeness[cols_affichage].copy()
        
        for col in df_affichage.columns:
            if col in ['Taux_ZS', 'Taux_CDT']:
                df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
            elif col not in ['Province', 'Performance']:
                df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
        
        styled_df = df_affichage.style.applymap(colorer_taux, subset=['Taux_ZS', 'Taux_CDT'])
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        st.markdown("""
        **Légende des couleurs :**
        - 🔴 **Rouge** : < 50% (Critique)
        - 🟡 **Jaune** : 50% - 79% (Insuffisant)
        - 💧 **Vert d'eau** : 80% - 89% (Bon)
        - 🟢 **Vert citron** : ≥ 90% (Excellent)
        """)
        
        col_rename_export = {
            'Province': 'Province', 'ZS_attendues': 'Zones_de_Sante_attendues',
            'ZS_soumises': 'Zones_de_Sante_soumises', 'Taux_ZS': 'Taux_completude_ZS',
            'CDT_attendus': 'CDT_attendus', 'CDT_soumis': 'CDT_soumis',
            'Taux_CDT': 'Taux_completude_CDT', 'Dépistages': 'Depistages',
            'Cas_présumés': 'Cas_presumes', 'TB_détectée': 'TB_detectee',
            'Traitement_DS': 'Traitement_DS_debute', 'Test_RR': 'Test_resistance_RR',
            'Traitement_RR': 'Traitement_RR_debute', 'Dépistés_TPT': 'Depistes_TPT',
            'TPT_commencé': 'TPT_commence', 'Performance': 'Performance'
        }
        df_export = completeness.rename(columns=col_rename_export)
        
        col1_export, col2_export = st.columns(2)
        with col1_export:
            st.download_button(
                label="📥 Télécharger (CSV)",
                data=df_export.to_csv(index=False).encode('utf-8'),
                file_name=f"completude_provinces_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2_export:
            st.download_button(
                label="📥 Télécharger (Excel)",
                data=to_excel(df_export),
                file_name=f"completude_provinces_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.markdown("---")
        show_performance_graphs(completeness)


def show_detail_zs(df, province):
    df_province = df[df['province_name'] == province]
    
    detail_zs = df_province.groupby('healthzone_name').agg({
        'facility_name': 'nunique',
        'q1_0_hf_total': 'sum', 'q1_2_hf_total': 'sum', 'q2_0_hf_total': 'sum',
        'q3_0_hf_total': 'sum', 'q4_0_hf_total': 'sum', 'q5_0_hf_total': 'sum',
        'q8_0_hf_total': 'sum', 'tpt_started_total': 'sum'
    }).reset_index()
    
    detail_zs.columns = ['Zone de Santé', 'CDT_soumis', 
                         'Dépistages', 'Cas_présumés', 'TB_détectée',
                         'Traitement_DS', 'Test_RR', 'Traitement_RR',
                         'Dépistés_TPT', 'TPT_commencé']
    
    detail_zs = detail_zs.fillna(0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏥 Zones de Santé", f"{len(detail_zs)}")
    with col2:
        total_cdt = detail_zs['CDT_soumis'].sum()
        st.metric("📋 CDT ayant soumis", f"{int(total_cdt)}")
    with col3:
        total_depistages = detail_zs['Dépistages'].sum()
        st.metric("👥 Dépistages totaux", f"{int(total_depistages):,}")
    with col4:
        total_tb = detail_zs['TB_détectée'].sum()
        st.metric("🦠 TB détectée", f"{int(total_tb):,}")
    
    st.markdown("---")
    st.dataframe(detail_zs, use_container_width=True, height=400)
    
    detail_zs_export = get_readable_columns(detail_zs)
    col1_exp, col2_exp = st.columns(2)
    with col1_exp:
        st.download_button(
            label=f"📥 Télécharger (CSV) - {province}",
            data=detail_zs_export.to_csv(index=False).encode('utf-8'),
            file_name=f"detail_zs_{province}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with col2_exp:
        st.download_button(
            label=f"📥 Télécharger (Excel) - {province}",
            data=to_excel(detail_zs_export),
            file_name=f"detail_zs_{province}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig_depistages = px.bar(
            detail_zs, x='Zone de Santé', y='Dépistages',
            title=f"Dépistages par Zone de Santé - {province}",
            color='Dépistages', color_continuous_scale='Blues', text='Dépistages'
        )
        fig_depistages.update_traces(textposition='outside')
        fig_depistages.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_depistages, use_container_width=True)
    
    with col_g2:
        fig_tb = px.bar(
            detail_zs, x='Zone de Santé', y='TB_détectée',
            title=f"TB détectée par Zone de Santé - {province}",
            color='TB_détectée', color_continuous_scale='Reds', text='TB_détectée'
        )
        fig_tb.update_traces(textposition='outside')
        fig_tb.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_tb, use_container_width=True)


def show_detail_etablissement(df, zone_sante):
    df_zs = df[df['healthzone_name'] == zone_sante]
    
    detail_etab = df_zs.groupby('facility_name').agg({
        'q1_0_hf_total': 'sum', 'q1_2_hf_total': 'sum', 'q2_0_hf_total': 'sum',
        'q3_0_hf_total': 'sum', 'q4_0_hf_total': 'sum', 'q5_0_hf_total': 'sum',
        'q8_0_hf_total': 'sum', 'tpt_started_total': 'sum'
    }).reset_index()
    
    detail_etab.columns = ['Établissement', 
                           'Dépistages', 'Cas_présumés', 'TB_détectée',
                           'Traitement_DS', 'Test_RR', 'Traitement_RR',
                           'Dépistés_TPT', 'TPT_commencé']
    
    detail_etab = detail_etab.fillna(0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏥 Établissements", f"{len(detail_etab)}")
    with col2:
        total_depistages = detail_etab['Dépistages'].sum()
        st.metric("👥 Dépistages totaux", f"{int(total_depistages):,}")
    with col3:
        total_tb = detail_etab['TB_détectée'].sum()
        st.metric("🦠 TB détectée", f"{int(total_tb):,}")
    with col4:
        total_tpt = detail_etab['TPT_commencé'].sum()
        st.metric("💊 TPT commencé", f"{int(total_tpt):,}")
    
    st.markdown("---")
    st.dataframe(detail_etab, use_container_width=True, height=400)
    
    detail_etab_export = get_readable_columns(detail_etab)
    col1_exp, col2_exp = st.columns(2)
    with col1_exp:
        st.download_button(
            label=f"📥 Télécharger (CSV) - {zone_sante}",
            data=detail_etab_export.to_csv(index=False).encode('utf-8'),
            file_name=f"detail_etab_{zone_sante}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with col2_exp:
        st.download_button(
            label=f"📥 Télécharger (Excel) - {zone_sante}",
            data=to_excel(detail_etab_export),
            file_name=f"detail_etab_{zone_sante}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig_depistages = px.bar(
            detail_etab, x='Établissement', y='Dépistages',
            title=f"Dépistages par Établissement - {zone_sante}",
            color='Dépistages', color_continuous_scale='Blues', text='Dépistages'
        )
        fig_depistages.update_traces(textposition='outside')
        fig_depistages.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_depistages, use_container_width=True)
    
    with col_g2:
        fig_tb = px.bar(
            detail_etab, x='Établissement', y='TB_détectée',
            title=f"TB détectée par Établissement - {zone_sante}",
            color='TB_détectée', color_continuous_scale='Reds', text='TB_détectée'
        )
        fig_tb.update_traces(textposition='outside')
        fig_tb.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_tb, use_container_width=True)


def show_performance_graphs(completeness):
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig_zs = go.Figure()
        fig_zs.add_trace(go.Bar(
            x=completeness['Province'], y=completeness['Taux_ZS'],
            text=completeness['Taux_ZS'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=completeness['Taux_ZS'].apply(
                lambda x: '#28a745' if x >= 90 else '#17becf' if x >= 80 else '#ffc107' if x >= 50 else '#dc3545'
            )
        ))
        fig_zs.update_layout(
            title="Taux de complétude des Zones de Santé",
            xaxis_title="Province", yaxis_title="Taux (%)",
            height=400, yaxis_range=[0, 120], showlegend=False
        )
        fig_zs.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Cible 100%")
        fig_zs.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Seuil minimal 80%")
        st.plotly_chart(fig_zs, use_container_width=True)
    
    with col_g2:
        fig_cdt = go.Figure()
        fig_cdt.add_trace(go.Bar(
            x=completeness['Province'], y=completeness['Taux_CDT'],
            text=completeness['Taux_CDT'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=completeness['Taux_CDT'].apply(
                lambda x: '#28a745' if x >= 90 else '#17becf' if x >= 80 else '#ffc107' if x >= 50 else '#dc3545'
            )
        ))
        fig_cdt.update_layout(
            title="Taux de complétude des CDT",
            xaxis_title="Province", yaxis_title="Taux (%)",
            height=400, yaxis_range=[0, 120], showlegend=False
        )
        fig_cdt.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Cible 100%")
        fig_cdt.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Seuil minimal 80%")
        st.plotly_chart(fig_cdt, use_container_width=True)
    
    st.markdown("### 📊 Synthèse des performances")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        moy_zs = completeness['Taux_ZS'].mean()
        st.metric("📈 Taux ZS moyen", f"{moy_zs:.1f}%")
    with col_m2:
        moy_cdt = completeness['Taux_CDT'].mean()
        st.metric("📈 Taux CDT moyen", f"{moy_cdt:.1f}%")
    with col_m3:
        nb_bonnes = len(completeness[completeness['Performance'] == '✅ Bonne'])
        st.metric("✅ Provinces en bonne performance", f"{nb_bonnes}/{len(completeness)}")
    with col_m4:
        nb_faibles = len(completeness[completeness['Performance'] == '🔴 Faible'])
        st.metric("🔴 Provinces en performance faible", f"{nb_faibles}/{len(completeness)}")


# ============================================================================
# ONGLET FINANCES
# ============================================================================

def get_mois_projet():
    date_debut = pd.to_datetime(PROJET_CONFIG['date_debut'])
    date_fin = pd.to_datetime(PROJET_CONFIG['date_fin'])
    return pd.date_range(start=date_debut, end=date_fin, freq='MS')


def get_semaines_du_mois(mois):
    annee = mois.year
    mois_num = mois.month
    
    premier_jour = pd.Timestamp(year=annee, month=mois_num, day=1)
    if mois_num == 12:
        dernier_jour = pd.Timestamp(year=annee + 1, month=1, day=1) - pd.Timedelta(days=1)
    else:
        dernier_jour = pd.Timestamp(year=annee, month=mois_num + 1, day=1) - pd.Timedelta(days=1)
    
    semaines = pd.date_range(start=premier_jour, end=dernier_jour, freq='W-MON')
    
    liste_semaines = []
    for i, s in enumerate(semaines):
        liste_semaines.append({
            'numero': i + 1,
            'debut': s - pd.Timedelta(days=6),
            'fin': s,
            'label': f"Semaine {i+1} ({s.strftime('%d/%m')})"
        })
    
    return liste_semaines


def load_finances_data():
    try:
        df_fin = pd.read_csv('finances_data.csv')
        
        if 'depenses_mensuelles' in df_fin.columns and 'depenses' not in df_fin.columns:
            df_fin = df_fin.rename(columns={'depenses_mensuelles': 'depenses'})
        
        if 'type_suivi' not in df_fin.columns:
            df_fin['type_suivi'] = 'mensuel'
        
        if 'depenses' not in df_fin.columns:
            df_fin['depenses'] = 0
        
        for col in ['nombre_dp_recu', 'nombre_dp_traite', 'nombre_dp_en_attente']:
            if col not in df_fin.columns:
                df_fin[col] = 0
        
        if 'province_name' not in df_fin.columns:
            df_fin['province_name'] = 'Toutes'
        
        if 'observations' not in df_fin.columns:
            df_fin['observations'] = ''
        
        df_fin['date_saisie'] = pd.to_datetime(df_fin['date_saisie'], errors='coerce')
        df_fin['mois_num'] = df_fin['date_saisie'].dt.month
        df_fin['annee'] = df_fin['date_saisie'].dt.year
        df_fin['mois_annee'] = df_fin['date_saisie'].dt.strftime('%Y-%m')
        df_fin['semaine_num'] = df_fin['date_saisie'].dt.isocalendar().week
        
        save_finances_data(df_fin)
        
        return df_fin
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'type_suivi', 'date_saisie', 'province_name', 'depenses',
            'nombre_dp_recu', 'nombre_dp_traite', 'nombre_dp_en_attente',
            'observations', 'mois_num', 'annee', 'mois_annee', 'semaine_num'
        ])


def save_finances_data(df_fin):
    df_to_save = df_fin.drop(columns=['mois_num', 'annee', 'mois_annee', 'semaine_num'], errors='ignore')
    df_to_save.to_csv('finances_data.csv', index=False)


def show_finances_tab(df_main):
    st.subheader("💰 Tableau de bord financier du projet")
    
    date_debut = pd.to_datetime(PROJET_CONFIG['date_debut'])
    date_fin = pd.to_datetime(PROJET_CONFIG['date_fin'])
    budget_total = PROJET_CONFIG['budget_total']
    
    mois_projet = get_mois_projet()
    nb_mois_total = len(mois_projet)
    prevision_mensuelle = budget_total / nb_mois_total
    
    nb_semaines_total = nb_mois_total * 4
    prevision_hebdo = budget_total / nb_semaines_total
    
    aujourdhui = pd.Timestamp.now()
    mois_ecoules = [m for m in mois_projet if m <= aujourdhui]
    nb_mois_ecoules = len(mois_ecoules)
    
    st.markdown(f"""
    <div style="background-color: #e7f3ff; padding: 1rem; border-radius: 10px; border-left: 5px solid #1f77b4; margin-bottom: 1rem;">
        <h4 style="margin-top: 0;">📋 Informations du projet</h4>
        <table style="width: 100%;">
            <tr>
                <td><strong>Nom du projet :</strong></td>
                <td>{PROJET_CONFIG['nom_projet']}</td>
                <td><strong>Période :</strong></td>
                <td>{date_debut.strftime('%B %Y')} → {date_fin.strftime('%B %Y')}</td>
            </tr>
            <tr>
                <td><strong>Budget total :</strong></td>
                <td><strong>{budget_total:,.0f} USD</strong></td>
                <td><strong>Durée :</strong></td>
                <td>{nb_mois_total} mois ({nb_semaines_total} semaines)</td>
            </tr>
            <tr>
                <td><strong>Prévision mensuelle :</strong></td>
                <td><strong>{prevision_mensuelle:,.2f} USD</strong></td>
                <td><strong>Prévision hebdomadaire :</strong></td>
                <td><strong>{prevision_hebdo:,.2f} USD</strong></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    df_fin = load_finances_data()
    
    if len(df_fin) > 0:
        if 'depenses' not in df_fin.columns:
            if 'depenses_mensuelles' in df_fin.columns:
                df_fin['depenses'] = df_fin['depenses_mensuelles']
            else:
                df_fin['depenses'] = 0
        
        if 'type_suivi' not in df_fin.columns:
            df_fin['type_suivi'] = 'mensuel'
    
    st.markdown("### ⚙️ Type de suivi")
    type_suivi = st.radio(
        "Choisissez le type de suivi à afficher",
        options=['📅 Mensuel', '📆 Hebdomadaire'],
        horizontal=True,
        key="type_suivi_radio"
    )
    
    with st.expander(f"📝 **Ajouter / Modifier une entrée financière**", expanded=False):
        with st.form("form_finances", clear_on_submit=True):
            
            type_saisie = st.radio(
                "Type de saisie",
                options=['Mensuel', 'Hebdomadaire'],
                horizontal=True,
                index=0 if 'Mensuel' in type_suivi else 1
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if type_saisie == 'Mensuel':
                    mois_options_str = [m.strftime('%B %Y') for m in mois_projet]
                    mois_selectionne_str = st.selectbox(
                        "📅 Mois concerné",
                        options=mois_options_str,
                        index=min(nb_mois_ecoules - 1, len(mois_options_str) - 1) if nb_mois_ecoules > 0 else 0
                    )
                    
                    mois_selectionne = pd.to_datetime(mois_selectionne_str, format='%B %Y')
                    date_saisie = mois_selectionne + pd.Timedelta(days=14)
                    depenses_label = "💸 Dépenses mensuelles (USD)"
                    depenses_default = prevision_mensuelle
                    cle_mois = mois_selectionne.strftime('%Y-%m')
                    type_enregistrement = 'mensuel'
                    
                    st.info(f"📅 Saisie mensuelle pour : **{mois_selectionne_str}**")
                    
                else:
                    mois_options_str = [m.strftime('%B %Y') for m in mois_projet]
                    mois_selectionne_str = st.selectbox(
                        "📅 Mois concerné",
                        options=mois_options_str,
                        index=min(nb_mois_ecoules - 1, len(mois_options_str) - 1) if nb_mois_ecoules > 0 else 0,
                        key="mois_hebdo"
                    )
                    
                    mois_selectionne = pd.to_datetime(mois_selectionne_str, format='%B %Y')
                    semaines = get_semaines_du_mois(mois_selectionne)
                    
                    semaine_options = [s['label'] for s in semaines]
                    semaine_selectionnee_label = st.selectbox(
                        "📆 Semaine concernée",
                        options=semaine_options,
                        index=0
                    )
                    
                    semaine_index = semaine_options.index(semaine_selectionnee_label)
                    semaine_selectionnee = semaines[semaine_index]
                    
                    date_saisie = semaine_selectionnee['fin']
                    depenses_label = "💸 Dépenses de la semaine (USD)"
                    depenses_default = prevision_hebdo
                    cle_mois = f"{mois_selectionne.strftime('%Y-%m')}-S{semaine_selectionnee['numero']}"
                    type_enregistrement = 'hebdomadaire'
                    
                    st.info(f"📆 Saisie hebdomadaire : **{semaine_selectionnee_label}**")
                
                depenses = st.number_input(
                    depenses_label,
                    min_value=0.0,
                    value=float(depenses_default),
                    step=500.0,
                    format="%.2f"
                )
                
                province = st.selectbox(
                    "🌍 Province (optionnel)",
                    options=['Toutes'] + sorted(df_main['province_name'].dropna().unique().tolist())
                )
            
            with col2:
                nb_dp_recu = st.number_input("📥 Nombre de DP reçus", min_value=0, value=0, step=1)
                nb_dp_traite = st.number_input("✅ Nombre de DP traités", min_value=0, value=0, step=1)
                nb_dp_attente = st.number_input("⏳ Nombre de DP en attente", min_value=0, value=0, step=1)
                observations = st.text_area("📝 Observations", value="", height=100)
            
            submitted = st.form_submit_button("✅ Enregistrer l'entrée", use_container_width=True)
            
            if submitted:
                if type_enregistrement == 'mensuel':
                    masque = (df_fin.get('type_suivi', '') == 'mensuel') & (df_fin['mois_annee'] == cle_mois) if len(df_fin) > 0 else pd.Series([False])
                else:
                    if len(df_fin) > 0:
                        semaine_target = semaine_selectionnee['fin'].isocalendar()[1]
                        annee_target = semaine_selectionnee['fin'].isocalendar()[0]
                        masque = (df_fin.get('type_suivi', '') == 'hebdomadaire') & \
                                 (df_fin['date_saisie'].dt.isocalendar().week == semaine_target) & \
                                 (df_fin['date_saisie'].dt.isocalendar().year == annee_target)
                    else:
                        masque = pd.Series([False])
                
                nouvelle_entree = {
                    'type_suivi': type_enregistrement,
                    'date_saisie': pd.to_datetime(date_saisie),
                    'province_name': province,
                    'depenses': depenses,
                    'nombre_dp_recu': nb_dp_recu,
                    'nombre_dp_traite': nb_dp_traite,
                    'nombre_dp_en_attente': nb_dp_attente,
                    'observations': observations
                }
                
                if masque.any():
                    idx = df_fin[masque].index[0]
                    for key, value in nouvelle_entree.items():
                        df_fin.loc[idx, key] = value
                    st.success(f"✅ Entrée {type_enregistrement} mise à jour !")
                else:
                    df_fin = pd.concat([df_fin, pd.DataFrame([nouvelle_entree])], ignore_index=True)
                    st.success(f"✅ Nouvelle entrée {type_enregistrement} ajoutée !")
                
                df_fin['date_saisie'] = pd.to_datetime(df_fin['date_saisie'], errors='coerce')
                df_fin['mois_num'] = df_fin['date_saisie'].dt.month
                df_fin['annee'] = df_fin['date_saisie'].dt.year
                df_fin['mois_annee'] = df_fin['date_saisie'].dt.strftime('%Y-%m')
                df_fin['semaine_num'] = df_fin['date_saisie'].dt.isocalendar().week
                df_fin = df_fin.sort_values('date_saisie').reset_index(drop=True)
                
                save_finances_data(df_fin)
                st.rerun()
    
    if len(df_fin) == 0:
        st.info("📋 Aucune donnée financière n'est encore enregistrée. Utilisez le formulaire ci-dessus.")
        return
    
    df_fin_mensuel = df_fin[df_fin.get('type_suivi', 'mensuel') == 'mensuel'].copy() if 'type_suivi' in df_fin.columns else df_fin.copy()
    df_fin_hebdo = df_fin[df_fin.get('type_suivi', 'mensuel') == 'hebdomadaire'].copy() if 'type_suivi' in df_fin.columns else pd.DataFrame()
    
    if 'depenses' not in df_fin.columns:
        df_fin['depenses'] = 0
    if 'depenses' not in df_fin_mensuel.columns:
        df_fin_mensuel['depenses'] = 0
    if len(df_fin_hebdo) > 0 and 'depenses' not in df_fin_hebdo.columns:
        df_fin_hebdo['depenses'] = 0
    
    if len(df_fin_mensuel) > 0:
        depenses_totales = df_fin_mensuel['depenses'].sum()
    else:
        depenses_totales = df_fin['depenses'].sum()
    
    budget_restant = budget_total - depenses_totales
    taux_absorption_global = (depenses_totales / budget_total * 100) if budget_total > 0 else 0
    taux_temporel = (nb_mois_ecoules / nb_mois_total * 100) if nb_mois_total > 0 else 0
    ecart = taux_absorption_global - taux_temporel
    
    dp_recu_total = df_fin['nombre_dp_recu'].sum() if 'nombre_dp_recu' in df_fin.columns else 0
    dp_traite_total = df_fin['nombre_dp_traite'].sum() if 'nombre_dp_traite' in df_fin.columns else 0
    dp_attente_total = df_fin['nombre_dp_en_attente'].sum() if 'nombre_dp_en_attente' in df_fin.columns else 0
    taux_traitement_dp = (dp_traite_total / dp_recu_total * 100) if dp_recu_total > 0 else 0
    
    prevision_a_date = prevision_mensuelle * nb_mois_ecoules
    
    st.markdown("---")
    st.markdown("### 📊 Indicateurs financiers globaux")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Budget total projet", f"${budget_total:,.0f}")
    with col2:
        st.metric("💸 Dépenses cumulées", f"${depenses_totales:,.2f}",
                 delta=f"{(depenses_totales/budget_total*100):.1f}% du budget" if budget_total > 0 else None)
    with col3:
        st.metric("💵 Budget restant", f"${budget_restant:,.2f}",
                 delta=f"{(budget_restant/budget_total*100):.1f}% restant" if budget_total > 0 else None)
    with col4:
        if taux_absorption_global >= 90:
            delta_abs = "🟢 Excellent"
            color_abs = "normal"
        elif taux_absorption_global >= 70:
            delta_abs = "🟡 Bon"
            color_abs = "normal"
        elif taux_absorption_global >= 50:
            delta_abs = "🟠 À surveiller"
            color_abs = "off"
        else:
            delta_abs = "🔴 Faible"
            color_abs = "inverse"
        
        st.metric("📈 Taux d'absorption global", f"{taux_absorption_global:.1f}%",
                 delta=delta_abs, delta_color=color_abs)
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("⏱️ Avancement temporel", f"{taux_temporel:.1f}%",
                 delta=f"{nb_mois_ecoules}/{nb_mois_total} mois")
    with col6:
        if ecart > 10:
            delta_ecart = "🟢 En avance"
            color_ecart = "normal"
        elif ecart > -10:
            delta_ecart = "🟢 Dans les temps"
            color_ecart = "normal"
        else:
            delta_ecart = "🔴 En retard"
            color_ecart = "inverse"
        
        st.metric("📊 Écart absorption/temps", f"{ecart:+.1f} pts",
                 delta=delta_ecart, delta_color=color_ecart)
    with col7:
        st.metric("🎯 Prévision à date", f"${prevision_a_date:,.2f}",
                 delta=f"{prevision_mensuelle:,.0f}/mois")
    with col8:
        ecart_montant = depenses_totales - prevision_a_date
        if ecart_montant >= 0:
            delta_montant = f"+${abs(ecart_montant):,.0f}"
            color_montant = "normal"
        else:
            delta_montant = f"-${abs(ecart_montant):,.0f}"
            color_montant = "inverse"
        
        st.metric("💹 Écart budgétaire", f"${depenses_totales:,.0f}",
                 delta=delta_montant, delta_color=color_montant)
    
    st.markdown("### 📋 Indicateurs DP (Demandes de Paiement)")
    
    col_dp1, col_dp2, col_dp3, col_dp4 = st.columns(4)
    
    with col_dp1:
        st.metric("📥 DP reçus", f"{int(dp_recu_total):,}")
    with col_dp2:
        st.metric("✅ DP traités", f"{int(dp_traite_total):,}", 
                 delta=f"{taux_traitement_dp:.1f}%" if dp_recu_total > 0 else None)
    with col_dp3:
        st.metric("⏳ DP en attente", f"{int(dp_attente_total):,}")
    with col_dp4:
        if dp_attente_total == 0 and dp_recu_total > 0:
            delta_dp = "🟢 Aucun en attente"
            color_dp = "normal"
        elif dp_attente_total <= 5:
            delta_dp = "🟡 À surveiller"
            color_dp = "normal"
        else:
            delta_dp = "🔴 Retard important"
            color_dp = "inverse"
        
        st.metric("📊 Taux traitement DP", f"{taux_traitement_dp:.1f}%",
                 delta=delta_dp, delta_color=color_dp)
    
    st.markdown("---")
    
    def colorer_statut(val):
        if '🟢' in str(val):
            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
        elif '🟡' in str(val):
            return 'background-color: #fff3cd; color: #856404; font-weight: bold;'
        elif '🟠' in str(val):
            return 'background-color: #ffe5b4; color: #8a4b08; font-weight: bold;'
        elif '🔴' in str(val):
            return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
        elif '⏳' in str(val):
            return 'background-color: #e7f3ff; color: #004085; font-weight: bold;'
        else:
            return ''
    
    if 'Mensuel' in type_suivi:
        st.markdown("### 📅 Suivi mensuel du budget")
        
        data_mensuel = []
        for mois in mois_projet:
            mois_str = mois.strftime('%B %Y')
            mois_annee_str = mois.strftime('%Y-%m')
            
            ligne = df_fin_mensuel[df_fin_mensuel['mois_annee'] == mois_annee_str] if len(df_fin_mensuel) > 0 else pd.DataFrame()
            depenses_mois = ligne['depenses'].sum() if len(ligne) > 0 else 0
            
            mois_est_passe = mois <= aujourdhui
            if mois_est_passe and depenses_mois == 0:
                statut = "🔴 Aucune dépense"
            elif mois_est_passe and depenses_mois < prevision_mensuelle * 0.7:
                statut = "🟡 Sous-consommation"
            elif mois_est_passe and depenses_mois > prevision_mensuelle * 1.2:
                statut = "🟠 Sur-consommation"
            elif mois_est_passe:
                statut = "🟢 OK"
            else:
                statut = "⏳ À venir"
            
            data_mensuel.append({
                'Mois': mois_str,
                'Prévision mensuelle ($)': prevision_mensuelle,
                'Dépenses réelles ($)': depenses_mois,
                'Écart ($)': depenses_mois - prevision_mensuelle,
                'Statut': statut
            })
        
        df_mensuel = pd.DataFrame(data_mensuel)
        
        df_mensuel_display = df_mensuel.copy()
        for col in ['Prévision mensuelle ($)', 'Dépenses réelles ($)', 'Écart ($)']:
            df_mensuel_display[col] = df_mensuel_display[col].apply(lambda x: f"${x:,.2f}")
        
        styled_mensuel = df_mensuel_display.style.applymap(colorer_statut, subset=['Statut'])
        st.dataframe(styled_mensuel, use_container_width=True, height=400)
        
        col1_export, col2_export = st.columns(2)
        with col1_export:
            st.download_button(
                label="📥 Télécharger le suivi mensuel (CSV)",
                data=df_mensuel.to_csv(index=False).encode('utf-8'),
                file_name=f"suivi_mensuel_budget_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2_export:
            st.download_button(
                label="📥 Télécharger le suivi mensuel (Excel)",
                data=to_excel(df_mensuel),
                file_name=f"suivi_mensuel_budget_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    else:
        st.markdown("### 📆 Suivi hebdomadaire du budget")
        
        if len(df_fin_hebdo) == 0:
            st.info("📋 Aucune saisie hebdomadaire pour le moment. Utilisez le formulaire ci-dessus.")
        else:
            data_hebdo = []
            for mois in mois_projet:
                mois_str = mois.strftime('%B %Y')
                semaines = get_semaines_du_mois(mois)
                
                for semaine in semaines:
                    semaine_target = semaine['fin'].isocalendar()[1]
                    annee_target = semaine['fin'].isocalendar()[0]
                    
                    masque = (
                        (df_fin_hebdo['date_saisie'].dt.isocalendar().week == semaine_target) &
                        (df_fin_hebdo['date_saisie'].dt.isocalendar().year == annee_target)
                    )
                    
                    ligne = df_fin_hebdo[masque]
                    depenses_semaine = ligne['depenses'].sum() if len(ligne) > 0 else 0
                    
                    semaine_est_passee = semaine['fin'] <= aujourdhui
                    if semaine_est_passee and depenses_semaine == 0:
                        statut = "🔴 Aucune dépense"
                    elif semaine_est_passee and depenses_semaine < prevision_hebdo * 0.7:
                        statut = "🟡 Sous-consommation"
                    elif semaine_est_passee and depenses_semaine > prevision_hebdo * 1.2:
                        statut = "🟠 Sur-consommation"
                    elif semaine_est_passee:
                        statut = "🟢 OK"
                    else:
                        statut = "⏳ À venir"
                    
                    data_hebdo.append({
                        'Mois': mois_str,
                        'Semaine': semaine['label'],
                        'Prévision hebdo ($)': prevision_hebdo,
                        'Dépenses réelles ($)': depenses_semaine,
                        'Écart ($)': depenses_semaine - prevision_hebdo,
                        'Statut': statut
                    })
            
            df_hebdo = pd.DataFrame(data_hebdo)
            
            df_hebdo_display = df_hebdo.copy()
            for col in ['Prévision hebdo ($)', 'Dépenses réelles ($)', 'Écart ($)']:
                df_hebdo_display[col] = df_hebdo_display[col].apply(lambda x: f"${x:,.2f}")
            
            styled_hebdo = df_hebdo_display.style.applymap(colorer_statut, subset=['Statut'])
            st.dataframe(styled_hebdo, use_container_width=True, height=500)
            
            col1_export, col2_export = st.columns(2)
            with col1_export:
                st.download_button(
                    label="📥 Télécharger le suivi hebdomadaire (CSV)",
                    data=df_hebdo.to_csv(index=False).encode('utf-8'),
                    file_name=f"suivi_hebdomadaire_budget_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            with col2_export:
                st.download_button(
                    label="📥 Télécharger le suivi hebdomadaire (Excel)",
                    data=to_excel(df_hebdo),
                    file_name=f"suivi_hebdomadaire_budget_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    st.markdown("---")
    st.markdown("### 📊 Visualisation de l'absorption budgétaire")
    
    if 'Mensuel' in type_suivi:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            df_cumul = df_mensuel.copy()
            df_cumul['Dépenses_num'] = df_cumul['Dépenses réelles ($)'].apply(
                lambda x: float(x.replace('$', '').replace(',', '')) if isinstance(x, str) else x
            )
            df_cumul['Prévision_num'] = df_cumul['Prévision mensuelle ($)'].apply(
                lambda x: float(x.replace('$', '').replace(',', '')) if isinstance(x, str) else x
            )
            df_cumul['Dépenses cumulées'] = df_cumul['Dépenses_num'].cumsum()
            df_cumul['Prévision cumulée'] = df_cumul['Prévision_num'].cumsum()
            
            fig_cumul = go.Figure()
            fig_cumul.add_trace(go.Scatter(
                x=df_cumul['Mois'], y=[budget_total] * len(df_cumul),
                mode='lines', name='Budget total',
                line=dict(color='#1f77b4', width=3, dash='dash')
            ))
            fig_cumul.add_trace(go.Scatter(
                x=df_cumul['Mois'], y=df_cumul['Prévision cumulée'],
                mode='lines+markers', name='Prévision cumulée',
                line=dict(color='#17becf', width=2)
            ))
            fig_cumul.add_trace(go.Scatter(
                x=df_cumul['Mois'], y=df_cumul['Dépenses cumulées'],
                mode='lines+markers', name='Dépenses cumulées',
                line=dict(color='#2ca02c', width=3)
            ))
            fig_cumul.update_layout(
                title='Absorption du budget dans le temps',
                xaxis_title='Mois', yaxis_title='Montant ($)',
                height=400, xaxis_tickangle=45
            )
            st.plotly_chart(fig_cumul, use_container_width=True)
        
        with col_g2:
            df_taux = df_mensuel.copy()
            df_taux['Dépenses_num'] = df_taux['Dépenses réelles ($)'].apply(
                lambda x: float(x.replace('$', '').replace(',', '')) if isinstance(x, str) else x
            )
            df_taux['Prévision_num'] = df_taux['Prévision mensuelle ($)'].apply(
                lambda x: float(x.replace('$', '').replace(',', '')) if isinstance(x, str) else x
            )
            df_taux['Taux mensuel'] = np.where(df_taux['Prévision_num'] > 0,
                                                df_taux['Dépenses_num'] / df_taux['Prévision_num'] * 100, 0)
            
            fig_taux = go.Figure()
            fig_taux.add_trace(go.Bar(
                x=df_taux['Mois'], y=df_taux['Taux mensuel'],
                name='Taux mensuel', marker_color='#1f77b4',
                text=df_taux['Taux mensuel'].apply(lambda x: f"{x:.0f}%"),
                textposition='outside'
            ))
            fig_taux.update_layout(
                title="Taux d'absorption mensuel (%)",
                xaxis_title='Mois', yaxis_title='Taux (%)',
                height=400, xaxis_tickangle=45, yaxis_range=[0, 120],
                showlegend=False
            )
            fig_taux.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Cible 100%")
            st.plotly_chart(fig_taux, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🔔 Alertes et recommandations")
    
    alertes_fin = []
    
    if taux_absorption_global < 50 and nb_mois_ecoules >= 3:
        alertes_fin.append(f"🔴 **CRITIQUE** : Taux d'absorption très faible ({taux_absorption_global:.1f}%)")
    elif taux_absorption_global < 70 and nb_mois_ecoules >= 3:
        alertes_fin.append(f"🟡 **ATTENTION** : Taux d'absorption ({taux_absorption_global:.1f}%) en dessous de la cible")
    elif taux_absorption_global >= 80:
        alertes_fin.append(f"🟢 **EXCELLENT** : Taux d'absorption optimal ({taux_absorption_global:.1f}%)")
    
    if ecart < -20:
        alertes_fin.append(f"🔴 **RETARD** : Écart de {ecart:.1f} points avec l'avancement temporel")
    elif ecart > 20:
        alertes_fin.append(f"🟠 **EN AVANCE** : Écart de {ecart:+.1f} points")
    
    if dp_attente_total > 20:
        alertes_fin.append(f"🔴 **CRITIQUE** : {int(dp_attente_total)} DP en attente")
    elif dp_attente_total > 10:
        alertes_fin.append(f"🟡 **ATTENTION** : {int(dp_attente_total)} DP en attente")
    
    if alertes_fin:
        for alerte in alertes_fin:
            st.warning(alerte)
    else:
        st.success("✅ Aucune alerte financière à signaler. Le projet est sur la bonne voie !")
    
    st.markdown("---")
    with st.expander("📜 **Voir l'historique des saisies**", expanded=False):
        cols_fin = ['type_suivi', 'date_saisie', 'province_name', 'depenses',
                    'nombre_dp_recu', 'nombre_dp_traite', 'nombre_dp_en_attente',
                    'observations']
        
        cols_fin = [c for c in cols_fin if c in df_fin.columns]
        df_hist = df_fin[cols_fin].copy()
        df_hist['date_saisie'] = pd.to_datetime(df_hist['date_saisie']).dt.strftime('%d/%m/%Y')
        
        rename_dict = {
            'type_suivi': 'Type', 'date_saisie': 'Date', 'province_name': 'Province',
            'depenses': 'Dépenses ($)', 'nombre_dp_recu': 'DP reçus',
            'nombre_dp_traite': 'DP traités', 'nombre_dp_en_attente': 'DP en attente',
            'observations': 'Observations'
        }
        df_hist = df_hist.rename(columns=rename_dict)
        df_hist['Dépenses ($)'] = df_hist['Dépenses ($)'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(df_hist, use_container_width=True, height=300)


def show_donnees_brutes_tab(df_filtered):
    st.subheader("📋 Aperçu des données collectées")
    
    colonnes_a_afficher = ['province_name', 'healthzone_name', 'facility_name', 'mois_nom', 'qannee', 'trimestre']
    colonnes_disponibles = [col for col in colonnes_a_afficher if col in df_filtered.columns]
    colonnes_disponibles.extend([col for col in df_filtered.columns if col.startswith('q') and '_hf_total' in col][:10])
    
    st.dataframe(df_filtered[colonnes_disponibles], use_container_width=True)
    
    df_export = get_readable_columns(df_filtered)
    
    st.markdown("### 📥 Exporter les données")
    col1_export, col2_export, col3_export = st.columns(3)
    
    with col1_export:
        st.download_button(
            label="📥 CSV - Données brutes",
            data=df_export.to_csv(index=False).encode('utf-8'),
            file_name=f"stop_tb_donnees_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True
        )
    
    with col2_export:
        st.download_button(
            label="📥 Excel - Données brutes",
            data=to_excel(df_export),
            file_name=f"stop_tb_donnees_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3_export:
        st.download_button(
            label="📥 CSV - Données originales",
            data=df_filtered.to_csv(index=False).encode('utf-8'),
            file_name=f"stop_tb_original_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True
        )
    
    with st.expander("📖 Voir la correspondance des noms de colonnes"):
        col_mapping = pd.DataFrame({
            'Code original': list(COLUMN_RENAME_MAP.keys()),
            'Nom lisible': list(COLUMN_RENAME_MAP.values())
        })
        st.dataframe(col_mapping, use_container_width=True, height=400)
        
        st.download_button(
            label="📥 Télécharger le mapping (CSV)",
            data=col_mapping.to_csv(index=False).encode('utf-8'),
            file_name=f"mapping_colonnes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main():
    try:
        df = load_and_process_data()
        
        st.sidebar.header("🔍 Filtres")
        
        st.sidebar.markdown(
            '<a href="https://posaftbci.streamlit.app/" target="_blank" style="display: block; background-color: #ff7f0e; color: white; padding: 0.6rem 1rem; border-radius: 8px; text-decoration: none; font-weight: bold; text-align: center; margin-bottom: 1rem; border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🚀 Basculer vers TIFA TBCI</a>',
            unsafe_allow_html=True
        )
        
        st.sidebar.subheader("📍 Niveau géographique")
        niveau = st.sidebar.radio(
            "Sélectionnez le niveau",
            options=['National', 'Provincial', 'Zone Sante', 'Etablissement'],
            horizontal=True
        )
        
        province_selectionne = "Toutes"
        zone_sante_selectionne = "Toutes"
        facility_selectionne = "Tous"
        
        provinces_disponibles = df['province_name'].dropna().unique().tolist() if 'province_name' in df.columns else []
        provinces_disponibles = sorted([p for p in provinces_disponibles if p and str(p) != 'nan'])
        provinces_options = ['Toutes'] + provinces_disponibles
        
        if niveau == 'Provincial':
            province_selectionne = st.sidebar.selectbox("Sélectionnez la Province", options=provinces_options, index=0)
            
        elif niveau == 'Zone Sante':
            province_selectionne = st.sidebar.selectbox("Sélectionnez la Province", options=provinces_options, index=0)
            
            if province_selectionne and province_selectionne != 'Toutes':
                zones_disponibles = df[df['province_name'] == province_selectionne]['healthzone_name'].dropna().unique().tolist()
                zones_disponibles = sorted([z for z in zones_disponibles if z and str(z) != 'nan'])
                zones_options = ['Toutes'] + zones_disponibles
                zone_sante_selectionne = st.sidebar.selectbox("Sélectionnez la Zone de Santé", options=zones_options, index=0)
            else:
                st.sidebar.info("Sélectionnez d'abord une province")
            
        elif niveau == 'Etablissement':
            province_selectionne = st.sidebar.selectbox("Sélectionnez la Province", options=provinces_options, index=0)
            
            if province_selectionne and province_selectionne != 'Toutes':
                zones_disponibles = df[df['province_name'] == province_selectionne]['healthzone_name'].dropna().unique().tolist()
                zones_disponibles = sorted([z for z in zones_disponibles if z and str(z) != 'nan'])
                zones_options = ['Toutes'] + zones_disponibles
                zone_sante_selectionne = st.sidebar.selectbox("Sélectionnez la Zone de Santé", options=zones_options, index=0)
                
                if zone_sante_selectionne and zone_sante_selectionne != 'Toutes':
                    facilities_disponibles = df[(df['province_name'] == province_selectionne) & 
                                                (df['healthzone_name'] == zone_sante_selectionne)]['facility_name'].dropna().unique().tolist()
                    facilities_disponibles = sorted([f for f in facilities_disponibles if f and str(f) != 'nan'])
                    facilities_options = ['Tous'] + facilities_disponibles
                    facility_selectionne = st.sidebar.selectbox("Sélectionnez l'Établissement", options=facilities_options, index=0)
                else:
                    st.sidebar.info("Sélectionnez d'abord une Zone de Santé")
            else:
                st.sidebar.info("Sélectionnez d'abord une province")
        
        st.sidebar.subheader("📅 Période")
        type_periode = st.sidebar.radio("Type de période", options=['Mois', 'Trimestre'], horizontal=True)
        
        df_filtered = df.copy()
        mois_selectionne = None
        annee_selectionne = None
        trimestre_selectionne = None
        
        if type_periode == 'Mois':
            if 'mois_nom' in df.columns and 'qannee' in df.columns:
                mois_options = sorted(df['mois_nom'].dropna().unique())
                if mois_options:
                    mois_selectionne = st.sidebar.selectbox("Mois", options=mois_options)
                    annee_options = sorted(df['qannee'].dropna().unique())
                    annee_selectionne = st.sidebar.selectbox("Année", options=annee_options)
                    df_filtered = df_filtered[(df_filtered['mois_nom'] == mois_selectionne) & 
                                               (df_filtered['qannee'] == annee_selectionne)]
        else:
            if 'trimestre' in df.columns and 'qannee' in df.columns:
                trimestre_options = ['T1', 'T2', 'T3', 'T4']
                trimestre_selectionne = st.sidebar.selectbox("Trimestre", options=trimestre_options)
                annee_options = sorted(df['qannee'].dropna().unique())
                if annee_options:
                    annee_selectionne = st.sidebar.selectbox("Année", options=annee_options)
                    df_filtered = df_filtered[(df_filtered['trimestre'] == trimestre_selectionne) & 
                                               (df_filtered['qannee'] == annee_selectionne)]
        
        df_filtered = filter_by_hierarchy(df_filtered, niveau, province_selectionne, facility_selectionne, zone_sante_selectionne)
        
        df_previous = get_previous_period_df(
            df, type_periode, 
            mois_selectionne=mois_selectionne if type_periode == 'Mois' else None,
            annee_selectionne=annee_selectionne,
            trimestre_selectionne=trimestre_selectionne if type_periode == 'Trimestre' else None
        )
        
        df_previous = filter_by_hierarchy(
            df_previous, niveau, province_selectionne, facility_selectionne, zone_sante_selectionne
        )
        
        st.sidebar.info(f"📊 **{len(df_filtered)}** établissements affichés")
        if niveau == 'Provincial' and province_selectionne and province_selectionne != 'Toutes':
            st.sidebar.success(f"📍 Province : {province_selectionne}")
        elif niveau == 'Zone Sante' and zone_sante_selectionne and zone_sante_selectionne != 'Toutes':
            st.sidebar.success(f"🏥 Zone de Santé : {zone_sante_selectionne}")
        elif niveau == 'Etablissement' and facility_selectionne and facility_selectionne != 'Tous':
            st.sidebar.success(f"🏥 Établissement : {facility_selectionne}")
        elif niveau == 'National' or (niveau == 'Provincial' and province_selectionne == 'Toutes'):
            st.sidebar.success("🌍 Vue Nationale")
        
        show_kpi_cards(df_filtered, niveau, df_previous, type_periode)
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📈 Dépistage & Diagnostic",
            "💊 Traitement",
            "🛡️ Prévention (TPT)",
            "📊 Complétude & Promptitude",
            "📋 Données brutes",
            "💊 Gestion des Médicaments",
            "💰 Finances"
        ])
        
        with tab1:
            show_depistage_tab(df_filtered)
        with tab2:
            show_traitement_tab(df_filtered)
        with tab3:
            show_prevention_tab(df_filtered)
        with tab4:
            show_completude_promptitude_tab(df_filtered, niveau, province_selectionne, zone_sante_selectionne)
        with tab5:
            show_donnees_brutes_tab(df_filtered)
        with tab6:
            show_medicaments_tab(df_filtered)
        with tab7:
            show_finances_tab(df)
        
        st.markdown("---")
        st.markdown(f"*Dernière mise à jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
    except FileNotFoundError:
        st.error("❌ **Fichier `drc_stop_tb_data.csv` introuvable !**")
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
