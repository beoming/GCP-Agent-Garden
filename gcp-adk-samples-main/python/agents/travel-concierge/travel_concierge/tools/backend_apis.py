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

"""백엔드 API를 호출하는 FunctionTool들"""

import os
from typing import Optional

import requests
from google.adk.tools import ToolContext
from pydantic import BaseModel, Field

from travel_concierge.shared_libraries import types

# 환경 변수에서 백엔드 API URL 가져오기 (기본값: localhost)
# 함수 내부에서 읽도록 변경하여 Agent Engine 환경 변수를 제대로 읽을 수 있도록 함
def get_flight_api_url():
    """항공편 검색 API URL을 환경 변수에서 가져옵니다."""
    return os.getenv("FLIGHT_SEARCH_API_URL", "https://flight-search-api-545259847156.us-central1.run.app")

def get_hotel_api_url():
    """호텔 검색 API URL을 환경 변수에서 가져옵니다."""
    return os.getenv("HOTEL_SEARCH_API_URL", "https://hotel-search-api-545259847156.us-central1.run.app")


class FlightSearchParams(BaseModel):
    """항공편 검색 파라미터"""
    origin: str = Field(description="출발지 도시명")
    destination: str = Field(description="도착지 도시명")
    departure_date: str = Field(description="출발일 (YYYY-MM-DD 형식)")
    return_date: Optional[str] = Field(None, description="귀국일 (YYYY-MM-DD 형식, 편도인 경우 None)")


def flight_search_tool(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    tool_context: ToolContext = None,
) -> dict:
    """
    백엔드 항공편 검색 API를 호출하는 tool.
    
    Args:
        origin: 출발지 도시명
        destination: 도착지 도시명
        departure_date: 출발일 (YYYY-MM-DD 형식)
        return_date: 귀국일 (YYYY-MM-DD 형식, 편도인 경우 None)
        tool_context: ADK tool context
        
    Returns:
        FlightsSelection 형식의 딕셔너리
    """
    try:
        # 백엔드 API 호출 (런타임에 환경 변수 읽기)
        flight_api_url = get_flight_api_url()
        url = f"{flight_api_url}/search"
        payload = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
        }
        if return_date:
            payload["return_date"] = return_date
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        api_response = response.json()
        
        # API 응답을 FlightsSelection 형식으로 변환
        flights_data = api_response.get("flights", [])
        
        # FlightsSelection 객체로 변환하여 반환
        flights_selection = types.FlightsSelection(flights=flights_data)
        
        return flights_selection.model_dump()
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"항공편 검색 API 호출 실패: {str(e)}",
            "flights": []
        }
    except Exception as e:
        return {
            "error": f"항공편 검색 중 오류 발생: {str(e)}",
            "flights": []
        }


class HotelSearchParams(BaseModel):
    """호텔 검색 파라미터"""
    location: str = Field(description="호텔 위치 (도시명)")
    check_in_date: str = Field(description="체크인 날짜 (YYYY-MM-DD 형식)")
    check_out_date: str = Field(description="체크아웃 날짜 (YYYY-MM-DD 형식)")


def hotel_search_tool(
    location: str,
    check_in_date: str,
    check_out_date: str,
    tool_context: ToolContext = None,
) -> dict:
    """
    백엔드 호텔 검색 API를 호출하는 tool.
    
    Args:
        location: 호텔 위치 (도시명)
        check_in_date: 체크인 날짜 (YYYY-MM-DD 형식)
        check_out_date: 체크아웃 날짜 (YYYY-MM-DD 형식)
        tool_context: ADK tool context
        
    Returns:
        HotelsSelection 형식의 딕셔너리
    """
    try:
        # 백엔드 API 호출 (런타임에 환경 변수 읽기)
        hotel_api_url = get_hotel_api_url()
        url = f"{hotel_api_url}/search"
        payload = {
            "location": location,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        api_response = response.json()
        
        # API 응답을 HotelsSelection 형식으로 변환
        hotels_data = api_response.get("hotels", [])
        
        # HotelsSelection 객체로 변환하여 반환
        hotels_selection = types.HotelsSelection(hotels=hotels_data)
        
        return hotels_selection.model_dump()
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"호텔 검색 API 호출 실패: {str(e)}",
            "hotels": []
        }
    except Exception as e:
        return {
            "error": f"호텔 검색 중 오류 발생: {str(e)}",
            "hotels": []
        }


