import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://healthai_user:your_password@localhost:5432/healthai",
)
MODEL_PATH = str(BASE_DIR / "models" / "xray_chexpert_multidisease_model.h5")
MODEL_LABELS_PATH = str(BASE_DIR / "models" / "xray_chexpert_labels.json")
UPLOADS_PATH = os.getenv("UPLOADS_PATH", str(BASE_DIR / "uploads"))

MILESTONE_1_LABELS = [
    "Atelectasis",
    "Cardiomegaly",
    "Edema",
    "Pleural Effusion",
    "Pneumonia",
]

