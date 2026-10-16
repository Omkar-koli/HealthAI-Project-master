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

The application no longer creates tables itself. The schema is created by the SQL files in `migrations/` (see below). In local mode, uploaded image bytes are stored in `uploads/` and PostgreSQL stores the path; in cloud mode they go to a Cloud Storage bucket.

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

## Cloud deployment (Milestone 4)

State no longer lives on the VM:

| State | Local development | Cloud (VM) |
|---|---|---|
| Database | throwaway Postgres container (`docker-compose.yml`) | Cloud SQL for PostgreSQL, **private IP only** |
| Uploaded images | `uploads/` volume | Cloud Storage bucket, accessed with the VM's service account (no key file) |
| Secrets | developer's local `.env` | Secret Manager, fetched at runtime (no `.env` in the container) |

The local stack and the cloud stack hold **different data on purpose**. The UI banner and `GET /health`
report `environment`, `database`, and `storage` so you can always tell which one you are looking at.

### Schema migrations

Tables are created by the files in `migrations/`, applied in order by an admin (never by the app):

```bash
psql -h <host> -U <admin_user> -d healthai -v ON_ERROR_STOP=1 -f migrations/001_create_studies.sql
psql -h <host> -U <admin_user> -d healthai -v ON_ERROR_STOP=1 -f migrations/002_grant_app_role.sql
```

`schema_migrations` records which versions have been applied. The local compose file mounts the same
folder into the Postgres container so a fresh local database gets the identical schema.

### Running in the cloud

`docker-compose.cloud.yml` contains no database service, no volumes, and no passwords. The backend reads
`DB_SECRET_NAME` (the *name* of a secret) and fetches the value from Secret Manager with the VM's service account.
