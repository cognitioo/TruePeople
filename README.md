# TruePeopleSearch Scraper

Extracts phone numbers from TruePeopleSearch.com using addresses from an Excel file.

## Quick Start
```bash
# Docker (easiest)
docker build -t scraper .
docker run -it -v $(pwd):/app scraper

# Manual
pip install -r requirements.txt
playwright install firefox
python main.py
```

## Configuration
1. Edit `.env` with your proxy credentials
2. Place `leads.xlsx` with addresses in Column B
3. Run - phone numbers are written to Column C of `leads.xlsx`

See [INSTALLATION.md](INSTALLATION.md) for detailed setup.
