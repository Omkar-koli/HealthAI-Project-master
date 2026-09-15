# HealthAI Milestone 1

A local chest X-ray analysis application using the existing pretrained CheXpert model, FastAPI, Streamlit, SQLAlchemy, and PostgreSQL.

## Milestone 1 workflow

1. Upload a JPG, JPEG, or PNG X-ray.
2. Save it with a UUID filename in `uploads/`.
3. Create a PostgreSQL `studies` row with `status = processing`.
4. Run the existing CheXpert model.
5. Keep the five Milestone 1 findings and select the highest probability.
6. Update the same row to `completed` with the prediction and confidence.
7. Display the result and recent persisted studies in Streamlit.

The five exposed findings are:

- Atelectasis
- Cardiomegaly
- Edema
- Pleural Effusion
- Pneumonia

The model internally remains the existing 8-output CheXpert model. No retraining is required.

## PostgreSQL setup

Install PostgreSQL locally, then create a database and user. In `psql`:

```sql
CREATE USER healthai_user WITH PASSWORD 'your_password';
CREATE DATABASE healthai OWNER healthai_user;
```

Copy `.env.example` to `.env` and set the real password:

```env
DATABASE_URL=postgresql+psycopg://healthai_user:your_password@localhost:5432/healthai
API_URL=http://127.0.0.1:8000
```

The application creates the `studies` table on startup. Uploaded image bytes are stored only in `uploads/`; PostgreSQL stores the path.

## Install dependencies

From the project root in PowerShell:

```powershell
..\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

## Run locally

Open two PowerShell terminals.

Backend:

```powershell
cd "E:\Fall 2026\Cloud Computing\HealthAI-Project-master\HealthAI-Project-master"
..\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd "E:\Fall 2026\Cloud Computing\HealthAI-Project-master\HealthAI-Project-master"
$env:API_URL = "http://127.0.0.1:8000"
..\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Open http://localhost:8501. API documentation is at http://127.0.0.1:8000/docs.

## Endpoints

- `GET /health`
- `POST /studies/analyze` with multipart field `file`
- `GET /studies/recent?limit=10`

`POST /studies/analyze` returns the study ID, status, top finding, confidence, and exactly five probabilities.

## Database schema

The application uses one table:

```text
studies
  id                 integer primary key
  image_name         varchar(255) not null
  image_path         varchar(500) not null
  status             varchar(32) not null
  predicted_condition varchar(128) nullable
  confidence         float nullable
  created_at         timestamp
```

## Active model files

- `models/xray_chexpert_multidisease_model.h5`
- `models/xray_chexpert_labels.json`

The old pneumonia-only model, DenseNet training path, NIH preparation path, analytics, and Grad-CAM are outside Milestone 1.
