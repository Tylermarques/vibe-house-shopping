# Vibe House Shopping

A Python Dash application for collecting and displaying data on local homes of interest.

## Project Structure

```
vibe-house-shopping/
├── app/
│   ├── __init__.py       # Package marker
│   ├── database.py       # SQLite models and database utilities (SQLAlchemy)
│   ├── parser.py         # HTML parser for extracting home data (BeautifulSoup)
│   ├── dash_app.py       # Dash application with map visualization (Plotly Dash + Leaflet)
│   └── watcher.py        # File watcher for import directory (watchdog)
├── data/                 # SQLite database (homes.db) stored here
├── import/               # Drop HTML files here for ingestion
├── requirements.txt      # Python dependencies
├── run.py                # Main entry point
└── CLAUDE.md             # This file
```

## Running the Application

```bash
pip install -r requirements.txt
python run.py
```

The app runs at http://localhost:8050

## How It Works

1. **File Watching**: The `ImportWatcher` monitors the `import/` directory for new `.html` or `.htm` files using the watchdog library.

2. **HTML Parsing**: When a file is detected, `HomeDataParser` extracts property data using BeautifulSoup with multiple parsing strategies:
   - Common CSS selectors for real estate sites
   - Meta tags (og:title, canonical URLs)
   - Regex patterns for addresses, prices, bed/bath counts, etc.
   - Embedded coordinate data from maps

3. **Geocoding**: If coordinates aren't found in the HTML, the parser uses geopy's Nominatim geocoder to look up the address.

4. **Database**: Extracted data is stored in SQLite via SQLAlchemy. Duplicates are detected by address + source file combination.

5. **Visualization**: The Dash app displays:
   - Interactive Leaflet map with markers for each home
   - Popups showing price, address, and key details
   - Sortable/filterable data table
   - Auto-refresh every 30 seconds

## Key Dependencies

- **dash** / **dash-leaflet**: Web framework and map component
- **sqlalchemy**: Database ORM
- **beautifulsoup4** / **lxml**: HTML parsing
- **watchdog**: File system monitoring
- **geopy**: Address geocoding

## Database Schema (Home model)

| Column        | Type     | Description                    |
|---------------|----------|--------------------------------|
| id            | Integer  | Primary key                    |
| address       | String   | Full street address            |
| city          | String   | City name                      |
| state         | String   | State abbreviation             |
| zip_code      | String   | ZIP code                       |
| price         | Float    | Listing price                  |
| bedrooms      | Integer  | Number of bedrooms             |
| bathrooms     | Float    | Number of bathrooms            |
| sqft          | Integer  | Square footage                 |
| lot_size      | Float    | Lot size in acres              |
| year_built    | Integer  | Year constructed               |
| property_type | String   | Single Family, Condo, etc.     |
| latitude      | Float    | GPS latitude                   |
| longitude     | Float    | GPS longitude                  |
| description   | Text     | Property description           |
| source_url    | String   | Original listing URL           |
| source_file   | String   | Name of imported HTML file     |
| imported_at   | DateTime | When the record was created    |
| raw_html      | Text     | First 50k chars of source HTML |

## Extending the Parser

The parser in `app/parser.py` uses a generic approach. To add support for a specific real estate site:

1. Add site-specific CSS selectors to the extraction methods
2. Add regex patterns that match the site's HTML structure
3. The parser tries multiple strategies and uses the first successful match

## Notes

- The import watcher processes existing files on startup
- Files are processed with a 0.5s delay to ensure complete writes
- Geocoding may fail for ambiguous addresses; coordinates will be None
- The map auto-centers on the average location of all homes with coordinates
