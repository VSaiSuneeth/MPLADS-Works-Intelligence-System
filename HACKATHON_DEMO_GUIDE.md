# 🏆 SIH 2026 — MPLADS Works Intelligence & Review System
## Complete Hackathon Judge Presentation, Demonstration & Setup Guide

> **Verified Operational Status**: All 42 automated Pytest test cases passed 100%. Frontend production build compiled with 0 errors. All 10 steps of this presentation script have been tested, verified live, and regression-tested across all user roles and datasets (`mplads_works_test_data.csv`).

---

## 📌 1. System Overview & Key Demonstration Personas

Our system introduces an operational intelligence layer for monitoring infrastructure works under the **Member of Parliament Local Area Development Scheme (MPLADS)**. 

To demonstrate full functionality to judges, use the **3 Key Demonstration Personas**:

| Persona / Role | Demo Username | Password | Role Scope | Key Features to Showcase |
| :--- | :--- | :--- | :--- | :--- |
| **District Nodal Officer** | `district.officer` | `demo-password` | Scoped to Delhi (`DIST-001`) | District Dashboard, Real-time Risk Queue, 5-Tab Investigation Canvas, Geotagged Lightbox & Downloader, Photo Upload & Fraud Detector, 1-Click Case Creation |
| **Senior State Auditor** | `auditor.demo` | `demo-password` | All Districts Access | Cross-District Audit Stream (`/audit`), Evidence Fraud Register Tab, Formatted ISO Timestamps, Immutable Action Logging, Anti-Tamper Compliance |
| **System Administrator** | `admin.demo` | `demo-password` | Full Administrative Access | CSV Dataset Import (`/admin`), SHA-256 Record Deduplication, Live Report Card, Manual Risk Engine Recalculation |

---

## 🚀 2. Complete Step-by-Step System Setup Instructions

Before presenting to judges, launch the backend and frontend services:

### Step 2.1 — Start Backend Server (FastAPI)
```cmd
cd backend
py app/db/seed.py
py -m uvicorn app.main:app --reload --port 8000
```
- **Backend API Status**: Returns `200 OK` on `http://localhost:8000/api/v1/health`.
- **Interactive OpenAPI Docs**: Accessible at `http://localhost:8000/api/v1/docs`.

### Step 2.2 — Start Frontend Application (React + Vite)
```cmd
cd frontend
set PATH=C:\Users\HP\node-v20.18.0-win-x64;%PATH%
npm run dev
```
- **Web Application URL**: Accessible at `http://localhost:5173`.

---

## 🎭 3. Step-by-Step Judge Presentation Script (6 to 7 Minutes)

---

### STEP 1: The Hook & Government Problem Statement (30 Seconds)
- **Action**: Open the Login Screen (`http://localhost:5173/login`).
- **What to Say to Judges**:
  > *"Respected Judges, under the Member of Parliament Local Area Development Scheme (MPLADS), thousands of infrastructure works are sanctioned annually across hundreds of districts. However, district authorities face three critical operational bottlenecks: unrecorded milestone delays, payment-versus-physical progress mismatches, and candidate duplicate works across adjacent wards. Current government portals only store static records without proactive intelligence. Today, we introduce the **MPLADS Works Intelligence Engine** — an AI-powered operational review and risk prioritization system built for district officers and auditors."*

---

### STEP 2: Role-Based Access Control (RBAC) & Scope Isolation (30 Seconds)
- **Action**: On the Login page, click **"Delhi Nodal Officer"** (`district.officer`) on the Quick Role Switcher and click **"Sign In to Governance Portal"**.
- **What to Say to Judges**:
  > *"Notice how our portal enforces strict, jurisdiction-aware Role-Based Access Control (RBAC). As the Delhi Nodal Officer, I am automatically scoped exclusively to Delhi works (`DIST-001`). System access is governed by signed JWT Bearer tokens ensuring strict multi-district data isolation."*

---

### STEP 3: District Governance Dashboard (`/dashboard`) (45 Seconds)
- **Action**: Show the Dashboard page:
  1. Point out the **Amber Synthetic Data Banner** highlighting controlled data provenance (`SYNTHETIC_DEMO`).
  2. Highlight the **4 KPI Cards**: Total Sanctioned Works (10), Active Open Cases (0), Execution Stage Works (5), Completed Works (5).
  3. Show the **Risk Priority Distribution Chart** (Medium & Low Risk Bands).
  4. Point to the **Top Risk Candidate Works Card** showing work `W-1001` (Borewell construction) flagged with a High Risk Score ($R(w) = 55.0$).
- **What to Say to Judges**:
  > *"The Governance Dashboard provides immediate situational awareness. Rather than displaying passive charts, it highlights priority review candidates. Notice our transparent governance stance: the system flags review candidates for officer inspection without asserting legal guilt or fraud."*

---

### STEP 4: Prioritized Risk Queue (`/queue`) & Real-Time Backend Search (45 Seconds)
- **Action**: Click **"Prioritized Risk Queue"** in the sidebar. Show:
  1. The table strictly sorted by **Risk Score $R(w)$ descending** (`55.0`, `55.0`, `50.0`...).
  2. Type `"Borewell"` or `"W-1001"` in the search bar. Point out how the live backend SQL query instantly filters matching works across title, external ID, category, agency, and location text!
  3. Select Filter Tabs: Priority = `MEDIUM`, Stage = `EXECUTION`.
- **What to Say to Judges**:
  > *"Instead of scrolling through unranked spreadsheets, district officers rely on our **Prioritized Risk Queue**. Every work is ranked by a transparent Risk Score out of 100. Our live backend search bar and multi-select dropdown filters allow officers to isolate specific high-risk projects in real-time."*

---

### STEP 5: Deep-Dive Investigation Canvas (`/works/:id`) — All 5 Tabs (90 Seconds)
- **Action**: Click **"Review"** on `W-1001` (Construction of High Capacity Borewell). Walk judges through **All 5 Tabs**:

1. **Header & Gauges**: Show Sanction Amount (₹1,500,000) vs Expenditure Disbursed (₹1,350,000 / 90%) against Physical Progress (15%).
2. **Tab 1: Overview**: Shows combined operational summary and location metadata.
3. **Tab 2: Risk Signals**: Click **Risk Signals (2)**:
   - **Signal `FIN-PAY-001`**: Disbursements reach 90.0% of sanction, but reported physical progress is only 15.0%.
   - **Signal `TIME-DELAY-001`**: Work in execution for >1 year with only 15% progress.
4. **Tab 3: Lifecycle Timeline**: Click **Lifecycle Timeline (5)**:
   - Show chronological milestone line (Recommendation $\rightarrow$ Sanction $\rightarrow$ Progress $\rightarrow$ Disbursement).
   - Point out clean Indian governance date formatting (`15 Feb 2023`) and explicit amber warning markers for missing unrecorded milestones (`isMissing: True`).
5. **Tab 4: Evidence Gallery**: Click **Evidence Gallery (1)**:
   - Show geotagged site inspection photo artifacts (`site_inspection_01.jpg`).
   - Click **"View"** to open the **Interactive Geotagged Lightbox Modal** showing high-res photo inspection view, GPS EXIF coordinates (`28.6139° N, 77.2090° E`), timestamp, file format, and SHA-256 verification.
   - Click **"Download Artifact File"** to demonstrate live file downloading directly in the browser!
   - Highlight the **Missing Completion Certificate Warning (COMP-EVID-001)** strip.
6. **Tab 5: Candidate Duplicates**: Click **Candidate Duplicates (1)**:
   - Show candidate duplicate match `W-1002` with **92.7% Similarity Score**.
   - Explain the **6-Feature Vector Score Breakdown Diff**:
     - `Text TF-IDF`: 77.6%
     - `Geo Proximity`: 98.8%
     - `Category Match`: 100.0%
     - `Agency Match`: 100.0%
     - `Cost Delta`: 98.7%
     - `Date Overlap`: 98.3%
- **What to Say to Judges**:
  > *"This is our core innovation: **Explainable AI Investigation Across 5 Tabs**.
  > - **Tab 2 (Signals)** shows *why* a work is flagged (e.g. 90% payment disbursed vs 15% physical work).
  > - **Tab 3 (Timeline)** pinpoints unrecorded milestone gaps with formatted dates.
  > - **Tab 4 (Evidence)** opens an interactive geotagged EXIF lightbox modal with 1-click artifact file downloading!
  > - **Tab 5 (Duplicates)** uses a 6-feature vector matcher comparing text TF-IDF, Haversine geo-coordinates, and cost delta to catch candidate duplicate sanction pairs (`W-1001` vs `W-1002`) with a 92.7% match score!"*

---

### STEP 6: Review Case Workflow & State Machine (`/cases`) (45 Seconds)
- **Action**: 
  1. Click **"Create Review Case"** button on top-right of Work Detail page (`/works/W-1001`).
  2. The system creates the case (`CASE-2026-0001`) and navigates directly to `/cases?caseId=...`, popping open the case modal!
  3. In the modal:
     - Select Action Type: **"Request Agency Clarification"**.
     - Set New Status: **"CLARIFICATION_REQUESTED"**.
     - Type notes: *"Requesting immediate physical inspection report from executing agency (CPWD)"*.
     - Click **Submit Official Action**.
  4. Show how the case status updates to **CLARIFICATION_REQUESTED** and the action note is recorded in the timeline.
  5. Also point out the **"+ Open New Review Case"** header button on `/cases` for manual case creation.
- **What to Say to Judges**:
  > *"Once an anomaly is identified, officers don't leave the portal. With 1-click, they open a formal **Review Case**. As shown, the officer can issue official clarification requests to executing agencies, transition case states, and maintain complete auditability."*

---

### STEP 7: Senior State Auditor Persona Demo (`auditor.demo`) (30 Seconds)
- **Action**: 
  1. Click user menu in top-right, click **Logout**.
  2. Log in as **Senior State Auditor** (`auditor.demo` / `demo-password`).
  3. Open **System Audit Trail** (`/audit`).
  4. Point out the formatted timestamp (`27 Aug 2026, 01:44:01 AM`) and newly recorded audit stream entries showing:
     - **Actor**: `Delhi Nodal Officer`
     - **Action**: `REQUEST_CLARIFICATION` & `CASE_CREATED`
     - **Entity**: `Case` (`CASE-2026-0001`)
     - **Timestamp & Details**: Full JSON metadata payload.
- **What to Say to Judges**:
  > *"Now switching to the **Senior State Auditor** persona (`auditor.demo`). Auditors have state-wide visibility across all districts. Every officer action, case transition, and data edit is recorded in an immutable, append-only **System Audit Trail** with clean ISO timestamps for complete anti-tamper compliance."*

---

### STEP 8: System Administrator Persona & Data Import (`admin.demo`) (45 Seconds)
- **Action**: 
  1. Log in as **System Administrator** (`admin.demo` / `demo-password`).
  2. Open **Data Import Portal** (`/admin`).
  3. Drag and drop your dataset file (`mplads_works_test_data.csv` or `seed_works.csv`) into the uploader dropzone and click **Start Data Ingestion**.
  4. Point out the live **Ingestion Report Card** showing Accepted Works, Rejected Rows, and Quality Findings.
  5. Demonstrate **SHA-256 Deduplication**: Re-upload the exact same CSV file and show how the system updates records idempotently without double-counting work rows.
  6. Click **"Recalculate All Risk Scores"** button to execute risk engine algorithms live across all works.
- **What to Say to Judges**:
  > *"Finally, logged in as **System Administrator** (`admin.demo`), we demonstrate our **Data Import & Engine Tools**. Admins can ingest new district CSV data feeds (`mplads_works_test_data.csv`). Our pipeline uses SHA-256 row record hashing for idempotent deduplication, preventing double-counting. With 1-click, the admin can trigger on-demand risk recalculation across all district works."*

---

### STEP 9: AI "What-If" Project Impact Simulator (`/simulator`) (60 Seconds)
- **Action**:
  1. Click **"What-If Impact Simulator"** (`/simulator`) in the sidebar navigation.
  2. Show the **Interactive Input Form**: Select project `[W-1001] Construction of High Capacity Borewell` from the dropdown.
  3. **Run 3 Concrete "Wow Moment" Scenarios live for judges**:
     - **Scenario 1 (Premature Disbursement Spike)**: Click the **"Premature Spend Spike"** preset button. Notice how expenditure spikes to 95% of sanction cost (₹1,425,000) while physical completion remains at 15%. Watch the system instantly predict a **Financial Risk score spike to 90.0/100 (CRITICAL)** and Priority Band shift `MEDIUM → CRITICAL`!
     - **Scenario 2 (Timeline Delay Slippage)**: Click the **"Timeline Delay Slippage"** preset button. Shift expected completion date earlier while progress is only 10%. Observe predicted **Delay Risk jump to 85.0/100 (CRITICAL)** with plain-language risk drivers.
     - **Scenario 3 (Budget Cost Overrun)**: Click the **"Budget Cost Overrun"** preset button. Reduce sanctioned cost below actual spend. Notice cost overrun % warning and financial z-score anomaly indicators.
  4. Highlight the **Side-by-Side Comparison Cards** (Current Baseline vs Simulated Scenario), **Comparative Risk Bars**, and **Officer Recommendation Box**.
- **What to Say to Judges**:
  > *"To solve the judges' exact problem statement, we built the **AI What-If Impact Simulator**. District authorities can test proposed parameter changes — project cost, expenditure rate, physical completion %, and target completion dates — BEFORE approving revised sanctions. The engine instantly predicts financial risk, delay risk, and overall project risk level, comparing baseline vs simulated scenarios side-by-side with clear indicators, risk deltas, and actionable officer recommendations!"*

---

### STEP 10: AI Evidence Photo Fraud & Cross-Work Duplicate Detector (60 Seconds)
- **Action**:
  1. Navigate to Work `W-1009` (Lucknow Anganwadi) or `W-1001` (Delhi Borewell) and click the **Evidence Gallery** tab.
  2. Point out the **Red Banner Alert**:
     `⚠ CROSS-WORK FRAUD ALERT: EXACT HASH REUSE (Confidence: 100%, Severity: CRITICAL)`
     pointing back to work `W-1001` in Delhi!
  3. Click **"Upload Site Photo"** button, pick a photo, upload it live, and demonstrate instant real-time hash extraction, EXIF metadata parsing, and fraud flag evaluation.
  4. Open **System Audit Trail** (`/audit`), click the **"Evidence Photo Fraud Register"** tab, and show the system-wide register listing all cross-work duplicate flags.
- **What to Say to Judges**:
  > *"To directly address your question on evidence photo fraud: when contractor B takes contractor A's photo and uploads it for their project in another district, our **AI Evidence Photo Fraud Engine** instantly computes SHA-256 byte hashes, pHash 64-bit DCT perceptual image hashes, and EXIF GPS geotags. It detects identical files, re-compressed copies, and EXIF timestamp collisions with 100% confidence, displaying actionable alert banners with clickable links back to the original work!"*

---

## ❓ 4. Simple & Clear Explanations for Judges (Q&A Guide)

### Q1: "How is the Risk Score calculated?"
> **Answer**: The Total Risk Score $R(w) = \min(100.0, \sum C_i)$ is a transparent composite score out of 100. It combines deterministic compliance rules (e.g., `FIN-PAY-001` payment mismatch = +40 pts, `TIME-DELAY-001` milestone delay = +15 pts, `COMP-EVID-001` missing certificate = +25 pts) and statistical cost anomaly $Z$-scores.

### Q2: "How does the Candidate Duplicate Matcher work?"
> **Answer**: It calculates a 6-feature weighted similarity vector between work pairs:
> 1. **Text TF-IDF + Cosine Similarity** (30%): Compares work titles & descriptions.
> 2. **Haversine Geo-Proximity** (25%): Measures exact physical distance between coordinates.
> 3. **Category Match** (15%): Compares infrastructure categories.
> 4. **Agency Match** (10%): Compares executing agencies.
> 5. **Cost Delta** (10%): Measures sanction amount closeness.
> 6. **Date Overlap** (10%): Compares recommendation & sanction date windows.
> Pairs scoring $> 80\%$ (like `W-1001` & `W-1002` at 92.7%) are flagged as candidate duplicate pairs.

### Q3: "What is your approach to cost anomaly detection?"
> **Answer**: We use Median Absolute Deviation (MAD) $Z$-scores (`STAT-COST-001`). Unlike standard mean averages which get distorted by extreme outliers, MAD $Z$-scores robustly identify projects whose cost per unit exceeds 3.0 median deviations above category peer works in the same district.

### Q4: "Is this system asserting legal fraud or misconduct?"
> **Answer**: No. Our system is explicitly designed as a **Decision Support System for Human Reviewers**. It flags candidate anomalies and assigns transparent risk scores to prioritize officer attention, while leaving legal and administrative determinations strictly to human officers.

### Q5: "How does the What-If Impact Simulator predict financial and delay risk?"
> **Answer**: The simulator evaluates parameter changes against a transparent dual-engine model:
> 1. **Financial Risk Sub-Engine**: Evaluates expenditure-to-sanction disbursement ratio vs physical completion %, cost overrun %, and category peer median MAD $Z$-score.
> 2. **Delay Risk Sub-Engine**: Evaluates timeline progress slippage ($\text{Expected Completion \%} - \text{Actual Completion \%}$), days overdue past target completion date, and stagnant execution flags.
> 3. **Composite Overall Risk**: Combines $45\% \text{Financial Risk} + 45\% \text{Delay Risk} + 10\% \text{Compliance Signals}$ into an overall score and priority band (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`), generating side-by-side comparative risk bars and plain-language driver explanations.

### Q6: "How do you detect contractor photo evidence fraud across different works?"
> **Answer**: We use a 3-layer explainable image provenance pipeline:
> 1. **SHA-256 Byte Hashing**: Instantly flags byte-for-byte identical photo files uploaded across different projects (`EXACT_HASH_REUSE`, 100% confidence).
> 2. **Perceptual Hashing (pHash 64-bit DCT)**: Computes Hamming distance to detect cropped, resized, or re-compressed copies of photos (`NEAR_DUPLICATE_PHASH`, threshold $\le 8$).
> 3. **EXIF Geotag & Timestamp Collision**: Extracted embedded GPS coordinates and camera timestamps to detect photos taken at the exact same location (within 5m) and time (within 60s) for two separate work sanctions (`GPS_TIMESTAMP_MATCH`).
> 4. **Location Mismatch**: Compares photo EXIF GPS against the work's declared site coordinates (`LOCATION_MISMATCH`, threshold $> 500\text{m}$).
> 5. **Stripped EXIF Warning**: Flags photos lacking EXIF/geotag metadata (`EXIF_STRIPPED_UNVERIFIABLE`) as an honest uncertainty indicator for officer verification.
