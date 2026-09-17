# 🏛️ MPLADS Works Intelligence & Review System
### SIH 2026 Problem Statement: PS 26102 — Ministry of Statistics and Programme Implementation (MoSPI)

[![System Status](https://img.shields.io/badge/System--Status-100%25%20Operational-brightgreen)](#)
[![Backend Tests](https://img.shields.io/badge/Pytest-53%2F53%20PASSED-success)](#)
[![Frontend Build](https://img.shields.io/badge/Vite-Build%20Clean-blue)](#)
[![Production Backend](https://img.shields.io/badge/Render-API%20Live-purple)](https://mplads-works-api.onrender.com)
[![Production Frontend](https://img.shields.io/badge/Render-UI%20Live-purple)](https://mplads-works-frontend.onrender.com)

---

## 📌 Problem Statement & Objective

**Problem Statement (PS 26102 - MoSPI)**: Development of an intelligent monitoring and operational review system for Members of Parliament Local Area Development Scheme (MPLADS) works to detect risk anomalies, prevent duplicate sanctions, verify physical progress evidence, and streamline district review workflows.

The **MPLADS Works Intelligence & Review System** is an end-to-end governance decision-support platform designed for District Nodal Officers, State Auditors, and Central Administrators. It transforms raw project lifecycle data into actionable risk intelligence through explainable rules, statistical outlier detection, machine learning anomaly signals, and evidence forensics.

---

## ✨ Core System Capabilities

### 1. 🛡️ Explainable Tri-Layer Risk Prioritization Engine
- **Deterministic Governance Rules**: Automated verification of cost limits, milestone chronology, payment mismatches, and evidence completeness.
- **Robust Statistical Outliers**: Median and Median Absolute Deviation (MAD) robust z-score calculation across peer category work distributions.
- **Machine Learning Anomaly Signal**: Multivariate `IsolationForest` (scikit-learn) model detecting subtle non-linear anomalies across cost, disbursement ratio, physical progress percentage, and delay timeline.
- **Governance Framing**: All flags are explicitly framed as operational indicators for human review rather than judicial determinations.

### 2. 🔍 Hybrid Duplicate & Similarity Detection
- **Multi-Feature Candidate Engine**: Combines TF-IDF title/description text similarity, Haversine geographic proximity, category matching, implementing agency overlap, and cost delta metrics.
- **Candidate Compare Interface**: Side-by-side work comparison with direct candidate navigation.

### 3. 📷 Evidence Photo Forensics & Cross-Work Fraud Flags
- **Perceptual Hashing (pHash)**: Detects visually identical or reused inspection photos across distinct works.
- **EXIF Metadata Extraction**: Inspects embedded camera model, EXIF timestamp, and GPS coordinates.
- **Geo-Fence Mismatch Alerts**: Flags evidence photos captured >500m away from declared work site coordinates.
- **SHA-256 Exact File Hash Reuse**: Prevents re-upload of identical photo files across different project files.

### 4. 🗺️ Geospatial Risk Distribution Map
- **Interactive Leaflet Dashboard Map**: Visualizes localized project risk bands (Critical: Red, High: Orange, Medium: Amber, Low: Green) with direct popup detail navigation.

### 5. 📥 eSAKSHI Public Export Adapter & Provenance Metadata
- **Official Data Mapping**: Normalizes public eSAKSHI export headers (`Work ID`, `Work Description`, `Sanction Amount (Rs)`, `Status`, `Latitude`, `Longitude`) into standard schema format.
- **Provenance Tracking**: Distinguishes `OFFICIAL_PUBLIC` data feeds from `CONTROLLED_PROTOTYPE` seed data with full audit metadata.

### 6. 📊 Contractor & Agency Concentration Analytics
- **Allocation Density Analysis**: Surfacing agency work shares, total sanction density, and district span metrics for human review.

### 7. 🔐 Role-Based Access Control (RBAC) & Jurisdiction Scope Isolation
- **District Scope**: District Officers (`district.officer`) restricted strictly to their assigned district jurisdiction.
- **Auditor & Admin Scope**: Auditors (`auditor.demo`) and Admins (`admin.demo`) maintain national multi-district oversight.

### 8. 📋 Review Case Workflow & Audit Trail
- **Formal Case State Machine**: `DETECTED` ➔ `TRIAGED` ➔ `UNDER_REVIEW` ➔ `RESOLVED` / `CLOSED` with strict 409 conflict handling on invalid transitions.
- **Immutable Audit Log**: Records all user actions, evidence uploads, and state changes.

### 9. 🧮 What-If Financial & Delay Simulator
- **Scenario Modeling**: Simulates cost overruns, disbursement delays, and physical progress lags against baseline risk scores.

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend UI** | React 18, TypeScript, Vite 5, Tailwind CSS, Lucide Icons, Leaflet Maps, Recharts |
| **Backend API** | Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn |
| **Machine Learning** | scikit-learn (`IsolationForest`), NumPy, Pillow, ImageHash, Piexif |
| **Database** | SQLite (Development & Local), PostgreSQL (Production Compatible) |
| **Testing & QA** | Pytest (53 Unit/Integration Tests), Vite TypeScript Compiler |
| **Deployment** | Render (Production Web Service & Static Site) |

---

## 🚀 Local Installation & Execution Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed local database
python app/db/seed.py

# Run backend development server
uvicorn app.main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### 2. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
- UI Client: `http://localhost:5173`

---

## 🧪 Automated Testing & Verification

### Run Backend Pytest Suite (53 Tests)
```bash
python -m pytest backend/tests/ -v
```

### Run Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 🌐 Live Production Deployment

- **Live Frontend Application**: [https://mplads-works-frontend.onrender.com](https://mplads-works-frontend.onrender.com)
- **Live Backend API Services**: [https://mplads-works-api.onrender.com](https://mplads-works-api.onrender.com)

### Verified Demo User Accounts
| Role | Username | Password | Jurisdiction Scope |
|------|----------|----------|-------------------|
| **District Officer** | `district.officer` | `demo-password` | Scoped to District `DIST-001` (10 works) |
| **Lucknow Officer** | `lucknow.officer` | `demo-password` | Scoped to District `DIST-002` |
| **State Auditor** | `auditor.demo` | `demo-password` | All Districts (`DIST-001`, `DIST-002`, `DIST-003`) |
| **Administrator** | `admin.demo` | `demo-password` | Full System Access |

---

## ⚖️ Governance & Data Disclaimer

The MPLADS Works Intelligence & Review System is designed as an operational review decision-support platform. All risk flags, similarity scores, and ML anomaly indicators serve as **decision-support signals for human review** by authorized government officers and auditors. They do not constitute judicial determinations or proof of wrongdoing. Synthetic prototype data is explicitly labeled as `SYNTHETIC_DEMO`.
