import asyncio

from drm_document_service.agents.pipeline import get_pipeline
from drm_document_service.config import config


async def demo_pipeline() -> None:
    pipeline = get_pipeline(config)

    await pipeline.health_check()

    test_query = "What is machine learning?"
    await pipeline.process_query(test_query)


def main() -> None:
    asyncio.run(demo_pipeline())


if __name__ == "__main__":
    main()
