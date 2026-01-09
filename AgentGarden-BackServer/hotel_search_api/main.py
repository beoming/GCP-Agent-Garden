"""호텔 검색 API 서버"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Hotel Search API", version="1.0.0")


class HotelSearchRequest(BaseModel):
    """호텔 검색 요청 모델"""
    location: str = Field(description="호텔 위치 (도시명)")
    check_in_date: str = Field(description="체크인 날짜 (YYYY-MM-DD 형식)")
    check_out_date: str = Field(description="체크아웃 날짜 (YYYY-MM-DD 형식)")


class Hotel(BaseModel):
    """호텔 정보"""
    name: str
    address: str
    check_in_time: str
    check_out_time: str
    thumbnail: str
    price: int


class HotelSearchResponse(BaseModel):
    """호텔 검색 응답 모델"""
    hotels: list[Hotel]


def get_hotel_thumbnail(hotel_name: str) -> str:
    """호텔명으로부터 썸네일 경로 반환"""
    name_lower = hotel_name.lower()
    if "hilton" in name_lower:
        return "/src/images/hilton.png"
    elif "marriott" in name_lower or "mariott" in name_lower:
        return "/src/images/mariott.png"
    elif "conrad" in name_lower:
        return "/src/images/conrad.jpg"
    elif "hyatt" in name_lower:
        return "/src/images/hyatt.png"
    elif "westin" in name_lower:
        return "/src/images/westin.png"
    else:
        return "/src/images/hotel.png"


@app.post("/search", response_model=HotelSearchResponse)
async def search_hotels(request: HotelSearchRequest):
    """
    호텔 검색 API
    
    실제 운영 환경에서는 외부 호텔 검색 API (예: Booking.com, Expedia 등)를 호출합니다.
    현재는 데모용으로 샘플 데이터를 반환합니다.
    """
    try:
        # 날짜 파싱
        check_in_dt = datetime.strptime(request.check_in_date, "%Y-%m-%d")
        check_out_dt = datetime.strptime(request.check_out_date, "%Y-%m-%d")
        
        # 체크인/체크아웃 날짜 검증
        if check_out_dt <= check_in_dt:
            raise HTTPException(
                status_code=400,
                detail="Check-out date must be after check-in date"
            )
        
        # 숙박 일수 계산
        nights = (check_out_dt - check_in_dt).days
        
        # 샘플 호텔 데이터 생성
        hotels_data = [
            {
                "name": f"{request.location} Marriott Waterfront",
                "address": f"2100 Alaskan Wy, {request.location}, WA 98121, United States",
                "price_per_night": 250,
            },
            {
                "name": f"{request.location} Hilton Downtown",
                "address": f"1301 6th Ave, {request.location}, WA 98101, United States",
                "price_per_night": 220,
            },
            {
                "name": f"{request.location} Hyatt Regency",
                "address": f"808 Howell St, {request.location}, WA 98101, United States",
                "price_per_night": 280,
            },
            {
                "name": f"{request.location} Westin Hotel",
                "address": f"1900 5th Ave, {request.location}, WA 98101, United States",
                "price_per_night": 240,
            },
        ]
        
        hotels = []
        for hotel_data in hotels_data:
            hotel = Hotel(
                name=hotel_data["name"],
                address=hotel_data["address"],
                check_in_time="16:00",
                check_out_time="11:00",
                thumbnail=get_hotel_thumbnail(hotel_data["name"]),
                price=hotel_data["price_per_night"],
            )
            hotels.append(hotel)
        
        return HotelSearchResponse(hotels=hotels)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "hotel_search_api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)


