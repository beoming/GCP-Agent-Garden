# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for handling images."""
import logging
import os
from typing import TYPE_CHECKING, Literal, Optional, Tuple

from google.cloud import storage

if TYPE_CHECKING:
    from google.adk.tools import ToolContext

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

IMAGE_MIME_TYPE = "image/png"


async def load_image_resource(
    source_type: Literal["artifact", "gcs"],
    source_path: str,
    tool_context: "ToolContext",
) -> Tuple[Optional[bytes], str, str]:
    """Loads image bytes from either a GCS path or a tool artifact.

    Args:
        source_type (str): The source of the image ('artifact' or 'gcs').
        source_path (str): The path to the image.
        tool_context (ToolContext): The context for artifact management.

    Returns:
        A tuple with the image bytes, identifier, and MIME type.
    """
    identifier = os.path.basename(source_path).split(".")[0]
    mime_suffix = "jpeg" if source_path.lower().endswith(".jpg") else "png"

    if source_type == "artifact":
        artifact = await tool_context.load_artifact(source_path)
        image_bytes = (
            artifact.inline_data.data if artifact and artifact.inline_data else None
        )
    else:
        gcs_uri = source_path[5:] if source_path.startswith("gs://") else source_path
        bucket_name, blob_name = gcs_uri.split("/", 1)
        storage_client = storage.Client()
        blob = storage_client.bucket(bucket_name).blob(blob_name)
        image_bytes = blob.download_as_bytes()

    return image_bytes, identifier, f"image/{mime_suffix}"
