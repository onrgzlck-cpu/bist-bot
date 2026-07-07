import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="BIST Gelişmiş Analiz Terminali", layout="wide")

st.title("🦅 BIST Pro Analiz ve Radar Terminali")
st.write("Akşam analizleri için teknik, temel ve grafik destekli tarama sistemi.")

# 1. Genişletilebilir BIST İzleme Listesi
TUM_HISSELER = ["DOFRB.IS", "GEREL.IS", "THYAO.IS", "EREGL.IS", "AKBNK.IS", "ASELS.IS", "TUPRS.IS", "BIMAS.IS", "SASA.IS", "GARAN.IS"]

# 2. SOL MENÜ (FİLTRELER VE SEÇİMLER)
st.sidebar.header("⚙️ Kontrol Paneli")

# Tümünü seç seçeneği olan Hisse Seçim Kutusu
hepsini_sec = st.sidebar.checkbox("Tüm Hisseleri Seç", value=True)
if hepsini_sec:
    secilen_hisseler = TUM_HISSELER
else:
    secilen_hisseler = st.sidebar.multiselect("Hisseleri Seçin", TUM_HISSELER, default=["DOFRB.IS", "GEREL.IS"])

zaman_dilimi = st.sidebar.selectbox("Grafik Zaman Dilimi", ["1d", "1h"])
gosterim_tipi = st.sidebar.radio("Tablo Filtresi", ["Sadece Sinyal Verenler", "Tüm Liste (Sinyalsizler Dahil)"])

# 3. ANALİZ MOTORU
def detayli_analiz_yap(ticker):
    try:
        # Akşam analizi için son 3 aylık günlük veriyi çekiyoruz
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 14: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Son Fiyatlar
        kapanislar = df['Close'].astype(float)
        en_yuksekler = df['High'].astype(float)
        en_dusukler = df['Low'].astype(float)
        
        son_fiyat = float(kapanislar.iloc[-1])
        
        # --- TEKNİK ANALİZ ---
        # RSI Hesaplama (14 Günlük)
        delta = kapanislar.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # SMC (Fair Value Gap) Kontrolü
        h1 = float(en_yuksekler.iloc[-3])
        l3 = float(en_dusukler.iloc[-1])
        smc_sinyal = "Yok"
        giris_yeri = 0.0
        hedef_yeri = 0.0
        
        if h1 < l3:
            smc_sinyal = "SMC Alım Fırsatı (FVG)"
            giris_yeri = round(h1, 2)
            hedef_yeri = round(l3, 2)
            
        # --- TEMEL ANALİZ ---
        hisse_bilgisi = yf.Ticker(ticker).info
        fk = hisse_bilgisi.get('trailingPE', "N/A")
        pd_dd = hisse_bilgisi.get('priceToBook', "N/A")
        sektor = hisse_bilgisi.get('sector', "Bilinmiyor")
        
        return {
            "Hisse": ticker.replace(".IS", ""),
            "Son Kapanış (TL)": round(son_fiyat, 2),
            "SMC Durumu": "SMC Alım (FVG)" if h1 < l3 else "Normal",
            "SMC Giriş (Retest)": giris_yeri if giris_yeri > 0 else "-",
            "SMC Hedef": hedef_yeri if hedef_yeri > 0 else "-",
            "RSI (14)": round(rsi, 2),
            "F/K Oranı": round(fk, 2) if isinstance(fk, (int, float)) else fk,
            "PD/DD Oranı": round(pd_dd, 2) if isinstance(pd_dd, (int, float)) else pd_dd,
            "Sektör": sektor
        }
    except:
        return None

# Excel'e dönüştürme fonksiyonu
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='BIST_Analiz')
    processed_data = output.getvalue()
    return processed_data

# 4. RADAR TARAMA TETİKLEYİCİSİ
if st.button("📡 Radar Taramasını Başlat"):
    sonuclar = []
    
    with st.spinner("BIST Verileri ve Raporlar Çekiliyor..."):
        for hisse in secilen_hisseler:
            analiz = detayli_analiz_yap(hisse)
            if analiz:
                sonuclar.append(analiz)
                
    if sonuclar:
        main_df = pd.DataFrame(sonuclar)
        
        # Filtreleme seçeneği uygulama
        if gosterim_tipi == "Sadece Sinyal Verenler":
            gosterilecek_df = main_df[main_df["SMC Durumu"] == "SMC Alım (FVG)"]
        else:
            gosterilecek_df = main_df
            
        st.subheader("📊 Tarama Sonuç Matrisi (Excel Tarzı)")
        
        # Renklendirilmiş Excel Tablosu Görünümü
        st.dataframe(gosterilecek_df.style.background_gradient(axis=0, cmap='YlGn', subset=["RSI (14)"]))
        
        # EXCEL İNDİRME BUTONU
        excel_data = to_excel(gosterilecek_df)
        st.download_button(
            label="📥 Sonuçları Excel Dosyası Olarak İndir",
            data=excel_data,
            file_name="bist_radar_analiz.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        
        # 5. HİSSE DETAY VE İNTERAKTİF GRAFİK BÖLÜMÜ
        st.subheader("🔍 Tekil Hisse Detay Analizi & Güncel Grafik")
        secilen_detay_hisse = st.selectbox("Grafiğini ve Detayını Görmek İstediğiniz Hisseyi Seçin", gosterilecek_df["Hisse"].unique())
        
        if secilen_detay_hisse:
            ticker_sym = f"{secilen_detay_hisse}.IS"
            g_df = yf.download(ticker_sym, period="3mo", interval=zaman_dilimi, progress=False)
            
            if isinstance(g_df.columns, pd.MultiIndex):
                g_df.columns = g_df.columns.droplevel(1)
                
            # Plotly Canlı Mum Grafiği (Telefon Uyumlu)
            fig = go.Figure(data=[go.Candlestick(
                x=g_df.index,
                open=g_df['Open'],
                high=g_df['High'],
                low=g_df['Low'],
                close=g_df['Close'],
                name="Mum Grafiği"
            )])
            fig.update_layout(title=f"{secilen_detay_hisse} Güncel Teknik Grafiği", xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.error("Seçilen hisselerden veri çekilemedi.")
