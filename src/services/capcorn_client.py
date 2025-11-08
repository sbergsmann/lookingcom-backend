"""CapCorn API client for making requests to the external API"""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime

from src.core.config import get_settings
from src.schemas.room_availability import (
    RoomAvailabilityRequest,
    RoomAvailabilityResponse,
    MemberResponse,
    RoomResponse,
    ChildResponse,
    RoomOption,
)
from src.schemas.reservation import ReservationRequest, ReservationResponse


class CapCornClient:
    """Client for interacting with CapCorn API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.capcorn_base_url
        self.timeout = 30.0
    
    def _build_room_availability_xml(self, request: RoomAvailabilityRequest) -> str:
        """Build XML for room availability request"""
        root = ET.Element("room_availability")
        
        # Language
        ET.SubElement(root, "language").text = str(request.language)
        
        # Members
        members = ET.SubElement(root, "members")
        member = ET.SubElement(members, "member")
        member.set("hotel_id", request.hotel_id)
        
        # Dates
        ET.SubElement(root, "arrival").text = request.arrival.isoformat()
        ET.SubElement(root, "departure").text = request.departure.isoformat()
        
        # Rooms
        rooms = ET.SubElement(root, "rooms")
        for room in request.rooms:
            room_elem = ET.SubElement(rooms, "room")
            room_elem.set("adults", str(room.adults))
            
            for child in room.children:
                child_elem = ET.SubElement(room_elem, "child")
                child_elem.set("age", str(child.age))
        
        return ET.tostring(root, encoding="unicode")
    
    def _parse_room_availability_response(self, xml_str: str) -> RoomAvailabilityResponse:
        """Parse XML response into Pydantic model"""
        root = ET.fromstring(xml_str)
        
        # Handle XML namespace
        ns = {"ns": "http://capcorn.at/"}
        
        members_data = []
        for member_elem in root.findall(".//ns:member", ns) or root.findall(".//member"):
            hotel_id = member_elem.get("hotel_id", "")
            
            rooms_data = []
            for room_elem in member_elem.findall(".//ns:room", ns) or member_elem.findall(".//room"):
                # Parse room details
                arrival = room_elem.findtext("ns:arrival", default="", namespaces=ns) or room_elem.findtext("arrival", "")
                departure = room_elem.findtext("ns:departure", default="", namespaces=ns) or room_elem.findtext("departure", "")
                adults = int(room_elem.findtext("ns:adults", default="0", namespaces=ns) or room_elem.findtext("adults", "0"))
                
                # Parse children
                children_data = []
                children_elem = room_elem.find("ns:children", ns) or room_elem.find("children")
                if children_elem is not None:
                    for child_elem in children_elem.findall("ns:child", ns) or children_elem.findall("child"):
                        age = int(child_elem.get("age", 0))
                        children_data.append(ChildResponse(age=age))
                
                # Parse options
                options_data = []
                options_elem = room_elem.find("ns:options", ns) or room_elem.find("options")
                if options_elem is not None:
                    for option_elem in options_elem.findall("ns:option", ns) or options_elem.findall("option"):
                        option = RoomOption(
                            catc=option_elem.findtext("ns:catc", default="", namespaces=ns) or option_elem.findtext("catc", ""),
                            type=option_elem.findtext("ns:type", default="", namespaces=ns) or option_elem.findtext("type", ""),
                            description=option_elem.findtext("ns:description", default="", namespaces=ns) or option_elem.findtext("description", ""),
                            size=int(option_elem.findtext("ns:size", default="0", namespaces=ns) or option_elem.findtext("size", "0")),
                            price=float(option_elem.findtext("ns:price", default="0", namespaces=ns) or option_elem.findtext("price", "0")),
                            price_per_person=float(option_elem.findtext("ns:price_per_person", default="0", namespaces=ns) or option_elem.findtext("price_per_person", "0")),
                            price_per_adult=float(option_elem.findtext("ns:price_per_adult", default="0", namespaces=ns) or option_elem.findtext("price_per_adult", "0")),
                            price_per_night=float(option_elem.findtext("ns:price_per_night", default="0", namespaces=ns) or option_elem.findtext("price_per_night", "0")),
                            board=int(option_elem.findtext("ns:board", default="1", namespaces=ns) or option_elem.findtext("board", "1")),
                            room_type=int(option_elem.findtext("ns:room_type", default="1", namespaces=ns) or option_elem.findtext("room_type", "1")),
                        )
                        options_data.append(option)
                
                rooms_data.append(RoomResponse(
                    arrival=arrival,
                    departure=departure,
                    adults=adults,
                    children=children_data,
                    options=options_data,
                ))
            
            members_data.append(MemberResponse(
                hotel_id=hotel_id,
                rooms=rooms_data,
            ))
        
        return RoomAvailabilityResponse(members=members_data)
    
    async def search_room_availability(
        self, request: RoomAvailabilityRequest
    ) -> RoomAvailabilityResponse:
        """Search for available rooms"""
        url = f"{self.base_url}/RoomAvailability"
        params = {
            "user": self.settings.capcorn_user,
            "password": self.settings.capcorn_password,
            "system": self.settings.capcorn_system,
        }
        
        xml_body = self._build_room_availability_xml(request)
        headers = {"Content-Type": "application/xml"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, params=params, content=xml_body, headers=headers)
            response.raise_for_status()
            
            return self._parse_room_availability_response(response.text)
    
    def _build_reservation_xml(self, request: ReservationRequest) -> str:
        """Build XML for reservation request (OTA format)"""
        root = ET.Element("OTA_HotelResNotifRQ")
        root.set("xmlns", "http://www.opentravel.org/OTA/2003/05")
        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("Version", "1")
        
        # POS
        pos = ET.SubElement(root, "POS")
        source = ET.SubElement(pos, "Source")
        source.set("AgentDutyCode", request.source)
        
        # HotelReservations
        hotel_reservations = ET.SubElement(root, "HotelReservations")
        hotel_reservation = ET.SubElement(hotel_reservations, "HotelReservation")
        hotel_reservation.set("CreateDateTime", datetime.now().isoformat())
        hotel_reservation.set("ResStatus", "Book")
        
        # RoomStays
        room_stays = ET.SubElement(hotel_reservation, "RoomStays")
        room_stay = ET.SubElement(room_stays, "RoomStay")
        
        # RoomTypes
        room_types = ET.SubElement(room_stay, "RoomTypes")
        room_type = ET.SubElement(room_types, "RoomType")
        room_type.set("NumberOfUnits", str(request.number_of_units))
        room_type.set("RoomTypeCode", request.room_type_code)
        
        # RatePlans
        rate_plans = ET.SubElement(room_stay, "RatePlans")
        rate_plan = ET.SubElement(rate_plans, "RatePlan")
        meals_included = ET.SubElement(rate_plan, "MealsIncluded")
        meals_included.set("MealPlanCodes", str(request.meal_plan.value))
        
        # GuestCounts
        guest_counts = ET.SubElement(room_stay, "GuestCounts")
        guest_counts.set("IsPerRoom", "true")
        for guest_count in request.guest_counts:
            guest_count_elem = ET.SubElement(guest_counts, "GuestCount")
            guest_count_elem.set("AgeQualifyingCode", str(guest_count.age_qualifying_code))
            guest_count_elem.set("Count", str(guest_count.count))
            if guest_count.age is not None:
                guest_count_elem.set("Age", str(guest_count.age))
        
        # TimeSpan
        time_span = ET.SubElement(room_stay, "TimeSpan")
        time_span.set("Start", request.arrival.isoformat())
        time_span.set("End", request.departure.isoformat())
        
        # Total
        total = ET.SubElement(room_stay, "Total")
        total.set("AmountAfterTax", f"{request.total_amount:.2f}")
        total.set("CurrencyCode", "EUR")
        
        # BasicPropertyInfo
        basic_property = ET.SubElement(room_stay, "BasicPropertyInfo")
        basic_property.set("HotelCode", request.hotel_id)
        
        # Services
        if request.services:
            services = ET.SubElement(hotel_reservation, "Services")
            for service in request.services:
                service_elem = ET.SubElement(services, "Service")
                service_elem.set("Quantity", str(service.quantity))
                
                service_details = ET.SubElement(service_elem, "ServiceDetails")
                service_desc = ET.SubElement(service_details, "ServiceDescription")
                service_desc.set("Name", service.name)
                
                price = ET.SubElement(service_elem, "Price")
                base = ET.SubElement(price, "Base")
                base.set("AmountAfterTax", f"{service.amount_after_tax:.2f}")
        
        # ResGuests
        res_guests = ET.SubElement(hotel_reservation, "ResGuests")
        res_guest = ET.SubElement(res_guests, "ResGuest")
        
        profiles = ET.SubElement(res_guest, "Profiles")
        profile_info = ET.SubElement(profiles, "ProfileInfo")
        profile = ET.SubElement(profile_info, "Profile")
        
        customer = ET.SubElement(profile, "Customer")
        customer.set("Language", "de")
        
        person_name = ET.SubElement(customer, "PersonName")
        ET.SubElement(person_name, "NamePrefix").text = request.guest.name_prefix
        ET.SubElement(person_name, "GivenName").text = request.guest.given_name
        ET.SubElement(person_name, "Surname").text = request.guest.surname
        
        telephone = ET.SubElement(customer, "Telephone")
        telephone.set("PhoneNumber", request.guest.phone_number)
        
        ET.SubElement(customer, "Email").text = request.guest.email
        
        address = ET.SubElement(customer, "Address")
        ET.SubElement(address, "AddressLine").text = request.guest.address.address_line
        ET.SubElement(address, "CityName").text = request.guest.address.city_name
        ET.SubElement(address, "PostalCode").text = request.guest.address.postal_code
        country_name = ET.SubElement(address, "CountryName")
        country_name.set("Code", request.guest.address.country_code)
        
        # Comments
        if request.booking_comment:
            comments = ET.SubElement(res_guest, "Comments")
            comment = ET.SubElement(comments, "Comment")
            ET.SubElement(comment, "ListItem").text = request.booking_comment
        
        # ResGlobalInfo
        res_global_info = ET.SubElement(hotel_reservation, "ResGlobalInfo")
        hotel_reservation_ids = ET.SubElement(res_global_info, "HotelReservationIDs")
        hotel_reservation_id = ET.SubElement(hotel_reservation_ids, "HotelReservationID")
        hotel_reservation_id.set("ResID_Value", request.reservation_id)
        hotel_reservation_id.set("ResID_Source", request.source)
        
        return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode")
    
    async def create_reservation(self, request: ReservationRequest) -> ReservationResponse:
        """Create a new reservation"""
        url = f"{self.base_url}/OTA_HotelResNotifRQ"
        params = {
            "hotelId": request.hotel_id,
            "pin": self.settings.capcorn_pin,
        }
        
        xml_body = self._build_reservation_xml(request)
        headers = {"Content-Type": "application/xml"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, params=params, content=xml_body, headers=headers)
                response.raise_for_status()
                
                return ReservationResponse(
                    success=True,
                    message="Reservation created successfully",
                    reservation_id=request.reservation_id,
                )
        except httpx.HTTPStatusError as e:
            return ReservationResponse(
                success=False,
                message=f"Failed to create reservation: {e.response.status_code}",
                errors=[e.response.text],
            )
        except Exception as e:
            return ReservationResponse(
                success=False,
                message=f"Failed to create reservation: {str(e)}",
                errors=[str(e)],
            )
