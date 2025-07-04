import asyncio
import os
import sys
import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.frames.frames import EndFrame
from setup_services import setup_services
from sprite_utils import get_static_and_talking_frames
from event_handlers import register_event_handlers
from confirm_logic import confirm_appointment

class BotRunner:
    def __init__(self, transport, tts, llm, enricher, quiet_frame, talking_frame):
        self.transport = transport
        self.tts = tts
        self.llm = llm
        self.enricher = enricher
        self.quiet_frame = quiet_frame
        self.talking_frame = talking_frame

    async def run(self):
        context = OpenAILLMContext(messages=[])
        context_agg = self.llm.create_context_aggregator(context)

        departments = await self.enricher.get_available_departments()
        open_schedule = await self.enricher.get_open_schedule()
        booked_slots = await self.enricher.get_booked_slots_per_department()

        self.llm.register_function("confirm_appointment", confirm_appointment)

        context.add_message(
            {
                "role": "system",
                "content": (
                    "You are a french MedAssist that understand french weekdays, that talks only in french and pronounces the words and the numbers and the hours in french correctly. "
                    "You are MedAssist, a helpful and professional virtual assistant for a medical center. "
                    "Your role is to guide patients in booking medical appointments clearly and efficiently. "
                    "Confirm each step along the way, and always ensure final confirmation before booking. "
                    "Only use the information provided—if something falls outside the scope of available departments or schedules, respond with 'I do not know' and refocus the conversation. "
                    "Gather appointment details incrementally: department name, preferred day, and preferred time. "
                    "Avoid overwhelming the user—keep communication simple, friendly, and conversational. "
                    "Do not read or interpret special characters or symbols. "
                    f"Available departments: {', '.join(departments)}. "
                    f"The {open_schedule} is the open schedules for the departments, make sure to choose from these. "
                    f"These times are time slots that are already booked per department, {booked_slots}, remember to exclude these slots for the available slots and let the user know if applicable."
                    f"If you were to give the user time slots for availabilites, always use ranges describing the available times from the first and to. This is very important not to be verbose in this matter and be prcise"
                    f"Always give the available times to the user using ranges and make it easy for the user to choose, make it as humanly as possible. Make sure to use the correct transitions between sentences and words"
                    f"Remember to always give the user the available time slots for the chosen department, if a time slot is not availble per department, let the user know since it would be already booked."
                    f"Make sure to confirm with the user before going ahead and booking the appointment."
                )
            }
        )

        context.set_tools([{
            "type": "function",
            "function": {
                "name": "confirm_appointment",
                "description": "Confirm appointment with department, day, and time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "department": {"type": "string"},
                        "day": {"type": "string"},
                        "time": {"type": "string"}
                    },
                    "required": ["department", "day", "time"]
                }
            }
        }])

        rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

        pipeline = Pipeline([
            self.transport.input(),
            rtvi,
            context_agg.user(),
            self.llm,
            self.tts,
            self.transport.output(),
            context_agg.assistant(),
        ])

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
            observers=[RTVIObserver(rtvi)]
        )

        await task.queue_frame(self.quiet_frame)
        register_event_handlers(rtvi, self.transport, task, context_agg)

        runner = PipelineRunner()
        await runner.run(task)


async def main():
    load_dotenv(override=True)
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG")

    asset_dir = os.path.join(os.path.dirname(__file__), "assets")
    quiet_frame, talking_frame = get_static_and_talking_frames(asset_dir)

    async with aiohttp.ClientSession() as session:
        transport, tts, llm, enricher = await setup_services(session)
        bot = BotRunner(transport, tts, llm, enricher, quiet_frame, talking_frame)
        await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
