"""
Offline Hotel Module

Manages hotel properties, rooms, rates, contracts, and inventory.
"""

from app.hotels.models import (
    Hotel, HotelCategory, RoomType, RoomAmenity, HotelAmenity,
    MealPlan, RateType, HotelRoom, HotelRate, HotelContract,
    RoomInventory, HotelImage, HotelEnquiry, OfflineHotelBooking,
    HotelStatus, ContractStatus, BookingStatus
)
from app.hotels.schemas import (
    HotelCreate, HotelUpdate, HotelResponse, HotelDetail, HotelListResponse,
    HotelCategoryCreate, HotelCategoryResponse,
    RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse,
    HotelRoomCreate, HotelRoomUpdate, HotelRoomResponse,
    HotelRateCreate, HotelRateUpdate, HotelRateResponse,
    HotelContractCreate, HotelContractUpdate, HotelContractResponse,
    RoomInventoryUpdate, RoomInventoryResponse,
    HotelSearchParams, HotelSearchResponse,
    BookingCreate, BookingUpdate, BookingResponse
)
from app.hotels.services import HotelService, HotelInventoryService
from app.hotels.api import router

__all__ = [
    # Models
    "Hotel", "HotelCategory", "RoomType", "RoomAmenity", "HotelAmenity",
    "MealPlan", "RateType", "HotelRoom", "HotelRate", "HotelContract",
    "RoomInventory", "HotelImage", "HotelEnquiry", "OfflineHotelBooking",
    "HotelStatus", "ContractStatus", "BookingStatus",
    # Schemas
    "HotelCreate", "HotelUpdate", "HotelResponse", "HotelDetail", "HotelListResponse",
    "HotelCategoryCreate", "HotelCategoryResponse",
    "RoomTypeCreate", "RoomTypeUpdate", "RoomTypeResponse",
    "HotelRoomCreate", "HotelRoomUpdate", "HotelRoomResponse",
    "HotelRateCreate", "HotelRateUpdate", "HotelRateResponse",
    "HotelContractCreate", "HotelContractUpdate", "HotelContractResponse",
    "RoomInventoryUpdate", "RoomInventoryResponse",
    "HotelSearchParams", "HotelSearchResponse",
    "BookingCreate", "BookingUpdate", "BookingResponse",
    # Services
    "HotelService", "HotelInventoryService",
    # Router
    "router"
]
