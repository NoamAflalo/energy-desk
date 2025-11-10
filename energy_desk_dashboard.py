# ==============================================
# energy_desk_dashboard.py — FINAL VERSION
# RUN: streamlit run energy_desk_dashboard.py
# ==============================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import blpapi

st.set_page_config(page_title="Noam Energy Desk", layout="wide", page_icon="fire")
st.title("Noam Energy Desk")
st.markdown("**Live COT + Prices + Distillate Z-Score & Correlations** — Built by @aflalo_noa37272")

# ==============================================
# BLOOMBERG CONNECTION
# ==============================================
@st.cache_resource(ttl=3600)
def connect_to_bloomberg():
    session_options = blpapi.SessionOptions()
    session_options.setServerHost("localhost")
    session_options.setServerPort(8194)
    session = blpapi.Session(session_options)
    if not session.start() or not session.openService("//blp/refdata"):
        st.error("Bloomberg connection failed")
        return None
    return session

def process_response(session, ticker):
    data = []
    done = False
    while not done:
        ev = session.nextEvent(500)
        for msg in ev:
            if msg.messageType() == blpapi.Name("HistoricalDataResponse"):
                security_data = msg.getElement("securityData")
                if security_data.hasElement("fieldData"):
                    for field in security_data.getElement("fieldData").values():
                        date = field.getElementAsDatetime("date")
                        value = field.getElementAsFloat("PX_LAST")
                        data.append((date, value))
            if ev.eventType() == blpapi.Event.RESPONSE:
                done = True
    if data:
        df = pd.DataFrame(data, columns=["Date", "PX_LAST"])
        df.set_index("Date", inplace=True)
        return df
    return pd.DataFrame()

# ==============================================
# LOAD ALL DATA
# ==============================================
@st.cache_data(ttl=3600)
def load_all_data():
    session = connect_to_bloomberg()
    if not session: st.stop()

    # === COT TICKERS (same as your notebook 1) ===
    cot_tickers = {
        "Producer Long WTI Index": "CFFDQPML Index", "Producer Short WTI Index": "CFFDQPMS Index", "Producer Net WTI Index": "CFFDQPMN Index",
        "SD Long WTI Index": "CFFDQSWL Index", "SD Short WTI Index": "CFFDQSWS Index", "SD Net WTI Index": "CFFDQSWN Index",
        "MM Long WTI Index": "CFFDQMML Index", "MM Short WTI Index": "CFFDQMMS Index", "MM Net WTI Index": "CFFDQMMN Index",
        "OR Long WTI Index": "CFFDQORL Index", "OR Short WTI Index": "CFFDQORS Index", "OR Net WTI Index": "CFFDQORN Index",
        "NR Long WTI Index": "NYM1CNRL Index", "NR Short WTI Index": "NYM1CNRS Index", "NR Net WTI Index": "NYM1CNRN Index",
        "Producer Long BRENT Index": "ICFUBPML Index", "Producer Short BRENT Index": "ICFUBPMS Index", "Producer Net BRENT Index": "ICFUBPMN Index",
        "SD Long BRENT Index": "ICFUBSWL Index", "SD Short BRENT Index": "ICFUBSWS Index", "SD Net BRENT Index": "ICFUBSWN Index",
        "MM Long BRENT Index": "ICFUBMML Index", "MM Short BRENT Index": "ICFUBMMS Index", "MM Net BRENT Index": "ICFUBMMN Index",
        "OR Long BRENT Index": "ICFUBORL Index", "OR Short BRENT Index": "ICFUBORS Index", "OR Net BRENT Index": "ICFUBORN Index",
        "NR Long BRENT Index": "ICFUBNRL Index", "NR Short BRENT Index": "ICFUBNRS Index", "NR Net BRENT Index": "ICFUBNRN Index",
        "Producer Long RBOB Index": "CFFDRPML Index", "Producer Short RBOB Index": "CFFDRPMS Index", "Producer Net RBOB Index": "CFFDRPMN Index",
        "SD Long RBOB Index": "CFFDRSWL Index", "SD Short RBOB Index": "CFFDRSWS Index", "SD Net RBOB Index": "CFFDRSWN Index",
        "MM Long RBOB Index": "CFFDRMML Index", "MM Short RBOB Index": "CFFDRMMS Index", "MM Net RBOB Index": "CFFDRMMN Index",
        "OR Long RBOB Index": "CFFDRORL Index", "OR Short RBOB Index": "CFFDRORS Index", "OR Net RBOB Index": "CFFDRORN Index",
        "NR Long RBOB Index": "NYM2XNRL Index", "NR Short RBOB Index": "NYM2XNRS Index", "NR Net RBOB Index": "NYM2XNRN Index",
        "Producer Long HO Index": "CFFDNPML Index", "Producer Short HO Index": "CFFDNPMS Index", "Producer Net HO Index": "CFFDNPMN Index",
        "SD Long HO Index": "CFFDNSWL Index", "SD Short HO Index": "CFFDNSWS Index", "SD Net HO Index": "CFFDNSWN Index",
        "MM Long HO Index": "CFFDNMML Index", "MM Short HO Index": "CFFDNMMS Index", "MM Net HO Index": "CFFDNMMN Index",
        "OR Long HO Index": "CFFDNORL Index", "OR Short HO Index": "CFFDNORS Index", "OR Net HO Index": "CFFDNORN Index",
        "NR Long HO Index": "NYM1HNRL Index", "NR Short HO Index": "NYM1HNRS Index", "NR Net HO Index": "NYM1HNRN Index",
        "Producer Long GO Index": "ICFUAPML Index", "Producer Short GO Index": "ICFUAPMS Index", "Producer Net GO Index": "ICFUAPMN Index",
        "SD Long GO Index": "ICFUASWL Index", "SD Short GO Index": "ICFUASWS Index", "SD Net GO Index": "ICFUASWN Index",
        "MM Long GO Index": "ICFUAMML Index", "MM Short GO Index": "ICFUAMMS Index", "MM Net GO Index": "ICFUAMMN Index",
        "OR Long GO Index": "ICFUAORL Index", "OR Short GO Index": "ICFUAORS Index", "OR Net GO Index": "ICFUAORN Index",
        "NR Long GO Index": "ICFUANRL Index", "NR Short GO Index": "ICFUANRS Index", "NR Net GO Index": "ICFUANRN Index",
    }

    # === MARKET TICKERS (notebook 2) ===
    market_tickers = {
        'Sing GO': 'FSG1M1 Index', 'Sing GO M5': 'FSG1M5 Index', 'Sing GO M6': 'FSG1M6 Index',
        'Sing Kero': 'FSSKM1 Index', 'Sing Kero M4': 'FSSKM4 Index', 'Sing Kero M5': 'FSSKM5 Index', 'Sing Kero M6': 'FSSKM6 Index',
        'Regrade': 'FSREM1 Index', 'Regrade M6': 'FSREM6 Index', 'GO EW': 'FISGM1 Index', 'GO EW M6': 'FISGM6 Index',
        'Gasoil Swap': 'FSGOM1 Index', 'Gasoil Swap M2': 'FSGOM2 Index', 'Gasoil Swap M6': 'FSGOM6 Index',
        'Gasoil Crack': 'FSQCM1 Index', 'Jet Diff': 'FWJSM1 Index', 'HO Swap': 'FSHOM1 Index', 'HO Swap M6': 'FSHOM6 Index',
        'Brent Swap M1': 'FSCOM1 Index', 'Brent Swap M2': 'FSCOM2 Index', 'Brent Swap M6': 'FSCOM6 Index',
        'WTI Swap': 'FSCLM1 Index', 'WTI Swap M6': 'FSCLM6 Index', 'VIX': 'VIX Index', 'S&P': 'SPX Index', 'BTC': 'XBX Index',
        '92 M1': 'FSGAM1 Index', '92 M5': 'FSGAM5 Index',
    }

    # === FUTURES ===
    futures_tickers = {"WTI": "CL1 Comdty", "BRENT": "CO1 Comdty", "RBOB": "XB1 Comdty", "HO": "HO1 Comdty", "GO": "QS1 Comdty"}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*6)

    # Fetch COT
    df_cot = pd.DataFrame()
    for name, ticker in cot_tickers.items():
        try:
            req = session.getService("//blp/refdata").createRequest("HistoricalDataRequest")
            req.getElement("securities").appendValue(ticker)
            req.getElement("fields").appendValue("PX_LAST")
            req.set("startDate", start_date.strftime("%Y%m%d"))
            req.set("endDate", end_date.strftime("%Y%m%d"))
            session.sendRequest(req)
            tmp = process_response(session, ticker)
            if not tmp.empty:
                tmp.index = pd.to_datetime(tmp.index)
                tmp = tmp[tmp.index.dayofweek < 5]
                df_cot[name] = tmp['PX_LAST']
        except: pass

    # === MULTIINDEX + ABSOLUTE + Δ ===
    def parse_column(col_name):
        parts = col_name.rsplit(' ', 2)
        product = parts[1]
        cat_pos = parts[0]
        cat = cat_pos.split()[0]
        pos = ' '.join(cat_pos.split()[1:])
        return product, cat, pos

    new_tuples = []
    for col in df_cot.columns:
        prod, cat, pos = parse_column(col)
        if cat == "NR":
            new_tuples.append((prod, "Non-Reportable", None, pos))
        else:
            new_tuples.append((prod, "Reportable", cat, pos))

    df_cot.columns = pd.MultiIndex.from_tuples(new_tuples, names=["Product", "Reportable/Non", "Category", "Position"])
    df_cot = df_cot.sort_index(axis=1)

    # Add Δ columns
    change_df = df_cot.diff()
    new_cols = [(c[0], c[1], c[2], c[3] + " | Δ") for c in change_df.columns]
    change_df.columns = pd.MultiIndex.from_tuples(new_cols, names=df_cot.columns.names)
    df_cot = pd.concat([df_cot, change_df], axis=1).sort_index(axis=1)

    # Futures + weekly
    futures_df = pd.DataFrame()
    for name, ticker in futures_tickers.items():
        try:
            req = session.getService("//blp/refdata").createRequest("HistoricalDataRequest")
            req.getElement("securities").appendValue(ticker)
            req.getElement("fields").appendValue("PX_LAST")
            req.set("startDate", start_date.strftime("%Y%m%d"))
            req.set("endDate", end_date.strftime("%Y%m%d"))
            session.sendRequest(req)
            tmp = process_response(session, ticker)
            if not tmp.empty:
                tmp.index = pd.to_datetime(tmp.index)
                tmp = tmp[tmp.index.dayofweek < 5]
                futures_df[name] = tmp['PX_LAST']
        except: pass

    cot_tuesdays = df_cot.index
    futures_weekly = futures_df.reindex(cot_tuesdays.union(futures_df.index)).ffill().reindex(cot_tuesdays)

    # Spreads
    spread_df = pd.DataFrame(index=futures_df.index)
    spread_df["WTI-BRENT"] = futures_df["WTI"] - futures_df["BRENT"]
    spread_weekly = spread_df.reindex(cot_tuesdays.union(spread_df.index)).ffill().reindex(cot_tuesdays)

    # Market data
    df_market = pd.DataFrame()
    for name, ticker in market_tickers.items():
        try:
            req = session.getService("//blp/refdata").createRequest("HistoricalDataRequest")
            req.getElement("securities").appendValue(ticker)
            req.getElement("fields").appendValue("PX_LAST")
            req.set("startDate", start_date.strftime("%Y%m%d"))
            req.set("endDate", end_date.strftime("%Y%m%d"))
            session.sendRequest(req)
            tmp = process_response(session, ticker)
            if not tmp.empty:
                tmp.index = pd.to_datetime(tmp.index)
                tmp = tmp[tmp.index.dayofweek < 5]
                df_market[name] = tmp['PX_LAST']
        except: pass

    # Derived columns
    if all(col in df_market.columns for col in ['Jet Diff', 'Gasoil Swap']):
        df_market['Jet Swap'] = df_market['Jet Diff'] + df_market['Gasoil Swap']

    return df_cot, futures_weekly, spread_weekly, df_market

df_cot, futures_weekly, spread_weekly, df_market = load_all_data()

# ==============================================
# PLOT FUNCTIONS
# ==============================================
def plot_cot(selections):
    idx = pd.IndexSlice
    fig = make_subplots()
    plotted = []
    for sel in selections:
        try:
            prod, rep, cat, pos = sel
            if rep == "Non-Reportable":
                series = df_cot.loc[:, idx[prod, "Non-Reportable", :, pos]]
            else:
                series = df_cot.loc[:, idx[prod, "Reportable", cat, pos]]
            series = series.iloc[:, 0] if series.ndim > 1 else series
            series = series.dropna()
            if series.empty: continue
            name = f"{prod} {cat if rep=='Reportable' else 'NR'} {pos}"
            fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines+markers", name=name, line=dict(width=3), marker=dict(size=7)))
            plotted.append(name)
        except: pass
    title = " vs ".join(plotted) if plotted else "No data"
    fig.update_layout(title=title, template="plotly_dark", height=600, yaxis_title="Contracts", hovermode="x unified")
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(zeroline=True, zerolinecolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ==============================================
# SIDEBAR & TABS
# ==============================================
tool = st.sidebar.selectbox("Tool", ["COT Positioning", "Distillate Z-Score & Correlations"])

if tool == "COT Positioning":
    st.header("COT Positioning")
    products = st.multiselect("Products", ["WTI", "BRENT", "RBOB", "HO", "GO"], default=["WTI", "BRENT"])
    cats = st.multiselect("Categories", ["MM", "OR", "Producer", "SD", "NR"], default=["MM", "OR"])
    pos_type = st.radio("Show", ["Absolute Position", "Weekly Change (Δ)"])
    pos = "Net" if pos_type == "Absolute Position" else "Net | Δ"

    selections = [(p, "Reportable" if c != "NR" else "Non-Reportable", c if c != "NR" else None, pos) for p in products for c in cats]
    plot_cot(selections)

    st.header("Prices & Spreads")
    price_items = st.multiselect("Select", ["WTI","BRENT","WTI-BRENT","RBOB","HO","GO"], default=["WTI","BRENT","WTI-BRENT"])
    weekly = st.checkbox("Weekly (Tue)", value=True)
    df_p = futures_weekly if weekly else futures_df
    df_s = spread_weekly if weekly else spread_df
    fig = make_subplots()
    for item in price_items:
        if item in df_p.columns:
            s = df_p[item].dropna()
        elif item in df_s.columns:
            s = df_s[item].dropna()
        else: continue
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines+markers" if weekly else "lines", name=item, line=dict(width=3)))
    fig.update_layout(title=" | ".join(price_items) + (" — Weekly" if weekly else " — Daily"), template="plotly_dark", height=600)
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.header("Correlation Matrix")
    cols = st.multiselect("Select", df_market.columns.tolist(), default=["Sing GO","Gasoil Crack","Regrade","Jet Diff","Brent Swap M1"])
    if len(cols) > 1:
        corr = df_market[cols].corr()
        fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns, colorscale="RdYlGn", zmin=-1, zmax=1))
        fig.update_layout(title="Correlation Matrix", height=700)
        st.plotly_chart(fig, use_container_width=True)

    st.header("Gasoil Crack Z-Score")
    lookback = st.slider("Lookback", 10, 100, 30)
    df_z = df_market.copy()
    df_z['Spread'] = df_z['Gasoil Crack']
    df_z['Mean'] = df_z['Spread'].rolling(lookback).mean()
    df_z['Std'] = df_z['Spread'].rolling(lookback).std()
    df_z['Z'] = (df_z['Spread'] - df_z['Mean']) / df_z['Std']
    df_z['Upper'] = 2.5
    df_z['Lower'] = -2.5
    divergences = df_z[(df_z['Z'] > 2.5) | (df_z['Z'] < -2.5)]

    fig = make_subplots()
    fig.add_trace(go.Scatter(x=df_z.index, y=df_z['Z'], name="Z-Score"))
    fig.add_trace(go.Scatter(x=df_z.index, y=df_z['Upper'], name="Upper", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=df_z.index, y=df_z['Lower'], name="Lower", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=divergences.index, y=divergences['Z'], mode="markers", name="Signal", marker=dict(color="red", size=10)))
    fig.update_layout(title="Gasoil Crack Z-Score", template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)

# ==============================================
# FOOTER
# ==============================================
st.sidebar.markdown("---")
st.sidebar.success("Built by @aflalo_noa37272")
st.sidebar.caption(f"Last update: {datetime.now().strftime('%H:%M')} GMT")
