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

"""Zendesk connector tool for Travel Concierge."""

import os

from dotenv import load_dotenv
from google.adk.tools.application_integration_tool.application_integration_toolset import (
    ApplicationIntegrationToolset,
)

load_dotenv()

# Zendesk Connection 설정
# - 프로젝트: GOOGLE_CLOUD_PROJECT (Agent Engine와 동일 프로젝트 사용)
# - 리전: Zendesk 커넥터가 배포된 리전(us-east4)을 사용
# - 커넥션 이름: ncczendesk
ZENDESK_CONNECTION_PROJECT_ID = os.getenv(
    "GOOGLE_CLOUD_PROJECT", "gsneotek-ncc-demo"
)

# Zendesk 커넥터 리전은 Agent Engine 리전(us-central1)과 달라도 됩니다.
# 커넥터가 실제로 배포된 리전(us-east4)을 사용해야 합니다.
ZENDESK_CONNECTION_REGION = os.getenv("ZENDESK_CONNECTION_REGION", "us-east4")

# Cloud Console에서 확인한 실제 Connection ID: ncczendesk
ZENDESK_CONNECTION_NAME = os.getenv("ZENDESK_CONNECTION_NAME", "ncczendesk")

TOOL_INSTR = """
**Tool Definition: Zendesk Connector via Application Integration**

This tool interacts with Zendesk Support using an Application Integration Connector.
It supports GET, LIST, CREATE, and UPDATE operations for Tickets, Users, Organizations, and Comments.

**Ticket Operations:**

**Getting Ticket Details:**
- If the user asks to get ticket details:
  1. The user will provide a ticket ID, use that value with the GET tool to return:
     - Ticket ID (available in the "id" JSON key/value)
     - Ticket Subject (available in the "subject" JSON key/value)
     - Ticket Description (available in the "description" JSON key/value)
     - Ticket Status (available in the "status" JSON key/value)
     - Ticket Priority (available in the "priority" JSON key/value)
     - Ticket Creator (available in the "requester_id" JSON key/value)
     - Created Time (available in the "created_at" JSON key/value)
     - Updated Time (available in the "updated_at" JSON key/value)

**Listing Tickets:**
- If the user asks to list tickets:
  1. Use the LIST tool to retrieve tickets
  2. Present a summary of tickets including ID, subject, status, and priority
  3. Format the response in an easy-to-read format

**Creating Tickets:**
- If the user asks to create a ticket:
  1. Collect minimal information from the user:
     - Subject (required)
     - Description (required)
     - Priority (optional, default to "normal")
     - Type (optional, default to "question")
  2. Before calling the tool, present the summarized details to the user
  3. Ask for explicit confirmation to proceed with creation
  4. After creation, provide the ticket ID for tracking

**Updating Tickets:**
- If the user asks to update a ticket:
  1. Collect the ticket ID and the fields to update
  2. Confirm the changes before proceeding
  3. Use the UPDATE tool to modify the ticket

**Adding Comments:**
- If the user asks to add a comment to a ticket:
  1. Collect the ticket ID and comment text
  2. Specify if the comment is public or private
  3. Use the appropriate tool to add the comment

**User and Organization Operations:**
- If the user asks about user or organization details:
  1. Use the GET tool with the provided ID
  2. Present relevant information in a readable format

**Best Practices:**
- Always confirm before creating or updating tickets
- Provide clear ticket IDs for reference
- Format responses in a user-friendly manner
- Handle errors gracefully and inform the user
"""

# Zendesk Toolset 생성
# Note: Zendesk는 API Token 인증을 사용하므로 auth_credential은 필요 없을 수 있습니다.
# Connection에 이미 인증 정보가 저장되어 있으므로, connection만 지정하면 됩니다.
try:
    zendesk_toolset = ApplicationIntegrationToolset(
        project=ZENDESK_CONNECTION_PROJECT_ID,
        location=ZENDESK_CONNECTION_REGION,
        connection=ZENDESK_CONNECTION_NAME,
        entity_operations={
            "Tickets": ["GET", "LIST", "CREATE", "UPDATE"],
            "Users": ["GET", "LIST", "CREATE", "UPDATE"],
            "Ticket Comments": ["GET", "LIST", "CREATE"],  # 문서에서 "Ticket Comments"로 명시
        },
        tool_name_prefix="zendesk",
        tool_instructions=TOOL_INSTR,
    )
except Exception as e:
    import warnings
    warnings.warn(f"Zendesk toolset 초기화 실패: {e}. Zendesk 기능이 비활성화됩니다.")
    zendesk_toolset = None

