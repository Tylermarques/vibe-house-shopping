"""Dash application for visualizing home data on a map."""

import dash
from dash import html, dcc, dash_table, callback, Input, Output
import dash_leaflet as dl
import pandas as pd

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


def create_home_list_layout():
    """Create the main home listing layout."""
    return html.Div([
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


def create_home_detail_layout(home_id: int):
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


def register_callbacks(app: dash.Dash):
    """Register all Dash callbacks."""

    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
    )
    def display_page(pathname):
        """Route to the appropriate page based on URL."""
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
    def refresh_data(n_intervals):
        """Refresh home data from the database."""
        return get_all_homes()

    @app.callback(
        Output("homes-data", "data", allow_duplicate=True),
        Input("refresh-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def refresh_data_button(n_clicks):
        """Refresh home data when button is clicked."""
        return get_all_homes()

    @app.callback(
        Output("homes-list", "children"),
        Input("homes-data", "data"),
    )
    def update_homes_list(homes_data):
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
