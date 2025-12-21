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
2. Place `leads.xlsx` with an "Address" column
3. Run and check `output.xlsx` for results

See [INSTALLATION.md](INSTALLATION.md) for detailed setup.
