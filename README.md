# Data-Driven Policy Dashboard

## Overview
A full-stack, cloud-ready dashboard for ingesting, analyzing, and visualizing policy documents (PDF, Excel, CSV, DOCX, images) with real-time insights, anomaly detection, and web enrichment.

## Features
- File upload and parsing (PDF, Excel, CSV, DOCX, images with OCR)
- NLP-based summarization and policy extraction
- Automated analytics (descriptive, trends, anomaly detection)
- Real-time and web-enriched insights
- Interactive dashboard with exportable reports
- Role-based access, audit logs, and security best practices
- Modular, API-driven, and cloud-deployable

## Tech Stack
- **Frontend:** React, TypeScript, Chart.js/Plotly, MUI/Ant Design
- **Backend:** FastAPI, Python, Pandas, Transformers, Tesseract OCR
- **Database:** PostgreSQL or MongoDB
- **Storage:** Local/S3 (abstracted)
- **Containerization:** Docker, docker-compose

## Quickstart

### 1. Clone & Install
```sh
git clone <repo-url>
cd <repo-root>
```

### 2. Backend
```sh
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend
```sh
cd frontend
npm install
npm run dev
```

### 4. Docker (Full Stack)
```sh
docker-compose up --build
```

## Folder Structure
```
/backend      # FastAPI backend
/frontend     # React frontend
/infrastructure # Docker, CI/CD, cloud configs
```

## Configuration
- Set environment variables in `backend/.env` and `frontend/.env` as needed.
- For production, configure S3/Cloud storage and secure secrets.

## License
MIT 