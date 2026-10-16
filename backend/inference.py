from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Dict

import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model

from backend.core.config import MILESTONE_1_LABELS, MODEL_LABELS_PATH, MODEL_PATH

_model = None
_labels: list[str] | None = None


def _get_model():
    global _model
    if _model is None:
        _model = load_model(MODEL_PATH)
    return _model


def _get_labels() -> list[str]:
    global _labels
    if _labels is None:
        with open(MODEL_LABELS_PATH, "r", encoding="utf-8") as file:
            _labels = json.load(file)
    return _labels


def analyze_image(image_bytes: bytes) -> Dict[str, float]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
    array = np.asarray(image, dtype=np.float32) / 255.0
    probabilities = _get_model().predict(np.expand_dims(array, axis=0), verbose=0)[0]
    labels = _get_labels()

    return {
        label: float(probabilities[labels.index(label)])
        for label in MILESTONE_1_LABELS
        if label in labels
    }
