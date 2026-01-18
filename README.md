<p align="center">
  <img src="https://img.shields.io/badge/python-3.14+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.14+"/>
  <img src="https://img.shields.io/badge/Dash-2.14+-00ADD8?style=for-the-badge&logo=plotly&logoColor=white" alt="Dash"/>
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">
  <br>
  <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/house.svg" alt="Vibe House Shopping" width="120">
  <br>
  Vibe House Shopping
  <br>
</h1>

<h4 align="center">A sleek Python Dash application for collecting and visualizing local home listings with powerful cost analysis.</h4>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-demo">Demo</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-api">API</a> •
  <a href="#-contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/github/last-commit/yourusername/vibe-house-shopping?style=flat-square" alt="Last Commit"/>
  <img src="https://img.shields.io/github/issues/yourusername/vibe-house-shopping?style=flat-square" alt="Issues"/>
  <img src="https://img.shields.io/github/stars/yourusername/vibe-house-shopping?style=flat-square" alt="Stars"/>
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome"/>
</p>

---

## Why Vibe House Shopping?

House hunting is overwhelming. Dozens of browser tabs, spreadsheets that never get updated, and that nagging feeling you missed something important. **Vibe House Shopping** fixes all of that.

> "Finally, a tool that lets me compare homes the way I actually think about them." — *Future You*

Drop saved HTML listings into a folder. Watch them appear on an interactive map. Run financial projections to see the *real* cost of ownership. Make decisions with confidence.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🗺️ Interactive Map View
- Leaflet-powered map with property markers
- Click-to-view popups with key details
- Auto-centers on your properties
- Filter and sort in real-time

</td>
<td width="50%">

### 📊 Cost Analysis Dashboard
- Side-by-side home comparisons
- 5-30 year financial projections
- ROI, equity, and cash flow charts
- Customizable parameters

</td>
</tr>
<tr>
<td width="50%">

### 🔄 Smart Import System
- Drop HTML files → instant import
- File watcher with auto-processing
- Multi-site parsing strategies
- Duplicate detection built-in

</td>
<td width="50%">

### 🏠 Complete Property Data
- Price, beds, baths, sqft
- Property taxes & HOA fees
- Lot size and year built
- Original listing preserved

</td>
</tr>
</table>

---

## 🎬 Demo

```
┌─────────────────────────────────────────────────────────────────┐
│  VIBE HOUSE SHOPPING                           [Map] [Analysis] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     🏠 $425,000                    🏠 $389,000                  │
│        ●                              ●                         │
│                    🏠 $510,000                                  │
│                       ●                                         │
│                                                                 │
│                              🏠 $475,000                        │
│                                 ●                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Address           Price      Beds  Baths  Sqft   Year           │
│ 123 Main St      $425,000    3     2.0   1,850  1985           │
│ 456 Oak Ave      $389,000    4     2.5   2,100  1992           │
│ 789 Pine Rd      $510,000    4     3.0   2,450  2001           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

Get up and running in 60 seconds:

```bash
# Clone the repo
git clone https://github.com/yourusername/vibe-house-shopping.git
cd vibe-house-shopping

# Install dependencies
pip install -e .

# Run the app
python run.py
```

Open [http://localhost:8050](http://localhost:8050) and start dropping HTML files into the `import/` folder.

---

## 📦 Installation

### Prerequisites

- Python 3.14 or higher
- pip or uv package manager

### Standard Installation

```bash
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

### Using uv (Recommended)

```bash
uv pip install -e .
uv run python run.py
```

---

## 📖 Usage

### Basic Workflow

1. **Save Listings**: Save property pages as HTML from any real estate site
2. **Drop Files**: Move HTML files into the `import/` directory
3. **View Map**: Open http://localhost:8050 to see properties on the map
4. **Analyze Costs**: Navigate to `/analysis` for financial projections

### Importing Properties

The file watcher automatically processes new files:

```bash
# Copy a saved listing
cp ~/Downloads/123-main-st.html import/

# Or save directly from browser to import/
```

Supported sources include Zillow, Redfin, Realtor.com, and most real estate sites.

### Cost Analysis Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Down Payment | 20% | Percentage of home price |
| Interest Rate | 4.79% | Annual mortgage rate |
| Loan Term | 30 years | Mortgage duration |
| Property Tax | 1.2% | Annual tax rate |
| Repairs | 0.03%/mo | Monthly repair budget |
| Appreciation | 3%/yr | Home value growth |
| Maintenance Inflation | 2%/yr | Cost increase rate |

---

## 🏗️ Architecture

```
vibe-house-shopping/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── database.py          # SQLAlchemy models & utilities
│   ├── parser.py            # Multi-strategy HTML parser
│   ├── dash_app.py          # Dash + Leaflet visualization
│   ├── cost_analysis.py     # Financial calculations
│   └── watcher.py           # File system monitor
├── data/                    # SQLite database storage
├── import/                  # HTML drop zone
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── test_cost_analysis.py
│   ├── test_database.py
│   └── test_parser.py
├── pyproject.toml           # Project configuration
├── run.py                   # Application entry point
└── README.md
```

### Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  HTML Files  │───▶│   Watcher    │───▶│    Parser    │
│   (import/)  │    │  (watchdog)  │    │(BeautifulSoup│
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────┐    ┌──────▼───────┐
                    │   Dash App   │◀───│   Database   │
                    │  (Leaflet +  │    │  (SQLite +   │
                    │   Plotly)    │    │  SQLAlchemy) │
                    └──────────────┘    └──────────────┘
```

---

## 🔌 API

### Database Models

```python
from app.database import Home, get_session

# Query all homes
with get_session() as session:
    homes = session.query(Home).all()
    for home in homes:
        print(f"{home.address}: ${home.price:,.0f}")
```

### Parser Usage

```python
from app.parser import HomeDataParser

parser = HomeDataParser()
data = parser.parse_file("path/to/listing.html")
# Returns: {
#   "address": "123 Main St",
#   "price": 425000,
#   "bedrooms": 3,
#   "bathrooms": 2.0,
#   ...
# }
```

### Cost Analysis

```python
from app.cost_analysis import calculate_projections

projections = calculate_projections(
    price=425000,
    down_payment_pct=0.20,
    interest_rate=0.0479,
    years=30
)
# Returns yearly projections for equity, ROI, costs, etc.
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_parser.py -v
```

---

## 🛠️ Development

### Adding Parser Support for New Sites

1. Identify unique selectors in the site's HTML
2. Add patterns to `app/parser.py`:

```python
# In the appropriate extraction method
SITE_SELECTORS = [
    ".listing-price",           # Existing
    "[data-testid='price']",    # New site
]
```

3. Test with sample files from the site

### Running in Development

```bash
# Auto-reload on changes
uv run python run.py

# Check for errors at http://localhost:8050
```

---

## 🗺️ Roadmap

- [ ] Dark mode support
- [ ] Export to CSV/Excel
- [ ] Neighborhood data integration
- [ ] School district overlays
- [ ] Commute time calculations
- [ ] Multi-user support
- [ ] Mobile-responsive design
- [ ] Webhook notifications

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Add tests for new functionality
- Update documentation as needed

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Dash](https://dash.plotly.com/) — The Python framework for building data apps
- [Dash Leaflet](https://dash-leaflet.com/) — Interactive maps for Dash
- [Plotly](https://plotly.com/) — Beautiful charts and graphs
- [SQLAlchemy](https://www.sqlalchemy.org/) — The Python SQL toolkit
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing made easy
- [watchdog](https://github.com/gorakhargosh/watchdog) — File system events

---

<p align="center">
  Made with ❤️ by house hunters, for house hunters
  <br>
  <br>
  <a href="#-features">Back to top</a>
</p>
