import json
import logging
from os import SEEK_SET
from pathlib import Path

import google.generativeai as genai
from tqdm import tqdm

import prompts
from dtypes import SectionDescription
from encoder import DataclassJSONEncoder
from llm import create_llm


class Writer:
    llm: genai.GenerativeModel
    session: genai.ChatSession
    uploaded_files: list[genai.types.File]

    topic: str
    research_dir: Path
    latest_draft: Path
    write_count: int

    logger: logging.Logger

    def __init__(self, topic: str, research_dir: Path, uploaded_files: list[genai.types.File]):
        self.topic = topic
        self.research_dir = research_dir
        self.write_count = 0
        self.logger = logging.getLogger("writer")

        self.uploaded_files = uploaded_files
        notes = "\n\n".join((file.read_text() for file in self.research_dir.joinpath("notes").glob("*.md")))
        self.llm = create_llm(system_instruction=prompts.WRITER_SYSTEM_INSTRUCTION.format(topic=topic, notes=notes))
        self.session = self.llm.start_chat()

    def define_outline(self) -> list[SectionDescription]:
        outline_response = self.session.send_message(
            [*self.uploaded_files, prompts.WRITER_OUTLINE_PROMPT],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=list[SectionDescription]
            ),
        )
        return [SectionDescription(**s) for s in json.loads(outline_response.text)]

    async def write_draft(self):
        self.logger.info("Starting survey paper generation...")

        self.logger.info("Generating outline for the survey paper...")
        outline = self.define_outline()
        self.logger.info("Outline generated")

        output_dir = self.research_dir.joinpath("output")
        self.latest_draft = output_dir.joinpath(f"survey_paper_{self.write_count}.md")

        with self.latest_draft.open("w") as f:
            for section in tqdm(
                outline, desc="Generating content for sections", total=len(outline), unit="section", dynamic_ncols=True
            ):
                section_response = await self.session.send_message_async(
                    prompts.WRITER_SECTION_CONTENT_PROMPT.format(
                        section_information=json.dumps(section, cls=DataclassJSONEncoder)
                    ),
                )
                f.write(f"{section_response.text}\n\n")

            f.seek(0, SEEK_SET)
            f.write(f"# {self.session.send_message(prompts.WRITER_TITLE_PROMPT).text}\n\n")

        self.logger.info("Survey paper draft written to %s", self.latest_draft)
        self.write_count += 1

    def write_updated_paper(self):
        self.logger.info("Writing updated survey paper...")

        paper_content = self.latest_draft.read_text()
        review_feedback = self.research_dir.joinpath(f"review_{self.write_count - 1}.md").read_text()

        rewrite_response = self.session.send_message(
            prompts.WRITER_PAPER_UPDATE_PROMPT.format(original_content=paper_content, feedback=review_feedback)
        )

        self.latest_draft = self.research_dir.joinpath("output").joinpath(f"survey_paper_{self.write_count}.md")
        self.latest_draft.write_text(rewrite_response.text)
        self.logger.info("Updated survey paper saved to %s", self.latest_draft)
        self.write_count += 1
