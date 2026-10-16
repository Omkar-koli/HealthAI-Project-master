"""Fetch secrets from Google Secret Manager at runtime.

Authentication uses Application Default Credentials. On the VM that means the
VM's attached service account via the metadata server: no key file, no
GOOGLE_APPLICATION_CREDENTIALS, and no password in any env var or file.
"""
from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=None)
def get_secret(secret_id: str, version: str = "latest") -> str:
    from google.cloud import secretmanager  # imported lazily: not needed for local dev

    project = os.environ["GCP_PROJECT"]
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8").strip()  # ignore accidental trailing newline/space
