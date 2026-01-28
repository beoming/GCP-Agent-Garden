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

"""Deployment script for Travel Concierge."""

import asyncio
import os

from absl import app, flags
from dotenv import load_dotenv

from travel_concierge.agent import root_agent

from google.adk.sessions import VertexAiSessionService

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket.")

flags.DEFINE_string(
    "initial_states_path",
    None,
    "Relative path to the initial state file, .e.g eval/itinerary_empty_default.json",
)
flags.DEFINE_string("map_key", None, "API Key for Google Places API")

flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")
flags.DEFINE_bool("create", False, "Creates a new deployment.")
flags.DEFINE_bool("quicktest", False, "Try a new deployment with one turn.")
flags.DEFINE_bool("delete", False, "Deletes an existing deployment.")
flags.mark_bool_flags_as_mutual_exclusive(["create", "delete", "quicktest"])


def create(env_vars: dict[str, str]) -> None:
    """Creates a new deployment."""
    print(env_vars)
    app = AdkApp(
        agent=root_agent,
        enable_tracing=True,
        env_vars=env_vars,
    )

    remote_agent = agent_engines.create(  
        app,
        display_name="Travel-Concierge-ADK",
        description="An Example AgentEngine Deployment",                    
        requirements=[
            "google-adk (>=1.16.0)",
            "google-cloud-aiplatform[agent_engines] (>=1.93.1)",
            "google-genai (>=1.16.1)",
            "pydantic (>=2.10.6,<3.0.0)",
            "absl-py (>=2.2.1,<3.0.0)",
            "pydantic (>=2.10.6,<3.0.0)",
            "requests (>=2.32.3,<3.0.0)",
            "arize-otel (>=0.8.2)",
            "arize (>=7.36.0)",
            "openinference-instrumentation-google-adk (>=0.1.0)",
            "openinference-instrumentation (>=0.1.34)",
            "python-dotenv (>=1.0.1)",
        ],
        extra_packages=[
            "./travel_concierge",  # The main package
        ],
    )
    print(f"Created remote agent: {remote_agent.resource_name}")


def delete(resource_id: str, project_id: str, location: str) -> None:
    # resource_id가 숫자만 있으면 전체 resource name으로 변환
    if resource_id.isdigit():
        resource_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{resource_id}"
    else:
        resource_name = resource_id
    remote_agent = agent_engines.get(resource_name)
    remote_agent.delete(force=True)
    print(f"Deleted remote agent: {resource_name}")


def send_message(session_service: VertexAiSessionService, resource_id: str, project_id: str, location: str, message: str) -> None:
    """Send a message to the deployed agent."""

    # resource_id가 숫자만 있으면 전체 resource name으로 변환
    if resource_id.isdigit():
        resource_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{resource_id}"
    else:
        resource_name = resource_id

    session = asyncio.run(session_service.create_session(
            app_name=resource_name,
            user_id="traveler0115"
        )
    )

    remote_agent = agent_engines.get(resource_name)

    print(f"Trying remote agent: {resource_name}")
    for event in remote_agent.stream_query(
        user_id="traveler0115",
        session_id=session.id,
        message=message,
    ):
        print(event)
    print("Done.")


def main(argv: list[str]) -> None:
    # .env 파일을 명시적으로 로드 (deployment 디렉토리 기준으로 상위 디렉토리에서 찾기)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)
    env_vars = {}

    project_id = (
        FLAGS.project_id if FLAGS.project_id else os.getenv("GOOGLE_CLOUD_PROJECT")
    )
    location = FLAGS.location if FLAGS.location else os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = FLAGS.bucket if FLAGS.bucket else os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    # Variables for Travel Concierge from .env
    initial_states_path = (
        FLAGS.initial_states_path
        if FLAGS.initial_states_path
        else os.getenv("TRAVEL_CONCIERGE_SCENARIO")
    )
    env_vars["TRAVEL_CONCIERGE_SCENARIO"] = initial_states_path
    map_key = (
        FLAGS.map_key
        if FLAGS.map_key
        else os.getenv("GOOGLE_PLACES_API_KEY")
    )
    env_vars["GOOGLE_PLACES_API_KEY"] = map_key
    
    # 백엔드 API URL 환경 변수 추가
    flight_api_url = os.getenv("FLIGHT_SEARCH_API_URL")
    hotel_api_url = os.getenv("HOTEL_SEARCH_API_URL")
    if flight_api_url:
        env_vars["FLIGHT_SEARCH_API_URL"] = flight_api_url
    if hotel_api_url:
        env_vars["HOTEL_SEARCH_API_URL"] = hotel_api_url
    
    # Zendesk Connection 환경 변수 추가
    zendesk_connection_name = os.getenv("ZENDESK_CONNECTION_NAME")
    if zendesk_connection_name:
        env_vars["ZENDESK_CONNECTION_NAME"] = zendesk_connection_name

    print(f"PROJECT: {project_id}")
    print(f"LOCATION: {location}")
    print(f"BUCKET: {bucket}")
    print(f"INITIAL_STATE: {initial_states_path}")
    print(f"MAP: {map_key[:5] if map_key else 'None'}")

    if not project_id:
        print("Missing required environment variable: GOOGLE_CLOUD_PROJECT")
        return
    elif not location:
        print("Missing required environment variable: GOOGLE_CLOUD_LOCATION")
        return
    elif not bucket:
        print("Missing required environment variable: GOOGLE_CLOUD_STORAGE_BUCKET")
        return
    elif not initial_states_path:
        print("Missing required environment variable: TRAVEL_CONCIERGE_SCENARIO")
        return
    elif not map_key:
        print("Missing required environment variable: GOOGLE_PLACES_API_KEY")
        return

    # location이 없거나 'global'이면 'us-central1'로 설정
    if not location or location == "global":
        location = "us-central1"
        print(f"WARNING: Location was 'global' or empty, using 'us-central1' instead")

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    if FLAGS.create:
        create(env_vars)
    elif FLAGS.delete:
        if not FLAGS.resource_id:
            print("resource_id is required for delete")
            return
        delete(FLAGS.resource_id, project_id, location)
    elif FLAGS.quicktest:
        if not FLAGS.resource_id:
            print("resource_id is required for quicktest")
            return
        session_service = VertexAiSessionService(project_id, location)
        send_message(session_service, FLAGS.resource_id, project_id, location, "Looking for inspirations around the Americas")
    else:
        print("Unknown command")


if __name__ == "__main__":
    app.run(main)
