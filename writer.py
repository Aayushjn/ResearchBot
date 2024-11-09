import logging
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pathlib import Path

# Prompts dictionary
prompts = {
    "OUTLINE_SYSTEM_PROMPT": "You are tasked with creating an outline for a survey paper on '{topic}'.",
    "OUTLINE_PROMPT": "Analyze the research material and suggest an appropriate outline for the survey paper, including recommended sections and subsections.",
    "WRITER_SYSTEM_PROMPT": "You are tasked with writing the '{section}' section of a survey paper on '{topic}'.",
    "SECTION_CONTENT_PROMPT": "Write detailed content for the section '{section}' in a survey paper on '{topic}', using insights from the available research material."
}

async def write_paper(llm: ChatGoogleGenerativeAI, topic: str, research_dir: Path):
    logger = logging.getLogger("writer")
    logger.info("Starting dynamic survey paper generation...")

    # Ask the LLM to propose an outline with sections based on the research material
    logger.info("Generating outline for the survey paper...")
    outline_response = llm.invoke([
        SystemMessage(content=prompts["OUTLINE_SYSTEM_PROMPT"].format(topic=topic)),
        HumanMessage(content=prompts["OUTLINE_PROMPT"])
    ])

    # Parse outline suggestions from LLM response
    outline = outline_response.content.split("\n")
    logger.info(f"Outline generated: {outline}")

    # Output file path
    paper_path = research_dir.joinpath("survey_paper_dynamic.md")

    # Start writing the paper
    with open(paper_path, "w", encoding="utf-8") as f:
        f.write(f"# Survey Paper on {topic}\n\n")

        # Generate content for each identified section
        for section in outline:
            section = section.strip()
            if section:  # Avoid empty lines
                logger.info(f"Generating content for section: {section}...")
                section_response = llm.invoke([
                    SystemMessage(content=prompts["WRITER_SYSTEM_PROMPT"].format(section=section, topic=topic)),
                    HumanMessage(content=prompts["SECTION_CONTENT_PROMPT"].format(section=section, topic=topic))
                ])
                f.write(f"## {section}\n\n{section_response.content}\n\n")
                logger.info(f"{section} section completed.")

    logger.info("Dynamic survey paper generation completed.")
    print(f"Survey paper written to {paper_path}")
