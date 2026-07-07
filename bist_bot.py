import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="BIST Gelişmiş Analiz Terminali", layout="wide")

st.title("🦅 BIST Pro Analiz ve Radar Terminali")
st.write("Akşam analizleri için teknik, temel ve grafik destekli tarama sistemi.")

# 1. Genişletilebilir BIST İzleme Listesi
TUM_HISSELER = ["A1CAP.IS","A1YEN.IS","AAGYO.IS","ACSEL.IS","ADEL.IS","ADESE.IS","ADGYO.IS","AEFES.IS","AFYON.IS","AGESA.IS","AGHOL.IS","AGROT.IS","AGYO.IS","AHGAZ.IS","AHSGY.IS","AKBNK.IS","AKCNS.IS","AKENR.IS","AKFGY.IS","AKFIS.IS","AKFYE.IS","AKGRT.IS","AKHAN.IS","AKMGY.IS","AKSA.IS","AKSEN.IS","AKSGY.IS","AKSUE.IS","AKYHO.IS","ALARK.IS","ALBRK.IS","ALCAR.IS","ALCTL.IS","ALFAS.IS","ALGYO.IS","ALKA.IS","ALKIM.IS","ALKLC.IS","ALTNY.IS","ALVES.IS","ANELE.IS","ANGEN.IS","ANHYT.IS","ANSGR.IS","APBDL.IS","APGLD.IS","APLIB.IS","APMDL.IS","APX30.IS","ARASE.IS","ARCLK.IS","ARDYZ.IS","ARENA.IS","ARFYE.IS","ARMGD.IS","ARSAN.IS","ARTMS.IS","ARZUM.IS","ASELS.IS","ASGYO.IS","ASTOR.IS","ASUZU.IS","ATAGY.IS","ATAKP.IS","ATATP.IS","ATATR.IS","ATEKS.IS","ATLAS.IS","ATSYH.IS","AVGYO.IS","AVHOL.IS","AVOD.IS","AVPGY.IS","AVTUR.IS","AYCES.IS","AYDEM.IS","AYEN.IS","AYES.IS","AYGAZ.IS","AZTEK.IS","BAGFS.IS","BAHKM.IS","BAKAB.IS","BALAT.IS","BALSU.IS","BANVT.IS","BARMA.IS","BASCM.IS","BASGZ.IS","BAYRK.IS","BEGYO.IS","BERA.IS","BESLR.IS","BESTE.IS","BETAE.IS","BEYAZ.IS","BFREN.IS","BIENY.IS","BIGCH.IS","BIGEN.IS","BIGTK.IS","BIMAS.IS","BINBN.IS","BINHO.IS","BIOEN.IS","BIZIM.IS","BJKAS.IS","BLCYT.IS","BLUME.IS","BMSCH.IS","BMSTL.IS","BNTAS.IS","BOBET.IS","BORLS.IS","BORSK.IS","BOSSA.IS","BRISA.IS","BRKO.IS","BRKSN.IS","BRKVY.IS","BRLSM.IS","BRMEN.IS","BRSAN.IS","BRYAT.IS","BSOKE.IS","BTCIM.IS","BUCIM.IS","BULGS.IS","BURCE.IS","BURVA.IS","BVSAN.IS","BYDNR.IS","CANTE.IS","CASA.IS","CATES.IS","CCOLA.IS","CELHA.IS","CEMAS.IS","CEMTS.IS","CEMZY.IS","CEOEM.IS","CGCAM.IS","CIMSA.IS","CLEBI.IS","CMBTN.IS","CMENT.IS","CONSE.IS","COSMO.IS","CRDFA.IS","CRFSA.IS","CUSAN.IS","CVKMD.IS","CWENE.IS","DAGI.IS","DAPGM.IS","DARDL.IS","DCTTR.IS","DENGE.IS","DERHL.IS","DERIM.IS","DESA.IS","DESPC.IS","DEVA.IS","DGATE.IS","DGGYO.IS","DGNMO.IS","DIRIT.IS","DITAS.IS","DMRGD.IS","DMSAS.IS","DNISI.IS","DOAS.IS","DOCO.IS","DOFER.IS","DOFRB.IS","DOGUB.IS","DOHOL.IS","DOKTA.IS","DSTKF.IS","DUNYH.IS","DURDO.IS","DURKN.IS","DYOBY.IS","DZGYO.IS","EBEBK.IS","ECILC.IS","ECOGR.IS","ECZYT.IS","EDATA.IS","EDIP.IS","EFOR.IS","EGEEN.IS","EGEGY.IS","EGEPO.IS","EGGUB.IS","EGPRO.IS","EGSER.IS","EKDMR.IS","EKGYO.IS","EKIZ.IS","EKOS.IS","EKSUN.IS","ELITE.IS","EMKEL.IS","EMNIS.IS","EMPAE.IS","ENDAE.IS","ENERY.IS","ENJSA.IS","ENKAI.IS","ENPRA.IS","ENSRI.IS","ENTRA.IS","EPLAS.IS","ERBOS.IS","ERCB.IS","EREGL.IS","ERSU.IS","ESCAR.IS","ESCOM.IS","ESEN.IS","ETILR.IS","ETYAT.IS","EUHOL.IS","EUKYO.IS","EUPWR.IS","EUREN.IS","EUYO.IS","EYGYO.IS","FADE.IS","FENER.IS","FLAP.IS","FMIZP.IS","FONET.IS","Menkul.IS","FORMT.IS","FORTE.IS","FRIGO.IS","FRMPL.IS","FROTO.IS","FZLGY.IS","GARAN.IS","GARFA.IS","GATEG.IS","GEDIK.IS","GEDZA.IS","GENIL.IS","GENKM.IS","GENTS.IS","GEREL.IS","GESAN.IS","GIPTA.IS","GLBMD.IS","GLCVY.IS","GLDTR.IS","GLRMK.IS","GLRYH.IS","GLYHO.IS","GMSTR.IS","GMTAS.IS","GOKNR.IS","GOLTS.IS","GOODY.IS","GOZDE.IS","GRNYO.IS","GRSEL.IS","GRTHO.IS","GSDDE.IS","GSDHO.IS","GSRAY.IS","GUBRF.IS","GUNDG.IS","GWIND.IS","GZNMI.IS","HALKB.IS","HALKS.IS","HATEK.IS","HATSN.IS","HDFGS.IS","HEDEF.IS","HEKTS.IS","HKTM.IS","HLGYO.IS","HOROZ.IS","HRKET.IS","HTTBT.IS","HUBVC.IS","HUNER.IS","HURGZ.IS","ICBCT.IS","ICUGS.IS","IDGYO.IS","IEYHO.IS","IHAAS.IS","IHEVA.IS","IHGZT.IS","IHLAS.IS","IHLGM.IS","IHYAY.IS","IMASM.IS","INDES.IS","INFO.IS","INGRM.IS","INTEK.IS","INTEM.IS","INVEO.IS","INVES.IS","ISATR.IS","ISBIR.IS","ISBTR.IS","ISCTR.IS","ISDMR.IS","ISFIN.IS","ISGLK.IS","ISGSY.IS","ISGYO.IS","ISIST.IS","ISKPL.IS","ISKUR.IS","ISMEN.IS","ISSEN.IS","ISYAT.IS","IZENR.IS","IZFAS.IS","IZINV.IS","IZMDC.IS","JANTS.IS","KAPLM.IS","KAREL.IS","KARSN.IS","KARTN.IS","KATMR.IS","KAYSE.IS","KBORU.IS","KCAER.IS","KCHOL.IS","KENT.IS","KERVN.IS","KFEIN.IS","KGYO.IS","KIMMR.IS","KLGYO.IS","KLKIM.IS","KLMSN.IS","KLNMA.IS","KLRHO.IS","KLSER.IS","KLSYN.IS","KLYPV.IS","KMPUR.IS","KNFRT.IS","KOCMT.IS","KONKA.IS","KONTR.IS","KONYA.IS","KOPOL.IS","KORDS.IS","KOTON.IS","KRDMA.IS","KRDMB.IS","KRDMD.IS","KRGYO.IS","KRONT.IS","KRPLS.IS","KRSTL.IS","KRTEK.IS","KRVGD.IS","KSTUR.IS","KTLEV.IS","KTSKR.IS","KUTPO.IS","KUVVA.IS","KUYAS.IS","KZBGY.IS","KZGYO.IS","LIDER.IS","LIDFA.IS","LILAK.IS","LINK.IS","LKMNH.IS","LMKDC.IS","LOGO.IS","LRSHO.IS","LUKSK.IS","LXGYO.IS","LYDHO.IS","LYDYE.IS","MAALT.IS","MACKO.IS","MAGEN.IS","MAKIM.IS","MAKTK.IS","MANAS.IS","MARBL.IS","MARKA.IS","MARMR.IS","MARTI.IS","MAVI.IS","MCARD.IS","MEDTR.IS","MEGAP.IS","MEGAP.IS","MEGMT.IS","MEKAG.IS","MEPET.IS","MERCN.IS","MERIT.IS","MERKO.IS","METRO.IS","MEYSU.IS","MGROS.IS","MHRGY.IS","MIATK.IS","MMCAS.IS","MNDRS.IS","MNDTR.IS","MOBTL.IS","MOGAN.IS","MOPAS.IS","MPARK.IS","MRGYO.IS","MRSHL.IS","MSGYO.IS","MTRKS.IS","MTRYO.IS","MZHLD.IS","NATEN.IS","NETAS.IS","NETCD.IS","NIBAS.IS","NPTLR.IS","NTGAZ.IS","NTHOL.IS","NUGYO.IS","NUHCM.IS","OBAMS.IS","OBASE.IS","ODAS.IS","ODINE.IS","OFSYM.IS","ONCSM.IS","ONRYT.IS","OPK30.IS","OPT25.IS","OPTGY.IS","OPTLR.IS","OPX30.IS","ORCAY.IS","ORGE.IS","ORMA.IS","ORZAX.IS","OSMEN.IS","OSTIM.IS","OTKAR.IS","OTTO.IS","OYAKC.IS","OYAYO.IS","OYLUM.IS","OYYAT.IS","OZATD.IS","OZGYO.IS","OZKGY.IS","OZKGY.IS","OZRDN.IS","OZSUB.IS","OZYSR.IS","PAGYO.IS","PAHOL.IS","PAMEL.IS","Menkul.IS","PAPIL.IS","PARSN.IS","PASEU.IS","PATEK.IS","PCILT.IS","PEKGY.IS","PENGD.IS","PENTA.IS","PETKM.IS","PETUN.IS","PGSUS.IS","PINSU.IS","PKART.IS","PKENT.IS","PLTUR.IS","PNLSN.IS","PNSUT.IS","POLHO.IS","POLTK.IS","PRDGS.IS","PRKAB.IS","PRKME.IS","PRZMA.IS","PSDTC.IS","PSGYO.IS","QNBFK.IS","QNBTR.IS","QTEMZ.IS","QUAGR.IS","RALYH.IS","RAYSG.IS","REEDR.IS","RGYAS.IS","RNPOL.IS","RODRG.IS","RTALB.IS","RUBNS.IS","RUZYE.IS","RYGYO.IS","RYSAS.IS","SAFKR.IS","SAHOL.IS","SAMAT.IS","SANEL.IS","SANFM.IS","SANKO.IS","SARKY.IS","SASA.IS","SAYAS.IS","SDTTR.IS","SEGMN.IS","SEGYO.IS","SEKFK.IS","SEKUR.IS","SELEC.IS","SELVA.IS","SERNT.IS","SEYKM.IS","SILVR.IS","SISE.IS","SKBNK.IS","SKTAS.IS","SKYLP.IS","SKYMD.IS","SMART.IS","SMRTG.IS","SMRVA.IS","SNGYO.IS","SNICA.IS","SNPAM.IS","SODSN.IS","SOHOE.IS","SOKE.IS","SOKM.IS","SONME.IS","SRVGY.IS","SUMAS.IS","SUNTK.IS","SURGY.IS","SUWEN.IS","SVGYO.IS","TABGD.IS","TARKM.IS","TATEN.IS","TATGD.IS","TAVHL.IS","TBORG.IS","TCELL.IS","TCKRC.IS","TDGYO.IS","TEHOL.IS","TEKTU.IS","TERA.IS","TEZOL.IS","TGSAS.IS","THYAO.IS","TKFEN.IS","TKNSA.IS","TLMAN.IS","TMPOL.IS","TMSN.IS","TNZTP.IS","TOASO.IS","TRALT.IS","TRCAS.IS","TRENJ.IS","TRGYO.IS","TRHOL.IS","TRILC.IS","TRMET.IS","TSGYO.IS","TSKB.IS","TSPOR.IS","TTKOM.IS","TTRAK.IS","TUCLK.IS","TUKAS.IS","TUPRS.IS","TUREX.IS","TURGG.IS","TURSG.IS","UCAYM.IS","UFUK.IS","ULAS.IS","ULKER.IS","ULUFA.IS","ULUSE.IS","ULUUN.IS","UNLU.IS","USAK.IS","USDTR.IS","VAKBN.IS","VAKFA.IS","VAKFN.IS","VAKKO.IS","VANGD.IS","VBTYZ.IS","VERTU.IS","VERUS.IS","VESBE.IS","VESTL.IS","VKFYO.IS","VKGYO.IS","VKING.IS","VRGYO.IS","VSNMD.IS","X030S.IS","X100S.IS","XBANA.IS","XBANK.IS","XBLSM.IS","XELKT.IS","XFINK.IS","XGIDA.IS","XGMYO.IS","XHARZ.IS","XHOLD.IS","XILTM.IS","XINSA.IS","XKAGT.IS","XKMYA.IS","XKOBI.IS","XKURY.IS","XMADN.IS","XMANA.IS","XMESY.IS","XSADA.IS","XSANK.IS","XSANT.IS","XSBAL.IS","XSBUR.IS","XSDNZ.IS","XSGRT.IS","XSIST.IS","XSIZM.IS","XSKAY.IS","XSKOC.IS","XSKON.IS","XSPOR.IS","XSTKR.IS","XTAST.IS","XTCRT.IS","XTEKS.IS","XTM25.IS","XTMTU.IS","XTRZM.IS","XTUMY.IS","XU030.IS","XU050.IS","XU100.IS","XUHIZ.IS","XULAS.IS","XUMAL.IS","XUSIN.IS","XUSRD.IS","XUTEK.IS","XUTUM.IS","XYLDZ.IS","XYORT.IS","XYUZO.IS","YAPRK.IS","YATAS.IS","YAYLA.IS","YBTAS.IS","YEOTK.IS","YESIL.IS","YGGYO.IS","YIGIT.IS","YKBNK.IS","YKSLN.IS","YONGA.IS","YUNSA.IS","YYAPI.IS","YYLGD.IS","Z30EA.IS","Z30KE.IS","Z30KP.IS","ZEDUR.IS","ZELOT.IS","ZERGY.IS","ZGOLD.IS","ZGYO.IS","ZOREN.IS","ZPBDL.IS","ZPLIB.IS","ZPT10.IS","ZPX30.IS","ZRE20.IS","ZRGYO.IS","ZSR25.IS","ZTLRF.IS","ZTLRK.IS","ZTM25.IS"]

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
