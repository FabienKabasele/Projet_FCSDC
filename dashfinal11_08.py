import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import calendar
import io

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
    .download-btn {
        background-color: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<div class="main-header"><h1>🩺 Stop TB - Tableau de Bord FCSDS</h1><p>Suivi des activités de lutte contre la tuberculose</p></div>', unsafe_allow_html=True)

# ============================================================================
# DICTIONNAIRE DE RENOMMAGE DES COLONNES POUR L'EXPORT
# ============================================================================

COLUMN_RENAME_MAP = {
    # Informations générales
    'province_name': 'Province',
    'healthzone_name': 'Zone_de_Sante',
    'facility_name': 'Etablissement',
    'facility_id': 'ID_Etablissement',
    'mois_nom': 'Mois',
    'qannee': 'Annee',
    'trimestre': 'Trimestre',
    'date_saisie': 'Date_de_saisie',
    'jour_soumission': 'Jour_soumission',
    'mois_soumission': 'Mois_soumission',
    'annee_soumission': 'Annee_soumission',
    'est_prompt': 'Soumission_a_temps',
    'statut_promptitude': 'Statut_promptitude',
    
    # Section 1.0 - Personnes dépistées
    'q1_0_h': 'Depistage_Hommes',
    'q1_0_f': 'Depistage_Femmes',
    'q1_0_hf_total': 'Depistage_Total',
    'q1_0_age15m': 'Depistage_0_15_ans',
    'q1_0_age15p': 'Depistage_plus_15_ans',
    'q1_0_age_total': 'Depistage_Tous_ages',
    'q1_0_niv_sante': 'Depistage_Niveau_sante',
    'q1_0_niv_com': 'Depistage_Niveau_communautaire',
    'q1_0_niv_total': 'Depistage_Niveau_total',
    
    # Section 1.1 - Personnes ayant des symptômes
    'q1_1_h': 'Symptomatiques_Hommes',
    'q1_1_f': 'Symptomatiques_Femmes',
    'q1_1_hf_total': 'Symptomatiques_Total',
    'q1_1_age15m': 'Symptomatiques_0_15_ans',
    'q1_1_age15p': 'Symptomatiques_plus_15_ans',
    'q1_1_age_total': 'Symptomatiques_Tous_ages',
    'q1_1_niv_sante': 'Symptomatiques_Niveau_sante',
    'q1_1_niv_com': 'Symptomatiques_Niveau_communautaire',
    'q1_1_niv_total': 'Symptomatiques_Niveau_total',
    
    # Section 1.2 - Cas présumés TB
    'q1_2_h': 'Cas_presumes_Hommes',
    'q1_2_f': 'Cas_presumes_Femmes',
    'q1_2_hf_total': 'Cas_presumes_Total',
    'q1_2_age15m': 'Cas_presumes_0_15_ans',
    'q1_2_age15p': 'Cas_presumes_plus_15_ans',
    'q1_2_age_total': 'Cas_presumes_Tous_ages',
    'q1_2_niv_sante': 'Cas_presumes_Niveau_sante',
    'q1_2_niv_com': 'Cas_presumes_Niveau_communautaire',
    'q1_2_niv_total': 'Cas_presumes_Niveau_total',
    
    # Section 1.3 - Examens réalisés
    'q1_3_h': 'Examens_realises_Hommes',
    'q1_3_f': 'Examens_realises_Femmes',
    'q1_3_hf_total': 'Examens_realises_Total',
    'q1_3_age15m': 'Examens_realises_0_15_ans',
    'q1_3_age15p': 'Examens_realises_plus_15_ans',
    'q1_3_age_total': 'Examens_realises_Tous_ages',
    'q1_3_niv_sante': 'Examens_realises_Niveau_sante',
    'q1_3_niv_com': 'Examens_realises_Niveau_communautaire',
    'q1_3_niv_total': 'Examens_realises_Niveau_total',
    
    # Section 1.4 - Personnes éligibles au test Xpert
    'q1_4_h': 'Eligibles_Xpert_Hommes',
    'q1_4_f': 'Eligibles_Xpert_Femmes',
    'q1_4_hf_total': 'Eligibles_Xpert_Total',
    'q1_4_age15m': 'Eligibles_Xpert_0_15_ans',
    'q1_4_age15p': 'Eligibles_Xpert_plus_15_ans',
    'q1_4_age_total': 'Eligibles_Xpert_Tous_ages',
    
    # Section 1.5 - Testés Xpert
    'q1_5_h': 'Testes_Xpert_Hommes',
    'q1_5_f': 'Testes_Xpert_Femmes',
    'q1_5_hf_total': 'Testes_Xpert_Total',
    'q1_5_age15m': 'Testes_Xpert_0_15_ans',
    'q1_5_age15p': 'Testes_Xpert_plus_15_ans',
    'q1_5_age_total': 'Testes_Xpert_Tous_ages',
    
    # Section 2.0 - TB détectée
    'q2_0_h': 'TB_detectee_Hommes',
    'q2_0_f': 'TB_detectee_Femmes',
    'q2_0_hf_total': 'TB_detectee_Total',
    'q2_0_age15m': 'TB_detectee_0_15_ans',
    'q2_0_age15p': 'TB_detectee_plus_15_ans',
    'q2_0_age_total': 'TB_detectee_Tous_ages',
    
    # Section 2.1 - TB confirmée bactériologiquement
    'q2_1_h': 'TB_confirmee_bacterio_Hommes',
    'q2_1_f': 'TB_confirmee_bacterio_Femmes',
    'q2_1_hf_total': 'TB_confirmee_bacterio_Total',
    'q2_1_age15m': 'TB_confirmee_bacterio_0_15_ans',
    'q2_1_age15p': 'TB_confirmee_bacterio_plus_15_ans',
    'q2_1_age_total': 'TB_confirmee_bacterio_Tous_ages',
    
    # Section 2.2 - TB confirmée cliniquement
    'q2_2_h': 'TB_confirmee_clinique_Hommes',
    'q2_2_f': 'TB_confirmee_clinique_Femmes',
    'q2_2_hf_total': 'TB_confirmee_clinique_Total',
    'q2_2_age15m': 'TB_confirmee_clinique_0_15_ans',
    'q2_2_age15p': 'TB_confirmee_clinique_plus_15_ans',
    'q2_2_age_total': 'TB_confirmee_clinique_Tous_ages',
    
    # Section 3.0 - Traitement DS-TB débuté
    'q3_0_h': 'Traitement_DS_debute_Hommes',
    'q3_0_f': 'Traitement_DS_debute_Femmes',
    'q3_0_hf_total': 'Traitement_DS_debute_Total',
    'q3_0_age15m': 'Traitement_DS_debute_0_15_ans',
    'q3_0_age15p': 'Traitement_DS_debute_plus_15_ans',
    'q3_0_age_total': 'Traitement_DS_debute_Tous_ages',
    
    # Section 3.4 - Nouveaux cas et rechutes par âge et sexe
    'q3_4_g04': 'Nouveaux_cas_0_4_ans_Hommes',
    'q3_4_g514': 'Nouveaux_cas_5_14_ans_Hommes',
    'q3_4_h1524': 'Nouveaux_cas_15_24_ans_Hommes',
    'q3_4_h2534': 'Nouveaux_cas_25_34_ans_Hommes',
    'q3_4_h3544': 'Nouveaux_cas_35_44_ans_Hommes',
    'q3_4_h4554': 'Nouveaux_cas_45_54_ans_Hommes',
    'q3_4_h5564': 'Nouveaux_cas_55_64_ans_Hommes',
    'q3_4_h65p': 'Nouveaux_cas_plus_65_ans_Hommes',
    'q3_4_f04': 'Nouveaux_cas_0_4_ans_Femmes',
    'q3_4_f514': 'Nouveaux_cas_5_14_ans_Femmes',
    'q3_4_f1524': 'Nouveaux_cas_15_24_ans_Femmes',
    'q3_4_f2534': 'Nouveaux_cas_25_34_ans_Femmes',
    'q3_4_f3544': 'Nouveaux_cas_35_44_ans_Femmes',
    'q3_4_f4554': 'Nouveaux_cas_45_54_ans_Femmes',
    'q3_4_f5564': 'Nouveaux_cas_55_64_ans_Femmes',
    'q3_4_f65p': 'Nouveaux_cas_plus_65_ans_Femmes',
    'q3_4_h_total': 'Nouveaux_cas_Total_Hommes',
    'q3_4_f_total': 'Nouveaux_cas_Total_Femmes',
    'q3_4_hf_total': 'Nouveaux_cas_Total_General',
    
    # Section 4.0 - Testés pour résistance RR/MDR
    'q4_0_h': 'Testes_resistance_Hommes',
    'q4_0_f': 'Testes_resistance_Femmes',
    'q4_0_hf_total': 'Testes_resistance_Total',
    'q4_0_age15m': 'Testes_resistance_0_15_ans',
    'q4_0_age15p': 'Testes_resistance_plus_15_ans',
    'q4_0_age_total': 'Testes_resistance_Tous_ages',
    
    # Section 4.1 - Diagnostiqués RR/MDR
    'q4_1_h': 'Diagnostiques_RRMDR_Hommes',
    'q4_1_f': 'Diagnostiques_RRMDR_Femmes',
    'q4_1_hf_total': 'Diagnostiques_RRMDR_Total',
    'q4_1_age15m': 'Diagnostiques_RRMDR_0_15_ans',
    'q4_1_age15p': 'Diagnostiques_RRMDR_plus_15_ans',
    'q4_1_age_total': 'Diagnostiques_RRMDR_Tous_ages',
    
    # Section 5.0 - Traitement RR/MDR débuté
    'q5_0_h': 'Traitement_RRMDR_debute_Hommes',
    'q5_0_f': 'Traitement_RRMDR_debute_Femmes',
    'q5_0_hf_total': 'Traitement_RRMDR_debute_Total',
    'q5_0_age15m': 'Traitement_RRMDR_debute_0_15_ans',
    'q5_0_age15p': 'Traitement_RRMDR_debute_plus_15_ans',
    'q5_0_age_total': 'Traitement_RRMDR_debute_Tous_ages',
    
    # Section 6.0 - Traitement DS réussi
    'q6_0_h': 'Traitement_DS_reussi_Hommes',
    'q6_0_f': 'Traitement_DS_reussi_Femmes',
    'q6_0_hf_total': 'Traitement_DS_reussi_Total',
    'q6_0_age15m': 'Traitement_DS_reussi_0_15_ans',
    'q6_0_age15p': 'Traitement_DS_reussi_plus_15_ans',
    'q6_0_age_total': 'Traitement_DS_reussi_Tous_ages',
    
    # Section 7.0 - Traitement RR/MDR réussi
    'q7_0_h': 'Traitement_RRMDR_reussi_Hommes',
    'q7_0_f': 'Traitement_RRMDR_reussi_Femmes',
    'q7_0_hf_total': 'Traitement_RRMDR_reussi_Total',
    'q7_0_age15m': 'Traitement_RRMDR_reussi_0_15_ans',
    'q7_0_age15p': 'Traitement_RRMDR_reussi_plus_15_ans',
    'q7_0_age_total': 'Traitement_RRMDR_reussi_Tous_ages',
    
    # Section 8.0 - Dépistage TPT
    'q8_0_h': 'TPT_depistage_Hommes',
    'q8_0_f': 'TPT_depistage_Femmes',
    'q8_0_hf_total': 'TPT_depistage_Total',
    'q8_0_age5m': 'TPT_depistage_0_5_ans',
    'q8_0_age5p': 'TPT_depistage_plus_5_ans',
    'q8_0_age_total': 'TPT_depistage_Tous_ages',
    
    # Section 8.1 - Contacts TPT
    'q8_1_h': 'TPT_contacts_Hommes',
    'q8_1_f': 'TPT_contacts_Femmes',
    'q8_1_hf_total': 'TPT_contacts_Total',
    'q8_1_age5m': 'TPT_contacts_0_5_ans',
    'q8_1_age5p': 'TPT_contacts_plus_5_ans',
    'q8_1_age_total': 'TPT_contacts_Tous_ages',
    
    # Section 8.2 - PVVIH TPT
    'q8_2_h': 'TPT_PVVIH_Hommes',
    'q8_2_f': 'TPT_PVVIH_Femmes',
    'q8_2_hf_total': 'TPT_PVVIH_Total',
    'q8_2_age5m': 'TPT_PVVIH_0_5_ans',
    'q8_2_age5p': 'TPT_PVVIH_plus_5_ans',
    'q8_2_age_total': 'TPT_PVVIH_Tous_ages',
    
    # Section 8.3 - Autres groupes TPT
    'q8_3_h': 'TPT_autres_groupes_Hommes',
    'q8_3_f': 'TPT_autres_groupes_Femmes',
    'q8_3_hf_total': 'TPT_autres_groupes_Total',
    'q8_3_age5m': 'TPT_autres_groupes_0_5_ans',
    'q8_3_age5p': 'TPT_autres_groupes_plus_5_ans',
    'q8_3_age_total': 'TPT_autres_groupes_Tous_ages',
    
    # Section 8.4 - Éligibles TPT (Contacts)
    'q8_4_h': 'TPT_eligibles_contacts_Hommes',
    'q8_4_f': 'TPT_eligibles_contacts_Femmes',
    'q8_4_hf_total': 'TPT_eligibles_contacts_Total',
    'q8_4_age5m': 'TPT_eligibles_contacts_0_5_ans',
    'q8_4_age5p': 'TPT_eligibles_contacts_plus_5_ans',
    'q8_4_age_total': 'TPT_eligibles_contacts_Tous_ages',
    
    # Section 8.5 - Éligibles TPT (PVVIH)
    'q8_5_h': 'TPT_eligibles_PVVIH_Hommes',
    'q8_5_f': 'TPT_eligibles_PVVIH_Femmes',
    'q8_5_hf_total': 'TPT_eligibles_PVVIH_Total',
    'q8_5_age15m': 'TPT_eligibles_PVVIH_0_15_ans',
    'q8_5_age15p': 'TPT_eligibles_PVVIH_plus_15_ans',
    'q8_5_age_total': 'TPT_eligibles_PVVIH_Tous_ages',
    
    # Section 8.6 - Éligibles TPT (Autres)
    'q8_6_h': 'TPT_eligibles_autres_Hommes',
    'q8_6_f': 'TPT_eligibles_autres_Femmes',
    'q8_6_hf_total': 'TPT_eligibles_autres_Total',
    'q8_6_age5m': 'TPT_eligibles_autres_0_5_ans',
    'q8_6_age5p': 'TPT_eligibles_autres_plus_5_ans',
    'q8_6_age_total': 'TPT_eligibles_autres_Tous_ages',
    
    # Section 9.0 - TPT commencé (Contacts)
    'q9_0': 'TPT_commence_contacts',
    'q9_1_h': 'TPT_commence_contacts_Hommes',
    'q9_1_f': 'TPT_commence_contacts_Femmes',
    'q9_1_hf_total': 'TPT_commence_contacts_Total',
    'q9_1_age5m': 'TPT_commence_contacts_0_5_ans',
    'q9_1_age5p': 'TPT_commence_contacts_plus_5_ans',
    'q9_1_age_total': 'TPT_commence_contacts_Tous_ages',
    
    # Section 9.2 - TPT commencé (PVVIH)
    'q9_2_h': 'TPT_commence_PVVIH_Hommes',
    'q9_2_f': 'TPT_commence_PVVIH_Femmes',
    'q9_2_hf_total': 'TPT_commence_PVVIH_Total',
    'q9_2_age15m': 'TPT_commence_PVVIH_0_15_ans',
    'q9_2_age15p': 'TPT_commence_PVVIH_plus_15_ans',
    'q9_2_age_total': 'TPT_commence_PVVIH_Tous_ages',
    
    # Section 9.3 - TPT commencé (Autres)
    'q9_3_h': 'TPT_commence_autres_Hommes',
    'q9_3_f': 'TPT_commence_autres_Femmes',
    'q9_3_hf_total': 'TPT_commence_autres_Total',
    'q9_3_age5m': 'TPT_commence_autres_0_5_ans',
    'q9_3_age5p': 'TPT_commence_autres_plus_5_ans',
    'q9_3_age_total': 'TPT_commence_autres_Tous_ages',
    
    # Section 10.0 - TPT terminé (Contacts)
    'q10_0_h': 'TPT_termine_contacts_Hommes',
    'q10_0_f': 'TPT_termine_contacts_Femmes',
    'q10_0_hf_total': 'TPT_termine_contacts_Total',
    'q10_0_age5m': 'TPT_termine_contacts_0_5_ans',
    'q10_0_age5p': 'TPT_termine_contacts_plus_5_ans',
    'q10_0_age_total': 'TPT_termine_contacts_Tous_ages',
    
    # Section 10.1 - TPT terminé (PVVIH)
    'q10_1_h': 'TPT_termine_PVVIH_Hommes',
    'q10_1_f': 'TPT_termine_PVVIH_Femmes',
    'q10_1_hf_total': 'TPT_termine_PVVIH_Total',
    'q10_1_age5m': 'TPT_termine_PVVIH_0_5_ans',
    'q10_1_age5p': 'TPT_termine_PVVIH_plus_5_ans',
    'q10_1_age_total': 'TPT_termine_PVVIH_Tous_ages',
    
    # Section 10.2 - TPT terminé (Autres)
    'q10_2_h': 'TPT_termine_autres_Hommes',
    'q10_2_f': 'TPT_termine_autres_Femmes',
    'q10_2_hf_total': 'TPT_termine_autres_Total',
    'q10_2_age5m': 'TPT_termine_autres_0_5_ans',
    'q10_2_age5p': 'TPT_termine_autres_plus_5_ans',
    'q10_2_age_total': 'TPT_termine_autres_Tous_ages',
    
    # Indicateurs calculés
    'xpert_test_rate': 'Taux_test_Xpert',
    'rrmdr_detection_rate': 'Taux_detection_RRMDR',
    'tpt_coverage': 'Couverture_TPT',
    'tpt_completion_rate': "Taux_achevement_TPT",
    'tpt_eligible_total': 'TPT_Eligibles_Total',
    'tpt_started_total': 'TPT_Commence_Total',
    'tpt_completed_total': 'TPT_Termine_Total',
    'enfants_moins_5_depistes': 'Enfants_moins_5_ans_depistes',
    'enfants_moins_5_eligibles': 'Enfants_moins_5_ans_eligibles',
    'enfants_moins_5_commences': 'Enfants_moins_5_ans_TPT_commence',
    'enfants_moins_5_termines': 'Enfants_moins_5_ans_TPT_termine',
}

def get_readable_column_name(col):
    """Retourne le nom lisible d'une colonne"""
    return COLUMN_RENAME_MAP.get(col, col)

def get_readable_columns(df):
    """Renomme toutes les colonnes du DataFrame avec des noms lisibles"""
    return df.rename(columns=COLUMN_RENAME_MAP)

def to_excel(df):
    """Convertit un DataFrame en fichier Excel (bytes)"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Donnees')
    return output.getvalue()

# ============================================================================
# DONNÉES DE RÉFÉRENCE POUR LA COMPLÉTUDE
# ============================================================================

ZS_CDT_REFERENCE = pd.DataFrame({
    'Province': [
        'Haut Katanga', 'Haut Lomami', 'Kasai Oriental', 'Kasai Central',
        'Lualaba', 'Lomami', 'Sud Kivu', 'Sankuru', 'Tanganyika'
    ],
    'ZS_attendues': [27, 16, 19, 25, 14, 16, 31, 16, 11],
    'CDT_attendus': [107, 74, 132, 109, 75, 106, 132, 93, 68]
})

DATE_LIMITE_JOUR = 7

# ============================================================================
# FONCTIONS DE TRAITEMENT DES DONNÉES
# ============================================================================

def clean_province_name(name):
    """Nettoie et uniformise les noms de provinces"""
    if pd.isna(name):
        return None
    
    name = str(name).strip()
    
    mapping = {
        'haut katanga': 'Haut Katanga',
        'hautkatanga': 'Haut Katanga',
        'katanga': 'Haut Katanga',
        'haut lomami': 'Haut Lomami',
        'hautlomami': 'Haut Lomami',
        'lomami': 'Lomami',
        'kasai oriental': 'Kasai Oriental',
        'kasaioriental': 'Kasai Oriental',
        'kasai central': 'Kasai Central',
        'kasaicentral': 'Kasai Central',
        'lualaba': 'Lualaba',
        'sud kivu': 'Sud Kivu',
        'sudkivu': 'Sud Kivu',
        'sankuru': 'Sankuru',
        'tanganyika': 'Tanganyika'
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

@st.cache_data
def load_and_process_data():
    """Charge le fichier CSV et recrée tous les calculs"""
    df = pd.read_csv('drc_stop_tb_data.csv')
    
    # Extraction des informations géographiques
    if 'q010b' in df.columns:
        df['province_name_raw'] = df['q010b']
        df['province_name'] = df['q010b'].apply(clean_province_name)
    
    if 'q011b' in df.columns:
        df['healthzone_name'] = df['q011b']
    
    if 'q012b' in df.columns:
        df['facility_name'] = df['q012b']
    
    if 'q012a' in df.columns:
        df['facility_id'] = df['q012a']
    
    # Conversion de la date de saisie
    if 'q001a' in df.columns:
        df['date_saisie'] = pd.to_datetime(df['q001a'], format='%d/%m/%Y', errors='coerce')
        df['jour_soumission'] = df['date_saisie'].dt.day
        df['mois_soumission'] = df['date_saisie'].dt.month
        df['annee_soumission'] = df['date_saisie'].dt.year
        df['est_prompt'] = df['jour_soumission'] <= DATE_LIMITE_JOUR
        df['statut_promptitude'] = df['est_prompt'].map({True: 'À temps', False: 'En retard'})
    
    # Ajout du trimestre
    if 'qmois' in df.columns:
        mois_num = df['qmois'].str.extract(r'(\d+)')[0].astype(float)
        mois_num = mois_num.fillna(0)
        trimestre_calc = np.ceil(mois_num / 3)
        trimestre_calc = trimestre_calc.replace(0, np.nan)
        df['trimestre'] = trimestre_calc.astype('Int64')
        df['trimestre'] = df['trimestre'].map({1: 'T1', 2: 'T2', 3: 'T3', 4: 'T4'})
    
    # ==================== SECTION 1.0 à 10.2 ====================
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
    
    # Calculs des totaux
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
    
    # INDICATEURS TPT
    df['tpt_eligible_total'] = df['q8_4_hf_total'] + df['q8_5_hf_total'] + df['q8_6_hf_total']
    df['tpt_started_total'] = df['q9_1_hf_total'] + df['q9_2_hf_total'] + df['q9_3_hf_total']
    df['tpt_completed_total'] = df['q10_0_hf_total'] + df['q10_1_hf_total'] + df['q10_2_hf_total']
    
    df['enfants_moins_5_depistes'] = df['q8_0_age5m']
    df['enfants_moins_5_eligibles'] = df['q8_4_age5m']
    df['enfants_moins_5_commences'] = df['q9_1_age5m']
    df['enfants_moins_5_termines'] = df['q10_0_age5m']
    
    # Taux (uniquement ceux qui sont valides sans suivi de cohorte)
    df['xpert_test_rate'] = np.where(df['q1_4_hf_total'] > 0, 
                                      df['q1_5_hf_total'] / df['q1_4_hf_total'] * 100, 0)
    df['rrmdr_detection_rate'] = np.where(df['q4_0_hf_total'] > 0,
                                           df['q4_1_hf_total'] / df['q4_0_hf_total'] * 100, 0)
    df['tpt_coverage'] = np.where(df['tpt_eligible_total'] > 0,
                                  df['tpt_started_total'] / df['tpt_eligible_total'] * 100, 0)
    df['tpt_completion_rate'] = np.where(df['tpt_started_total'] > 0,
                                         df['tpt_completed_total'] / df['tpt_started_total'] * 100, 0)
    
    # Mapping des mois
    mois_map = {
        'mois_1': 'Janvier', 'mois_2': 'Février', 'mois_3': 'Mars',
        'mois_4': 'Avril', 'mois_5': 'Mai', 'mois_6': 'Juin',
        'mois_7': 'Juillet', 'mois_8': 'Août', 'mois_9': 'Septembre',
        'mois_10': 'Octobre', 'mois_11': 'Novembre', 'mois_12': 'Décembre'
    }
    if 'qmois' in df.columns:
        df['mois_nom'] = df['qmois'].map(mois_map)
    
    # Supprimer les lignes avec province_name NULL
    df = df[df['province_name'].notna()]
    
    return df

def filter_by_hierarchy(df, niveau, province=None, facility=None, zone_sante=None):
    """Filtre les données selon le niveau hiérarchique"""
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

# ============================================================================
# FONCTIONS DE VISUALISATION
# ============================================================================

def show_kpi_cards(df_filtered, niveau):
    """Affiche les cartes KPI avec badge de niveau"""
    
    if niveau == 'National':
        st.markdown('<div class="national-badge">🌍 NIVEAU NATIONAL</div>', unsafe_allow_html=True)
    elif niveau == 'Provincial':
        st.markdown('<div class="provincial-badge">📍 NIVEAU PROVINCIAL</div>', unsafe_allow_html=True)
    elif niveau == 'Zone Sante':
        st.markdown('<div class="zs-badge">🏥 NIVEAU ZONE DE SANTÉ</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="facility-badge">🏥 NIVEAU ÉTABLISSEMENT</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("👥 Personnes dépistées", f"{df_filtered['q1_0_hf_total'].sum():,.0f}")
    with col2:
        st.metric("🔬 Cas présumés", f"{df_filtered['q1_2_hf_total'].sum():,.0f}")
    with col3:
        st.metric("🧪 Testés Xpert", f"{df_filtered['q1_5_hf_total'].sum():,.0f}")
    with col4:
        st.metric("🦠 TB détectée", f"{df_filtered['q2_0_hf_total'].sum():,.0f}")
    with col5:
        st.metric("💊 Traitements DS débutés", f"{df_filtered['q3_0_hf_total'].sum():,.0f}")
    with col6:
        tpt_cov = df_filtered['tpt_coverage'].mean()
        st.metric("🛡️ Couverture TPT", f"{tpt_cov:.1f}%")

def show_depistage_tab(df_filtered):
    """Onglet Dépistage et Diagnostic"""
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
    """Onglet Traitement - Sans taux de succès (besoin de suivi de cohorte)"""
    st.subheader("💊 Résultats du traitement")
    
    # Note explicative
    st.info("ℹ️ **Note importante :** Les taux de succès des traitements DS-TB et RR/MDR nécessitent un suivi de cohorte respectivement sur 12 et 24 mois. Ils ne peuvent pas être calculés à partir des données mensuelles de ce dashboard. Les chiffres ci-dessous montrent les effectifs de patients ayant débuté et terminé leur traitement.")
    
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
        df_filtered['q3_4_g04'].sum(),
        df_filtered['q3_4_g514'].sum(),
        df_filtered['q3_4_h1524'].sum(),
        df_filtered['q3_4_h2534'].sum(),
        df_filtered['q3_4_h3544'].sum(),
        df_filtered['q3_4_h4554'].sum(),
        df_filtered['q3_4_h5564'].sum(),
        df_filtered['q3_4_h65p'].sum()
    ]
    
    femmes_data = [
        df_filtered['q3_4_f04'].sum(),
        df_filtered['q3_4_f514'].sum(),
        df_filtered['q3_4_f1524'].sum(),
        df_filtered['q3_4_f2534'].sum(),
        df_filtered['q3_4_f3544'].sum(),
        df_filtered['q3_4_f4554'].sum(),
        df_filtered['q3_4_f5564'].sum(),
        df_filtered['q3_4_f65p'].sum()
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
    """Onglet Prévention TPT avec focus enfants <5 ans"""
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

def show_logistique_tab(df_filtered):
    """Onglet Logistique"""
    st.subheader("📦 Gestion des stocks et intrants")
    
    produits = {
        'Cartouches Xpert MTB/RIF': {
            'initial': 'xpert_stock_initial',
            'physique': 'xpert_stock_physique',
            'rupture': 'xpert_jours_rupture',
            'expiration': 'xpert_quantite_expiration'
        },
        'Ethambutol (E) 100 mg': {
            'initial': 'e100_stock_initial',
            'physique': 'e100_stock_physique',
            'rupture': 'e100_jours_rupture',
            'expiration': 'e100_quantite_expiration'
        },
        'RHZE 150/75/400/275 mg': {
            'initial': 'rhze_stock_initial',
            'physique': 'rhze_stock_physique',
            'rupture': 'rhze_jours_rupture',
            'expiration': 'rhze_quantite_expiration'
        },
        'RH 150/75 mg': {
            'initial': 'rh150_stock_initial',
            'physique': 'rh150_stock_physique',
            'rupture': 'rh150_jours_rupture',
            'expiration': 'rh150_quantite_expiration'
        },
        'RH 75/50 mg': {
            'initial': 'rh75_stock_initial',
            'physique': 'rh75_stock_physique',
            'rupture': 'rh75_jours_rupture',
            'expiration': 'rh75_quantite_expiration'
        }
    }
    
    for produit, colonnes in produits.items():
        with st.expander(f"📊 {produit}"):
            if all(col in df_filtered.columns for col in colonnes.values()):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Stock initial", f"{df_filtered[colonnes['initial']].sum():,.0f}")
                with col2:
                    st.metric("Stock physique", f"{df_filtered[colonnes['physique']].sum():,.0f}")
                with col3:
                    jours_rupture = df_filtered[colonnes['rupture']].sum()
                    st.metric("Jours de rupture", f"{jours_rupture:.0f}")
                with col4:
                    qte_expiration = df_filtered[colonnes['expiration']].sum()
                    st.metric("Expiration <6 mois", f"{qte_expiration:.0f}")
                
                if jours_rupture > 0:
                    st.warning(f"⚠️ Rupture de stock : {jours_rupture:.0f} jours")
                if qte_expiration > 0:
                    st.error(f"🔴 Expiration imminente : {qte_expiration:.0f} unités")
            else:
                st.info(f"Données non disponibles pour {produit}")

# ============================================================================
# FONCTIONS DE COMPLÉTUDE ET PROMPTITUDE
# ============================================================================

def show_completude_promptitude_tab(df, niveau=None, province_selectionne=None, zone_sante_selectionne=None):
    """Onglet Complétude et Promptitude avec tableau récapitulatif par province, ZS ou établissement"""
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
    """Affiche le résumé par province"""
    if 'province_name' in df.columns:
        completeness = df.groupby('province_name').agg({
            'healthzone_name': 'nunique',
            'facility_name': 'nunique',
            'q1_0_hf_total': 'sum',
            'q1_2_hf_total': 'sum',
            'q2_0_hf_total': 'sum',
            'q3_0_hf_total': 'sum',
            'q4_0_hf_total': 'sum',
            'q5_0_hf_total': 'sum',
            'q8_0_hf_total': 'sum',
            'tpt_started_total': 'sum'
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
            if col not in ['Province', 'Performance']:
                df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
        
        st.dataframe(df_affichage, use_container_width=True, height=400)
        
        # Export avec noms lisibles
        col_rename_export = {
            'Province': 'Province',
            'ZS_attendues': 'Zones_de_Sante_attendues',
            'ZS_soumises': 'Zones_de_Sante_soumises',
            'Taux_ZS': 'Taux_completude_ZS',
            'CDT_attendus': 'CDT_attendus',
            'CDT_soumis': 'CDT_soumis',
            'Taux_CDT': 'Taux_completude_CDT',
            'Dépistages': 'Depistages',
            'Cas_présumés': 'Cas_presumes',
            'TB_détectée': 'TB_detectee',
            'Traitement_DS': 'Traitement_DS_debute',
            'Test_RR': 'Test_resistance_RR',
            'Traitement_RR': 'Traitement_RR_debute',
            'Dépistés_TPT': 'Depistes_TPT',
            'TPT_commencé': 'TPT_commence',
            'Performance': 'Performance'
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
    """Affiche le détail par Zone de Santé pour une province spécifique"""
    
    df_province = df[df['province_name'] == province]
    
    detail_zs = df_province.groupby('healthzone_name').agg({
        'facility_name': 'nunique',
        'q1_0_hf_total': 'sum',
        'q1_2_hf_total': 'sum',
        'q2_0_hf_total': 'sum',
        'q3_0_hf_total': 'sum',
        'q4_0_hf_total': 'sum',
        'q5_0_hf_total': 'sum',
        'q8_0_hf_total': 'sum',
        'tpt_started_total': 'sum'
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
    
    # Export avec noms lisibles
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
            detail_zs,
            x='Zone de Santé',
            y='Dépistages',
            title=f"Dépistages par Zone de Santé - {province}",
            color='Dépistages',
            color_continuous_scale='Blues',
            text='Dépistages'
        )
        fig_depistages.update_traces(textposition='outside')
        fig_depistages.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_depistages, use_container_width=True)
    
    with col_g2:
        fig_tb = px.bar(
            detail_zs,
            x='Zone de Santé',
            y='TB_détectée',
            title=f"TB détectée par Zone de Santé - {province}",
            color='TB_détectée',
            color_continuous_scale='Reds',
            text='TB_détectée'
        )
        fig_tb.update_traces(textposition='outside')
        fig_tb.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_tb, use_container_width=True)

def show_detail_etablissement(df, zone_sante):
    """Affiche le détail par Établissement pour une Zone de Santé spécifique"""
    
    df_zs = df[df['healthzone_name'] == zone_sante]
    
    detail_etab = df_zs.groupby('facility_name').agg({
        'q1_0_hf_total': 'sum',
        'q1_2_hf_total': 'sum',
        'q2_0_hf_total': 'sum',
        'q3_0_hf_total': 'sum',
        'q4_0_hf_total': 'sum',
        'q5_0_hf_total': 'sum',
        'q8_0_hf_total': 'sum',
        'tpt_started_total': 'sum'
    }).reset_index()
    
    detail_etab.columns = ['Établissement', 
                           'Dépistages', 'Cas_présumés', 'TB_détectée',
                           'Traitement_DS', 'Test_RR', 'Traitement_RR',
                           'Dépistés_TPT', 'TPT_commencé']
    
    detail_etab = detail_etab.fillna(0)
    
    province = df_zs['province_name'].iloc[0] if len(df_zs) > 0 else ""
    
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
    
    # Export avec noms lisibles
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
            detail_etab,
            x='Établissement',
            y='Dépistages',
            title=f"Dépistages par Établissement - {zone_sante}",
            color='Dépistages',
            color_continuous_scale='Blues',
            text='Dépistages'
        )
        fig_depistages.update_traces(textposition='outside')
        fig_depistages.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_depistages, use_container_width=True)
    
    with col_g2:
        fig_tb = px.bar(
            detail_etab,
            x='Établissement',
            y='TB_détectée',
            title=f"TB détectée par Établissement - {zone_sante}",
            color='TB_détectée',
            color_continuous_scale='Reds',
            text='TB_détectée'
        )
        fig_tb.update_traces(textposition='outside')
        fig_tb.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_tb, use_container_width=True)
    
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        fig_traitement = px.bar(
            detail_etab,
            x='Établissement',
            y='Traitement_DS',
            title=f"Traitements DS-TB par Établissement - {zone_sante}",
            color='Traitement_DS',
            color_continuous_scale='Greens',
            text='Traitement_DS'
        )
        fig_traitement.update_traces(textposition='outside')
        fig_traitement.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_traitement, use_container_width=True)
    
    with col_g4:
        fig_tpt = px.bar(
            detail_etab,
            x='Établissement',
            y='TPT_commencé',
            title=f"TPT commencé par Établissement - {zone_sante}",
            color='TPT_commencé',
            color_continuous_scale='Purples',
            text='TPT_commencé'
        )
        fig_tpt.update_traces(textposition='outside')
        fig_tpt.update_layout(xaxis_tickangle=45, height=400)
        st.plotly_chart(fig_tpt, use_container_width=True)

def show_performance_graphs(completeness):
    """Affiche les graphiques de performance"""
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig_zs = go.Figure()
        fig_zs.add_trace(go.Bar(
            x=completeness['Province'],
            y=completeness['Taux_ZS'],
            text=completeness['Taux_ZS'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=completeness['Taux_ZS'].apply(
                lambda x: '#28a745' if x >= 100 else '#ffc107' if x >= 80 else '#dc3545'
            )
        ))
        fig_zs.update_layout(
            title="Taux de complétude des Zones de Santé",
            xaxis_title="Province",
            yaxis_title="Taux (%)",
            height=400,
            yaxis_range=[0, 120],
            showlegend=False
        )
        fig_zs.add_hline(y=100, line_dash="dash", line_color="green", 
                        annotation_text="Cible 100%")
        fig_zs.add_hline(y=80, line_dash="dash", line_color="orange", 
                        annotation_text="Seuil minimal 80%")
        st.plotly_chart(fig_zs, use_container_width=True)
    
    with col_g2:
        fig_cdt = go.Figure()
        fig_cdt.add_trace(go.Bar(
            x=completeness['Province'],
            y=completeness['Taux_CDT'],
            text=completeness['Taux_CDT'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=completeness['Taux_CDT'].apply(
                lambda x: '#28a745' if x >= 100 else '#ffc107' if x >= 80 else '#dc3545'
            )
        ))
        fig_cdt.update_layout(
            title="Taux de complétude des CDT",
            xaxis_title="Province",
            yaxis_title="Taux (%)",
            height=400,
            yaxis_range=[0, 120],
            showlegend=False
        )
        fig_cdt.add_hline(y=100, line_dash="dash", line_color="green", 
                         annotation_text="Cible 100%")
        fig_cdt.add_hline(y=80, line_dash="dash", line_color="orange", 
                         annotation_text="Seuil minimal 80%")
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

def show_donnees_brutes_tab(df_filtered):
    """Onglet Données brutes avec export en CSV et Excel"""
    st.subheader("📋 Aperçu des données collectées")
    
    colonnes_a_afficher = ['province_name', 'healthzone_name', 'facility_name', 'mois_nom', 'qannee', 'trimestre']
    colonnes_disponibles = [col for col in colonnes_a_afficher if col in df_filtered.columns]
    colonnes_disponibles.extend([col for col in df_filtered.columns if col.startswith('q') and '_hf_total' in col][:10])
    
    st.dataframe(df_filtered[colonnes_disponibles], use_container_width=True)
    
    # Export avec noms de colonnes lisibles
    df_export = get_readable_columns(df_filtered)
    
    st.markdown("### 📥 Exporter les données")
    col1_export, col2_export, col3_export = st.columns(3)
    
    with col1_export:
        st.download_button(
            label="📥 CSV - Données brutes",
            data=df_export.to_csv(index=False).encode('utf-8'),
            file_name=f"stop_tb_donnees_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
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
        # Export des données filtrées avec les noms originaux (pour compatibilité)
        st.download_button(
            label="📥 CSV - Données originales",
            data=df_filtered.to_csv(index=False).encode('utf-8'),
            file_name=f"stop_tb_original_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Afficher un aperçu des noms de colonnes
    with st.expander("📖 Voir la correspondance des noms de colonnes"):
        col_mapping = pd.DataFrame({
            'Code original': list(COLUMN_RENAME_MAP.keys()),
            'Nom lisible': list(COLUMN_RENAME_MAP.values())
        })
        st.dataframe(col_mapping, use_container_width=True, height=400)
        
        # Export du mapping
        st.download_button(
            label="📥 Télécharger le mapping (CSV)",
            data=col_mapping.to_csv(index=False).encode('utf-8'),
            file_name=f"mapping_colonnes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ============================================================================
# ONGLET STOCKS PAR PROVINCE
# ============================================================================

def safe_int_convert(value):
    """Convertit une valeur en entier de manière sécurisée"""
    try:
        if pd.isna(value) or np.isinf(value) or np.isnan(value):
            return 0
        return int(value)
    except (ValueError, TypeError):
        return 0

def show_stocks_province_tab(df):
    """Onglet 7 : Gestion des stocks par province"""
    st.subheader("📊 Gestion des stocks par province")
    st.markdown("**Analyse des stocks :** Consommation Moyenne Mensuelle (CMM) vs Stock Disponible")
    
    colonnes_necessaires = ['province_name', 'q_cmm', 'q_stock_disp', 'stock_pro', 'stock_cdr']
    colonnes_manquantes = [col for col in colonnes_necessaires if col not in df.columns]
    
    if colonnes_manquantes:
        st.warning(f"⚠️ Colonnes manquantes dans les données : {', '.join(colonnes_manquantes)}")
        with st.expander("🔍 Voir les colonnes disponibles"):
            st.write(list(df.columns))
        return
    
    for col in ['q_cmm', 'q_stock_disp', 'stock_pro', 'stock_cdr']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[col] = df[col].replace([np.inf, -np.inf], 0)
    
    stocks_province = df.groupby('province_name').agg({
        'q_cmm': 'sum',
        'q_stock_disp': 'sum',
        'stock_pro': 'sum',
        'stock_cdr': 'sum'
    }).reset_index()
    
    for col in ['q_cmm', 'q_stock_disp', 'stock_pro', 'stock_cdr']:
        stocks_province[col] = stocks_province[col].fillna(0)
    
    stocks_province['alerte_rouge'] = stocks_province['q_cmm'] < stocks_province['q_stock_disp']
    stocks_province['ratio_stock_cmm'] = stocks_province.apply(
        lambda row: row['q_stock_disp'] / row['q_cmm'] if row['q_cmm'] > 0 else 0, 
        axis=1
    )
    
    ordre_provinces = [
        'Haut Katanga', 'Haut Lomami', 'Kasai Oriental', 'Kasai Central',
        'Lualaba', 'Lomami', 'Sud Kivu', 'Sankuru', 'Tanganyika'
    ]
    stocks_province['province_name'] = pd.Categorical(stocks_province['province_name'], 
                                                       categories=ordre_provinces, 
                                                       ordered=True)
    stocks_province = stocks_province.sort_values('province_name')
    
    total_cmm = safe_int_convert(stocks_province['q_cmm'].sum())
    total_stock = safe_int_convert(stocks_province['q_stock_disp'].sum())
    total_stock_pro = safe_int_convert(stocks_province['stock_pro'].sum())
    total_stock_cdr = safe_int_convert(stocks_province['stock_cdr'].sum())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Total CMM", f"{total_cmm:,.0f}")
    with col2:
        st.metric("🏭 Total Stock Disponible", f"{total_stock:,.0f}")
    with col3:
        st.metric("📋 Total Stock Programmé", f"{total_stock_pro:,.0f}")
    with col4:
        st.metric("🏢 Total Stock CDR", f"{total_stock_cdr:,.0f}")
    
    df_affichage = stocks_province.copy()
    df_affichage['ratio_stock_cmm'] = df_affichage['ratio_stock_cmm'].apply(
        lambda x: f"{x:.1f}x" if x > 0 else "N/A"
    )
    df_affichage['alerte'] = df_affichage['alerte_rouge'].apply(
        lambda x: "🔴 ALERTE : Stock > CMM" if x else "✅ OK"
    )
    
    colonnes_affichage = {
        'province_name': 'Province',
        'q_cmm': 'CMM',
        'q_stock_disp': 'Stock Disponible',
        'stock_pro': 'Stock Programmée',
        'stock_cdr': 'Stock CDR',
        'ratio_stock_cmm': 'Ratio Stock/CMM',
        'alerte': 'Statut'
    }
    
    df_style = df_affichage[list(colonnes_affichage.keys())].rename(columns=colonnes_affichage)
    st.dataframe(df_style, use_container_width=True)
    
    # Export stocks
    col_exp1, col_exp2 = st.columns(2)
    stocks_export = stocks_province.rename(columns={
        'province_name': 'Province',
        'q_cmm': 'CMM',
        'q_stock_disp': 'Stock_Disponible',
        'stock_pro': 'Stock_Programme',
        'stock_cdr': 'Stock_CDR',
        'ratio_stock_cmm': 'Ratio_Stock_CMM',
        'alerte_rouge': 'Alerte'
    })
    
    with col_exp1:
        st.download_button(
            label="📥 Télécharger les stocks (CSV)",
            data=stocks_export.to_csv(index=False).encode('utf-8'),
            file_name=f"stocks_provinces_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col_exp2:
        st.download_button(
            label="📥 Télécharger les stocks (Excel)",
            data=to_excel(stocks_export),
            file_name=f"stocks_provinces_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stocks_province['province_name'],
        y=stocks_province['q_cmm'],
        name='CMM',
        marker_color='#1f77b4'
    ))
    fig.add_trace(go.Bar(
        x=stocks_province['province_name'],
        y=stocks_province['q_stock_disp'],
        name='Stock Disponible',
        marker_color=stocks_province['alerte_rouge'].apply(
            lambda x: '#d62728' if x else '#2ca02c'
        )
    ))
    fig.update_layout(
        title="Comparaison CMM et Stock Disponible par province",
        xaxis_title="Province",
        yaxis_title="Quantité",
        barmode='group',
        height=500,
        xaxis={'tickangle': 45}
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main():
    try:
        df = load_and_process_data()
        
        # ==================== SIDEBAR FILTRES ====================
        st.sidebar.header("🔍 Filtres")
        
        # 1. NIVEAU HIÉRARCHIQUE
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
            province_selectionne = st.sidebar.selectbox(
                "Sélectionnez la Province", 
                options=provinces_options,
                index=0
            )
            
        elif niveau == 'Zone Sante':
            province_selectionne = st.sidebar.selectbox(
                "Sélectionnez la Province", 
                options=provinces_options,
                index=0
            )
            
            if province_selectionne and province_selectionne != 'Toutes':
                zones_disponibles = df[df['province_name'] == province_selectionne]['healthzone_name'].dropna().unique().tolist()
                zones_disponibles = sorted([z for z in zones_disponibles if z and str(z) != 'nan'])
                zones_options = ['Toutes'] + zones_disponibles
                
                zone_sante_selectionne = st.sidebar.selectbox(
                    "Sélectionnez la Zone de Santé", 
                    options=zones_options,
                    index=0
                )
            else:
                st.sidebar.info("Sélectionnez d'abord une province pour voir les Zones de Santé")
            
        elif niveau == 'Etablissement':
            province_selectionne = st.sidebar.selectbox(
                "Sélectionnez la Province", 
                options=provinces_options,
                index=0
            )
            
            if province_selectionne and province_selectionne != 'Toutes':
                zones_disponibles = df[df['province_name'] == province_selectionne]['healthzone_name'].dropna().unique().tolist()
                zones_disponibles = sorted([z for z in zones_disponibles if z and str(z) != 'nan'])
                zones_options = ['Toutes'] + zones_disponibles
                
                zone_sante_selectionne = st.sidebar.selectbox(
                    "Sélectionnez la Zone de Santé", 
                    options=zones_options,
                    index=0
                )
                
                if zone_sante_selectionne and zone_sante_selectionne != 'Toutes':
                    facilities_disponibles = df[(df['province_name'] == province_selectionne) & 
                                                (df['healthzone_name'] == zone_sante_selectionne)]['facility_name'].dropna().unique().tolist()
                    facilities_disponibles = sorted([f for f in facilities_disponibles if f and str(f) != 'nan'])
                    facilities_options = ['Tous'] + facilities_disponibles
                    
                    facility_selectionne = st.sidebar.selectbox(
                        "Sélectionnez l'Établissement", 
                        options=facilities_options,
                        index=0
                    )
                else:
                    st.sidebar.info("Sélectionnez d'abord une Zone de Santé pour voir les établissements")
            else:
                st.sidebar.info("Sélectionnez d'abord une province pour voir les Zones de Santé")
        
        # 2. PÉRIODE
        st.sidebar.subheader("📅 Période")
        type_periode = st.sidebar.radio(
            "Type de période",
            options=['Mois', 'Trimestre'],
            horizontal=True
        )
        
        df_filtered = df.copy()
        
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
        
        # Application du filtre hiérarchique
        df_filtered = filter_by_hierarchy(df_filtered, niveau, province_selectionne, facility_selectionne, zone_sante_selectionne)
        
        # Affichage du contexte
        st.sidebar.info(f"📊 **{len(df_filtered)}** établissements affichés")
        if niveau == 'Provincial' and province_selectionne and province_selectionne != 'Toutes':
            st.sidebar.success(f"📍 Province : {province_selectionne}")
        elif niveau == 'Zone Sante' and zone_sante_selectionne and zone_sante_selectionne != 'Toutes':
            st.sidebar.success(f"🏥 Zone de Santé : {zone_sante_selectionne}")
            if province_selectionne and province_selectionne != 'Toutes':
                st.sidebar.success(f"📍 Province : {province_selectionne}")
        elif niveau == 'Etablissement' and facility_selectionne and facility_selectionne != 'Tous':
            st.sidebar.success(f"🏥 Établissement : {facility_selectionne}")
            if zone_sante_selectionne and zone_sante_selectionne != 'Toutes':
                st.sidebar.success(f"📍 Zone de Santé : {zone_sante_selectionne}")
        elif niveau == 'National' or (niveau == 'Provincial' and province_selectionne == 'Toutes'):
            st.sidebar.success("🌍 Vue Nationale")
        
        # KPI principaux
        show_kpi_cards(df_filtered, niveau)
        
        # Onglets
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📈 Dépistage & Diagnostic",
            "💊 Traitement",
            "🛡️ Prévention (TPT)",
            "📦 Logistique",
            "📊 Complétude & Promptitude",
            "📋 Données brutes",
            "🏭 Stocks par Province"
        ])
        
        with tab1:
            show_depistage_tab(df_filtered)
        with tab2:
            show_traitement_tab(df_filtered)
        with tab3:
            show_prevention_tab(df_filtered)
        with tab4:
            show_logistique_tab(df_filtered)
        with tab5:
            show_completude_promptitude_tab(df_filtered, niveau, province_selectionne, zone_sante_selectionne)
        with tab6:
            show_donnees_brutes_tab(df_filtered)
        with tab7:
            show_stocks_province_tab(df)
        
        st.markdown("---")
        st.markdown(f"*Dernière mise à jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
    except FileNotFoundError:
        st.error("""
        ❌ **Fichier introuvable !**
        
        Le fichier `drc_stop_tb_data.csv` n'a pas été trouvé.
        Vérifiez qu'il se trouve dans le même répertoire que ce script.
        """)
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
