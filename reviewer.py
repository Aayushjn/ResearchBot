import logging
from pathlib import Path

import google.generativeai as genai

import prompts
from llm import create_llm


class Reviewer:
    llm: genai.GenerativeModel
    session: genai.ChatSession

    topic: str
    research_dir: Path
    review_count: int

    logger: logging.Logger

    def __init__(self, topic: str, research_dir: Path):
        self.topic = topic
        self.research_dir = research_dir
        self.review_count = 0
        self.logger = logging.getLogger("reviewer")

        self.llm = create_llm(system_instruction=prompts.REVIEWER_SYSTEM_INSTRUCTION)
        self.session = self.llm.start_chat()

    def review_paper(self):
        self.logger.info("Starting paper review...")
        paper_content = (
            self.research_dir.joinpath("output").joinpath(f"survey_paper_{self.review_count}.md").read_text()
        )
        self.research_dir.joinpath(f"review_{self.review_count}.md").write_text(
            self.session.send_message(paper_content).text
        )
        self.logger.info("Paper review saved to %s", self.research_dir.joinpath(f"review_{self.review_count}.md"))
        self.review_count += 1
