import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

# Local development convenience only. In the deployed container there is no .env file.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Database
#   Cloud mode  (DB_HOST set): connect to Cloud SQL over its private IP. The
#                              password is read from Secret Manager at startup.
#   Local mode  (DB_HOST unset): use DATABASE_URL from the developer's .env.
# ---------------------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST")

if DB_HOST:
    from backend.core.secret_manager import get_secret

    _db_user = os.environ["DB_USER"]
    _db_name = os.environ["DB_NAME"]
    _db_port = os.getenv("DB_PORT", "5432")
    _db_password = get_secret(os.environ["DB_SECRET_NAME"])
    DATABASE_URL = (
        f"postgresql+psycopg://{quote(_db_user, safe='')}:{quote(_db_password, safe='')}"
        f"@{DB_HOST}:{_db_port}/{_db_name}"
    )
    APP_ENV = "cloud"
    DATABASE_MODE = "cloud-sql-private-ip"
else:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://healthai_user:your_password@localhost:5432/healthai",
    )
    APP_ENV = "local"
    DATABASE_MODE = "local-dev-container"

# ---------------------------------------------------------------------------
# Model (read-only artifact baked into the image; it is code, not state)
# ---------------------------------------------------------------------------
MODEL_PATH = str(BASE_DIR / "models" / "xray_chexpert_multidisease_model.h5")
MODEL_LABELS_PATH = str(BASE_DIR / "models" / "xray_chexpert_labels.json")

# ---------------------------------------------------------------------------
# Uploads: "gcs" (Cloud Storage bucket, via the VM's service account) or "local"
# ---------------------------------------------------------------------------
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()
GCS_BUCKET = os.getenv("GCS_BUCKET", "")
GCP_PROJECT = os.getenv("GCP_PROJECT", "")
UPLOADS_PATH = os.getenv("UPLOADS_PATH", str(BASE_DIR / "uploads"))

if STORAGE_BACKEND == "gcs" and not GCS_BUCKET:
    raise RuntimeError("STORAGE_BACKEND=gcs requires GCS_BUCKET to be set.")

MILESTONE_1_LABELS = [
    "Atelectasis",
    "Cardiomegaly",
    "Edema",
    "Pleural Effusion",
    "Pneumonia",
]
