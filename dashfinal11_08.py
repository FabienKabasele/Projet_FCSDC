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
from streamlit_gsheets import GSheetsConnection

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
    .info-box {
        background-color: #e7f3ff;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .formula-box {
        background-color: #f8f9fa;
        padding: 0.5rem 0.8rem;
        border-radius: 5px;
        border-left: 3px solid #6c757d;
        font-family: monospace;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<div class="main-header"><h1>🩺 Stop TB - Tableau de Bord FCSDS</h1><p>Suivi des activités de lutte contre la tuberculose</p></div>', unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION DU PROJET (FINANCES)
# ============================================================================

PROJET_CONFIG = {
    'date_debut': '2026-06-01',
    'date_fin': '2027-03-31',
    'nom_projet': 'Stop TB - FCSDS'
}

PROJET_CONFIG_AFFICHAGE = {
    'date_debut': '2026-06-01',
    'date_fin': '2026-11-30'
}

NB_MOIS_CONSOMMATION = 6

# ============================================================================
# CONFIGURATION DES MOTS DE PASSE
# ============================================================================

PASSWORDS = {
    'saisie_distribution': 'Distrib2026',
    'consultation_finances': 'FinanceView2026',
}

def check_password(password_key, session_key=None):
    if session_key is None:
        session_key = password_key
    
    if st.session_state.get(f'auth_{session_key}', False):
        return True
    
    st.markdown("""
        <div style="background-color: #fff3cd; padding: 1rem; border-radius: 10px; border-left: 5px solid #ffc107; margin-bottom: 1rem;">
            <h4 style="margin-top: 0;">🔐 Accès protégé</h4>
            <p>Veuillez saisir le mot de passe pour accéder à cette section.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form(f"login_form_{session_key}", clear_on_submit=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            password = st.text_input("Mot de passe", type="password", key=f"pwd_{session_key}")
        with col2:
            st.write("")
            st.write("")
            submit = st.form_submit_button("🔓 Valider", use_container_width=True)
        
        if submit:
            if password == PASSWORDS.get(password_key, ''):
                st.session_state[f'auth_{session_key}'] = True
                st.success("✅ Authentification réussie !")
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")
    
    return False

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
    'q1_2_h': 'Cas_presumes_Hommes', 'q1_2_f': 'Cas_presumes_Femmes',
    'q1_2_hf_total': 'Cas_presumes_Total',
    'q1_5_h': 'Testes_Xpert_Hommes', 'q1_5_f': 'Testes_Xpert_Femmes',
    'q1_5_hf_total': 'Testes_Xpert_Total',
    'q2_0_h': 'TB_detectee_Hommes', 'q2_0_f': 'TB_detectee_Femmes',
    'q2_0_hf_total': 'TB_detectee_Total',
    'q2_1_hf_total': 'TB_confirmee_bacterio_Total',
    'q2_2_hf_total': 'TB_confirmee_clinique_Total',
    'q3_0_h': 'Traitement_DS_debute_Hommes', 'q3_0_f': 'Traitement_DS_debute_Femmes',
    'q3_0_hf_total': 'Traitement_DS_debute_Total',
    'q3_4_g04': 'Nouveaux_cas_0_4_ans_Hommes', 'q3_4_g514': 'Nouveaux_cas_5_14_ans_Hommes',
    'q3_4_h1524': 'Nouveaux_cas_15_24_ans_Hommes', 'q3_4_h2534': 'Nouveaux_cas_25_34_ans_Hommes',
    'q3_4_h3544': 'Nouveaux_cas_35_44_ans_Hommes', 'q3_4_h4554': 'Nouveaux_cas_45_54_ans_Hommes',
    'q3_4_h5564': 'Nouveaux_cas_55_64_ans_Hommes', 'q3_4_h65p': 'Nouveaux_cas_plus_65_ans_Hommes',
    'q3_4_f04': 'Nouveaux_cas_0_4_ans_Femmes', 'q3_4_f514': 'Nouveaux_cas_5_14_ans_Femmes',
    'q3_4_f1524': 'Nouveaux_cas_15_24_ans_Femmes', 'q3_4_f2534': 'Nouveaux_cas_25_34_ans_Femmes',
    'q3_4_f3544': 'Nouveaux_cas_35_44_ans_Femmes', 'q3_4_f4554': 'Nouveaux_cas_45_54_ans_Femmes',
    'q3_4_f5564': 'Nouveaux_cas_55_64_ans_Femmes', 'q3_4_f65p': 'Nouveaux_cas_plus_65_ans_Femmes',
    'q4_0_hf_total': 'Testes_resistance_Total',
    'q4_1_hf_total': 'Diagnostiques_RRMDR_Total',
    'q5_0_h': 'Traitement_RRMDR_debute_Hommes', 'q5_0_f': 'Traitement_RRMDR_debute_Femmes',
    'q5_0_hf_total': 'Traitement_RRMDR_debute_Total',
    'q6_0_hf_total': 'Traitement_DS_reussi_Total',
    'q7_0_hf_total': 'Traitement_RRMDR_reussi_Total',
    'q8_0_hf_total': 'TPT_depistage_Total', 'q8_0_age5m': 'TPT_depistage_0_5_ans',
    'q8_0_age5p': 'TPT_depistage_plus_5_ans',
    'q8_4_hf_total': 'TPT_eligibles_contacts_Total',
    'q8_4_age5m': 'TPT_eligibles_contacts_0_5_ans',
    'q8_4_age5p': 'TPT_eligibles_contacts_plus_5_ans',
    'q8_5_hf_total': 'TPT_eligibles_PVVIH_Total',
    'q8_6_hf_total': 'TPT_eligibles_autres_Total',
    'q9_1_hf_total': 'TPT_commence_contacts_Total',
    'q9_1_age5m': 'TPT_commence_contacts_0_5_ans',
    'q9_2_hf_total': 'TPT_commence_PVVIH_Total',
    'q9_3_hf_total': 'TPT_commence_autres_Total',
    'q10_0_hf_total': 'TPT_termine_contacts_Total',
    'q10_1_hf_total': 'TPT_termine_PVVIH_Total',
    'q10_2_hf_total': 'TPT_termine_autres_Total',
    'tpt_eligible_total': 'TPT_Eligibles_Total', 'tpt_started_total': 'TPT_Commence_Total',
    'tpt_completed_total': 'TPT_Termine_Total',
    'enfants_moins_5_depistes': 'Enfants_moins_5_ans_depistes',
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
        'national': 'National',
        'haut katanga': 'Haut Katanga', 'hautkatanga': 'Haut Katanga',
        'haut lomami': 'Haut Lomami', 'hautlomami': 'Haut Lomami',
        'kasai oriental': 'Kasai Oriental', 'kasaioriental': 'Kasai Oriental',
        'kasai central': 'Kasai Central', 'kasaicentral': 'Kasai Central',
        'lualaba': 'Lualaba',
        'sud kivu': 'Sud Kivu', 'sudkivu': 'Sud Kivu',
        'sankuru': 'Sankuru',
        'tanganyika': 'Tanganyika',
        'lomami': 'Lomami',
    }
    name_clean = name.lower().strip()
    if name_clean in mapping:
        return mapping[name_clean]
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

def convertir_mois_fr_en_standard(mois_str):
    mois_map_fr = {
        'janv': '01', 'janvier': '01',
        'févr': '02', 'fevr': '02', 'février': '02', 'fevrier': '02',
        'mars': '03',
        'avr': '04', 'avril': '04',
        'mai': '05',
        'juin': '06',
        'juil': '07', 'juillet': '07',
        'août': '08', 'aout': '08',
        'sept': '09', 'septembre': '09',
        'oct': '10', 'octobre': '10',
        'nov': '11', 'novembre': '11',
        'déc': '12', 'dec': '12', 'décembre': '12', 'decembre': '12'
    }
    
    try:
        mois_str_clean = str(mois_str).strip().lower()
        parts = mois_str_clean.split('-')
        if len(parts) == 2:
            nom_mois, annee_court = parts
            num_mois = None
            for key, val in mois_map_fr.items():
                if nom_mois.startswith(key[:4]):
                    num_mois = val
                    break
            if num_mois is None:
                return None
            annee = '20' + annee_court if len(annee_court) == 2 else annee_court
            return f"{annee}-{num_mois}"
    except:
        pass
    return None


@st.cache_data
def load_budget_previsionnel():
    try:
        df_budget = pd.read_csv(
            'budget_previsionnel.csv',
            sep=';',
            decimal=',',
            encoding='utf-8-sig',
            skipinitialspace=True
        )
        
        df_budget = df_budget.rename(columns={df_budget.columns[0]: 'province_name'})
        
        if 'Montant total' in df_budget.columns:
            df_budget = df_budget.drop(columns=['Montant total'])
        
        df_budget = df_budget[df_budget['province_name'].str.strip() != 'Total budget']
        df_budget = df_budget[df_budget['province_name'].notna()]
        
        df_budget['province_name'] = df_budget['province_name'].str.strip()
        df_budget['province_name'] = df_budget['province_name'].apply(clean_province_name)
        
        for col in df_budget.columns:
            if col != 'province_name':
                df_budget[col] = pd.to_numeric(df_budget[col], errors='coerce').fillna(0)
        
        colonnes_mois = [c for c in df_budget.columns if c != 'province_name']
        df_budget['budget_total_province'] = df_budget[colonnes_mois].sum(axis=1)
        
        df_budget_long = df_budget.melt(
            id_vars=['province_name'],
            value_vars=colonnes_mois,
            var_name='mois',
            value_name='montant_prevu'
        )
        
        df_budget_long['mois_str'] = df_budget_long['mois'].apply(convertir_mois_fr_en_standard)
        df_budget_long = df_budget_long[df_budget_long['mois_str'].notna()]
        
        return df_budget, df_budget_long
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erreur de chargement du budget : {e}")
        return pd.DataFrame(), pd.DataFrame()


def get_budget_total():
    df_budget, _ = load_budget_previsionnel()
    if len(df_budget) == 0:
        return 0
    return df_budget['budget_total_province'].sum()


def get_prevision_mois(mois_str):
    df_budget, _ = load_budget_previsionnel()
    if len(df_budget) == 0:
        return 0
    
    mois_map_fr = {
        '01': 'janv', '02': 'févr', '03': 'mars', '04': 'avr',
        '05': 'mai', '06': 'juin', '07': 'juil', '08': 'août',
        '09': 'sept', '10': 'oct', '11': 'nov', '12': 'déc'
    }
    
    try:
        date_obj = pd.to_datetime(mois_str + '-01')
        num_mois = date_obj.strftime('%m')
        annee_court = date_obj.strftime('%y')
        nom_fr = mois_map_fr.get(num_mois, '')
        
        for col in df_budget.columns:
            if col == 'province_name' or col == 'budget_total_province':
                continue
            col_clean = col.lower()
            if nom_fr.lower() in col_clean and annee_court in col_clean:
                return df_budget[col].sum()
    except:
        pass
    
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
    
    # Totaux H/F
    df['q1_0_hf_total'] = df['q1_0_h'] + df['q1_0_f']
    df['q1_0_age_total'] = df['q1_0_age15m'] + df['q1_0_age15p']
    df['q1_1_hf_total'] = df['q1_1_h'] + df['q1_1_f']
    df['q1_2_hf_total'] = df['q1_2_h'] + df['q1_2_f']
    df['q1_3_hf_total'] = df['q1_3_h'] + df['q1_3_f']
    df['q1_4_hf_total'] = df['q1_4_h'] + df['q1_4_f']
    df['q1_5_hf_total'] = df['q1_5_h'] + df['q1_5_f']
    df['q2_0_hf_total'] = df['q2_0_h'] + df['q2_0_f']
    df['q2_1_hf_total'] = df['q2_1_h'] + df['q2_1_f']
    df['q2_2_hf_total'] = df['q2_2_h'] + df['q2_2_f']
    df['q3_0_hf_total'] = df['q3_0_h'] + df['q3_0_f']
    
    df['q3_4_h_total'] = (df['q3_4_g04'] + df['q3_4_g514'] + df['q3_4_h1524'] + 
                          df['q3_4_h2534'] + df['q3_4_h3544'] + df['q3_4_h4554'] + 
                          df['q3_4_h5564'] + df['q3_4_h65p'])
    df['q3_4_f_total'] = (df['q3_4_f04'] + df['q3_4_f514'] + df['q3_4_f1524'] + 
                          df['q3_4_f2534'] + df['q3_4_f3544'] + df['q3_4_f4554'] + 
                          df['q3_4_f5564'] + df['q3_4_f65p'])
    df['q3_4_hf_total'] = df['q3_4_h_total'] + df['q3_4_f_total']
    
    df['q4_0_hf_total'] = df['q4_0_h'] + df['q4_0_f']
    df['q4_1_hf_total'] = df['q4_1_h'] + df['q4_1_f']
    df['q5_0_hf_total'] = df['q5_0_h'] + df['q5_0_f']
    df['q6_0_hf_total'] = df['q6_0_h'] + df['q6_0_f']
    df['q7_0_hf_total'] = df['q7_0_h'] + df['q7_0_f']
    df['q8_0_hf_total'] = df['q8_0_h'] + df['q8_0_f']
    df['q8_1_hf_total'] = df['q8_1_h'] + df['q8_1_f']
    df['q8_2_hf_total'] = df['q8_2_h'] + df['q8_2_f']
    df['q8_3_hf_total'] = df['q8_3_h'] + df['q8_3_f']
    df['q8_4_hf_total'] = df['q8_4_h'] + df['q8_4_f']
    df['q8_5_hf_total'] = df['q8_5_h'] + df['q8_5_f']
    df['q8_6_hf_total'] = df['q8_6_h'] + df['q8_6_f']
    df['q9_1_hf_total'] = df['q9_1_h'] + df['q9_1_f']
    df['q9_2_hf_total'] = df['q9_2_h'] + df['q9_2_f']
    df['q9_3_hf_total'] = df['q9_3_h'] + df['q9_3_f']
    df['q10_0_hf_total'] = df['q10_0_h'] + df['q10_0_f']
    df['q10_1_hf_total'] = df['q10_1_h'] + df['q10_1_f']
    df['q10_2_hf_total'] = df['q10_2_h'] + df['q10_2_f']
    
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
# FONCTIONS GOOGLE SHEETS
# ============================================================================

def load_finances_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_fin = conn.read(worksheet="finances", ttl=0)
        
        df_fin = df_fin.dropna(how='all')
        
        if len(df_fin) == 0:
            return pd.DataFrame(columns=[
                'type_suivi', 'date_saisie', 'province_name', 'depenses',
                'nombre_dp_recu', 'nombre_dp_traite', 'nombre_dp_en_attente',
                'observations', 'mois_num', 'annee', 'mois_annee', 'semaine_num'
            ])
        
        df_fin['date_saisie'] = pd.to_datetime(df_fin['date_saisie'], errors='coerce')
        df_fin['mois_num'] = df_fin['date_saisie'].dt.month
        df_fin['annee'] = df_fin['date_saisie'].dt.year
        df_fin['mois_annee'] = df_fin['date_saisie'].dt.strftime('%Y-%m')
        df_fin['semaine_num'] = df_fin['date_saisie'].dt.isocalendar().week
        
        if 'type_suivi' not in df_fin.columns:
            df_fin['type_suivi'] = 'mensuel'
        
        if 'depenses' not in df_fin.columns:
            df_fin['depenses'] = 0
        
        for col in ['nombre_dp_recu', 'nombre_dp_traite', 'nombre_dp_en_attente']:
            if col not in df_fin.columns:
                df_fin[col] = 0
            else:
                df_fin[col] = pd.to_numeric(df_fin[col], errors='coerce').fillna(0)
        
        df_fin['depenses'] = pd.to_numeric(df_fin['depenses'], errors='coerce').fillna(0)
        
        if 'province_name' not in df_fin.columns:
            df_fin['province_name'] = 'National'
        
        if 'observations' not in df_fin.columns:
            df_fin['observations'] = ''
        
        return df_fin
    except Exception as e:
        st.error(f"❌ Erreur de connexion à Google Sheets (finances): {e}")
        return pd.DataFrame(columns=[
            'type_suivi', 'date_saisie', 'province_name', 'depenses',
            'nombre_dp_recu', 'nombre_dp_traite', 'nombre_dp_en_attente',
            'observations', 'mois_num', 'annee', 'mois_annee', 'semaine_num'
        ])


def save_finances_data(df_fin):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_to_save = df_fin.drop(columns=['mois_num', 'annee', 'mois_annee', 'semaine_num'], errors='ignore')
        conn.update(worksheet="finances", data=df_to_save)
        return True
    except Exception as e:
        st.error(f"❌ Erreur de sauvegarde vers Google Sheets (finances): {e}")
        return False


def load_distribution_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_dist = conn.read(worksheet="distribution", ttl=0)
        
        df_dist = df_dist.dropna(how='all')
        
        if len(df_dist) == 0:
            return pd.DataFrame(columns=[
                'date_saisie', 'semaine', 'type_niveau', 'medicament', 'code_entite',
                'nom_entite', 'quantite_prevue', 'quantite_expediee', 'quantite_recue',
                'observations', 'semaine_num', 'annee', 'mois_annee'
            ])
        
        df_dist['date_saisie'] = pd.to_datetime(df_dist['date_saisie'], errors='coerce')
        df_dist['semaine_num'] = df_dist['date_saisie'].dt.isocalendar().week
        df_dist['annee'] = df_dist['date_saisie'].dt.isocalendar().year
        df_dist['mois_annee'] = df_dist['date_saisie'].dt.strftime('%Y-%m')
        
        for col in ['quantite_prevue', 'quantite_expediee', 'quantite_recue']:
            if col in df_dist.columns:
                df_dist[col] = pd.to_numeric(df_dist[col], errors='coerce').fillna(0)
            else:
                df_dist[col] = 0
        
        if 'code_entite' not in df_dist.columns:
            df_dist['code_entite'] = '-'
        
        if 'observations' not in df_dist.columns:
            df_dist['observations'] = ''
        
        return df_dist
    except Exception as e:
        st.error(f"❌ Erreur de connexion à Google Sheets (distribution): {e}")
        return pd.DataFrame(columns=[
            'date_saisie', 'semaine', 'type_niveau', 'medicament', 'code_entite',
            'nom_entite', 'quantite_prevue', 'quantite_expediee', 'quantite_recue',
            'observations', 'semaine_num', 'annee', 'mois_annee'
        ])


def save_distribution_data(df_dist):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_to_save = df_dist.drop(columns=['semaine_num', 'annee', 'mois_annee'], errors='ignore')
        conn.update(worksheet="distribution", data=df_to_save)
        return True
    except Exception as e:
        st.error(f"❌ Erreur de sauvegarde vers Google Sheets (distribution): {e}")
        return False


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
    
    # Infobulle explicative
    st.markdown("""
    <div class="info-box">
        <strong>ℹ️ Comment lire cette cascade :</strong> Chaque étape montre la proportion de patients qui passe à l'étape suivante.
        Le pourcentage affiché dans le graphique indique le taux de passage entre chaque étape (percent previous).
        <br><br>
        <strong>⚠️ À noter :</strong> Nous ne disposons pas encore d'estimation officielle des cas TB attendus dans la zone.
        Le <em>taux de détection</em> affiché est un taux interne (parmi les testés), <strong>PAS</strong> une couverture en traitement au sens programme (cas mis en traitement / cas attendus).
    </div>
    """, unsafe_allow_html=True)
    
    cascade_data = pd.DataFrame({
        'Étape': ['Personnes dépistées', 'Cas présumés TB', 'Testés (Xpert)', 'TB détectée', 'TB confirmée bactério'],
        'Nombre': [
            df_filtered['q1_0_hf_total'].sum(),
            df_filtered['q1_2_hf_total'].sum(),
            df_filtered['q1_5_hf_total'].sum(),
            df_filtered['q2_0_hf_total'].sum(),
            df_filtered['q2_1_hf_total'].sum()
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
        
        # Note sur la répartition par sexe
        total_h = df_filtered['q1_0_h'].sum()
        total_f = df_filtered['q1_0_f'].sum()
        if total_h + total_f > 0:
            pct_f = (total_f / (total_h + total_f)) * 100
            if pct_f > 55:
                st.markdown(f"""
                <div class="warning-box">
                    <strong>⚠️ Note sur la répartition :</strong> Les femmes représentent <strong>{pct_f:.1f}%</strong> des personnes dépistées sur cette période.
                    Cela peut sembler différent de la tendance nationale historique (majorité d'hommes).
                    <br>Plusieurs explications possibles : saisie initiale, dépistage ciblé (CPN/PTME), couverture géographique partielle.
                    Un comparatif avec N-1 sera ajouté quand les données seront disponibles.
                </div>
                """, unsafe_allow_html=True)
    
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
    
    st.markdown("---")
    st.subheader("🧬 Détection de la tuberculose résistante (RR/MDR)")
    
    st.markdown("""
    <div class="info-box">
        <strong>Formule du taux de détection RR/MDR :</strong>
        <div class="formula-box">
        Taux = (Diagnostiqués RR/MDR ÷ Testés pour résistance) × 100
        </div>
        <strong>⚠️ Ce taux n'est PAS une couverture en traitement.</strong> C'est la proportion de cas résistants parmi les cas testés.
        </div>
    """, unsafe_allow_html=True)
    
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
        total_testes = df_filtered['q4_0_hf_total'].sum()
        total_diag = df_filtered['q4_1_hf_total'].sum()
        taux_rr = (total_diag / total_testes * 100) if total_testes > 0 else 0
        
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
        
        st.caption(f"Formule : {total_diag:,} ÷ {total_testes:,} × 100 = **{taux_rr:.1f}%**")


def show_traitement_tab(df_filtered):
    st.subheader("💊 Traitement de la tuberculose")
    
    # ⚠️ AVERTISSEMENT PRINCIPAL
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ IMPORTANT — Distinction des cohortes</strong><br>
        Ce tableau de bord <strong>ne dispose pas encore de données 2025</strong> pour évaluer les résultats de fin de traitement.<br><br>
        Les indicateurs ci-dessous sont donc présentés <strong>en deux blocs séparés</strong> :<br>
        • <strong>Bloc 1 — Cohortes en cours (2026)</strong> : patients mis en traitement dans la période affichée<br>
        • <strong>Bloc 2 — Résultats antérieurs</strong> : à renseigner quand les cohortes 2025 seront disponibles<br><br>
        <em>Ne pas interpréter les "réussites" comme découlant des "débuts" du même mois.</em>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================================
    # BLOC 1 : COHORTE EN COURS (2026)
    # ============================================================
    st.markdown("## 📊 Bloc 1 — Cohorte en cours (2026)")
    st.markdown("*Patients dépistés et mis en traitement dans la période affichée*")
    
    st.markdown("### Tuberculose sensible (DS-TB) — Mise en traitement")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ds_data = pd.DataFrame({
            'Sexe': ['Hommes', 'Femmes'],
            'Cas détectés': [df_filtered['q2_0_h'].sum(), df_filtered['q2_0_f'].sum()],
            'Mis en traitement': [df_filtered['q3_0_h'].sum(), df_filtered['q3_0_f'].sum()]
        })
        ds_melted = ds_data.melt(id_vars=['Sexe'], var_name='Étape', value_name='Nombre')
        fig_ds = px.bar(ds_melted, x='Sexe', y='Nombre', color='Étape', 
                        barmode='group', title="Cas détectés vs Mis en traitement (DS-TB)")
        st.plotly_chart(fig_ds, use_container_width=True)
    
    with col2:
        total_detectes = df_filtered['q2_0_hf_total'].sum()
        total_mis_en_traitement = df_filtered['q3_0_hf_total'].sum()
        taux_mise_traitement = (total_mis_en_traitement / total_detectes * 100) if total_detectes > 0 else 0
        
        st.metric("🦠 Cas TB détectés (période)", f"{int(total_detectes):,}")
        st.metric("💊 Cas mis en traitement DS (période)", f"{int(total_mis_en_traitement):,}")
        
        st.markdown(f"""
        <div class="formula-box">
        <strong>Taux de mise en traitement DS-TB :</strong><br>
        {int(total_mis_en_traitement):,} ÷ {int(total_detectes):,} × 100 = <strong>{taux_mise_traitement:.1f}%</strong>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("💡 Ce taux mesure la proportion de cas détectés qui sont effectivement mis sous traitement dans la même période.")
    
    st.markdown("### Tuberculose résistante (RR/MDR) — Mise en traitement")
    
    col3, col4 = st.columns(2)
    
    with col3:
        rr_data_tx = pd.DataFrame({
            'Sexe': ['Hommes', 'Femmes'],
            'Diagnostiqués RR/MDR': [df_filtered['q4_1_h'].sum(), df_filtered['q4_1_f'].sum()],
            'Mis en traitement': [df_filtered['q5_0_h'].sum(), df_filtered['q5_0_f'].sum()]
        })
        rr_melted = rr_data_tx.melt(id_vars=['Sexe'], var_name='Étape', value_name='Nombre')
        fig_rr_tx = px.bar(rr_melted, x='Sexe', y='Nombre', color='Étape', 
                           barmode='group', title="Diagnostiqués RR/MDR vs Mis en traitement")
        st.plotly_chart(fig_rr_tx, use_container_width=True)
    
    with col4:
        total_diag_rr = df_filtered['q4_1_hf_total'].sum()
        total_mis_en_traitement_rr = df_filtered['q5_0_hf_total'].sum()
        taux_mise_traitement_rr = (total_mis_en_traitement_rr / total_diag_rr * 100) if total_diag_rr > 0 else 0
        
        st.metric("🧬 Diagnostiqués RR/MDR (période)", f"{int(total_diag_rr):,}")
        st.metric("💊 Mis en traitement RR/MDR (période)", f"{int(total_mis_en_traitement_rr):,}")
        
        st.markdown(f"""
        <div class="formula-box">
        <strong>Taux de mise en traitement RR/MDR :</strong><br>
        {int(total_mis_en_traitement_rr):,} ÷ {int(total_diag_rr):,} × 100 = <strong>{taux_mise_traitement_rr:.1f}%</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # ============================================================
    # BLOC 2 : RÉSULTATS ANTÉRIEURS (2025)
    # ============================================================
    st.markdown("---")
    st.markdown("## 📊 Bloc 2 — Résultats de traitement (cohortes antérieures)")
    
    st.markdown("""
    <div class="info-box">
        <strong>ℹ️ Ces indicateurs concernent des patients mis en traitement lors de périodes antérieures (ex. 2025).</strong><br>
        Ils ne peuvent <strong>PAS</strong> être lius comme découlant des mises en traitement du Bloc 1.<br><br>
        • Le <strong>taux de succès DS-TB</strong> est évalué après <strong>12 mois</strong> de suivi.<br>
        • Le <strong>taux de succès RR/MDR</strong> est évalué après <strong>24 mois</strong> de suivi.<br><br>
        <em>Les données 2025 n'étant pas encore saisies dans la base, les valeurs ci-dessous peuvent être nulles ou partielles.</em>
    </div>
    """, unsafe_allow_html=True)
    
    col5, col6 = st.columns(2)
    
    with col5:
        total_reussis_ds = df_filtered['q6_0_hf_total'].sum()
        st.metric("✅ Traitements DS-TB réussis (cohorte antérieure)", f"{int(total_reussis_ds):,}",
                 help="Issus de patients mis en traitement 12 mois auparavant")
        st.caption("💡 Résultats à interpréter uniquement sur les cohortes concernées.")
    
    with col6:
        total_reussis_rr = df_filtered['q7_0_hf_total'].sum()
        st.metric("✅ Traitements RR/MDR réussis (cohorte antérieure)", f"{int(total_reussis_rr):,}",
                 help="Issus de patients mis en traitement 24 mois auparavant")
        st.caption("💡 Résultats à interpréter uniquement sur les cohortes concernées.")
    
    # ============================================================
    # CONTRÔLES DE COHÉRENCE
    # ============================================================
    st.markdown("---")
    st.markdown("### 🔍 Contrôles de cohérence automatiques")
    
    # Contrôle 1 : réussites > mises en traitement du même mois ?
    if total_reussis_ds > total_mis_en_traitement:
        st.warning(f"""
        ⚠️ **Anomalie détectée :** Le nombre de traitements DS-TB réussis ({int(total_reussis_ds):,}) 
        dépasse le nombre de patients mis en traitement dans la période ({int(total_mis_en_traitement):,}).
        Cela peut indiquer une erreur de saisie ou un mélange de cohortes.
        """)
    else:
        st.success("✅ Contrôle DS-TB : cohérent avec les cohortes actuelles")
    
    if total_reussis_rr > total_mis_en_traitement_rr:
        st.warning(f"""
        ⚠️ **Anomalie détectée :** Le nombre de traitements RR/MDR réussis ({int(total_reussis_rr):,}) 
        dépasse le nombre de patients mis en traitement dans la période ({int(total_mis_en_traitement_rr):,}).
        """)
    else:
        st.success("✅ Contrôle RR/MDR : cohérent avec les cohortes actuelles")
    
    # ============================================================
    # NOUVEAUX CAS PAR ÂGE
    # ============================================================
    st.markdown("---")
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
    
    # ⚠️ AVERTISSEMENT PRINCIPAL
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ IMPORTANT — Cascade scindée en deux</strong><br>
        Un patient qui <strong>commence</strong> un TPT ne peut <strong>pas</strong> le <strong>terminer</strong> le même mois 
        (le TPT dure plusieurs mois selon le schéma : 3HP, 6H, etc.).<br><br>
        La cascade est donc présentée en <strong>deux blocs séparés</strong> :<br>
        • <strong>Bloc 1 — Démarrage (2026)</strong> : de l'éligibilité au démarrage du TPT<br>
        • <strong>Bloc 2 — Achèvement (cohortes antérieures)</strong> : patients ayant terminé leur TPT<br><br>
        <em>Les données 2025 n'étant pas encore saisies, le Bloc 2 peut être vide ou partiel.</em>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================================
    # BLOC 1 : CASCADE DE DÉMARRAGE (2026)
    # ============================================================
    st.markdown("## 📊 Bloc 1 — Cascade de démarrage du TPT (2026)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_depistes = df_filtered['q8_0_hf_total'].sum()
        st.metric("👥 Dépistés pour TPT", f"{total_depistes:,.0f}",
                 help="Personnes dépistées pour le TPT (contacts, PVVIH, autres groupes)")
    
    with col2:
        total_eligibles = df_filtered['tpt_eligible_total'].sum()
        st.metric("✅ Éligibles TPT", f"{total_eligibles:,.0f}",
                 help="Personnes éligibles au TPT après dépistage")
    
    with col3:
        total_commences = df_filtered['tpt_started_total'].sum()
        st.metric("💊 Ont commencé le TPT", f"{total_commences:,.0f}",
                 help="Personnes ayant effectivement démarré un schéma TPT")
    
    st.markdown("---")
    st.markdown("### 📈 Cascade TPT — Démarrage")
    
    # Cascade limitée au démarrage
    cascade_tpt_data = pd.DataFrame({
        'Étape': ['Dépistés TPT', 'Éligibles TPT', 'TPT commencé'],
        'Nombre': [total_depistes, total_eligibles, total_commences]
    })
    
    fig_cascade_tpt = px.funnel(cascade_tpt_data, x='Nombre', y='Étape',
                                 title="Cascade TPT — Dépistage → Éligibilité → Démarrage",
                                 color_discrete_sequence=['#17becf'])
    fig_cascade_tpt.update_traces(textposition="inside", textinfo="value+percent previous")
    st.plotly_chart(fig_cascade_tpt, use_container_width=True)
    
    # Formules explicites
    taux_eligibilite = (total_eligibles / total_depistes * 100) if total_depistes > 0 else 0
    taux_demarrage = (total_commences / total_eligibles * 100) if total_eligibles > 0 else 0
    
    st.markdown(f"""
    <div class="formula-box">
    <strong>Taux d'éligibilité :</strong> {int(total_eligibles):,} ÷ {int(total_depistes):,} × 100 = <strong>{taux_eligibilite:.1f}%</strong><br>
    <strong>Taux de démarrage (parmi éligibles) :</strong> {int(total_commences):,} ÷ {int(total_eligibles):,} × 100 = <strong>{taux_demarrage:.1f}%</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================================
    # FOCUS ENFANTS < 5 ANS vs ≥ 5 ANS
    # ============================================================
    st.markdown("---")
    st.markdown("### 👶 Focus : Enfants de moins de 5 ans vs 5 ans et plus")
    
    enfants_moins_5_depistes = df_filtered['q8_0_age5m'].sum()
    enfants_plus_5_depistes = df_filtered['q8_0_age5p'].sum()
    enfants_moins_5_eligibles = df_filtered['q8_4_age5m'].sum()
    enfants_plus_5_eligibles = df_filtered['q8_4_age5p'].sum()
    enfants_moins_5_commences = df_filtered['q9_1_age5m'].sum()
    enfants_plus_5_commences = df_filtered['q9_1_age5p'].sum()
    
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        st.markdown("#### 👶 Enfants < 5 ans (contacts)")
        st.metric("Dépistés", f"{enfants_moins_5_depistes:,.0f}")
        st.metric("Éligibles", f"{enfants_moins_5_eligibles:,.0f}")
        st.metric("TPT commencé", f"{enfants_moins_5_commences:,.0f}")
    
    with col_e2:
        st.markdown("#### 🧒 Enfants ≥ 5 ans (contacts)")
        st.metric("Dépistés", f"{enfants_plus_5_depistes:,.0f}")
        st.metric("Éligibles", f"{enfants_plus_5_eligibles:,.0f}")
        st.metric("TPT commencé", f"{enfants_plus_5_commences:,.0f}")
    
    # Graphique comparatif < 5 ans vs ≥ 5 ans
    age_compare_data = pd.DataFrame({
        'Tranche d\'âge': ['< 5 ans', '≥ 5 ans', '< 5 ans', '≥ 5 ans', '< 5 ans', '≥ 5 ans'],
        'Étape': ['Dépistés', 'Dépistés', 'Éligibles', 'Éligibles', 'TPT commencé', 'TPT commencé'],
        'Nombre': [
            enfants_moins_5_depistes, enfants_plus_5_depistes,
            enfants_moins_5_eligibles, enfants_plus_5_eligibles,
            enfants_moins_5_commences, enfants_plus_5_commences
        ]
    })
    
    fig_age_compare = px.bar(age_compare_data, x='Étape', y='Nombre', color='Tranche d\'âge',
                              barmode='group', title="Comparaison < 5 ans vs ≥ 5 ans (cascade TPT contacts)",
                              color_discrete_sequence=['#ff7f0e', '#1f77b4'])
    st.plotly_chart(fig_age_compare, use_container_width=True)
    
    # ============================================================
    # CASCADE PAR GROUPE CIBLE
    # ============================================================
    st.markdown("---")
    st.subheader("📊 Cascade TPT par groupe cible (démarrage seulement)")
    
    st.markdown("""
    <div class="info-box">
        <strong>Définition des groupes cibles :</strong><br>
        • <strong>Contacts</strong> : personnes ayant été en contact étroit avec un cas de TB confirmé (incluant enfants < 5 ans et ≥ 5 ans)<br>
        • <strong>PVVIH</strong> : personnes vivant avec le VIH<br>
        • <strong>Autres groupes à risque</strong> : personnel soignant, prisonniers, patients sous immunosuppresseurs, diabétiques, etc. selon le guide national.
    </div>
    """, unsafe_allow_html=True)
    
    tpt_flow = pd.DataFrame({
        'Groupe cible': ['Contacts', 'PVVIH', 'Autres groupes'],
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
        'TPT commencé': [
            df_filtered['q9_1_hf_total'].sum(),
            df_filtered['q9_2_hf_total'].sum(),
            df_filtered['q9_3_hf_total'].sum()
        ]
    })
    
    tpt_flow_melted = tpt_flow.melt(id_vars=['Groupe cible'], var_name='Étape', value_name='Nombre')
    fig_tpt_flow = px.bar(tpt_flow_melted, x='Groupe cible', y='Nombre', color='Étape',
                          barmode='group', title="Cascade TPT par groupe cible (dépistage → démarrage)")
    st.plotly_chart(fig_tpt_flow, use_container_width=True)
    
    # ============================================================
    # BLOC 2 : ACHÈVEMENT (COHORTES ANTÉRIEURES)
    # ============================================================
    st.markdown("---")
    st.markdown("## 📊 Bloc 2 — Achèvement du TPT (cohortes antérieures)")
    
    st.markdown("""
    <div class="info-box">
        <strong>ℹ️ Ces indicateurs concernent des patients ayant <em>commencé</em> un TPT lors de périodes antérieures.</strong><br>
        Ils ne peuvent <strong>PAS</strong> être lus comme découlant des démarrages du Bloc 1.<br><br>
        Le TPT dure plusieurs mois (3HP = 3 mois, 6H = 6 mois, etc.). Un patient qui commence en juillet 2026 
        ne peut terminer qu'à partir d'octobre 2026 minimum.<br><br>
        <em>Les données 2025 n'étant pas encore disponibles, ces valeurs peuvent être nulles ou partielles.</em>
    </div>
    """, unsafe_allow_html=True)
    
    total_termines = df_filtered['tpt_completed_total'].sum()
    
    col_t1, col_t2, col_t3 = st.columns(3)
    
    with col_t1:
        st.metric("🏁 TPT terminés (cohorte antérieure)", f"{total_termines:,.0f}",
                 help="Patients ayant terminé leur TPT (issu des cohortes antérieures)")
    
    with col_t2:
        st.metric("👶 dont enfants < 5 ans", f"{df_filtered['q10_0_age5m'].sum():,.0f}")
    
    with col_t3:
        taux_achevement = (total_termines / total_commences * 100) if total_commences > 0 else 0
        st.metric("📊 Taux d'achèvement", f"{taux_achevement:.1f}%",
                 help="⚠️ À interpréter uniquement sur les cohortes concernées")
    
    st.markdown(f"""
    <div class="formula-box">
    <strong>Formule du taux d'achèvement TPT :</strong><br>
    TPT terminés ÷ TPT commencés (même cohorte) × 100<br>
    <em>⚠️ Actuellement calculé sur les données disponibles, à affiner quand les cohortes 2025 seront saisies.</em>
    </div>
    """, unsafe_allow_html=True)
    
    # Détail par groupe cible (terminés)
    if total_termines > 0:
        st.markdown("### Détail des TPT terminés par groupe cible")
        
        tpt_fin = pd.DataFrame({
            'Groupe cible': ['Contacts', 'PVVIH', 'Autres groupes'],
            'TPT terminé': [
                df_filtered['q10_0_hf_total'].sum(),
                df_filtered['q10_1_hf_total'].sum(),
                df_filtered['q10_2_hf_total'].sum()
            ]
        })
        
        fig_tpt_fin = px.bar(tpt_fin, x='Groupe cible', y='TPT terminé',
                              title="TPT terminés par groupe cible",
                              color='Groupe cible', text='TPT terminé')
        fig_tpt_fin.update_traces(textposition='outside')
        st.plotly_chart(fig_tpt_fin, use_container_width=True)


# ============================================================================
# FONCTIONS DISTRIBUTION MÉDICAMENTS
# ============================================================================

def get_semaines_annee(annee):
    semaines = []
    for i in range(1, 53):
        try:
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


def show_medicaments_tab(df_filtered):
    st.subheader("💊 Gestion des stocks de médicaments")
    
    medicaments_presents = []
    for medicament, info in MEDICAMENTS.items():
        prefix = info['prefix']
        if f"{prefix}_stock_disponible" in df_filtered.columns:
            medicaments_presents.append(medicament)
    
    if not medicaments_presents:
        st.warning("⚠️ Aucune donnée de médicaments trouvée dans le fichier.")
        return
    
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
        
        data_stocks.append(row)
    
    df_stocks = pd.DataFrame(data_stocks)
    
    colonnes_ordre = ['Médicament', 'Stock Initial', 'Quantité Reçue', 'Stock Disponible', 
                      'Quantité Consommée', 'Stock Théorique', 'Stock Physique', 
                      'Pertes Exp', 'Jours Rupture (moyenne)', 'Nb CDT en rupture', 
                      'Taux de rupture (%)', 'Date Expiration', 'Statut']
    colonnes_existantes = [col for col in colonnes_ordre if col in df_stocks.columns]
    df_stocks_display = df_stocks[colonnes_existantes]
    
    st.dataframe(df_stocks_display, use_container_width=True, height=400)
    
    st.markdown("---")
    st.subheader("📤 Suivi de distribution des médicaments")
    
    if st.session_state.get('auth_saisie_distribution', False):
        if st.button("🚪 Se déconnecter du formulaire", key="logout_distribution"):
            st.session_state['auth_saisie_distribution'] = False
            st.rerun()
        
        df_dist = load_distribution_data()
        
        with st.expander("📝 **Ajouter / Modifier une entrée de distribution**", expanded=False):
            with st.form("form_distribution", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    annee_courante = datetime.now().year
                    annee_options = [annee_courante - 1, annee_courante, annee_courante + 1]
                    annee_dist = st.selectbox("📅 Année", options=annee_options, index=1, key="annee_dist")
                    
                    semaines = get_semaines_annee(annee_dist)
                    semaine_options = [s['label'] for s in semaines]
                    
                    semaine_actuelle = datetime.now().isocalendar()[1]
                    index_defaut = min(semaine_actuelle - 1, len(semaine_options) - 1) if semaine_actuelle > 0 else 0
                    
                    semaine_label = st.selectbox("📆 Semaine", options=semaine_options, index=index_defaut, key="semaine_dist")
                    semaine_idx = semaine_options.index(semaine_label)
                    semaine_selectionnee = semaines[semaine_idx]
                    
                    date_saisie = semaine_selectionnee['fin']
                    
                    type_niveau = st.selectbox("🏢 Niveau de distribution", options=TYPES_NIVEAUX)
                    medicament_dist = st.selectbox("💊 Médicament", options=list(MEDICAMENTS.keys()), key="med_dist")
                
                with col2:
                    code_entite = st.text_input("🔢 Code entité", value="", placeholder="Ex: CDR-001, ZS-012")
                    nom_entite = st.text_input("🏥 Nom de l'entité", value="", placeholder="Ex: CDR Kinshasa")
                    quantite_prevue = st.number_input("📋 Quantité prévue", min_value=0, value=0, step=100)
                    quantite_expediee = st.number_input("📤 Quantité expédiée", min_value=0, value=0, step=100)
                    quantite_recue = st.number_input("📥 Quantité reçue", min_value=0, value=0, step=100)
                
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
                        
                        if save_distribution_data(df_dist):
                            st.success(f"✅ Entrée ajoutée pour {nom_entite} ({semaine_label}) !")
                            st.rerun()
    else:
        st.info("🔐 **Formulaire protégé** - Veuillez vous authentifier pour saisir des données")
        check_password('saisie_distribution', 'saisie_distribution')
    
    st.markdown("---")
    df_dist_display = load_distribution_data()
    
    if len(df_dist_display) == 0:
        st.info("📋 Aucune donnée de distribution n'est encore enregistrée.")
    else:
        st.markdown("### 📊 Indicateurs de distribution")
        
        total_prevu = df_dist_display['quantite_prevue'].sum()
        total_expedie = df_dist_display['quantite_expediee'].sum()
        total_recu = df_dist_display['quantite_recue'].sum()
        
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
        
        styled_df = df_affichage.style.map(colorer_taux, subset=['Taux_ZS', 'Taux_CDT'])
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        st.markdown("""
        **Légende des couleurs :**
        - 🔴 **Rouge** : < 50% (Critique)
        - 🟡 **Jaune** : 50% - 79% (Insuffisant)
        - 💧 **Vert d'eau** : 80% - 89% (Bon)
        - 🟢 **Vert citron** : ≥ 90% (Excellent)
        """)


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


# ============================================================================
# SUIVI BUDGÉTAIRE PAR PROVINCE ET NIVEAU NATIONAL
# ============================================================================

def show_finances_par_province(df_fin, budget_total):
    st.markdown("---")
    st.markdown("### 📊 Suivi budgétaire par province et niveau national")
    
    df_budget, df_budget_long = load_budget_previsionnel()
    
    if len(df_budget) == 0:
        st.warning("⚠️ Fichier `budget_previsionnel.csv` non trouvé ou vide.")
        return
    
    df_budget_prov = df_budget[['province_name', 'budget_total_province']].copy()
    df_budget_prov.columns = ['Province', 'Budget_prevu']
    
    df_fin_clean = df_fin.copy()
    if 'province_name' in df_fin_clean.columns:
        df_fin_clean['province_name'] = df_fin_clean['province_name'].replace({'Toutes': 'National', '': 'National'})
        df_fin_clean['province_name'] = df_fin_clean['province_name'].fillna('National')
    
    if 'depenses' in df_fin_clean.columns and len(df_fin_clean) > 0:
        depenses_par_entite = df_fin_clean.groupby('province_name').agg({
            'depenses': 'sum'
        }).reset_index()
        depenses_par_entite.columns = ['Province', 'Depenses_reelles']
    else:
        depenses_par_entite = pd.DataFrame(columns=['Province', 'Depenses_reelles'])
    
    df_province = df_budget_prov.merge(
        depenses_par_entite, 
        on='Province', 
        how='left'
    )
    
    entites_sans_budget = depenses_par_entite[
        ~depenses_par_entite['Province'].isin(df_budget_prov['Province'])
    ]
    if len(entites_sans_budget) > 0:
        entites_sans_budget = entites_sans_budget.copy()
        entites_sans_budget['Budget_prevu'] = 0
        df_province = pd.concat([df_province, entites_sans_budget], ignore_index=True)
    
    df_province['Depenses_reelles'] = df_province['Depenses_reelles'].fillna(0)
    df_province['Reste_a_depenser'] = df_province['Budget_prevu'] - df_province['Depenses_reelles']
    
    df_province['Taux_absorption'] = df_province.apply(
        lambda row: round((row['Depenses_reelles'] / row['Budget_prevu'] * 100), 1) 
        if row['Budget_prevu'] > 0 else 0,
        axis=1
    )
    
    df_province['_ordre'] = df_province['Province'].apply(
        lambda x: 0 if 'National' in str(x) else 1
    )
    df_province = df_province.sort_values(['_ordre', 'Province']).drop(columns='_ordre').reset_index(drop=True)
    
    def statut_entite(taux, depenses):
        if depenses == 0:
            return '⚪ Aucune dépense'
        elif taux >= 90:
            return '🟢 Excellent'
        elif taux >= 80:
            return '💧 Bon'
        elif taux >= 50:
            return '🟡 Moyen'
        else:
            return '🔴 Faible'
    
    df_province['Statut'] = df_province.apply(
        lambda row: statut_entite(row['Taux_absorption'], row['Depenses_reelles']),
        axis=1
    )
    
    df_affichage = df_province[[
        'Province', 'Budget_prevu', 'Depenses_reelles',
        'Reste_a_depenser', 'Taux_absorption', 'Statut'
    ]].copy()
    
    df_affichage.columns = [
        'Province / Niveau', 'Budget prévu ($)', 'Dépenses réelles ($)',
        'Reste à dépenser ($)', 'Taux absorption (%)', 'Statut'
    ]
    
    df_affichage['Province / Niveau'] = df_affichage['Province / Niveau'].apply(
        lambda x: '🌍 National (central)' if str(x) == 'National' else x
    )
    
    df_affichage['Budget prévu ($)'] = df_affichage['Budget prévu ($)'].apply(lambda x: f"${x:,.2f}")
    df_affichage['Dépenses réelles ($)'] = df_affichage['Dépenses réelles ($)'].apply(lambda x: f"${x:,.2f}")
    df_affichage['Reste à dépenser ($)'] = df_affichage['Reste à dépenser ($)'].apply(lambda x: f"${x:,.2f}")
    df_affichage['Taux absorption (%)'] = df_affichage['Taux absorption (%)'].apply(lambda x: f"{x:.1f}%")
    
    budget_total_reel = df_province['Budget_prevu'].sum()
    depenses_total_reel = df_province['Depenses_reelles'].sum()
    reste_total = budget_total_reel - depenses_total_reel
    taux_global = (depenses_total_reel / budget_total_reel * 100) if budget_total_reel > 0 else 0
    
    total_row = pd.DataFrame([{
        'Province / Niveau': '**TOTAL**',
        'Budget prévu ($)': f"${budget_total_reel:,.2f}",
        'Dépenses réelles ($)': f"${depenses_total_reel:,.2f}",
        'Reste à dépenser ($)': f"${reste_total:,.2f}",
        'Taux absorption (%)': f"{taux_global:.1f}%",
        'Statut': '📊 Bilan'
    }])
    
    df_affichage_final = pd.concat([df_affichage, total_row], ignore_index=True)
    
    def colorer_ligne(row):
        entity_str = str(row['Province / Niveau'])
        taux_str = str(row['Taux absorption (%)'])
        
        if 'National' in entity_str:
            return ['background-color: #e7f3ff; color: #004085; font-weight: bold;'] * len(row)
        
        if 'TOTAL' in entity_str:
            return ['background-color: #f0f2f6; color: #000000; font-weight: bold;'] * len(row)
        
        try:
            taux = float(taux_str.replace('%', ''))
            if taux >= 90:
                return ['background-color: #d4edda; color: #155724;'] * len(row)
            elif taux >= 80:
                return ['background-color: #d1ecf1; color: #0c5460;'] * len(row)
            elif taux >= 50:
                return ['background-color: #fff3cd; color: #856404;'] * len(row)
            elif taux > 0:
                return ['background-color: #f8d7da; color: #721c24;'] * len(row)
            else:
                return ['background-color: #f0f2f6; color: #6c757d;'] * len(row)
        except:
            return [''] * len(row)
    
    styled_df = df_affichage_final.style.apply(colorer_ligne, axis=1)
    
    st.dataframe(styled_df, use_container_width=True, height=500)
    
    st.caption("ℹ️ **National (central)** est le budget consommé au niveau central, indépendamment des provinces. Il est intégré dans la ligne TOTAL.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    df_national = df_province[df_province['Province'] == 'National']
    df_provinces = df_province[df_province['Province'] != 'National']
    
    with col1:
        budget_nat = df_national['Budget_prevu'].sum() if len(df_national) > 0 else 0
        st.metric("🌍 Budget National", f"${budget_nat:,.0f}")
    with col2:
        dep_nat = df_national['Depenses_reelles'].sum() if len(df_national) > 0 else 0
        taux_nat = (dep_nat / budget_nat * 100) if budget_nat > 0 else 0
        st.metric("💸 Dépenses Nationales", f"${dep_nat:,.0f}",
                 delta=f"{taux_nat:.1f}% absorbé")
    with col3:
        budget_prov = df_provinces['Budget_prevu'].sum() if len(df_provinces) > 0 else 0
        st.metric("🏥 Budget Provinces", f"${budget_prov:,.0f}",
                 delta=f"{len(df_provinces)} provinces")
    with col4:
        dep_prov = df_provinces['Depenses_reelles'].sum() if len(df_provinces) > 0 else 0
        taux_prov = (dep_prov / budget_prov * 100) if budget_prov > 0 else 0
        st.metric("💸 Dépenses Provinces", f"${dep_prov:,.0f}",
                 delta=f"{taux_prov:.1f}% absorbé")
    
    # ========== SUIVI MENSUEL PAR ENTITÉ ==========
    st.markdown("---")
    st.markdown("### 📅 Suivi budgétaire mensuel par entité")
    
    entites_disponibles = sorted(df_province['Province'].dropna().unique().tolist())
    entite_selectionnee = st.selectbox(
        "Sélectionnez une entité (province ou National)",
        options=entites_disponibles,
        key="select_entite_finance",
        format_func=lambda x: '🌍 National (central)' if x == 'National' else x
    )
    
    if entite_selectionnee:
        df_budget_prov_mois = df_budget_long[
            df_budget_long['province_name'] == entite_selectionnee
        ].copy()
        
        df_dep_prov = df_fin_clean[
            df_fin_clean['province_name'] == entite_selectionnee
        ].copy()
        
        if len(df_dep_prov) > 0 and 'mois_annee' in df_dep_prov.columns:
            depenses_par_mois = df_dep_prov.groupby('mois_annee').agg({
                'depenses': 'sum'
            }).reset_index()
            depenses_par_mois.columns = ['mois_str', 'depenses_reelles']
        else:
            depenses_par_mois = pd.DataFrame(columns=['mois_str', 'depenses_reelles'])
        
        df_suivi_mois = df_budget_prov_mois.merge(
            depenses_par_mois,
            on='mois_str',
            how='left'
        )
        
        df_suivi_mois['depenses_reelles'] = df_suivi_mois['depenses_reelles'].fillna(0)
        df_suivi_mois['ecart'] = df_suivi_mois['montant_prevu'] - df_suivi_mois['depenses_reelles']
        
        df_suivi_mois['taux'] = df_suivi_mois.apply(
            lambda row: round((row['depenses_reelles'] / row['montant_prevu'] * 100), 1) 
            if row['montant_prevu'] > 0 else 0,
            axis=1
        )
        
        df_suivi_mois = df_suivi_mois.sort_values('mois_str')
        
        df_suivi_display = df_suivi_mois[['mois_str', 'montant_prevu', 'depenses_reelles', 'ecart', 'taux']].copy()
        df_suivi_display.columns = ['Mois', 'Budget prévu ($)', 'Dépenses réelles ($)', 'Écart ($)', 'Taux (%)']
        
        for col in ['Budget prévu ($)', 'Dépenses réelles ($)', 'Écart ($)']:
            df_suivi_display[col] = df_suivi_display[col].apply(lambda x: f"${x:,.2f}")
        
        df_suivi_display['Taux (%)'] = df_suivi_display['Taux (%)'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_suivi_display, use_container_width=True, height=400)


# ============================================================================
# ONGLET FINANCES
# ============================================================================

def get_mois_projet():
    date_debut = pd.to_datetime(PROJET_CONFIG['date_debut'])
    date_fin = pd.to_datetime(PROJET_CONFIG['date_fin'])
    return pd.date_range(start=date_debut, end=date_fin, freq='MS')


def get_mois_projet_affichage():
    date_debut = pd.to_datetime(PROJET_CONFIG_AFFICHAGE['date_debut'])
    date_fin = pd.to_datetime(PROJET_CONFIG_AFFICHAGE['date_fin'])
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


def show_finances_tab(df_main):
    if not st.session_state.get('auth_consultation_finances', False):
        st.markdown("""
            <div style="background-color: #f8d7da; padding: 2rem; border-radius: 10px; border-left: 5px solid #dc3545; margin-bottom: 1rem; text-align: center;">
                <h2 style="margin-top: 0;">🔒 Accès restreint aux finances</h2>
                <p style="font-size: 1.1rem;">Cette section contient des informations financières sensibles.</p>
                <p>Veuillez saisir le mot de passe pour accéder au tableau de bord financier.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_finances", clear_on_submit=False):
                password = st.text_input(
                    "🔑 Mot de passe", 
                    type="password", 
                    key="pwd_finances_input",
                    placeholder="Entrez votre mot de passe"
                )
                
                submit = st.form_submit_button("🔓 Accéder aux finances", use_container_width=True)
                
                if submit:
                    if password == PASSWORDS.get('consultation_finances', ''):
                        st.session_state['auth_consultation_finances'] = True
                        st.success("✅ Authentification réussie !")
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect.")
        
        return
    
    col_logout1, col_logout2 = st.columns([4, 1])
    with col_logout2:
        if st.button("🚪 Se déconnecter", key="logout_finances", use_container_width=True):
            st.session_state['auth_consultation_finances'] = False
            st.rerun()
    
    st.subheader("💰 Tableau de bord financier du projet")
    
    date_debut = pd.to_datetime(PROJET_CONFIG['date_debut'])
    date_fin = pd.to_datetime(PROJET_CONFIG['date_fin'])
    
    budget_total = get_budget_total()
    
    if budget_total == 0:
        st.warning("⚠️ Impossible de lire le budget depuis `budget_previsionnel.csv`. Utilisation de 0 par défaut.")
        budget_total = 0
    
    df_budget, _ = load_budget_previsionnel()
    
    mois_projet_complet = get_mois_projet()
    nb_mois_total = len(mois_projet_complet)
    
    mois_projet = get_mois_projet_affichage()
    nb_mois_affichage = len(mois_projet)
    
    prevision_mensuelle_moyenne = budget_total / NB_MOIS_CONSOMMATION if NB_MOIS_CONSOMMATION > 0 else 0
    
    nb_semaines_consommation = NB_MOIS_CONSOMMATION * 4
    prevision_hebdo = budget_total / nb_semaines_consommation if nb_semaines_consommation > 0 else 0
    
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
                <td><strong>Période du budget :</strong></td>
                <td>{date_debut.strftime('%B %Y')} → {date_fin.strftime('%B %Y')}</td>
            </tr>
            <tr>
                <td><strong>Budget total (provinces + National) :</strong></td>
                <td><strong>{budget_total:,.0f} USD</strong></td>
                <td><strong>Période d'affichage :</strong></td>
                <td>{pd.to_datetime(PROJET_CONFIG_AFFICHAGE['date_debut']).strftime('%B %Y')} → {pd.to_datetime(PROJET_CONFIG_AFFICHAGE['date_fin']).strftime('%B %Y')} ({nb_mois_affichage} mois)</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    df_fin = load_finances_data()
    
    if len(df_fin) > 0:
        for col in ['depenses', 'nombre_dp_recu', 'nombre_dp_traite', 'nombre_dp_en_attente']:
            if col in df_fin.columns:
                df_fin[col] = pd.to_numeric(df_fin[col], errors='coerce').fillna(0)
        
        for col in ['type_suivi', 'province_name', 'observations']:
            if col in df_fin.columns:
                df_fin[col] = df_fin[col].astype('object')
                df_fin[col] = df_fin[col].where(df_fin[col].notna(), '')
                df_fin[col] = df_fin[col].astype(str)
                df_fin[col] = df_fin[col].replace('nan', '')
        
        if 'date_saisie' in df_fin.columns:
            df_fin['date_saisie'] = pd.to_datetime(df_fin['date_saisie'], errors='coerce')
    
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
                    depenses_default = prevision_mensuelle_moyenne
                    cle_mois = mois_selectionne.strftime('%Y-%m')
                    type_enregistrement = 'mensuel'
                    
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
                
                depenses = st.number_input(
                    depenses_label,
                    min_value=0.0,
                    value=float(depenses_default),
                    step=500.0,
                    format="%.2f"
                )
                
                province = st.selectbox(
                    "🌍 Province / Niveau",
                    options=['National'] + sorted(df_main['province_name'].dropna().unique().tolist()),
                    help="Sélectionnez 'National' pour les dépenses réalisées au niveau central"
                )
            
            with col2:
                nb_dp_recu = st.number_input("📥 Nombre de DP reçus", min_value=0, value=0, step=1)
                nb_dp_traite = st.number_input("✅ Nombre de DP traités", min_value=0, value=0, step=1)
                nb_dp_attente = st.number_input("⏳ Nombre de DP en attente", min_value=0, value=0, step=1)
                observations = st.text_area("📝 Observations", value="", height=100)
            
            submitted = st.form_submit_button("✅ Enregistrer l'entrée", use_container_width=True)
            
            if submitted:
                if type_enregistrement == 'mensuel':
                    if len(df_fin) > 0 and 'province_name' in df_fin.columns:
                        masque = (
                            (df_fin.get('type_suivi', pd.Series(['mensuel'] * len(df_fin))) == 'mensuel') &
                            (df_fin['mois_annee'] == cle_mois) &
                            (df_fin['province_name'] == province)
                        )
                    else:
                        masque = pd.Series([False])
                else:
                    if len(df_fin) > 0 and 'province_name' in df_fin.columns:
                        semaine_target = semaine_selectionnee['fin'].isocalendar()[1]
                        annee_target = semaine_selectionnee['fin'].isocalendar()[0]
                        masque = (
                            (df_fin.get('type_suivi', pd.Series(['mensuel'] * len(df_fin))) == 'hebdomadaire') &
                            (df_fin['date_saisie'].dt.isocalendar().week == semaine_target) &
                            (df_fin['date_saisie'].dt.isocalendar().year == annee_target) &
                            (df_fin['province_name'] == province)
                        )
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
                    idx_a_supprimer = df_fin[masque].index.tolist()
                    df_fin = df_fin.drop(idx_a_supprimer).reset_index(drop=True)
                    df_fin = pd.concat([df_fin, pd.DataFrame([nouvelle_entree])], ignore_index=True)
                    st.success(f"✅ Entrée {type_enregistrement} mise à jour pour {province} !")
                else:
                    df_fin = pd.concat([df_fin, pd.DataFrame([nouvelle_entree])], ignore_index=True)
                    st.success(f"✅ Nouvelle entrée {type_enregistrement} ajoutée pour {province} !")
                
                df_fin['date_saisie'] = pd.to_datetime(df_fin['date_saisie'], errors='coerce')
                df_fin['mois_num'] = df_fin['date_saisie'].dt.month
                df_fin['annee'] = df_fin['date_saisie'].dt.year
                df_fin['mois_annee'] = df_fin['date_saisie'].dt.strftime('%Y-%m')
                df_fin['semaine_num'] = df_fin['date_saisie'].dt.isocalendar().week
                df_fin = df_fin.sort_values('date_saisie').reset_index(drop=True)
                
                if save_finances_data(df_fin):
                    st.rerun()
    
    if len(df_fin) == 0:
        st.info("📋 Aucune donnée financière n'est encore enregistrée.")
        show_finances_par_province(df_fin, budget_total)
        return
    
    df_fin['mois_annee'] = pd.to_datetime(df_fin['date_saisie'], errors='coerce').dt.strftime('%Y-%m')
    
    depenses_totales = df_fin['depenses'].sum()
    
    depenses_par_mois_toutes = df_fin.groupby('mois_annee').agg({
        'depenses': 'sum'
    }).reset_index()
    depenses_par_mois_toutes.columns = ['mois_annee', 'total_depenses']
    
    budget_restant = budget_total - depenses_totales
    taux_absorption_global = (depenses_totales / budget_total * 100) if budget_total > 0 else 0
    taux_temporel = (nb_mois_ecoules / nb_mois_affichage * 100) if nb_mois_affichage > 0 else 0
    ecart = taux_absorption_global - taux_temporel
    
    dp_recu_total = df_fin['nombre_dp_recu'].sum() if 'nombre_dp_recu' in df_fin.columns else 0
    dp_traite_total = df_fin['nombre_dp_traite'].sum() if 'nombre_dp_traite' in df_fin.columns else 0
    dp_attente_total = df_fin['nombre_dp_en_attente'].sum() if 'nombre_dp_en_attente' in df_fin.columns else 0
    taux_traitement_dp = (dp_traite_total / dp_recu_total * 100) if dp_recu_total > 0 else 0
    
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
        st.metric("⏱️ Avancement temporel (6 mois)", f"{taux_temporel:.1f}%",
                 delta=f"{nb_mois_ecoules}/{nb_mois_affichage} mois")
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
        st.metric("📥 DP reçus", f"{int(dp_recu_total):,}")
    with col8:
        st.metric("✅ DP traités", f"{int(dp_traite_total):,}",
                 delta=f"{taux_traitement_dp:.1f}%" if dp_recu_total > 0 else None)
    
    show_finances_par_province(df_fin, budget_total)


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
