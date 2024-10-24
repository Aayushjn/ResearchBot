import asyncio
import logging
from logging.config import dictConfig
from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv

import llm
from researcher import perform_research
from writer import write_paper


async def main():
    logger = logging.getLogger("researchbot")

    topic = input("Topic: ")

    research_dir = Path.cwd().joinpath("research").joinpath(topic)
    research_dir.joinpath("papers").mkdir(parents=True, exist_ok=True)
    research_dir.joinpath("notes").mkdir(parents=True, exist_ok=True)

    researcher = llm.create_llm()
    logger.info("Researcher Initialized!")
    await perform_research(researcher, topic=topic)

    writer = llm.create_llm()
    logger.info("Writer Initialized!")
    await write_paper(writer, topic=topic)


load_dotenv(find_dotenv())
dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "researchbot": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
)
asyncio.run(main())
