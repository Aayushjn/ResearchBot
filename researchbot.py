import asyncio
from logging.config import dictConfig
from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv

from researcher import Researcher
from reviewer import Reviewer
from writer import Writer


async def main():
    topic = input("Topic: ").title()

    research_dir = Path.cwd().joinpath("research").joinpath(topic)
    research_dir.joinpath("papers").mkdir(parents=True, exist_ok=True)
    research_dir.joinpath("notes").mkdir(parents=True, exist_ok=True)
    research_dir.joinpath("output").mkdir(parents=True, exist_ok=True)

    researcher = Researcher(topic=topic, research_dir=research_dir)
    await researcher.perform_research()

    uploaded_files = list(researcher.uploaded_papers.values())

    writer = Writer(topic=topic, research_dir=research_dir, uploaded_files=uploaded_files)
    writer.write_draft()

    reviewer = Reviewer(topic=topic, research_dir=research_dir)
    reviewer.review_paper()
    writer.write_updated_paper()
    reviewer.review_paper()


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
