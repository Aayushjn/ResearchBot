import logging

from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import prompts


async def write_paper(llm: ChatGoogleGenerativeAI, topic: str, research_dir: Path):
    logger = logging.getLogger("writer")
    response = llm.invoke(
        [
            SystemMessage(content=prompts.WRITER_SYSTEM_PROMPT.format(topic=topic)),
            HumanMessage(content=prompts.SEMANTIC_SCHOLAR_PROMPT),
        ]
    )
