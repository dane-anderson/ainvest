import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


PANEL_BG = "#091733"
GRID = "rgba(255,255,255,0.04)"
TEXT = "#E7EEF9"
ACCENT = "#3A8DFF"
GREEN = "#2EE59D"
RED = "#FF4D6D"
AMBER = "#FFB020"


def render_chart_module(hist, ticker, signal, daily_change, source_used="Live market fallback"):
    if hist is None or hist.empty:
        return

    hist = hist.copy().sort_index()

    required_cols = {"Open", "High", "Low", "Close"}
    if not required_cols.issubset(hist.columns):
        st.warning("Chart data missing OHLC fields.")
        return

    if "Volume" not in hist.columns:
        hist["Volume"] = np.nan

    # Indicators
    hist["EMA20"] = hist["Close"].ewm(span=20, adjust=False).mean()
    hist["EMA50"] = hist["Close"].ewm(span=50, adjust=False).mean()
    hist["Ret"] = hist["Close"].pct_change()

    typical = (hist["High"] + hist["Low"] + hist["Close"]) / 3.0
    vol = hist["Volume"].fillna(0)
    cum_vol = vol.cumsum()
    cum_pv = (typical * vol).cumsum()
    hist["VWAP"] = np.where(cum_vol > 0, cum_pv / cum_vol, np.nan)

    latest_close = float(hist["Close"].iloc[-1])

    lookback = hist.tail(20) if len(hist) >= 20 else hist
    high_20d = float(lookback["High"].max()) if not lookback.empty else None
    low_20d = float(lookback["Low"].min()) if not lookback.empty else None

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.76, 0.24],
    )

    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name="Price",
            increasing_line_color=GREEN,
            increasing_fillcolor=GREEN,
            decreasing_line_color=RED,
            decreasing_fillcolor=RED,
            increasing_line_width=1,
            decreasing_line_width=1,
            opacity=0.95,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist["VWAP"],
            name="VWAP",
            mode="lines",
            line=dict(color=ACCENT, width=1.8),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist["EMA20"],
            name="EMA20",
            mode="lines",
            line=dict(color=AMBER, width=1.3),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist["EMA50"],
            name="EMA50",
            mode="lines",
            line=dict(color="rgba(231,238,249,0.55)", width=1.2),
        ),
        row=1,
        col=1,
    )

    if high_20d is not None:
        fig.add_hline(
            y=high_20d,
            line_dash="dot",
            line_color="rgba(58,141,255,0.45)",
            line_width=1,
            row=1,
            col=1,
        )

    if low_20d is not None:
        fig.add_hline(
            y=low_20d,
            line_dash="dot",
            line_color="rgba(231,238,249,0.22)",
            line_width=1,
            row=1,
            col=1,
        )

    fig.add_hline(
        y=latest_close,
        line_dash="dash",
        line_color="rgba(231,238,249,0.25)",
        line_width=1,
        row=1,
        col=1,
    )

    fig.add_annotation(
        x=hist.index[-1],
        y=latest_close,
        text=f"{latest_close:.2f}",
        showarrow=False,
        xanchor="right",
        font=dict(color=TEXT, size=11),
        bgcolor="rgba(11,22,51,0.96)",
        bordercolor="rgba(255,255,255,0.14)",
        borderwidth=1,
    )

    vol_colors = np.where(
        hist["Close"] >= hist["Open"],
        "rgba(46,229,157,0.22)",
        "rgba(255,77,109,0.22)",
    )

    fig.add_trace(
        go.Bar(
            x=hist.index,
            y=hist["Volume"],
            name="Volume",
            marker_color=vol_colors,
        ),
        row=2,
        col=1,
    )

    avg_vol_20 = float(hist["Volume"].tail(20).mean()) if hist["Volume"].notna().any() else None
    if avg_vol_20 is not None:
        fig.add_hline(
            y=avg_vol_20,
            line_dash="dash",
            line_color="rgba(231,238,249,0.18)",
            line_width=1,
            row=2,
            col=1,
        )

    fig.update_layout(
        height=540,
        margin=dict(l=10, r=10, t=35, b=8),
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
        font=dict(color=TEXT),
        hovermode="x unified",
        title=dict(
            text=f"<b>{ticker} · 1M Market Structure</b>",
            x=0.02,
            y=1.0,
            font=dict(
                size=16,
                color="#FFFFFF"
            ),
        ),
            
        
        xaxis_rangeslider_visible=False,
    
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.93,
            xanchor="left",
            x=0.0,
            font=dict(
                size=12,              # 👈 bigger
                color="#FFFFFF",      # 👈 pure white
                family="Inter, Arial" # 👈 optional but clean
        ),
    ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        showline=False,
        rangeslider_visible=False,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        showline=False,
        tickfont=dict(color="rgba(231,238,249,0.72)", size=10),
    )

    if len(hist) > 1:
        start_idx = max(0, len(hist) - 40)
        extra_pad = (hist.index[-1] - hist.index[-2]) * 2
        fig.update_xaxes(range=[hist.index[start_idx], hist.index[-1] + extra_pad])

    fig.update_annotations(font_color=TEXT)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "scrollZoom": True,
        },
    )