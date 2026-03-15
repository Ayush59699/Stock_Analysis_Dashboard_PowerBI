import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Load data
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "stock_analysis.xlsx")

def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    return pd.read_excel(DATA_FILE, sheet_name=None)

# App setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
app.title = "Stock Analysis Dashboard"

# Color map
COLOR_MAP = {
    "TCS.NS": "#1f77b4", "INFY.NS": "#2ca02c",
    "HDFCBANK.NS": "#ff7f0e", "ICICIBANK.NS": "#d62728",
    "RELIANCE.NS": "#9467bd", "^NSEI": "#7f7f7f"
}

# Layout components
navbar = dbc.NavbarSimple(
    brand="NSE Stock Analysis Dashboard",
    brand_href="#",
    color="dark",
    dark=True,
)

def create_overview(sheets):
    if not sheets: return html.H3("Data not found. Run pipeline first.")
    df_prices = sheets["prices"]
    df_summary = sheets["summary"]
    
    # KPIs
    kpi_cards = []
    for _, row in df_summary.iterrows():
        card = dbc.Card([
            dbc.CardBody([
                html.H5(row["ticker"], className="card-title"),
                html.H6(f"₹{row['current_price']}", className="card-subtitle"),
                html.P(f"1Y Return: {row['return_1y_pct']}%", className="card-text"),
                html.P(f"Signal: {row['signal_scorecard']}", className="card-text")
            ])
        ], className="m-2", style={"width": "18rem"})
        kpi_cards.append(card)
        
    # Rebased prices
    df_prices['rebased'] = df_prices.groupby('ticker')['close'].transform(lambda x: x / x.iloc[0] * 100)
    fig_price = px.line(df_prices, x="date", y="rebased", color="ticker", color_discrete_map=COLOR_MAP,
                        title="Normalized Prices (Base=100)")
    
    return html.Div([
        dbc.Row([dbc.Col(c) for c in kpi_cards], className="mb-4", style={"display": "flex", "flexWrap": "wrap"}),
        dcc.Graph(figure=fig_price)
    ])

def create_technical(sheets):
    if not sheets: return html.Div()
    df_tech = sheets["technicals"]
    tickers = df_tech["ticker"].unique()
    
    return html.Div([
        html.H4("Technical Indicators"),
        dcc.Dropdown(id="tech-ticker", options=[{"label": t, "value": t} for t in tickers], value="RELIANCE.NS", clearable=False),
        dcc.Graph(id="tech-chart")
    ])

@app.callback(Output("tech-chart", "figure"), [Input("tech-ticker", "value")])
def update_tech_chart(ticker):
    sheets = load_data()
    if not sheets: return go.Figure()
    df = sheets["technicals"]
    df = df[df["ticker"] == ticker]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["bb_upper"], line=dict(color='gray', dash='dash'), name="BB Upper"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["bb_lower"], line=dict(color='gray', dash='dash'), name="BB Lower"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma_50"], line=dict(color='orange'), name="MA 50"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma_200"], line=dict(color='red'), name="MA 200"))
    fig.update_layout(title=f"{ticker} Technicals")
    return fig

app.layout = dbc.Container([
    navbar,
    dbc.Tabs([
        dbc.Tab(label="Overview", tab_id="tab-1"),
        dbc.Tab(label="Technical Signals", tab_id="tab-2"),
    ], id="tabs", active_tab="tab-1", className="mt-3"),
    html.Div(id="tab-content", className="p-4")
], fluid=True)

@app.callback(Output("tab-content", "children"), [Input("tabs", "active_tab")])
def render_tab_content(active_tab):
    sheets = load_data()
    if active_tab == "tab-1":
        return create_overview(sheets)
    elif active_tab == "tab-2":
        return create_technical(sheets)
    return "Work in progress"

if __name__ == "__main__":
    app.run(debug=True, port=8050)

