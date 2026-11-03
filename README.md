# BrewWise ☕

**BrewWise** is an intelligent, multi-modal pour-over coffee recipe generator that bridges the gap between specialty coffee roasters and home brewers.

## Features
- **Bag Vision & OCR**: Instant extraction of coffee bean metadata with token-optimised compact schemas.
- **Normalisation**: Canonical roaster, process, and roast level mapping.
- **Dynamic Recipe Synthesis**: Dialed-in pour-over recipes tailored to coffee origins, bean processing, and brewing equipment.
- **Arithmetic Verification**: Strict validation of coffee doses, brew ratios, pour sequences, and temperature ranges.
- **Modern Responsive UI**: Mobile-first camera capture, bag review, and live brewing assistant.

## Quick Start

### Backend
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn brewwise.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
