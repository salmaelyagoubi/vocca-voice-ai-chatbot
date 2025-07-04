from datetime import datetime, timedelta
from loguru import logger
from mongo_loader import DataEnricher

async def confirm_appointment(function_name, tool_call_id, args, llm, context, result_callback):
    try:
        department = args["department"]
        day = args["day"]
        time_str = args["time"]

        enricher = DataEnricher()
        await enricher.connect_to_db()

        # Calculate the next date matching the requested day
        today = datetime.now()
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if day not in days_of_week:
            raise ValueError(f"Invalid day: {day}")

        target_weekday = days_of_week.index(day)
        days_ahead = (target_weekday - today.weekday() + 7) % 7
        next_day_date = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        # Register the booking
        appointment_id = await enricher.register_booking(department, next_day_date, time_str)

        logger.info(f"Appointment saved. ID: {appointment_id}")
        await result_callback([
            {
                "role": "system",
                "content": f"The appointment has been confirmed for {department} on {next_day_date} at {time_str}. Thank you!"
            }
        ])

    except Exception as e:
        logger.error(f"Failed to confirm appointment: {e}")
        await result_callback([
            {
                "role": "system",
                "content": "Sorry, something went wrong. Could you please confirm the department, day, and time again?"
            }
        ])
