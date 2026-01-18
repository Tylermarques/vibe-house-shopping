"""Dash application for visualizing home data on a map."""

import dash
from dash import html, dcc, dash_table, callback, Input, Output
import dash_leaflet as dl
import pandas as pd

from .database import get_all_homes, init_db


def create_app() -> dash.Dash:
    """Create and configure the Dash application."""
    app = dash.Dash(
        __name__,
        title="Vibe House Shopping",
        suppress_callback_exceptions=True,
    )

    app.layout = html.Div(
        [
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
                            dash_table.DataTable(
                                id="homes-table",
                                columns=[
                                    {"name": "Address", "id": "address"},
                                    {"name": "City", "id": "city"},
                                    {"name": "State", "id": "state"},
                                    {"name": "Price", "id": "price", "type": "numeric", "format": {"specifier": "$,.0f"}},
                                    {"name": "Beds", "id": "bedrooms"},
                                    {"name": "Baths", "id": "bathrooms"},
                                    {"name": "Sq Ft", "id": "sqft", "type": "numeric", "format": {"specifier": ","}},
                                    {"name": "Year Built", "id": "year_built"},
                                    {"name": "Type", "id": "property_type"},
                                ],
                                style_table={"overflowX": "auto"},
                                style_cell={
                                    "textAlign": "left",
                                    "padding": "10px",
                                    "fontFamily": "system-ui, -apple-system, sans-serif",
                                },
                                style_header={
                                    "backgroundColor": "#f8f9fa",
                                    "fontWeight": "bold",
                                    "borderBottom": "2px solid #dee2e6",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {"row_index": "odd"},
                                        "backgroundColor": "#f8f9fa",
                                    }
                                ],
                                page_size=20,
                                sort_action="native",
                                filter_action="native",
                            ),
                        ],
                        className="table-container",
                    ),
                ],
                className="main-content",
            ),
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


def register_callbacks(app: dash.Dash):
    """Register all Dash callbacks."""

    @app.callback(
        Output("homes-data", "data"),
        [Input("refresh-button", "n_clicks"), Input("auto-refresh", "n_intervals")],
    )
    def refresh_data(n_clicks, n_intervals):
        """Refresh home data from the database."""
        return get_all_homes()

    @app.callback(
        Output("homes-table", "data"),
        Input("homes-data", "data"),
    )
    def update_table(homes_data):
        """Update the data table with home data."""
        if not homes_data:
            return []
        return homes_data

    @app.callback(
        Output("marker-layer", "children"),
        Input("homes-data", "data"),
    )
    def update_map_markers(homes_data):
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

                popup_html = f"""
                <div class="popup-content">
                    <div class="popup-price">{price_str}</div>
                    <div class="popup-address">{home.get('address', 'Address N/A')}</div>
                    <div class="popup-details">
                        {beds} bed | {baths} bath | {sqft} sqft<br/>
                        {home.get('property_type', '')}
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
    def update_home_count(homes_data):
        """Update the home count display."""
        count = len(homes_data) if homes_data else 0
        return f"{count} home{'s' if count != 1 else ''} in database"

    @app.callback(
        Output("home-map", "center"),
        Output("home-map", "zoom"),
        Input("homes-data", "data"),
    )
    def update_map_view(homes_data):
        """Update map center and zoom based on home locations."""
        if not homes_data:
            return [39.8283, -98.5795], 4  # Default: center of US

        # Get homes with coordinates
        homes_with_coords = [
            h for h in homes_data if h.get("latitude") and h.get("longitude")
        ]

        if not homes_with_coords:
            return [39.8283, -98.5795], 4

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

        return [center_lat, center_lng], zoom
