from pipecat.frames.frames import EndFrame

def register_event_handlers(rtvi, transport, task, context_aggregator):
    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        await rtvi.set_bot_ready()
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_first_participant_joined")
    async def on_join(transport, participant):
        print(f"Participant joined: {participant}")
        await transport.capture_participant_transcription(participant["id"])

    @transport.event_handler("on_participant_left")
    async def on_leave(transport, participant, reason):
        print(f"Participant left: {participant}")
        await task.cancel()
