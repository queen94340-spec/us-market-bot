# US Market Real-Time Alert Program

This script polls Yahoo Finance data and prints alerts for **S&P 500**, **VOO**, and **NVIDIA**.

## Requirements

- Python 3.9+
- `requests`

Install dependencies:

```bash
pip install requests
```

## Usage

Fetch once:

```bash
python app.py --once
```

Poll every 60 seconds with a 1% alert threshold:

```bash
python app.py --interval 60 --threshold 1.0
```

Adjust the threshold (percent change from previous close) as needed.
