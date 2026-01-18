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
            # Store for current theme (light or dark)
            dcc.Store(id="theme-store", data="light"),
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
                /* CSS Variables for theming */
                :root {
                    /* Light mode (default) */
                    --bg-primary: #f5f5f5;
                    --bg-secondary: #ffffff;
                    --bg-tertiary: #f8f9fa;
                    --bg-hover: #f0f0f0;
                    --bg-alt: #fafafa;
                    --text-primary: #333333;
                    --text-secondary: #666666;
                    --text-tertiary: #888888;
                    --text-description: #444444;
                    --border-primary: #eeeeee;
                    --border-secondary: #dddddd;
                    --border-tertiary: #dee2e6;
                    --border-light: #f0f0f0;
                    --accent-primary: #667eea;
                    --accent-secondary: #764ba2;
                    --accent-hover: #5a6fd6;
                    --shadow-color: rgba(0, 0, 0, 0.1);
                    --shadow-light: rgba(0, 0, 0, 0.05);
                    --popup-text: #2d3748;
                    --table-footer-bg: #e8e8e8;
                    --table-footer-border: #cccccc;
                    --tooltip-bg: #333333;
                    --tooltip-text: #ffffff;
                    --chart-template: plotly_white;
                }

                [data-theme="dark"] {
                    /* Dark mode */
                    --bg-primary: #1a1a2e;
                    --bg-secondary: #16213e;
                    --bg-tertiary: #1f2940;
                    --bg-hover: #253550;
                    --bg-alt: #1c2a3f;
                    --text-primary: #e8e8e8;
                    --text-secondary: #b0b0b0;
                    --text-tertiary: #888888;
                    --text-description: #c0c0c0;
                    --border-primary: #2a3a50;
                    --border-secondary: #3a4a60;
                    --border-tertiary: #3a4a60;
                    --border-light: #2a3a50;
                    --accent-primary: #7c8ff8;
                    --accent-secondary: #9b6dd4;
                    --accent-hover: #8a9cf8;
                    --shadow-color: rgba(0, 0, 0, 0.3);
                    --shadow-light: rgba(0, 0, 0, 0.2);
                    --popup-text: #e8e8e8;
                    --table-footer-bg: #253550;
                    --table-footer-border: #3a4a60;
                    --tooltip-bg: #e8e8e8;
                    --tooltip-text: #1a1a2e;
                    --chart-template: plotly_dark;
                }

                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }
                body {
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: var(--bg-primary);
                    color: var(--text-primary);
                    transition: background-color 0.3s ease, color 0.3s ease;
                }
                .app-container {
                    max-width: 1800px;
                    margin: 0 auto;
                    padding: 20px 40px;
                    width: 100%;
                }
                .controls {
                    display: flex;
                    align-items: center;
                    gap: 20px;
                    margin-bottom: 20px;
                }
                .refresh-button {
                    background-color: var(--accent-primary);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    font-size: 1rem;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                .refresh-button:hover {
                    background-color: var(--accent-hover);
                }
                .home-count {
                    font-size: 1.1rem;
                    color: var(--text-secondary);
                }
                .main-content {
                    display: flex;
                    flex-direction: column;
                    gap: 30px;
                    width: 100%;
                }
                .map-container, .table-container {
                    background: var(--bg-secondary);
                    padding: 25px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px var(--shadow-color);
                    width: 100%;
                    transition: background-color 0.3s ease, box-shadow 0.3s ease;
                }
                .map-container h2, .table-container h2 {
                    margin-bottom: 15px;
                    color: var(--text-primary);
                }
                .leaflet-popup-content {
                    font-family: system-ui, -apple-system, sans-serif;
                }
                .popup-content {
                    line-height: 1.6;
                }
                .popup-content strong {
                    color: var(--accent-primary);
                }
                .popup-price {
                    font-size: 1.2rem;
                    font-weight: bold;
                    color: var(--popup-text);
                    margin-bottom: 8px;
                }
                .popup-address {
                    font-weight: 600;
                    margin-bottom: 8px;
                }
                .popup-details {
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }
                .home-link {
                    color: var(--accent-primary);
                    text-decoration: none;
                    cursor: pointer;
                }
                .home-link:hover {
                    text-decoration: underline;
                }
                .back-link {
                    display: inline-block;
                    margin-bottom: 20px;
                    color: var(--accent-primary);
                    text-decoration: none;
                    font-size: 1rem;
                }
                .back-link:hover {
                    text-decoration: underline;
                }
                .detail-container {
                    background: var(--bg-secondary);
                    padding: 30px 40px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px var(--shadow-color);
                    margin-bottom: 20px;
                    width: 100%;
                    transition: background-color 0.3s ease, box-shadow 0.3s ease;
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
                    color: var(--text-primary);
                    margin-bottom: 8px;
                }
                .detail-location {
                    font-size: 1.1rem;
                    color: var(--text-secondary);
                }
                .detail-price {
                    font-size: 2.2rem;
                    font-weight: bold;
                    color: var(--accent-primary);
                }
                .detail-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .detail-item {
                    padding: 15px;
                    background: var(--bg-tertiary);
                    border-radius: 8px;
                    transition: background-color 0.3s ease;
                }
                .detail-label {
                    font-size: 0.85rem;
                    color: var(--text-secondary);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 5px;
                }
                .detail-value {
                    font-size: 1.2rem;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                .detail-section {
                    margin-bottom: 30px;
                }
                .detail-section h3 {
                    font-size: 1.2rem;
                    color: var(--text-primary);
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid var(--border-primary);
                }
                .detail-description {
                    line-height: 1.7;
                    color: var(--text-description);
                    white-space: pre-wrap;
                }
                .detail-map {
                    height: 300px;
                    border-radius: 8px;
                    margin-top: 15px;
                }
                .detail-meta {
                    font-size: 0.9rem;
                    color: var(--text-tertiary);
                }
                .detail-meta a {
                    color: var(--accent-primary);
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
                    color: var(--text-secondary);
                    margin-bottom: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 12px 10px;
                    text-align: left;
                    border-bottom: 1px solid var(--border-primary);
                }
                th {
                    background-color: var(--bg-tertiary);
                    font-weight: 600;
                    color: var(--text-primary);
                    border-bottom: 2px solid var(--border-tertiary);
                }
                tr:hover {
                    background-color: var(--bg-tertiary);
                }
                tbody tr:nth-child(odd) {
                    background-color: var(--bg-alt);
                }
                tbody tr:nth-child(odd):hover {
                    background-color: var(--bg-hover);
                }
                /* Navigation styles */
                .nav-bar {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 20px;
                    margin-bottom: 20px;
                    padding: 12px 20px;
                    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
                    border-radius: 8px;
                    box-shadow: 0 2px 5px var(--shadow-color);
                }
                .nav-title {
                    font-size: 1.4rem;
                    font-weight: 600;
                    color: white;
                }
                .nav-links {
                    display: flex;
                    gap: 10px;
                }
                .nav-link {
                    color: rgba(255,255,255,0.9);
                    text-decoration: none;
                    font-weight: 500;
                    padding: 8px 16px;
                    border-radius: 6px;
                    transition: background-color 0.2s;
                }
                .nav-link:hover {
                    background-color: rgba(255,255,255,0.15);
                    color: white;
                }
                .nav-link.active {
                    background-color: rgba(255,255,255,0.25);
                    color: white;
                }
                /* Cost Analysis Page Styles */
                .analysis-container {
                    display: grid;
                    grid-template-columns: 320px 1fr;
                    gap: 30px;
                    width: 100%;
                }
                .analysis-sidebar {
                    background: var(--bg-secondary);
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px var(--shadow-color);
                    height: fit-content;
                    position: sticky;
                    top: 20px;
                    transition: background-color 0.3s ease, box-shadow 0.3s ease;
                }
                .analysis-main {
                    background: var(--bg-secondary);
                    padding: 25px 30px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px var(--shadow-color);
                    min-width: 0;
                    overflow: hidden;
                    flex: 1;
                    transition: background-color 0.3s ease, box-shadow 0.3s ease;
                }
                .param-group {
                    margin-bottom: 20px;
                }
                .param-group h4 {
                    margin-bottom: 10px;
                    color: var(--text-primary);
                    font-size: 0.95rem;
                }
                .param-input {
                    display: flex;
                    flex-direction: column;
                    margin-bottom: 12px;
                }
                .param-input label {
                    font-size: 0.85rem;
                    color: var(--text-secondary);
                    margin-bottom: 4px;
                }
                .param-input input, .param-input select {
                    padding: 8px 12px;
                    border: 1px solid var(--border-secondary);
                    border-radius: 6px;
                    font-size: 0.95rem;
                    background-color: var(--bg-secondary);
                    color: var(--text-primary);
                    transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
                }
                .param-input input:focus, .param-input select:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                }
                .home-checkbox-list {
                    max-height: 200px;
                    overflow-y: auto;
                    border: 1px solid var(--border-primary);
                    border-radius: 6px;
                    padding: 10px;
                    background-color: var(--bg-secondary);
                    transition: background-color 0.3s ease, border-color 0.3s ease;
                }
                .home-checkbox-item {
                    display: flex;
                    align-items: center;
                    padding: 8px 0;
                    border-bottom: 1px solid var(--border-light);
                    overflow: hidden;
                }
                .home-checkbox-item .home-link {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    flex: 1;
                    min-width: 0;
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
                    border-bottom: 2px solid var(--border-primary);
                    padding-bottom: 0;
                }
                .chart-tab {
                    padding: 10px 20px;
                    border: none;
                    background: none;
                    cursor: pointer;
                    font-size: 0.95rem;
                    color: var(--text-secondary);
                    border-bottom: 2px solid transparent;
                    margin-bottom: -2px;
                    transition: all 0.2s;
                }
                .chart-tab:hover {
                    color: var(--accent-primary);
                }
                .chart-tab.active {
                    color: var(--accent-primary);
                    border-bottom-color: var(--accent-primary);
                    font-weight: 500;
                }
                .slider-container {
                    margin-top: 10px;
                }
                .slider-value {
                    text-align: center;
                    font-weight: 500;
                    color: var(--accent-primary);
                    margin-top: 5px;
                }
                .summary-cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }
                .summary-card {
                    background: var(--bg-tertiary);
                    padding: 15px;
                    border-radius: 8px;
                    transition: background-color 0.3s ease;
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
                    color: var(--text-secondary);
                    text-transform: uppercase;
                    text-align: left;
                }
                .summary-card td.value {
                    font-size: 1rem;
                    font-weight: 600;
                    color: var(--text-primary);
                    text-align: right;
                }
                .no-homes-message {
                    padding: 40px;
                    text-align: center;
                    color: var(--text-secondary);
                }
                /* Data table styles */
                .data-table-container {
                    margin-top: 30px;
                    overflow-x: auto;
                }
                .data-table-container h3 {
                    margin-bottom: 15px;
                    color: var(--text-primary);
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
                    border: 1px solid var(--border-secondary);
                    white-space: nowrap;
                }
                .data-table th {
                    background-color: var(--bg-tertiary);
                    font-weight: 600;
                    color: var(--text-primary);
                    position: sticky;
                    top: 0;
                }
                .data-table th:first-child, .data-table td:first-child {
                    text-align: left;
                    position: sticky;
                    left: 0;
                    background-color: var(--bg-tertiary);
                    z-index: 1;
                }
                .data-table tbody tr:nth-child(odd) {
                    background-color: var(--bg-alt);
                }
                .data-table tbody tr:nth-child(odd) td:first-child {
                    background-color: var(--bg-alt);
                }
                .data-table tbody tr:hover {
                    background-color: var(--bg-hover);
                }
                .data-table tbody tr:hover td:first-child {
                    background-color: var(--bg-hover);
                }
                .data-table tfoot td {
                    font-weight: 600;
                    background-color: var(--table-footer-bg);
                    border-top: 2px solid var(--table-footer-border);
                }
                .data-table tfoot td:first-child {
                    background-color: var(--table-footer-bg);
                }
                /* Tooltip styling for data cells */
                .data-table td[title] {
                    position: relative;
                    cursor: help;
                }
                .data-table td[title]:hover::after {
                    content: attr(title);
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    background: var(--tooltip-bg);
                    color: var(--tooltip-text);
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    white-space: nowrap;
                    z-index: 10;
                    pointer-events: none;
                }
                .data-table td[title]:hover::before {
                    content: '';
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%) translateY(6px);
                    border: 5px solid transparent;
                    border-top-color: var(--tooltip-bg);
                    z-index: 10;
                }
                @media (max-width: 900px) {
                    .analysis-container {
                        grid-template-columns: 1fr;
                    }
                    .analysis-sidebar {
                        position: static;
                    }
                }

                /* Theme toggle button */
                .theme-toggle {
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    padding: 8px 12px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 1.1rem;
                    transition: background-color 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .theme-toggle:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
                .theme-toggle .icon-sun,
                .theme-toggle .icon-moon {
                    display: none;
                }
                :root .theme-toggle .icon-moon {
                    display: inline;
                }
                [data-theme="dark"] .theme-toggle .icon-sun {
                    display: inline;
                }
                [data-theme="dark"] .theme-toggle .icon-moon {
                    display: none;
                }

                /* Dash slider component styling for dark mode */
                [data-theme="dark"] .rc-slider-track {
                    background-color: var(--accent-primary);
                }
                [data-theme="dark"] .rc-slider-handle {
                    border-color: var(--accent-primary);
                    background-color: var(--bg-secondary);
                }
                [data-theme="dark"] .rc-slider-rail {
                    background-color: var(--border-secondary);
                }
                [data-theme="dark"] .rc-slider-mark-text {
                    color: var(--text-secondary);
                }

                /* Plotly chart dark mode styling */
                [data-theme="dark"] .js-plotly-plot .plotly .modebar-btn path {
                    fill: var(--text-secondary);
                }
                [data-theme="dark"] .js-plotly-plot .plotly .modebar-btn:hover path {
                    fill: var(--text-primary);
                }
            </style>
            <script>
                // Theme switching functionality
                (function() {
                    // Check for saved theme preference or default to system preference
                    function getPreferredTheme() {
                        const savedTheme = localStorage.getItem('theme');
                        if (savedTheme) {
                            return savedTheme;
                        }
                        // Check system preference
                        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                            return 'dark';
                        }
                        return 'light';
                    }

                    // Apply theme to document
                    function applyTheme(theme) {
                        if (theme === 'dark') {
                            document.documentElement.setAttribute('data-theme', 'dark');
                        } else {
                            document.documentElement.removeAttribute('data-theme');
                        }
                        localStorage.setItem('theme', theme);

                        // Dispatch custom event for Plotly chart updates
                        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: theme } }));
                    }

                    // Toggle theme
                    window.toggleTheme = function() {
                        const currentTheme = document.documentElement.getAttribute('data-theme');
                        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                        applyTheme(newTheme);
                    };

                    // Apply theme on page load
                    applyTheme(getPreferredTheme());

                    // Listen for system theme changes
                    if (window.matchMedia) {
                        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                            if (!localStorage.getItem('theme')) {
                                applyTheme(e.matches ? 'dark' : 'light');
                            }
                        });
                    }
                })();
            </script>
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
    """Create the navigation bar with site title, nav links, and theme toggle."""
    return html.Div([
        html.Span("Vibe House Shopping", className="nav-title"),
        html.Div([
            html.A("Home Listings", href="/", className=f"nav-link {'active' if active_page == 'homes' else ''}"),
            html.A("Cost Analysis", href="/analysis", className=f"nav-link {'active' if active_page == 'analysis' else ''}"),
            html.Button(
                [
                    html.Span("\u2600\ufe0f", className="icon-sun"),  # Sun emoji
                    html.Span("\ud83c\udf19", className="icon-moon"),  # Moon emoji
                ],
                className="theme-toggle",
                id="theme-toggle-btn",
                n_clicks=0,
            ),
        ], className="nav-links"),
    ], className="nav-bar")


def create_home_list_layout() -> html.Div:
    """Create the main home listing layout."""
    return html.Div([
        # Navigation
        create_nav_bar("homes"),
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
    """Generate a unified comparison table for the analysis results.

    All selected homes are shown in a single table for easy comparison.
    Each row is a year, and columns show values for each home side-by-side.

    Args:
        active_tab: The currently active chart tab (value, equity, cash, costs, roi)
        all_results: Dictionary of analysis results keyed by home label
        years: Number of years in the analysis

    Returns:
        HTML table element showing the data
    """
    if not all_results:
        return []

    home_labels = list(all_results.keys())
    num_homes = len(home_labels)
    first_results = list(all_results.values())[0]["results"]
    all_years = [r.year for r in first_results]

    # Define which fields to show based on the active tab
    tab_config = {
        "value": [("Home Value", "home_value", True)],
        "equity": [("Equity", "equity", True), ("Loan Balance", "loan_balance", True)],
        "cash": [("Total Cash Invested", "total_cash_invested", True)],
        "costs": [
            ("Property Taxes", "annual_taxes", True),
            ("Repairs", "annual_repair", True),
            ("Maintenance", "annual_maintenance", True),
            ("Mortgage", "annual_mortgage_payment", True),
            ("Total Outflow", "annual_cash_outflow", True),
        ],
        "roi": [("ROI", "roi", False), ("Equity", "equity", True), ("Cash Invested", "total_cash_invested", True)],
    }

    fields = tab_config.get(active_tab, tab_config["value"])

    # Build header rows
    # Row 1: Year + metric names (spanning all homes)
    header_row1_cells = [html.Th("Year", rowSpan=2)]
    for field_name, _, _ in fields:
        header_row1_cells.append(
            html.Th(field_name, colSpan=num_homes, style={"textAlign": "center"})
        )

    # Row 2: Home names under each metric (color-coded)
    header_row2_cells = []
    for _ in fields:
        for label in home_labels:
            color = all_results[label]["color"]
            header_row2_cells.append(
                html.Th(
                    label[:20],
                    style={"color": color, "fontSize": "0.8rem", "fontWeight": "normal"},
                    title=label,
                )
            )

    # Build data rows - one row per year
    data_rows = []
    for year_idx, year in enumerate(all_years):
        cells = [html.Td(str(year))]

        for field_name, field_key, is_currency in fields:
            for label in home_labels:
                data = all_results[label]
                results = data["results"]
                color = data["color"]
                r = results[year_idx]

                if field_key == "roi":
                    val = r.roi
                    cell_text = f"{val:.2f}x" if val else "—"
                else:
                    val = getattr(r, field_key)
                    cell_text = f"${val:,.0f}" if is_currency else f"{val:,.2f}"

                cells.append(
                    html.Td(
                        cell_text,
                        style={"color": color},
                        title=f"{label}: {cell_text}",
                    )
                )

        data_rows.append(html.Tr(cells))

    # Build totals row for costs tab
    footer_rows = []
    if active_tab == "costs":
        total_cells = [html.Td("Total", style={"fontWeight": "600"})]
        for field_name, field_key, is_currency in fields:
            for label in home_labels:
                data = all_results[label]
                results = data["results"]
                color = data["color"]
                # Sum all years (skip year 0 for annual costs)
                total = sum(getattr(r, field_key) for r in results[1:])
                cell_text = f"${total:,.0f}" if is_currency else f"{total:,.2f}"
                total_cells.append(
                    html.Td(
                        cell_text,
                        style={"color": color, "fontWeight": "600"},
                        title=f"{label} Total: {cell_text}",
                    )
                )
        footer_rows.append(html.Tr(total_cells))

    title_map = {
        "value": "Home Value Comparison",
        "equity": "Equity Comparison",
        "cash": "Cash Invested Comparison",
        "costs": "Annual Costs Comparison",
        "roi": "ROI Comparison",
    }

    return html.Div([
        html.H3(title_map.get(active_tab, "Comparison")),
        html.Table([
            html.Thead([
                html.Tr(header_row1_cells),
                html.Tr(header_row2_cells),
            ]),
            html.Tbody(data_rows),
            html.Tfoot(footer_rows) if footer_rows else None,
        ], className="data-table"),
    ])


def register_callbacks(app: dash.Dash) -> None:
    """Register all Dash callbacks."""

    # Clientside callback for theme toggle
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks > 0) {
                toggleTheme();
            }
            // Return current theme
            const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
            return theme;
        }
        """,
        Output("theme-store", "data"),
        Input("theme-toggle-btn", "n_clicks"),
        prevent_initial_call=True,
    )

    # Clientside callback to initialize theme from localStorage
    app.clientside_callback(
        """
        function(pathname) {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                return savedTheme;
            }
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                return 'dark';
            }
            return 'light';
        }
        """,
        Output("theme-store", "data", allow_duplicate=True),
        Input("url", "pathname"),
        prevent_initial_call=True,
    )

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
            Input("theme-store", "data"),
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
        current_theme: str | None,
    ) -> tuple[go.Figure, list[html.Div] | html.Div, html.Div | list[Any]]:
        """Update the analysis chart, summary cards, and data table based on selections."""
        # Determine chart template based on theme
        chart_template = "plotly_dark" if current_theme == "dark" else "plotly_white"
        paper_bgcolor = "rgba(0,0,0,0)" if current_theme == "dark" else "rgba(0,0,0,0)"
        plot_bgcolor = "rgba(0,0,0,0)" if current_theme == "dark" else "rgba(0,0,0,0)"

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
                template=chart_template,
                height=500,
                paper_bgcolor=paper_bgcolor,
                plot_bgcolor=plot_bgcolor,
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
            fig.update_layout(title="No valid homes selected", template=chart_template)
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
            template=chart_template,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            autosize=True,
            yaxis=dict(automargin=False, fixedrange=False),
            xaxis=dict(automargin=False),
            margin=dict(l=80, r=40, t=60, b=60),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
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
