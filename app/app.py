import streamlit as st
import finnhub
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# --- CONFIGURATION FINNHUB ---
# Remplace 'TON_API_KEY' par ta véritable clé Finnhub
FINNHUB_KEY = 'd5ehirpr01qmi0sin490d5ehirpr01qmi0sin49g'
finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)

# --- FONCTION D'ACQUISITION DES DONNÉES ---
def get_finnhub_data(tickers):
    end = int(time.time())
    start = end - (30 * 24 * 60 * 60)  # 30 jours en arrière (timestamp)
    
    all_data = {}
    for symbol in tickers:
        try:
            # Récupération des bougies (candles) journalières
            res = finnhub_client.stock_candles(symbol, 'D', start, end)
            if res['s'] == 'ok':
                # 'c' correspond aux cours de clôture (Close)
                all_data[symbol] = res['c']
            else:
                st.error(f"Erreur pour {symbol}: {res.get('s', 'Inconnu')}")
        except Exception as e:
            st.error(f"Erreur de connexion Finnhub pour {symbol}: {e}")
    
    df = pd.DataFrame(all_data)
    return df.dropna()

# --- INTERFACE & CALCULS ---
st.set_page_config(page_title="Quant B - Finnhub Edition", layout="wide")
st.title("📈 Quant B: Portfolio Manager (via Finnhub)")

assets = ["AAPL", "JPM", "KO"]
df_prices = get_finnhub_data(assets)

if not df_prices.empty and len(df_prices.columns) == len(assets):
    # Sidebar : Accès utilisateur aux paramètres
    st.sidebar.header("🛠️ Stratégie Portfolio")
    weights = []
    for a in assets:
        w = st.sidebar.slider(f"Poids {a}", 0.0, 1.0, 1/len(assets))
        weights.append(w)
    
    # Normalisation des poids
    total_w = sum(weights)
    final_weights = np.array(weights) / total_w if total_w > 0 else np.array([0.33, 0.33, 0.34])

    # Simulation du Portfolio
    returns_df = df_prices.pct_change().dropna()
    portfolio_rets = returns_df.dot(final_weights)
    # Valeur cumulative (Base 100)
    cum_val = (1 + portfolio_rets).cumprod() * 100

    # --- COMPARAISON VISUELLE (Main Chart) ---
    st.subheader("Comparaison : Actifs Individuels vs Portfolio")
    # Normalisation base 100 des actifs pour le graphique
    comparison = (df_prices / df_prices.iloc[0]) * 100
    comparison['PORTFOLIO'] = cum_val
    st.line_chart(comparison)

    # --- MÉTRIQUES ---
    st.subheader("Analyse du Risque et Performance")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Matrice de Corrélation**")
        st.dataframe(returns_df.corr())
    
    with col2:
        # Volatilité Annualisée
        vol = portfolio_rets.std() * np.sqrt(252)
        st.metric("Volatilité Annualisée", f"{vol:.2%}")
        
        # Rendement Total
        total_ret = (cum_val.iloc[-1] - 100)
        st.metric("Rendement Total (1 mois)", f"{total_ret:.2f}%")
        
        # Effet de diversification
        avg_indiv_vol = (returns_df.std() * np.sqrt(252)).mean()
        st.write(f"**Effet de diversification :** Réduction du risque de {avg_indiv_vol - vol:.2%}")

else:
    st.warning("En attente des données Finnhub... Vérifie ta clé API et ta connexion.")