import os
from dotenv import load_dotenv
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.openai.llm import OpenAILLMService
from mongo_loader import DataEnricher
from pipecat.transports.services.daily import DailyTransport, DailyParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from runner import configure

load_dotenv(override=True)

async def setup_services(session):
    room_url, token = await configure(session)

    transport = DailyTransport(
        room_url, token, "Chatbot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            video_out_enabled=True,
            video_out_width=1024,
            video_out_height=576,
            vad_analyzer=SileroVADAnalyzer(),
            transcription_enabled=True,
        )
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id=os.getenv("CARTESIA_VOICE_ID")
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    enricher = DataEnricher()
    await enricher.connect_to_db()

    return transport, tts, llm, enricher
