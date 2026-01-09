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

"""Demonstration of Travel AI Conceirge using Agent Development Kit"""

from google.adk.agents import Agent
import uuid
from travel_concierge import prompt

from travel_concierge.sub_agents.booking.agent import booking_agent
from travel_concierge.sub_agents.in_trip.agent import in_trip_agent
from travel_concierge.sub_agents.inspiration.agent import inspiration_agent
from travel_concierge.sub_agents.planning.agent import planning_agent
from travel_concierge.sub_agents.post_trip.agent import post_trip_agent
from travel_concierge.sub_agents.pre_trip.agent import pre_trip_agent

from travel_concierge.tools.memory import _load_precreated_itinerary
from travel_concierge.tools.zendesk_tool import zendesk_toolset

from travel_concierge.tracing import instrument_adk_with_arize
from openinference.instrumentation import using_session

_ = instrument_adk_with_arize()


with using_session(session_id=uuid.uuid4()):
    # Zendesk toolset을 tools 리스트에 추가 (ApplicationIntegrationToolset은 직접 전달)
    tools_list = []
    if zendesk_toolset:
        tools_list.append(zendesk_toolset)
    
    root_agent = Agent(
        model="gemini-2.0-flash-001",
        name="root_agent",
        description="A Travel Conceirge using the services of multiple sub-agents",
        instruction=prompt.ROOT_AGENT_INSTR,
        sub_agents=[
            inspiration_agent,
            planning_agent,
            booking_agent,
            pre_trip_agent,
            in_trip_agent,
            post_trip_agent,
        ],
        tools=tools_list if tools_list else None,  # Zendesk toolset 추가
        before_agent_callback=_load_precreated_itinerary,
    )
