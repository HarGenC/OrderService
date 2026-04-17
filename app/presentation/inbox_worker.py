import asyncio

from app.application.process_inbox_events import ProcessInboxEventsUseCase


class InboxWorker:
    def __init__(self, use_case: ProcessInboxEventsUseCase):
        self._use_case = use_case

    async def run(self):
        while True:
            await self._use_case()
            await asyncio.sleep(0.01)
