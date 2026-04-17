import asyncio
import sys

from app.application.container import ApplicationContainer
from app.presentation import api
from app.presentation.inbox_worker import InboxWorker
from app.presentation.container import PresentationContainer
import uvicorn
from fastapi import FastAPI
from loguru import logger
from dotenv import load_dotenv

from app.presentation.api import router
from app.presentation.kafka_consumer_worker import KafkaConsumerWorker
from app.presentation.outbox_worker import OutboxWorker


async def build_api(container: ApplicationContainer):
    app = FastAPI()
    app.include_router(router)
    container.wire(modules=[api])
    return app


async def main():
    load_dotenv()
    logger.remove()
    logger.add(
        sys.stderr, colorize=True, format="{time:HH:mm:ss} | {level} | {message}"
    )

    presentation_container = PresentationContainer()
    presentation_container.config.from_yaml("app/config.yaml", required=True)

    app = await build_api(presentation_container.application)
    outbox_worker: OutboxWorker = presentation_container.outbox_worker()
    kafka_consumer_worker: KafkaConsumerWorker = (
        presentation_container.kafka_consumer_worker()
    )
    inbox_worker: InboxWorker = presentation_container.inbox_worker()

    api_task = asyncio.create_task(
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        ).serve()
    )
    outbox_worker_task = asyncio.create_task(outbox_worker.run())
    kafka_consumer_worker_task = asyncio.create_task(kafka_consumer_worker.run())
    inbox_worker_task = asyncio.create_task(inbox_worker.run())
    await asyncio.gather(
        api_task, outbox_worker_task, kafka_consumer_worker_task, inbox_worker_task
    )


if __name__ == "__main__":
    asyncio.run(main())
