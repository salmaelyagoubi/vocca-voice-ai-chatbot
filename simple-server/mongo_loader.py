import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from pipecat.frames.frames import Frame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from bson import ObjectId
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

class DataEnricher(FrameProcessor):
    """Handles the appointment booking logic with database integration."""

    def __init__(self):
        super().__init__()
        load_dotenv()
        self.db_config = {
            "MONGO_URI": f"{os.environ.get('MONGO_URI')}",
            "MONGO_DB": f"{os.environ.get('MONGO_DB')}"
        }
        self.connection = None
        self.available_days = []
        self.available_departments = []
        self.appointment_details = {}
        self.open_schedule = None
        self.get_booked_slots_sched = None
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    async def connect_to_db(self):
        try:
            client = AsyncIOMotorClient(self.db_config["MONGO_URI"],
                                        tls=True,
                                        tlsAllowInvalidCertificates=False)
            self.connection = client[self.db_config["MONGO_DB"]]
            await self.connection.command("ping")
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close_connection(self):
        self.connection = None

    async def get_available_days(self):
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        try:
            departments = self.connection["departments"]
            cursor = departments.find({"operating_hours": {"$exists": True, "$ne": []}}, {"operating_hours.day_of_week": 1})
            day_set = set()
            async for doc in cursor:
                for oh in doc.get("operating_hours", []):
                    day_set.add(oh["day_of_week"])
            ordered_days = sorted(list(day_set), key=self.days.index)
            self.available_days = ordered_days
            logger.info(f"Retrieved available days: {ordered_days}")
            return ordered_days
        except Exception as e:
            logger.error(f"Failed to retrieve available days: {e}")
            raise

    async def get_available_departments(self):
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        try:
            departments = []
            collection = self.connection["departments"]
            cursor = collection.find(
                {"operating_hours": {"$exists": True, "$ne": []}},
                {"name": 1}
            )
            async for doc in cursor:
                departments.append(doc["name"])
            self.available_departments = departments
            logger.info(f"Available departments: {departments}")
            return departments
        except Exception as e:
            logger.error(f"Failed to retrieve available departments: {e}")
            raise

    async def get_open_schedule(self):
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        try:
            departments_collection = self.connection["departments"]
            bookings_collection = self.connection["bookings"]
            cursor = departments_collection.find({"operating_hours": {"$exists": True}})
            schedule = {}
            async for department in cursor:
                name = department["name"]
                operating_hours = department.get("operating_hours", [])
                schedule[name] = {}
                for oh in operating_hours:
                    day = oh["day_of_week"]
                    start_time = datetime.strptime(oh["start_time"], "%H:%M").time()
                    end_time = datetime.strptime(oh["end_time"], "%H:%M").time()
                    today = datetime.today()
                    day_index = self.days.index(day)
                    today_index = today.weekday()
                    days_ahead = (day_index - today_index + 7) % 7
                    next_day = today + timedelta(days=days_ahead)
                    booked_cursor = bookings_collection.find({
                        "department_id": department["_id"],
                        "status": "booked",
                        "booking_time": {
                            "$gte": datetime.combine(next_day.date(), start_time),
                            "$lt": datetime.combine(next_day.date(), end_time)
                        }
                    })
                    booked_times_set = set()
                    async for booking in booked_cursor:
                        booked_times_set.add(booking["booking_time"].time())
                    current_time = start_time
                    slots = []
                    while current_time < end_time:
                        if current_time not in booked_times_set:
                            slots.append(current_time.strftime("%H:%M"))
                        current_time = (datetime.combine(today, current_time) + timedelta(minutes=30)).time()
                    schedule[name][day] = slots
            schedule_str = "Here are the available appointment slots: "
            for dept, day_slots in schedule.items():
                schedule_str += f"{dept}: "
                for day, slots in day_slots.items():
                    if slots:
                        schedule_str += f"{day} ({', '.join(slots)}), "
                schedule_str = schedule_str.rstrip(", ") + ". "
            self.open_schedule = schedule_str.rstrip()
            logger.info("Retrieved and formatted open schedule.")
            return self.open_schedule
        except Exception as e:
            logger.error(f"Failed to retrieve open schedule: {e}")
            raise

    async def get_available_times(self, day: str, department_id: ObjectId):
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        try:
            departments_collection = self.connection["departments"]
            bookings_collection = self.connection["bookings"]
            department = await departments_collection.find_one({"_id": department_id})
            if not department:
                logger.info(f"No department found with ID: {department_id}")
                return []
            matching_hours = [
                oh for oh in department.get("operating_hours", [])
                if oh["day_of_week"].lower() == day.lower()
            ]
            if not matching_hours:
                logger.info(f"No operating hours found for {day} and department ID {department_id}")
                return []
            available_times = []
            today = datetime.today()
            day_index = self.days.index(day)
            today_index = today.weekday()
            days_ahead = (day_index - today_index + 7) % 7
            target_date = today + timedelta(days=days_ahead)
            target_date_only = target_date.date()
            for hours in matching_hours:
                start = datetime.strptime(hours["start_time"], "%H:%M").time()
                end = datetime.strptime(hours["end_time"], "%H:%M").time()
                booked_cursor = bookings_collection.find({
                    "department_id": department_id,
                    "status": "confirmed",
                    "booking_time": {
                        "$gte": datetime.combine(target_date_only, start),
                        "$lt": datetime.combine(target_date_only, end)
                    }
                })
                booked_times_set = set()
                async for booking in booked_cursor:
                    booked_times_set.add(booking["booking_time"].time())
                current_time = start
                while current_time < end:
                    if current_time not in booked_times_set:
                        available_times.append(current_time.strftime("%H:%M"))
                    current_time = (datetime.combine(today, current_time) + timedelta(minutes=30)).time()
            logger.info(f"Available times for {day} and department ID {department_id}: {available_times}")
            return available_times
        except Exception as e:
            logger.error(f"Failed to retrieve available times for {day} and department ID {department_id}: {e}")
            raise

    async def get_department_id(self, department_name):
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        try:
            doc = await self.connection["departments"].find_one({"name": department_name})
            return doc["_id"] if doc else None
        except Exception as e:
            logger.error(f"Failed to retrieve department ID for {department_name}: {e}")
            raise

    async def get_booked_slots_per_department(self):
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        try:
            departments_collection = self.connection["departments"]
            bookings_collection = self.connection["bookings"]

            booked_slots = {}

            async for dept in departments_collection.find():
                department_id = dept["_id"]
                department_name = dept["name"]

                bookings_cursor = bookings_collection.find({
                    "department_id": department_id,
                    "status": {"$in": ["booked", "confirmed"]}
                })

                slots = []
                async for booking in bookings_cursor:
                    time = booking.get("booking_time")
                    if isinstance(time, datetime):
                        slots.append(time.strftime("%Y-%m-%d %H:%M:%S"))

                booked_slots[department_name] = slots

            logger.info("Booked slots retrieved per department.")
            return booked_slots

        except Exception as e:
            logger.error(f"Error retrieving booked slots: {e}")
            raise

    async def check_availability(self, department_id, booking_time):
        if not self.connection:
            raise ValueError("Database connection is not established.")
        try:
            if isinstance(booking_time, str):
                booking_time = datetime.strptime(booking_time, "%Y-%m-%d %H:%M:%S")
            collection = self.connection["bookings"]
            count = await collection.count_documents({
                "department_id": department_id,
                "booking_time": booking_time,
                "status": "booked"
            })
            return count == 0
        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            raise

    async def book_appointment(self, department_id, user_id, booking_time):
        if not self.connection:
            raise ValueError("Database connection is not established.")
        try:
            if isinstance(booking_time, str):
                booking_time = datetime.strptime(booking_time, "%Y-%m-%d %H:%M:%S")
            collection = self.connection["bookings"]
            result = await collection.insert_one({
                "department_id": department_id,
                "user_id": user_id,
                "booking_time": booking_time,
                "status": "booked"
            })
            logger.info(f"Appointment booked successfully. Appointment ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to book appointment: {e}")
            raise

    def _extract_appointment_info(self, text: str) -> Optional[Dict[str, Any]]:
        pattern = r"Appointment for (?P<department>.+) on (?P<day>.+) at (?P<time>.+)"
        match = re.match(pattern, text)
        if match:
            return match.groupdict()
        return None
    
    async def register_booking(self, department_name: str, date_str: str, time_str: str):
        if self.connection is None:
            raise ValueError("Database connection is not established.")
        try:
            departments_collection = self.connection["departments"]
            bookings_collection = self.connection["bookings"]

            department = await departments_collection.find_one({"name": department_name})
            if not department:
                raise ValueError(f"Department '{department_name}' not found.")

            booking_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

            booking = {
                "department_id": department["_id"],
                "booking_time": booking_time,
                "status": "booked",
                "created_at": datetime.utcnow()
            }

            result = await bookings_collection.insert_one(booking)
            logger.info(f"Booking registered with ID {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to register booking: {e}")
            raise

    async def _handle_appointment(self, appointment_info: Dict[str, Any]):
        department = appointment_info.get("department")
        day = appointment_info.get("day")
        time = appointment_info.get("time")
        if not department or not day or not time:
            logger.error("Incomplete appointment information.")
            return
        try:
            department_id = await self.get_department_id(department)
            if not department_id:
                logger.error(f"Department not found: {department}")
                return
            booking_time = datetime.strptime(f"{day} {time}", "%Y-%m-%d %H:%M:%S")
            is_available = await self.check_availability(department_id, booking_time)
            if not is_available:
                logger.warning(f"Time slot not available: {booking_time}")
                return
            user_id = 1
            appointment_id = await self.book_appointment(department_id, user_id, booking_time)
            logger.info(f"Appointment booked successfully. ID: {appointment_id}")
        except Exception as e:
            logger.error(f"Failed to handle appointment: {e}")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        try:
            await super().process_frame(frame, direction)
            if direction == FrameDirection.OUTBOUND:
                if hasattr(frame, 'text') and frame.text:
                    appointment_info = self._extract_appointment_info(frame.text)
                    if appointment_info:
                        logger.info(f"Appointment detected: {appointment_info}")
                        await self._handle_appointment(appointment_info)
        except Exception as e:
            logger.error(f"Error during frame processing: {e}")
        await self.push_frame(frame, direction)
