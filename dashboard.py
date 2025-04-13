import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import db
from runner import process_company, add_new_company

# Try to import sklearn for trend line (optional)
try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Initialize the database
db.init_db()

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# Set the title
app.title = "Company Reputation Tracker"

# Define the navbar
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fas fa-chart-line me-2", style={"fontSize": "1.5rem"})),
                        dbc.Col(dbc.NavbarBrand("Company Reputation Tracker", className="ms-2")),
                    ],
                    align="center",
                ),
                href="/",
                style={"textDecoration": "none"},
            )
        ]
    ),
    color="primary",
    dark=True,
)

# Function to create company dropdown options
def get_company_options():
    companies = db.get_companies()
    if not companies:
        return []
    return [{"label": f"{company.name} (ID: {company.id})", "value": company.id} for company in companies]

# Function to get sentiment chart
def create_sentiment_chart(company_id):
    stats = db.get_sentiment_stats(company_id)
    
    if stats["TOTAL"] > 0:
        chart_data = pd.DataFrame({
            "Sentiment": ["Positive", "Neutral", "Negative"],
            "Count": [
                stats["POSITIVE"],
                stats["NEUTRAL"],
                stats["NEGATIVE"]
            ]
        })
        
        fig = px.bar(
            chart_data, 
            x="Sentiment", 
            y="Count",
            color="Sentiment",
            color_discrete_map={
                "Positive": "#28a745",
                "Neutral": "#6c757d",
                "Negative": "#dc3545"
            },
            text="Count",
            labels={"Count": "Number of Mentions", "Sentiment": ""},
            template="plotly_white"  # Cleaner template
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            height=500,  # Adjusted height
            font=dict(size=14),  # Larger font
            xaxis=dict(
                tickangle=0,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                tickfont=dict(size=14)
            )
        )
        
        # Make the bars wider
        fig.update_traces(
            width=0.6,  # Wider bars
            textposition='auto',
            textfont=dict(size=16)
        )
        
        # Add percentage labels
        total = stats["TOTAL"]
        for i, sentiment in enumerate(["Positive", "Neutral", "Negative"]):
            if sentiment == "Positive":
                count = stats["POSITIVE"]
            elif sentiment == "Neutral":
                count = stats["NEUTRAL"]
            else:
                count = stats["NEGATIVE"]
            
            percentage = (count / total * 100) if total > 0 else 0
            fig.add_annotation(
                x=sentiment,
                y=count,
                text=f"{percentage:.1f}%",
                showarrow=False,
                yshift=10
            )
        
        return fig, stats
    
    return None, stats

# Function to create sentiment timeline chart
def create_sentiment_timeline(company_id, start_date=None, end_date=None):
    """Create a timeline of sentiment scores.
    
    Args:
        company_id: The company ID
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
    """
    # Get all mentions
    mentions = db.get_mentions(company_id)
    
    if not mentions:
        # Return empty figure if no mentions
        fig = px.line(title="No mentions available")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Sentiment Score",
            height=300
        )
        return fig
    
    # Format the data for the chart
    timeline_data = []
    for mention in mentions:
        if mention.published_at:
            # Apply date range filter if provided
            if start_date and end_date:
                if not (start_date <= mention.published_at < end_date):
                    continue
            timeline_data.append({
                "date": mention.published_at,
                "score": mention.sentiment_score,
                "sentiment": mention.sentiment,
                "title": mention.title,
                "source": mention.source
            })
    
    # Sort by date
    timeline_data = sorted(timeline_data, key=lambda x: x["date"])
    
    # Create DataFrame
    df = pd.DataFrame(timeline_data)
    
    if df.empty:
        # Return empty figure if no data with dates
        fig = px.line(title="No dated mentions available")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Sentiment Score",
            height=300
        )
        return fig
    
    # Create the scatter plot
    fig = px.scatter(
        df,
        x="date",
        y="score",
        color="sentiment",
        color_discrete_map={
            "POSITIVE": "#28a745",
            "NEUTRAL": "#6c757d",
            "NEGATIVE": "#dc3545"
        },
        hover_data=["title", "source", "sentiment"],
        labels={
            "date": "Date",
            "score": "Sentiment Score",
            "sentiment": "Sentiment",
            "title": "Title",
            "source": "Source"
        },
        title="Sentiment Over Time",
        template="plotly_white"
    )
    
    # Add a trend line
    if len(df) >= 2 and SKLEARN_AVAILABLE:
        df_trend = df.copy()
        df_trend['date_num'] = pd.to_numeric(df_trend['date'])
        X = df_trend['date_num'].values.reshape(-1, 1)
        y = df_trend['score'].values
        
        try:
            model = LinearRegression()
            model.fit(X, y)
            
            # Create prediction line
            x_range = np.linspace(df_trend['date_num'].min(), df_trend['date_num'].max(), 100)
            y_pred = model.predict(x_range.reshape(-1, 1))
            
            # Add trend line
            trend_df = pd.DataFrame({
                'date': pd.to_datetime(x_range, unit='ns'),
                'trend': y_pred
            })
            
            fig.add_trace(
                px.line(
                    trend_df, 
                    x='date', 
                    y='trend',
                    color_discrete_sequence=['rgba(100, 100, 100, 0.5)']
                ).data[0]
            )
        except Exception as e:
            print(f"Error creating trend line: {e}")
    
    # Update layout
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=300,
        xaxis=dict(
            title="Date",
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title="Sentiment Score",
            gridcolor='rgba(0,0,0,0.1)',
            range=[-1.1, 1.1],
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)',
            zerolinewidth=1
        ),
        hovermode="closest",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add reference zones
    fig.add_shape(
        type="rect",
        x0=df["date"].min(),
        x1=df["date"].max(),
        y0=0.1,
        y1=1.1,
        fillcolor="rgba(40, 167, 69, 0.1)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=df["date"].min(),
        x1=df["date"].max(),
        y0=-0.1,
        y1=0.1,
        fillcolor="rgba(108, 117, 125, 0.1)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=df["date"].min(),
        x1=df["date"].max(),
        y0=-1.1,
        y1=-0.1,
        fillcolor="rgba(220, 53, 69, 0.1)",
        line=dict(width=0),
        layer="below"
    )
    
    return fig

# Define the layout of the app
app.layout = dbc.Container([
    navbar,
    dbc.Row([
        # Sidebar/Left column
        dbc.Col([
            html.Div([
                html.H4("Companies", className="mb-3"),
                # Company selector
                html.Label("Select Company"),
                dcc.Dropdown(
                    id="company-select",
                    options=get_company_options(),
                    placeholder="Select a company",
                    className="mb-3"
                ),
                # Update button
                dbc.Button(
                    "🔄 Update Mentions Now", 
                    id="update-mentions-btn", 
                    color="primary", 
                    className="mb-3 w-100"
                ),
                html.Div(id="update-status"),
                html.Hr(),
                # Add company form
                html.H5("Add New Company", className="mb-3"),
                dbc.Input(id="company-name-input", placeholder="Company Name", className="mb-2"),
                dbc.Input(id="company-aliases-input", placeholder="Aliases (comma-separated)", className="mb-2"),
                dbc.Button("Add Company", id="add-company-btn", color="success", className="w-100 mb-3"),
                html.Div(id="add-company-status"),
                html.Hr(),
                html.P(
                    "This application tracks company mentions and analyzes sentiment automatically. "
                    "Updates run daily via GitHub Actions.",
                    className="text-muted small"
                )
            ], className="p-3 bg-light rounded")
        ], md=3),
        
        # Main content/Right column
        dbc.Col([
            html.Div(id="main-content")
        ], md=9)
    ], className="mt-4"),
], fluid=True)

# Callback to handle company selection
@callback(
    Output("main-content", "children"),
    Input("company-select", "value")
)
def update_company_content(company_id):
    if not company_id:
        return html.Div([
            html.H4("No Company Selected"),
            html.P("Please select a company from the dropdown or add a new company.")
        ])
    
    # Get company data
    company = db.get_company(company_id)
    mentions = db.get_mentions(company_id)
    
    # Get company aliases
    aliases_display = ""
    if company.aliases:
        aliases = company.aliases.split(",")
        aliases_display = html.P([
            html.Strong("Aliases: "),
            ", ".join(aliases)
        ])
    
    # Create sentiment chart and stats
    sentiment_fig, stats = create_sentiment_chart(company_id)
    
    # Create metrics for sentiment statistics
    total = stats["TOTAL"]
    positive_pct = (stats["POSITIVE"] / total * 100) if total > 0 else 0
    neutral_pct = (stats["NEUTRAL"] / total * 100) if total > 0 else 0
    negative_pct = (stats["NEGATIVE"] / total * 100) if total > 0 else 0
    
    # Calculate average sentiment score (scale from -1 to 1)
    total_score = 0
    score_count = 0
    
    # Get all mentions to calculate average score
    all_mentions = db.get_mentions(company_id)
    for mention in all_mentions:
        if mention.sentiment_score is not None:
            total_score += mention.sentiment_score
            score_count += 1
    
    avg_score = total_score / score_count if score_count > 0 else 0
    
    # Determine sentiment trend indicator
    sentiment_trend = "→"  # Neutral by default
    sentiment_color = "secondary"
    
    if avg_score > 0.2:
        sentiment_trend = "↑"  # Positive trend
        sentiment_color = "success"
    elif avg_score < -0.2:
        sentiment_trend = "↓"  # Negative trend
        sentiment_color = "danger"
    
    metrics_row = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H3(stats["TOTAL"]),
                html.P("Total Mentions", className="text-muted")
            ], className="text-center")
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H3([
                        f"{avg_score:.2f} ",
                        html.Span(sentiment_trend, className=f"text-{sentiment_color}")
                    ], className="d-flex align-items-center justify-content-center"),
                    html.P("Sentiment Score", className="text-muted"),
                    dbc.Progress([
                        dbc.Progress(
                            value=max(0, -avg_score * 100), 
                            color="danger", 
                            bar=True,
                            style={"marginRight": "50%"}
                        ),
                        dbc.Progress(
                            value=max(0, avg_score * 100), 
                            color="success", 
                            bar=True,
                            style={"marginLeft": "50%"}
                        )
                    ], style={"height": "10px"})
                ])
            ], className="text-center")
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H3(f"{positive_pct:.1f}%"),
                    html.P("Positive", className="text-muted text-success")
                ])
            ], className="text-center")
        ]), width=2),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H3(f"{neutral_pct:.1f}%"),
                    html.P("Neutral", className="text-muted text-secondary")
                ])
            ], className="text-center")
        ]), width=2),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H3(f"{negative_pct:.1f}%"),
                    html.P("Negative", className="text-muted text-danger")
                ])
            ], className="text-center")
        ]), width=2)
    ])
    
    # Sort mentions by date
    sorted_mentions = sorted(
        mentions, 
        key=lambda m: m.published_at if m.published_at else datetime.min,
        reverse=True
    )
    
    # Create recent mentions cards
    recent_mentions_cards = []
    for mention in sorted_mentions[:5]:
        # Set color based on sentiment
        card_color = "light"
        border_color = "secondary"
        
        if mention.sentiment == "POSITIVE":
            card_color = "success"
            border_color = "success"
        elif mention.sentiment == "NEGATIVE":
            card_color = "danger"
            border_color = "danger"
        
        recent_mentions_cards.append(
            dbc.Card([
                dbc.CardBody([
                    html.H5(mention.title, className="card-title"),
                    html.P(f"{mention.source} • {mention.published_at.strftime('%Y-%m-%d') if mention.published_at else 'Unknown date'}", className="text-muted small"),
                    html.A("Read article", href=mention.url, target="_blank")
                ])
            ], className=f"mb-3 border-{border_color}")
        )
    
    # Create filter controls for the mentions table
    filter_controls = dbc.Row([
        dbc.Col([
            html.Label("Sentiment"),
            dcc.Dropdown(
                id="sentiment-filter",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Positive", "value": "POSITIVE"},
                    {"label": "Neutral", "value": "NEUTRAL"},
                    {"label": "Negative", "value": "NEGATIVE"}
                ],
                value="all",
                clearable=False
            )
        ], md=3),
        dbc.Col([
            html.Label("Time Period"),
            dcc.Dropdown(
                id="time-filter",
                options=[
                    {"label": "All Time", "value": "all"},
                    {"label": "Last 7 days", "value": "7"},
                    {"label": "Last 30 days", "value": "30"},
                    {"label": "Last 90 days", "value": "90"}
                ],
                value="all",
                clearable=False
            )
        ], md=3),
        dbc.Col([
            html.Label("Date Range"),
            dcc.DatePickerRange(
                id="date-range-filter",
                min_date_allowed=datetime(2000, 1, 1),
                max_date_allowed=datetime.now(),
                initial_visible_month=datetime.now(),
                end_date=datetime.now(),
                start_date=datetime.now() - timedelta(days=30),
                display_format="YYYY-MM-DD"
            )
        ], md=6)
    ], className="mb-3")
    
    # Prepare the mentions table
    mentions_table = html.Div(id="filtered-mentions-table")
    
    # Store the company ID for use in other callbacks
    store = dcc.Store(id="current-company-id", data=company_id)
    
    return html.Div([
        store,
        html.H2(company.name),
        aliases_display,
        html.Hr(),
        
        dbc.Row([
            # Left column - Sentiment Overview
            dbc.Col([
                html.H4("Sentiment Overview"),
                metrics_row,
                html.Div(
                    dcc.Graph(
                        figure=sentiment_fig, 
                        style={'height': '450px'}, 
                        config={'displayModeBar': False}  # Hide the mode bar for cleaner look
                    ) if sentiment_fig else html.P("No mentions found for this company."),
                    style={'height': '500px'}  # Containing div height
                )
            ], md=7),
            
            # Right column - Recent Mentions
            dbc.Col([
                html.H4("Recent Mentions"),
                html.Div(
                    recent_mentions_cards if recent_mentions_cards else html.P("No mentions available."),
                    style={'maxHeight': '500px', 'overflowY': 'auto'}  # Matching height with scrollable container
                )
            ], md=5)
        ], className="mb-4"),  # Add margin below
        
        # New row for sentiment timeline
        dbc.Row([
            dbc.Col([
                html.H4("Sentiment Timeline"),
                dcc.Graph(
                    id="sentiment-timeline-chart",
                    config={'displayModeBar': False}
                )
            ], className="mb-4")
        ]),
        
        html.Hr(),
        html.H4("All Mentions"),
        filter_controls,
        mentions_table
    ])

# Callback to update the sentiment timeline chart based on date range
@callback(
    Output("sentiment-timeline-chart", "figure"),
    Input("current-company-id", "data"),
    Input("date-range-filter", "start_date"),
    Input("date-range-filter", "end_date")
)
def update_sentiment_timeline(company_id, start_date, end_date):
    if not company_id:
        return px.line(title="No company selected")
    
    # Convert string dates to datetime objects if they exist
    start_date_obj = None
    end_date_obj = None
    
    if start_date and end_date:
        start_date_obj = datetime.strptime(start_date.split('T')[0], '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date.split('T')[0], '%Y-%m-%d') + timedelta(days=1)  # Include the end date
    
    # Create the timeline with date filters
    return create_sentiment_timeline(company_id, start_date_obj, end_date_obj)

# Callback to handle filtering the mentions table
@callback(
    Output("filtered-mentions-table", "children"),
    Input("current-company-id", "data"),
    Input("sentiment-filter", "value"),
    Input("time-filter", "value"),
    Input("date-range-filter", "start_date"),
    Input("date-range-filter", "end_date")
)
def update_mentions_table(company_id, sentiment, time_period, start_date, end_date):
    if not company_id:
        return html.P("No company selected.")
    
    # Get all mentions for the company
    mentions = db.get_mentions(company_id)
    
    # Apply sentiment filter
    if sentiment != "all":
        mentions = [m for m in mentions if m.sentiment == sentiment]
    
    # Apply time filter (dropdown) or date range filter
    if time_period != "all":
        days = int(time_period)
        cutoff_date = datetime.now() - timedelta(days=days)
        mentions = [m for m in mentions if m.published_at and m.published_at >= cutoff_date]
    elif start_date and end_date:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date.split('T')[0], '%Y-%m-%d')
        end_date = datetime.strptime(end_date.split('T')[0], '%Y-%m-%d') + timedelta(days=1)  # Include the end date
        mentions = [m for m in mentions if m.published_at and start_date <= m.published_at < end_date]
    
    if not mentions:
        return html.P("No mentions match the selected filters.")
    
    # Convert to DataFrame for the table
    table_data = []
    for mention in mentions:
        table_data.append({
            "Date": mention.published_at.strftime('%Y-%m-%d') if mention.published_at else "Unknown",
            "Title": mention.title,
            "Source": mention.source,
            "Sentiment": mention.sentiment.capitalize(),
            "Score": f"{mention.sentiment_score:.2f}" if mention.sentiment_score is not None else "N/A",
            "URL": mention.url
        })
    
    df = pd.DataFrame(table_data)
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Date", "id": "Date"},
            {"name": "Title", "id": "Title"},
            {"name": "Source", "id": "Source"},
            {"name": "Sentiment", "id": "Sentiment"},
            {"name": "Score", "id": "Score"},
            {"name": "URL", "id": "URL", "presentation": "markdown"}
        ],
        style_cell={
            'textAlign': 'left',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0,
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{Sentiment} = "Positive"'},
                'backgroundColor': 'rgba(40, 167, 69, 0.1)'
            },
            {
                'if': {'filter_query': '{Sentiment} = "Negative"'},
                'backgroundColor': 'rgba(220, 53, 69, 0.1)'
            }
        ],
        page_size=10,
        sort_action="native",
        filter_action="native",
        style_table={'overflowX': 'auto'},
        markdown_options={"html": True},
        cell_selectable=False
    )

# Callback to handle the update mentions button
@callback(
    Output("update-status", "children"),
    Input("update-mentions-btn", "n_clicks"),
    State("company-select", "value"),
    prevent_initial_call=True
)
def update_mentions(n_clicks, company_id):
    if not company_id:
        return dbc.Alert("Please select a company first.", color="warning")
    
    try:
        result = process_company(company_id)
        if result and result.get("status") == "success":
            mentions_added = result.get("mentions_added", 0)
            return dbc.Alert(f"✅ Added {mentions_added} new mentions!", color="success")
        else:
            error_msg = result.get("message", "Unknown error")
            return dbc.Alert(f"Error: {error_msg}", color="danger")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

# Callback to handle adding a new company
@callback(
    [Output("add-company-status", "children"),
     Output("company-select", "options"),
     Output("company-name-input", "value"),
     Output("company-aliases-input", "value")],
    Input("add-company-btn", "n_clicks"),
    [State("company-name-input", "value"),
     State("company-aliases-input", "value")],
    prevent_initial_call=True
)
def add_company(n_clicks, name, aliases):
    if not name:
        return dbc.Alert("Please enter a company name.", color="warning"), get_company_options(), None, None
    
    aliases_list = [alias.strip() for alias in aliases.split(",")] if aliases else []
    
    try:
        company_id = add_new_company(name, aliases_list)
        if company_id:
            return dbc.Alert(f"Added company: {name}", color="success"), get_company_options(), "", ""
        else:
            return dbc.Alert("Failed to add company. Please try again.", color="danger"), get_company_options(), name, aliases
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger"), get_company_options(), name, aliases

# Run the server
if __name__ == "__main__":
    app.run(debug=True, port=8050)