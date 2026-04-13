import asyncio
import sys

from app.application.container import ApplicationContainer
from app.presentation import api
from app.presentation.container import PresentationContainer
import uvicorn
from fastapi import FastAPI
from loguru import logger

from app.presentation.api import router


async def build_api(container: ApplicationContainer):
    app = FastAPI()
    app.include_router(router)
    container.wire(modules=[api])
    return app


async def main():
    logger.remove()
    logger.add(
        sys.stderr, colorize=True, format="{time:HH:mm:ss} | {level} | {message}"
    )

    presentation_container = PresentationContainer()
    presentation_container.config.from_yaml("app/config.yaml", required=True)

    app = await build_api(presentation_container.application)

    api_task = asyncio.create_task(
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        ).serve()
    )
    await asyncio.gather(api_task)


if __name__ == "__main__":
    asyncio.run(main())
