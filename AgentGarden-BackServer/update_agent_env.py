#!/usr/bin/env python3
"""Agent Engine 환경 변수 업데이트 스크립트"""

import os
from vertexai import agent_engines

# 프로젝트 설정
PROJECT_ID = "gsneotek-ncc-demo"
LOCATION = "us-central1"
RESOURCE_ID = "484511893407399936"

# 환경 변수
ENV_VARS = {
    "FLIGHT_SEARCH_API_URL": "https://flight-search-api-nelifvy57a-uc.a.run.app",
    "HOTEL_SEARCH_API_URL": "https://hotel-search-api-nelifvy57a-uc.a.run.app",
}

def main():
    """Agent Engine의 환경 변수를 업데이트합니다."""
    print(f"🔄 Agent Engine 환경 변수 업데이트 중...")
    print(f"프로젝트: {PROJECT_ID}")
    print(f"리전: {LOCATION}")
    print(f"Resource ID: {RESOURCE_ID}")
    print(f"\n환경 변수:")
    for key, value in ENV_VARS.items():
        print(f"  {key}={value}")
    
    try:
        # Agent Engine 가져오기
        remote_agent = agent_engines.get(RESOURCE_ID)
        
        # 현재 설정 확인
        print(f"\n📋 현재 Agent Engine 정보:")
        print(f"  이름: {remote_agent.display_name}")
        print(f"  Resource Name: {remote_agent.resource_name}")
        
        # 환경 변수 업데이트
        # Note: Agent Engine의 환경 변수는 재배포 시에만 설정 가능할 수 있습니다.
        # 이 경우 deploy.py를 수정하여 재배포해야 합니다.
        print(f"\n⚠️  Agent Engine의 환경 변수는 재배포 시에만 설정할 수 있습니다.")
        print(f"다음 단계:")
        print(f"1. travel-concierge 프로젝트의 .env 파일에 환경 변수 추가")
        print(f"2. deploy.py 스크립트 수정하여 환경 변수 포함")
        print(f"3. Agent Engine 재배포")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print(f"\n대안: deploy.py를 수정하여 재배포하세요.")

if __name__ == "__main__":
    main()


