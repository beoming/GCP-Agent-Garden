"""항공편 검색 API 서버"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Flight Search API", version="1.0.0")


class FlightSearchRequest(BaseModel):
    """항공편 검색 요청 모델"""
    origin: str = Field(description="출발지 도시명")
    destination: str = Field(description="도착지 도시명")
    departure_date: str = Field(description="출발일 (YYYY-MM-DD 형식)")
    return_date: Optional[str] = Field(None, description="귀국일 (YYYY-MM-DD 형식, 편도인 경우 None)")


class AirportEvent(BaseModel):
    """공항 이벤트"""
    city_name: str
    airport_code: str
    timestamp: str


class Flight(BaseModel):
    """항공편 정보"""
    flight_number: str
    departure: AirportEvent
    arrival: AirportEvent
    airlines: list[str]
    airline_logo: str
    price_in_usd: int
    number_of_stops: int


class FlightSearchResponse(BaseModel):
    """항공편 검색 응답 모델"""
    flights: list[Flight]


def get_airport_code(city: str) -> str:
    """도시명으로부터 공항 코드를 반환 (간단한 매핑)"""
    airport_map = {
        "San Diego": "SAN",
        "Seattle": "SEA",
        "New York": "JFK",
        "Los Angeles": "LAX",
        "Chicago": "ORD",
        "Miami": "MIA",
        "San Francisco": "SFO",
        "Boston": "BOS",
        "Washington": "DCA",
        "Atlanta": "ATL",
        "Lima": "LIM",
        "Cusco": "CUZ",
        "Peru": "LIM",
    }
    return airport_map.get(city, "XXX")


def get_airline_logo(airline: str) -> str:
    """항공사명으로부터 로고 경로 반환"""
    airline_map = {
        "American Airlines": "/images/american.png",
        "United Airlines": "/images/united.png",
        "Delta Air Lines": "/images/delta1.jpg",
        "Alaska Airlines": "/images/alaska.png",
        "Southwest Airlines": "/images/southwest.png",
    }
    return airline_map.get(airline, "/images/airplane.png")


@app.post("/search", response_model=FlightSearchResponse)
async def search_flights(request: FlightSearchRequest):
    """
    항공편 검색 API
    
    실제 운영 환경에서는 외부 항공편 검색 API (예: Amadeus, Sabre 등)를 호출합니다.
    현재는 데모용으로 샘플 데이터를 반환합니다.
    """
    try:
        # 날짜 파싱
        departure_dt = datetime.strptime(request.departure_date, "%Y-%m-%d")
        
        # 출발지/도착지 공항 코드
        origin_code = get_airport_code(request.origin)
        dest_code = get_airport_code(request.destination)
        
        # 샘플 항공편 데이터 생성
        flights = []
        
        # 편도 항공편들 (최대 4개)
        airlines_list = [
            ["American Airlines"],
            ["United Airlines"],
            ["Delta Air Lines"],
            ["Alaska Airlines"],
        ]
        
        prices = [450, 520, 380, 490]
        stops = [0, 1, 0, 0]
        flight_numbers = ["AA1234", "UA5678", "DL9012", "AS3456"]
        departure_times = ["08:00", "14:30", "06:45", "19:20"]
        arrival_times = ["10:30", "17:15", "09:20", "22:05"]
        
        for i in range(min(4, len(airlines_list))):
            # 출발 시간 계산
            departure_timestamp = f"{request.departure_date}T{departure_times[i]}:00"
            
            # 도착 시간 계산 (비행 시간 고려)
            arrival_timestamp = f"{request.departure_date}T{arrival_times[i]}:00"
            
            flight = Flight(
                flight_number=flight_numbers[i],
                departure=AirportEvent(
                    city_name=request.origin,
                    airport_code=origin_code,
                    timestamp=departure_timestamp,
                ),
                arrival=AirportEvent(
                    city_name=request.destination,
                    airport_code=dest_code,
                    timestamp=arrival_timestamp,
                ),
                airlines=airlines_list[i],
                airline_logo=get_airline_logo(airlines_list[i][0]),
                price_in_usd=prices[i],
                number_of_stops=stops[i],
            )
            flights.append(flight)
        
        # 왕복인 경우 귀국 항공편도 추가
        if request.return_date:
            return_dt = datetime.strptime(request.return_date, "%Y-%m-%d")
            return_flight_numbers = ["AA1235", "UA5679", "DL9013", "AS3457"]
            return_departure_times = ["16:00", "11:30", "13:45", "08:20"]
            return_arrival_times = ["18:30", "14:15", "16:20", "10:05"]
            
            for i in range(min(4, len(airlines_list))):
                return_departure_timestamp = f"{request.return_date}T{return_departure_times[i]}:00"
                return_arrival_timestamp = f"{request.return_date}T{return_arrival_times[i]}:00"
                
                return_flight = Flight(
                    flight_number=return_flight_numbers[i],
                    departure=AirportEvent(
                        city_name=request.destination,
                        airport_code=dest_code,
                        timestamp=return_departure_timestamp,
                    ),
                    arrival=AirportEvent(
                        city_name=request.origin,
                        airport_code=origin_code,
                        timestamp=return_arrival_timestamp,
                    ),
                    airlines=airlines_list[i],
                    airline_logo=get_airline_logo(airlines_list[i][0]),
                    price_in_usd=prices[i],
                    number_of_stops=stops[i],
                )
                flights.append(return_flight)
        
        return FlightSearchResponse(flights=flights)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "flight_search_api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

