"""Dash application for visualizing home data on a map."""

from typing import Any

import dash
import dash_leaflet as dl
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, dash_table, dcc, html
from plotly.subplots import make_subplots

from .cost_analysis import DEFAULTS, CostAnalysisParams, run_analysis
from .database import get_all_homes, get_home_by_id, init_db


def create_app() -> dash.Dash:
    """Create and configure the Dash application."""
    app = dash.Dash(
        __name__,
        title="Vibe House Shopping",
        suppress_callback_exceptions=True,
    )

    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-content"),
            # Hidden div for storing data
            dcc.Store(id="homes-data", data=get_all_homes()),
            # Interval for auto-refresh (every 30 seconds)
            dcc.Interval(id="auto-refresh", interval=30000, n_intervals=0),
        ],
        className="app-container",
    )

    # Add CSS styles
    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }
                body {
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #f5f5f5;
                    color: #333;
                }
                .app-container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 12px;
                    color: white;
                }
                .header-title {
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                }
                .header-subtitle {
                    font-size: 1.1rem;
                    opacity: 0.9;
                }
                .controls {
                    display: flex;
                    align-items: center;
                    gap: 20px;
                    margin-bottom: 20px;
                }
                .refresh-button {
                    background-color: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    font-size: 1rem;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                .refresh-button:hover {
                    background-color: #5a6fd6;
                }
                .home-count {
                    font-size: 1.1rem;
                    color: #666;
                }
                .main-content {
                    display: flex;
                    flex-direction: column;
                    gap: 30px;
                }
                .map-container, .table-container {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .map-container h2, .table-container h2 {
                    margin-bottom: 15px;
                    color: #333;
                }
                .leaflet-popup-content {
                    font-family: system-ui, -apple-system, sans-serif;
                }
                .popup-content {
                    line-height: 1.6;
                }
                .popup-content strong {
                    color: #667eea;
                }
                .popup-price {
                    font-size: 1.2rem;
                    font-weight: bold;
                    color: #2d3748;
                    margin-bottom: 8px;
                }
                .popup-address {
                    font-weight: 600;
                    margin-bottom: 8px;
                }
                .popup-details {
                    color: #666;
                    font-size: 0.9rem;
                }
                .home-link {
                    color: #667eea;
                    text-decoration: none;
                    cursor: pointer;
                }
                .home-link:hover {
                    text-decoration: underline;
                }
                .back-link {
                    display: inline-block;
                    margin-bottom: 20px;
                    color: #667eea;
                    text-decoration: none;
                    font-size: 1rem;
                }
                .back-link:hover {
                    text-decoration: underline;
                }
                .detail-container {
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .detail-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 30px;
                    flex-wrap: wrap;
                    gap: 20px;
                }
                .detail-title {
                    font-size: 1.8rem;
                    color: #333;
                    margin-bottom: 8px;
                }
                .detail-location {
                    font-size: 1.1rem;
                    color: #666;
                }
                .detail-price {
                    font-size: 2.2rem;
                    font-weight: bold;
                    color: #667eea;
                }
                .detail-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .detail-item {
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                .detail-label {
                    font-size: 0.85rem;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 5px;
                }
                .detail-value {
                    font-size: 1.2rem;
                    font-weight: 600;
                    color: #333;
                }
                .detail-section {
                    margin-bottom: 30px;
                }
                .detail-section h3 {
                    font-size: 1.2rem;
                    color: #333;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #eee;
                }
                .detail-description {
                    line-height: 1.7;
                    color: #444;
                    white-space: pre-wrap;
                }
                .detail-map {
                    height: 300px;
                    border-radius: 8px;
                    margin-top: 15px;
                }
                .detail-meta {
                    font-size: 0.9rem;
                    color: #888;
                }
                .detail-meta a {
                    color: #667eea;
                    text-decoration: none;
                }
                .detail-meta a:hover {
                    text-decoration: underline;
                }
                .not-found {
                    text-align: center;
                    padding: 60px 20px;
                }
                .not-found h2 {
                    font-size: 1.5rem;
                    color: #666;
                    margin-bottom: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 12px 10px;
                    text-align: left;
                    border-bottom: 1px solid #eee;
                }
                th {
                    background-color: #f8f9fa;
                    font-weight: 600;
                    color: #333;
                    border-bottom: 2px solid #dee2e6;
                }
                tr:hover {
                    background-color: #f8f9fa;
                }
                tbody tr:nth-child(odd) {
                    background-color: #fafafa;
                }
                tbody tr:nth-child(odd):hover {
                    background-color: #f0f0f0;
                }
                /* Navigation styles */
                .nav-bar {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 20px;
                    padding: 15px 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }
                .nav-link {
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                    padding: 8px 16px;
                    border-radius: 6px;
                    transition: background-color 0.2s;
                }
                .nav-link:hover {
                    background-color: #f0f0ff;
                }
                .nav-link.active {
                    background-color: #667eea;
                    color: white;
                }
                /* Cost Analysis Page Styles */
                .analysis-container {
                    display: grid;
                    grid-template-columns: 350px 1fr;
                    gap: 20px;
                }
                .analysis-sidebar {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    height: fit-content;
                    position: sticky;
                    top: 20px;
                }
                .analysis-main {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    min-width: 0;
                    overflow: hidden;
                }
                .param-group {
                    margin-bottom: 20px;
                }
                .param-group h4 {
                    margin-bottom: 10px;
                    color: #333;
                    font-size: 0.95rem;
                }
                .param-input {
                    display: flex;
                    flex-direction: column;
                    margin-bottom: 12px;
                }
                .param-input label {
                    font-size: 0.85rem;
                    color: #666;
                    margin-bottom: 4px;
                }
                .param-input input, .param-input select {
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    font-size: 0.95rem;
                }
                .param-input input:focus, .param-input select:focus {
                    outline: none;
                    border-color: #667eea;
                }
                .home-checkbox-list {
                    max-height: 200px;
                    overflow-y: auto;
                    border: 1px solid #eee;
                    border-radius: 6px;
                    padding: 10px;
                }
                .home-checkbox-item {
                    display: flex;
                    align-items: center;
                    padding: 8px 0;
                    border-bottom: 1px solid #f0f0f0;
                }
                .home-checkbox-item:last-child {
                    border-bottom: none;
                }
                .home-checkbox-item input {
                    margin-right: 10px;
                }
                .home-checkbox-item label {
                    font-size: 0.9rem;
                    cursor: pointer;
                }
                .chart-tabs {
                    display: flex;
                    gap: 5px;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 0;
                }
                .chart-tab {
                    padding: 10px 20px;
                    border: none;
                    background: none;
                    cursor: pointer;
                    font-size: 0.95rem;
                    color: #666;
                    border-bottom: 2px solid transparent;
                    margin-bottom: -2px;
                    transition: all 0.2s;
                }
                .chart-tab:hover {
                    color: #667eea;
                }
                .chart-tab.active {
                    color: #667eea;
                    border-bottom-color: #667eea;
                    font-weight: 500;
                }
                .slider-container {
                    margin-top: 10px;
                }
                .slider-value {
                    text-align: center;
                    font-weight: 500;
                    color: #667eea;
                    margin-top: 5px;
                }
                .summary-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }
                .summary-card {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                }
                .summary-card .card-title {
                    font-weight: 600;
                    margin-bottom: 10px;
                    font-size: 0.85rem;
                }
                .summary-card table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .summary-card td {
                    padding: 4px 0;
                    border: none;
                }
                .summary-card td.label {
                    font-size: 0.8rem;
                    color: #666;
                    text-transform: uppercase;
                    text-align: left;
                }
                .summary-card td.value {
                    font-size: 1rem;
                    font-weight: 600;
                    color: #333;
                    text-align: right;
                }
                .no-homes-message {
                    padding: 40px;
                    text-align: center;
                    color: #666;
                }
                /* Data table styles */
                .data-table-container {
                    margin-top: 30px;
                    overflow-x: auto;
                }
                .data-table-container h3 {
                    margin-bottom: 15px;
                    color: #333;
                    font-size: 1.1rem;
                }
                .data-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.85rem;
                }
                .data-table th, .data-table td {
                    padding: 8px 12px;
                    text-align: right;
                    border: 1px solid #e0e0e0;
                    white-space: nowrap;
                }
                .data-table th {
                    background-color: #f8f9fa;
                    font-weight: 600;
                    color: #333;
                    position: sticky;
                    top: 0;
                }
                .data-table th:first-child, .data-table td:first-child {
                    text-align: left;
                    position: sticky;
                    left: 0;
                    background-color: #f8f9fa;
                    z-index: 1;
                }
                .data-table tbody tr:nth-child(odd) {
                    background-color: #fafafa;
                }
                .data-table tbody tr:nth-child(odd) td:first-child {
                    background-color: #fafafa;
                }
                .data-table tbody tr:hover {
                    background-color: #f0f0f0;
                }
                .data-table tbody tr:hover td:first-child {
                    background-color: #f0f0f0;
                }
                .data-table tfoot td {
                    font-weight: 600;
                    background-color: #e8e8e8;
                    border-top: 2px solid #ccc;
                }
                .data-table tfoot td:first-child {
                    background-color: #e8e8e8;
                }
                @media (max-width: 900px) {
                    .analysis-container {
                        grid-template-columns: 1fr;
                    }
                    .analysis-sidebar {
                        position: static;
                    }
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """

    # Register callbacks
    register_callbacks(app)

    return app


def create_nav_bar(active_page: str = "homes") -> html.Div:
    """Create the navigation bar."""
    return html.Div([
        html.A("Home Listings", href="/", className=f"nav-link {'active' if active_page == 'homes' else ''}"),
        html.A("Cost Analysis", href="/analysis", className=f"nav-link {'active' if active_page == 'analysis' else ''}"),
    ], className="nav-bar")


def create_home_list_layout() -> html.Div:
    """Create the main home listing layout."""
    return html.Div([
        # Navigation
        create_nav_bar("homes"),
        # Header
        html.Div(
            [
                html.H1("Vibe House Shopping", className="header-title"),
                html.P(
                    "Drop HTML files into the import/ directory to add homes",
                    className="header-subtitle",
                ),
            ],
            className="header",
        ),
        # Refresh button and stats
        html.Div(
            [
                html.Button(
                    "Refresh Data",
                    id="refresh-button",
                    className="refresh-button",
                ),
                html.Span(id="home-count", className="home-count"),
            ],
            className="controls",
        ),
        # Main content area
        html.Div(
            [
                # Map
                html.Div(
                    [
                        html.H2("Map View"),
                        dl.Map(
                            id="home-map",
                            center=[39.8283, -98.5795],  # Center of US
                            zoom=4,
                            children=[
                                dl.TileLayer(),
                                dl.LayerGroup(id="marker-layer"),
                            ],
                            style={
                                "width": "100%",
                                "height": "500px",
                                "borderRadius": "8px",
                            },
                        ),
                    ],
                    className="map-container",
                ),
                # Data table
                html.Div(
                    [
                        html.H2("All Homes"),
                        html.Div(id="homes-list"),
                    ],
                    className="table-container",
                ),
            ],
            className="main-content",
        ),
    ])


def create_home_detail_layout(home_id: int) -> html.Div:
    """Create the detail view layout for a single home."""
    home = get_home_by_id(home_id)

    if not home:
        return html.Div([
            html.A("← Back to all homes", href="/", className="back-link"),
            html.Div([
                html.H2("Home not found"),
                html.P("The home you're looking for doesn't exist or has been removed."),
            ], className="not-found"),
        ])

    # Format values
    price_str = f"${home['price']:,.0f}" if home.get("price") else "Price not available"
    beds = str(home.get("bedrooms") or "—")
    baths = str(home.get("bathrooms") or "—")
    sqft = f"{home['sqft']:,}" if home.get("sqft") else "—"
    lot_size = f"{home['lot_size']:.2f} acres" if home.get("lot_size") else "—"
    year_built = str(home.get("year_built") or "—")
    prop_type = home.get("property_type") or "—"
    num_rooms = str(home.get("num_rooms") or "—")
    garage = str(home.get("garage_spaces") or "—")
    mls_id = home.get("mls_id") or "—"

    location_parts = [p for p in [home.get("city"), home.get("state"), home.get("zip_code")] if p]
    location_str = ", ".join(location_parts) if location_parts else ""

    # Build the detail grid items
    detail_items = [
        ("Bedrooms", beds),
        ("Bathrooms", baths),
        ("Total Rooms", num_rooms),
        ("Square Feet", sqft),
        ("Garage Spaces", garage),
        ("Lot Size", lot_size),
        ("Year Built", year_built),
        ("Property Type", prop_type),
        ("MLS #", mls_id),
    ]

    detail_grid = html.Div([
        html.Div([
            html.Div(label, className="detail-label"),
            html.Div(value, className="detail-value"),
        ], className="detail-item")
        for label, value in detail_items
    ], className="detail-grid")

    # Build sections
    sections = []

    # Image section
    if home.get("image_url"):
        sections.append(html.Div([
            html.Img(
                src=home["image_url"],
                style={
                    "width": "100%",
                    "maxHeight": "400px",
                    "objectFit": "cover",
                    "borderRadius": "8px",
                },
            ),
        ], className="detail-section"))

    # Video link section
    if home.get("video_url"):
        sections.append(html.Div([
            html.H3("Virtual Tour"),
            html.A(
                "View Video Tour",
                href=home["video_url"],
                target="_blank",
                className="home-link",
                style={"fontSize": "1.1rem"},
            ),
        ], className="detail-section"))

    # Description section
    if home.get("description"):
        sections.append(html.Div([
            html.H3("Description"),
            html.P(home["description"], className="detail-description"),
        ], className="detail-section"))

    # Map section
    if home.get("latitude") and home.get("longitude"):
        sections.append(html.Div([
            html.H3("Location"),
            dl.Map(
                center=[home["latitude"], home["longitude"]],
                zoom=15,
                children=[
                    dl.TileLayer(),
                    dl.Marker(position=[home["latitude"], home["longitude"]]),
                ],
                style={"width": "100%", "height": "300px", "borderRadius": "8px"},
            ),
        ], className="detail-section"))

    # Meta section
    meta_items = []
    if home.get("source_url"):
        meta_items.append(html.Span([
            "Source: ",
            html.A(home["source_url"], href=home["source_url"], target="_blank"),
        ]))
    if home.get("source_file"):
        meta_items.append(html.Span(f"Imported from: {home['source_file']}"))
    if home.get("imported_at"):
        meta_items.append(html.Span(f"Added: {home['imported_at'][:10]}"))

    if meta_items:
        sections.append(html.Div([
            html.H3("Source Information"),
            html.Div([
                html.Div(item) for item in meta_items
            ], className="detail-meta"),
        ], className="detail-section"))

    return html.Div([
        html.A("← Back to all homes", href="/", className="back-link"),
        html.Div([
            # Header with address and price
            html.Div([
                html.Div([
                    html.H1(home.get("address") or "Address not available", className="detail-title"),
                    html.P(location_str, className="detail-location") if location_str else None,
                ]),
                html.Div(price_str, className="detail-price"),
            ], className="detail-header"),

            # Key details grid
            detail_grid,

            # Additional sections
            *sections,
        ], className="detail-container"),
    ])


def create_cost_analysis_layout() -> html.Div:
    """Create the cost analysis page layout."""
    homes = get_all_homes()

    # Filter to homes with prices (required for analysis)
    homes_with_prices = [h for h in homes if h.get("price")]

    if not homes_with_prices:
        return html.Div([
            create_nav_bar("analysis"),
            html.Div(
                [
                    html.H1("Vibe House Shopping", className="header-title"),
                    html.P("Cost Analysis", className="header-subtitle"),
                ],
                className="header",
            ),
            html.Div([
                html.H3("No homes available for analysis"),
                html.P("Import some home listings with prices to use the cost analysis feature."),
            ], className="no-homes-message"),
        ])

    # Create home checkboxes with clickable links
    home_checkboxes = []
    for home in homes_with_prices:
        price_str = f"${home['price']:,.0f}" if home.get("price") else ""
        address = home.get('address', 'Unknown')[:40]
        home_checkboxes.append(
            html.Div([
                dcc.Checklist(
                    id={"type": "home-checkbox", "index": home["id"]},
                    options=[{"label": "", "value": home["id"]}],
                    value=[],
                    style={"display": "inline-block", "verticalAlign": "middle"},
                ),
                html.A(
                    f"{address} - {price_str}",
                    href=f"/home/{home['id']}",
                    className="home-link",
                    style={"marginLeft": "4px", "verticalAlign": "middle"},
                ),
            ], className="home-checkbox-item")
        )

    return html.Div([
        # Navigation
        create_nav_bar("analysis"),
        # Header
        html.Div(
            [
                html.H1("Vibe House Shopping", className="header-title"),
                html.P("Cost Analysis", className="header-subtitle"),
            ],
            className="header",
        ),
        # Main content
        html.Div([
            # Sidebar with controls
            html.Div([
                # Home selection
                html.Div([
                    html.H4("Select Homes to Compare"),
                    html.Div(home_checkboxes, className="home-checkbox-list"),
                ], className="param-group"),

                # Time horizon slider
                html.Div([
                    html.H4("Time Horizon"),
                    html.Div([
                        dcc.Slider(
                            id="years-slider",
                            min=5,
                            max=30,
                            step=1,
                            value=30,
                            marks={5: "5", 10: "10", 15: "15", 20: "20", 25: "25", 30: "30"},
                        ),
                        html.Div(id="years-display", className="slider-value"),
                    ], className="slider-container"),
                ], className="param-group"),

                # Financial parameters
                html.Div([
                    html.H4("Loan Parameters"),
                    html.Div([
                        html.Label("Down Payment (%)"),
                        dcc.Input(
                            id="down-payment-input",
                            type="number",
                            value=DEFAULTS["down_payment_pct"] * 100,
                            min=0,
                            max=100,
                            step=1,
                        ),
                    ], className="param-input"),
                    html.Div([
                        html.Label("Interest Rate (%)"),
                        dcc.Input(
                            id="interest-rate-input",
                            type="number",
                            value=DEFAULTS["interest_rate"] * 100,
                            min=0,
                            max=20,
                            step=0.01,
                        ),
                    ], className="param-input"),
                    html.Div([
                        html.Label("Loan Term (years)"),
                        dcc.Input(
                            id="loan-term-input",
                            type="number",
                            value=DEFAULTS["loan_term_years"],
                            min=5,
                            max=30,
                            step=1,
                        ),
                    ], className="param-input"),
                    html.Div([
                        html.Label("Purchase Fees ($)"),
                        dcc.Input(
                            id="purchase-fees-input",
                            type="number",
                            value=DEFAULTS["purchase_fees"],
                            min=0,
                            step=1000,
                        ),
                    ], className="param-input"),
                ], className="param-group"),

                html.Div([
                    html.H4("Growth & Costs"),
                    html.Div([
                        html.Label("Annual Appreciation (%)"),
                        dcc.Input(
                            id="growth-rate-input",
                            type="number",
                            value=DEFAULTS["annual_growth_rate"] * 100,
                            min=-10,
                            max=20,
                            step=0.1,
                        ),
                    ], className="param-input"),
                    html.Div([
                        html.Label("Monthly Repair Est. (% of value)"),
                        dcc.Input(
                            id="repair-pct-input",
                            type="number",
                            value=DEFAULTS["monthly_repair_pct"] * 100,
                            min=0,
                            max=1,
                            step=0.001,
                        ),
                    ], className="param-input"),
                    html.Div([
                        html.Label("Maintenance Inflation (%)"),
                        dcc.Input(
                            id="maint-inflation-input",
                            type="number",
                            value=DEFAULTS["maintenance_inflation"] * 100,
                            min=0,
                            max=10,
                            step=0.1,
                        ),
                    ], className="param-input"),
                ], className="param-group"),

            ], className="analysis-sidebar"),

            # Main chart area
            html.Div([
                # Chart type tabs
                html.Div([
                    html.Button("Home Value", id="tab-value", className="chart-tab active", n_clicks=0),
                    html.Button("Equity", id="tab-equity", className="chart-tab", n_clicks=0),
                    html.Button("Cash Invested", id="tab-cash", className="chart-tab", n_clicks=0),
                    html.Button("Annual Costs", id="tab-costs", className="chart-tab", n_clicks=0),
                    html.Button("ROI", id="tab-roi", className="chart-tab", n_clicks=0),
                ], className="chart-tabs"),

                # Store for active tab
                dcc.Store(id="active-chart-tab", data="value"),

                # Summary cards
                html.Div(id="summary-cards", className="summary-cards"),

                # Chart
                dcc.Graph(
                    id="analysis-chart",
                    config={"displayModeBar": True, "responsive": True},
                    style={"height": "500px"},
                ),

                # Data table below chart
                html.Div(id="analysis-data-table", className="data-table-container"),

            ], className="analysis-main"),
        ], className="analysis-container"),
    ])


def generate_data_table(active_tab: str, all_results: dict[str, Any], years: int) -> html.Div | list[Any]:
    """Generate a data table for the analysis results based on the active tab.

    Args:
        active_tab: The currently active chart tab (value, equity, cash, costs, roi)
        all_results: Dictionary of analysis results keyed by home label
        years: Number of years in the analysis

    Returns:
        HTML table element showing the data
    """
    if not all_results:
        return []

    # Get the first home's results to determine the number of years
    first_results = list(all_results.values())[0]["results"]

    if active_tab == "costs":
        # For Annual Costs tab, show breakdown of cost components
        return generate_costs_table(all_results, years)
    elif active_tab == "value":
        return generate_simple_table(
            all_results, "home_value", "Home Value by Year", is_currency=True
        )
    elif active_tab == "equity":
        return generate_simple_table(
            all_results, "equity", "Equity by Year", is_currency=True
        )
    elif active_tab == "cash":
        return generate_simple_table(
            all_results, "total_cash_invested", "Total Cash Invested by Year", is_currency=True
        )
    elif active_tab == "roi":
        return generate_simple_table(
            all_results, "roi", "ROI by Year", is_currency=False, is_ratio=True
        )

    return []


def generate_simple_table(
    all_results: dict[str, Any],
    field: str,
    title: str,
    is_currency: bool = True,
    is_ratio: bool = False,
) -> html.Div | list[Any]:
    """Generate a simple table with years as columns and homes as rows."""
    if not all_results:
        return []

    # Get all years from the first result
    first_results = list(all_results.values())[0]["results"]
    all_years = [r.year for r in first_results]

    # Build header row
    header_cells = [html.Th("Home")] + [html.Th(f"Year {yr}") for yr in all_years]

    # Build data rows
    rows = []
    for label, data in all_results.items():
        results = data["results"]
        cells = [html.Td(label[:30])]

        for r in results:
            if field == "roi":
                val = r.roi if r.roi else 0
                cell_text = f"{val:.2f}x" if val else "—"
            else:
                val = getattr(r, field)
                if is_currency:
                    cell_text = f"${val:,.0f}"
                elif is_ratio:
                    cell_text = f"{val:.2f}x" if val else "—"
                else:
                    cell_text = f"{val:,.0f}"
            cells.append(html.Td(cell_text))

        rows.append(html.Tr(cells))

    return html.Div([
        html.H3(title),
        html.Table([
            html.Thead(html.Tr(header_cells)),
            html.Tbody(rows),
        ], className="data-table"),
    ])


def generate_costs_table(all_results: dict[str, Any], years: int) -> html.Div | list[Any]:
    """Generate a detailed costs table showing breakdown of annual costs.

    For the Annual Costs tab, we show:
    - Year 0: Purchase fees (closing costs)
    - Year 1+: Property taxes, repairs, maintenance, mortgage payment, and total
    """
    if not all_results:
        return []

    tables = []

    for label, data in all_results.items():
        results = data["results"]
        home = data["home"]
        color = data["color"]

        # Get first result for initial investment info
        first = results[0]

        # Build header - Year as a column
        header_cells = [
            html.Th("Year"),
            html.Th("Property Taxes"),
            html.Th("Repairs"),
            html.Th("Maintenance (HOA)"),
            html.Th("Mortgage Payment"),
            html.Th("Total Annual Cost"),
        ]

        # Build rows for each year
        rows = []

        # Year 0 row - shows closing fees
        yr0 = results[0]
        rows.append(html.Tr([
            html.Td("0 (Purchase)"),
            html.Td("—"),
            html.Td("—"),
            html.Td("—"),
            html.Td("—"),
            html.Td(f"${yr0.total_cash_invested:,.0f}", style={"fontWeight": "600"}),
        ]))

        # Cumulative totals for footer
        total_taxes = 0
        total_repairs = 0
        total_maintenance = 0
        total_mortgage = 0
        total_all = yr0.total_cash_invested  # Start with initial investment

        for r in results[1:]:
            total_taxes += r.annual_taxes
            total_repairs += r.annual_repair
            total_maintenance += r.annual_maintenance
            total_mortgage += r.annual_mortgage_payment

            year_total = (
                r.annual_taxes
                + r.annual_repair
                + r.annual_maintenance
                + r.annual_mortgage_payment
            )
            total_all += year_total

            rows.append(html.Tr([
                html.Td(str(r.year)),
                html.Td(f"${r.annual_taxes:,.0f}"),
                html.Td(f"${r.annual_repair:,.0f}"),
                html.Td(f"${r.annual_maintenance:,.0f}"),
                html.Td(f"${r.annual_mortgage_payment:,.0f}"),
                html.Td(f"${year_total:,.0f}", style={"fontWeight": "600"}),
            ]))

        # Footer with totals
        footer_row = html.Tr([
            html.Td("Total"),
            html.Td(f"${total_taxes:,.0f}"),
            html.Td(f"${total_repairs:,.0f}"),
            html.Td(f"${total_maintenance:,.0f}"),
            html.Td(f"${total_mortgage:,.0f}"),
            html.Td(f"${total_all:,.0f}"),
        ])

        tables.append(html.Div([
            html.H3(label, style={"color": color}),
            html.Table([
                html.Thead(html.Tr(header_cells)),
                html.Tbody(rows),
                html.Tfoot([footer_row]),
            ], className="data-table"),
        ], style={"marginBottom": "30px"}))

    return html.Div([
        html.H3("Annual Cost Breakdown"),
        *tables,
    ])


def register_callbacks(app: dash.Dash) -> None:
    """Register all Dash callbacks."""

    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
    )
    def display_page(pathname: str | None) -> html.Div:
        """Route to the appropriate page based on URL."""
        if pathname == "/analysis":
            return create_cost_analysis_layout()
        if pathname and pathname.startswith("/home/"):
            try:
                home_id = int(pathname.split("/")[-1])
                return create_home_detail_layout(home_id)
            except (ValueError, IndexError):
                pass
        return create_home_list_layout()

    @app.callback(
        Output("homes-data", "data"),
        Input("auto-refresh", "n_intervals"),
    )
    def refresh_data(n_intervals: int) -> list[dict[str, Any]]:
        """Refresh home data from the database."""
        return get_all_homes()

    @app.callback(
        Output("homes-data", "data", allow_duplicate=True),
        Input("refresh-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def refresh_data_button(n_clicks: int | None) -> list[dict[str, Any]]:
        """Refresh home data when button is clicked."""
        return get_all_homes()

    @app.callback(
        Output("homes-list", "children"),
        Input("homes-data", "data"),
    )
    def update_homes_list(homes_data: list[dict[str, Any]] | None) -> html.Table | html.P:
        """Update the homes list with clickable entries."""
        if not homes_data:
            return html.P("No homes in database. Drop HTML files into the import/ directory to add homes.")

        # Create table with clickable rows
        header = html.Tr([
            html.Th("Address"),
            html.Th("City"),
            html.Th("State/Prov"),
            html.Th("Price"),
            html.Th("Beds"),
            html.Th("Baths"),
            html.Th("Sq Ft"),
            html.Th("Rooms"),
            html.Th("Garage"),
            html.Th("Year Built"),
            html.Th("Type"),
            html.Th("MLS #"),
        ])

        rows = []
        for home in homes_data:
            price_str = f"${home['price']:,.0f}" if home.get("price") else "—"
            sqft_str = f"{home['sqft']:,}" if home.get("sqft") else "—"

            row = html.Tr([
                html.Td(html.A(
                    home.get("address") or "—",
                    href=f"/home/{home['id']}",
                    className="home-link",
                )),
                html.Td(home.get("city") or "—"),
                html.Td(home.get("state") or "—"),
                html.Td(price_str),
                html.Td(home.get("bedrooms") or "—"),
                html.Td(home.get("bathrooms") or "—"),
                html.Td(sqft_str),
                html.Td(home.get("num_rooms") or "—"),
                html.Td(home.get("garage_spaces") or "—"),
                html.Td(home.get("year_built") or "—"),
                html.Td(home.get("property_type") or "—"),
                html.Td(home.get("mls_id") or "—"),
            ])
            rows.append(row)

        return html.Table(
            [html.Thead(header), html.Tbody(rows)],
            style={
                "width": "100%",
                "borderCollapse": "collapse",
                "fontSize": "0.95rem",
            },
        )

    @app.callback(
        Output("marker-layer", "children"),
        Input("homes-data", "data"),
    )
    def update_map_markers(homes_data: list[dict[str, Any]] | None) -> list[dl.Marker]:
        """Update map markers based on home data."""
        if not homes_data:
            return []

        markers = []
        for home in homes_data:
            if home.get("latitude") and home.get("longitude"):
                # Create popup content
                price_str = f"${home['price']:,.0f}" if home.get("price") else "Price N/A"
                beds = home.get("bedrooms") or "?"
                baths = home.get("bathrooms") or "?"
                sqft = f"{home['sqft']:,}" if home.get("sqft") else "?"
                garage = home.get("garage_spaces") or 0
                mls_id = home.get("mls_id") or ""

                # Build image HTML if available
                image_html = ""
                if home.get("image_url"):
                    image_html = f'<img src="{home["image_url"]}" style="width:100%;max-height:120px;object-fit:cover;border-radius:4px;margin-bottom:8px;" onerror="this.style.display=\'none\'"/>'

                # Build MLS line if available
                mls_html = f"<br/>MLS: {mls_id}" if mls_id else ""

                popup_html = f"""
                <div class="popup-content">
                    {image_html}
                    <div class="popup-price">{price_str}</div>
                    <div class="popup-address">
                        <a href="/home/{home['id']}" class="home-link">{home.get('address', 'Address N/A')}</a>
                    </div>
                    <div class="popup-details">
                        {beds} bed | {baths} bath | {sqft} sqft{f' | {garage} garage' if garage else ''}<br/>
                        {home.get('property_type', '')}{mls_html}
                    </div>
                </div>
                """

                marker = dl.Marker(
                    position=[home["latitude"], home["longitude"]],
                    children=[
                        dl.Tooltip(home.get("address", "Unknown")),
                        dl.Popup(html.Div(dash.dcc.Markdown(popup_html, dangerously_allow_html=True))),
                    ],
                )
                markers.append(marker)

        return markers

    @app.callback(
        Output("home-count", "children"),
        Input("homes-data", "data"),
    )
    def update_home_count(homes_data: list[dict[str, Any]] | None) -> str:
        """Update the home count display."""
        count = len(homes_data) if homes_data else 0
        return f"{count} home{'s' if count != 1 else ''} in database"

    @app.callback(
        Output("home-map", "viewport"),
        Input("homes-data", "data"),
    )
    def update_map_view(homes_data: list[dict[str, Any]] | None) -> dict[str, Any]:
        """Update map viewport based on home locations.

        Note: We use the 'viewport' property instead of 'center'/'zoom' because
        dash-leaflet's center and zoom props are immutable after initial render.
        The viewport property allows dynamic updates after the map is mounted.
        """
        if not homes_data:
            return dict(center=[39.8283, -98.5795], zoom=4, transition="flyTo")

        # Get homes with coordinates
        homes_with_coords = [
            h for h in homes_data if h.get("latitude") and h.get("longitude")
        ]

        if not homes_with_coords:
            return dict(center=[39.8283, -98.5795], zoom=4, transition="flyTo")

        # Calculate center
        lats = [h["latitude"] for h in homes_with_coords]
        lngs = [h["longitude"] for h in homes_with_coords]

        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)

        # Calculate appropriate zoom level based on spread
        lat_spread = max(lats) - min(lats) if len(lats) > 1 else 0
        lng_spread = max(lngs) - min(lngs) if len(lngs) > 1 else 0
        spread = max(lat_spread, lng_spread)

        if spread < 0.01:
            zoom = 15
        elif spread < 0.05:
            zoom = 13
        elif spread < 0.1:
            zoom = 12
        elif spread < 0.5:
            zoom = 10
        elif spread < 1:
            zoom = 9
        elif spread < 5:
            zoom = 7
        else:
            zoom = 5

        return dict(center=[center_lat, center_lng], zoom=zoom, transition="flyTo")

    # Cost Analysis Page Callbacks

    @app.callback(
        Output("years-display", "children"),
        Input("years-slider", "value"),
        prevent_initial_call=False,
    )
    def update_years_display(years: int | None) -> str:
        """Update the years display text."""
        if years is None:
            return "30 years"
        return f"{years} years"

    @app.callback(
        Output("active-chart-tab", "data"),
        [
            Input("tab-value", "n_clicks"),
            Input("tab-equity", "n_clicks"),
            Input("tab-cash", "n_clicks"),
            Input("tab-costs", "n_clicks"),
            Input("tab-roi", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def update_active_tab(
        value_clicks: int,
        equity_clicks: int,
        cash_clicks: int,
        costs_clicks: int,
        roi_clicks: int,
    ) -> str:
        """Update the active chart tab based on button clicks."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return "value"
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        tab_map = {
            "tab-value": "value",
            "tab-equity": "equity",
            "tab-cash": "cash",
            "tab-costs": "costs",
            "tab-roi": "roi",
        }
        return tab_map.get(button_id, "value")

    @app.callback(
        [
            Output("tab-value", "className"),
            Output("tab-equity", "className"),
            Output("tab-cash", "className"),
            Output("tab-costs", "className"),
            Output("tab-roi", "className"),
        ],
        Input("active-chart-tab", "data"),
    )
    def update_tab_styles(active_tab: str) -> list[str]:
        """Update tab button styles based on active tab."""
        tabs = ["value", "equity", "cash", "costs", "roi"]
        return [
            "chart-tab active" if tab == active_tab else "chart-tab"
            for tab in tabs
        ]

    @app.callback(
        [
            Output("analysis-chart", "figure"),
            Output("summary-cards", "children"),
            Output("analysis-data-table", "children"),
        ],
        [
            Input("active-chart-tab", "data"),
            Input("years-slider", "value"),
            Input("down-payment-input", "value"),
            Input("interest-rate-input", "value"),
            Input("loan-term-input", "value"),
            Input("purchase-fees-input", "value"),
            Input("growth-rate-input", "value"),
            Input("repair-pct-input", "value"),
            Input("maint-inflation-input", "value"),
            Input({"type": "home-checkbox", "index": ALL}, "value"),
        ],
        prevent_initial_call=False,
    )
    def update_analysis_chart(
        active_tab: str,
        years: int | None,
        down_payment_pct: float | None,
        interest_rate: float | None,
        loan_term: int | None,
        purchase_fees: float | None,
        growth_rate: float | None,
        repair_pct: float | None,
        maint_inflation: float | None,
        home_selections: list[list[int]],
    ) -> tuple[go.Figure, list[html.Div] | html.Div]:
        """Update the analysis chart and summary cards based on selections."""
        # Get selected home IDs from the checkbox values
        selected_ids = []
        if home_selections:
            for selection in home_selections:
                if selection:
                    selected_ids.extend(selection)

        # Create empty figure if no homes selected
        if not selected_ids:
            fig = go.Figure()
            fig.update_layout(
                title="Select homes to compare",
                xaxis_title="Year",
                yaxis_title="Value ($)",
                template="plotly_white",
                height=500,
            )
            return fig, html.Div("Select one or more homes to see analysis", className="no-homes-message"), []

        # Get home data
        homes_data = []
        for home_id in selected_ids:
            home = get_home_by_id(home_id)
            if home and home.get("price"):
                homes_data.append(home)

        if not homes_data:
            fig = go.Figure()
            fig.update_layout(title="No valid homes selected")
            return fig, [], []

        # Convert inputs to proper values (handle None)
        years = years or 30
        down_pct = (down_payment_pct or 20) / 100
        int_rate = (interest_rate or 4.79) / 100
        loan_yrs = loan_term or 30
        fees = purchase_fees or 35000
        growth = (growth_rate or 3) / 100
        repair = (repair_pct or 0.03) / 100
        maint_inf = (maint_inflation or 2) / 100

        # Run analysis for each home
        all_results = {}
        colors = ["#667eea", "#f093fb", "#f5576c", "#4facfe", "#43e97b", "#fa709a"]

        for i, home in enumerate(homes_data):
            # Use home-specific values if available, otherwise use global params
            home_tax_rate = home.get("property_tax_rate")
            # If tax rate looks like a dollar amount (> 1), convert to rate
            if home_tax_rate and home_tax_rate > 1:
                home_tax_rate = home_tax_rate / home["price"]
            home_tax_rate = home_tax_rate or DEFAULTS["property_tax_rate"]

            home_hoa = home.get("hoa_monthly") or DEFAULTS["hoa_monthly"]

            params = CostAnalysisParams(
                home_price=home["price"],
                down_payment_pct=down_pct,
                purchase_fees=fees,
                property_tax_rate=home_tax_rate,
                monthly_repair_pct=repair,
                hoa_monthly=home_hoa,
                annual_growth_rate=growth,
                interest_rate=int_rate,
                loan_term_years=loan_yrs,
                maintenance_inflation=maint_inf,
            )

            results = run_analysis(params, years)
            label = f"{home.get('address', 'Unknown')[:30]}"
            all_results[label] = {
                "results": results,
                "color": colors[i % len(colors)],
                "home": home,
            }

        # Create figure based on active tab
        fig = go.Figure()

        chart_configs = {
            "value": {
                "title": "Home Value Over Time",
                "yaxis": "Value ($)",
                "field": "home_value",
            },
            "equity": {
                "title": "Equity Over Time",
                "yaxis": "Equity ($)",
                "field": "equity",
            },
            "cash": {
                "title": "Total Cash Invested Over Time",
                "yaxis": "Cash Invested ($)",
                "field": "total_cash_invested",
            },
            "costs": {
                "title": "Annual Cash Outflow Over Time",
                "yaxis": "Annual Costs ($)",
                "field": "annual_cash_outflow",
            },
            "roi": {
                "title": "Return on Investment Over Time",
                "yaxis": "ROI (Equity / Cash Invested)",
                "field": "roi",
            },
        }

        config = chart_configs.get(active_tab, chart_configs["value"])

        for label, data in all_results.items():
            results = data["results"]
            color = data["color"]

            x_values = [r.year for r in results]
            if config["field"] == "roi":
                y_values = [r.roi if r.roi else 0 for r in results]
            else:
                y_values = [getattr(r, config["field"]) for r in results]

            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="lines",
                    name=label,
                    line=dict(color=color, width=2),
                    hovertemplate=f"{label}<br>Year %{{x}}<br>{config['yaxis']}: %{{y:,.0f}}<extra></extra>"
                    if config["field"] != "roi"
                    else f"{label}<br>Year %{{x}}<br>ROI: %{{y:.2f}}x<extra></extra>",
                )
            )

        fig.update_layout(
            title=config["title"],
            xaxis_title="Year",
            yaxis_title=config["yaxis"],
            template="plotly_white",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            autosize=True,
            yaxis=dict(automargin=False, fixedrange=False),
            xaxis=dict(automargin=False),
            margin=dict(l=80, r=40, t=60, b=60),
        )

        if config["field"] != "roi":
            fig.update_yaxes(tickformat="$,.0f")

        # Create summary cards for the final year
        summary_cards = []
        for label, data in all_results.items():
            final = data["results"][-1]
            home = data["home"]
            color = data["color"]

            price_str = f"${home['price']:,.0f}"
            equity_str = f"${final.equity:,.0f}"
            roi_str = f"{final.roi:.2f}x" if final.roi else "N/A"
            cash_str = f"${final.total_cash_invested:,.0f}"

            summary_cards.append(
                html.Div([
                    html.A(
                        label[:25],
                        href=f"/home/{home['id']}",
                        className="card-title home-link",
                        style={"color": color, "display": "block"},
                    ),
                    html.Table([
                        html.Tbody([
                            html.Tr([html.Td("Price", className="label"), html.Td(price_str, className="value")]),
                            html.Tr([html.Td(f"Equity (Yr {years})", className="label"), html.Td(equity_str, className="value")]),
                            html.Tr([html.Td("ROI", className="label"), html.Td(roi_str, className="value")]),
                            html.Tr([html.Td("Total Invested", className="label"), html.Td(cash_str, className="value")]),
                        ])
                    ]),
                ], className="summary-card")
            )

        # Generate data table based on active tab
        data_table = generate_data_table(active_tab, all_results, years)

        return fig, summary_cards, data_table
