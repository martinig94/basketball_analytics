# Basketball Analytics

A Python-based analytics project for EuroLeague basketball, focused on team and player performance analysis with automated documentation generation.

## Features

- Player and team statistical breakdowns (offensive and defensive)
- Shot location analysis across 9 court zones
- Clutch performance and fast-break efficiency metrics
- Season splits and league ranking comparisons
- Automated static site generation with tables and charts

## Tech Stack

- **Data**: `euroleague_api`, `pandas`, `numpy`
- **Visualization**: `matplotlib`, `seaborn`, `plotly`
- **Docs**: MkDocs (Material theme), WeasyPrint

## Project Structure

```
basketball_analytics/
├── main.py                  # Entry point — generates documentation tables
├── utils_euroleague.py      # Data fetching
├── utils_plot.py            # Visualization helpers
├── utils_roster.py          # Roster management
├── utils_markdown.py        # Markdown generation
├── constants.py             # Season and team settings
├── zone_mapping.py          # Shot zone definitions
├── team_colors.py           # Team color styling
└── data/                    # Cached CSVs (boxscores, shots, rosters)
```

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the main analysis:
   ```bash
   python main.py
   ```
4. Build and serve the docs site:
   ```bash
   mkdocs serve
   ```
