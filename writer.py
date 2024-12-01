import logging
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pathlib import Path
from reviewer_agent import review_paper_with_stages

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

    # Step 1: Generate outline for the survey paper
    logger.info("Generating outline for the survey paper...")
    outline_response = llm.invoke([
        SystemMessage(content=prompts["OUTLINE_SYSTEM_PROMPT"].format(topic=topic)),
        HumanMessage(content=prompts["OUTLINE_PROMPT"])
    ])

    # Parse outline suggestions from LLM response
    outline = outline_response.content.split("\n")
    logger.info(f"Outline generated: {outline}")

    # Output file paths
    paper_path = research_dir.joinpath("survey_paper_dynamic.md")  # Original paper
    reviewed_paper_path = research_dir.joinpath("survey_paper_dynamic_reviewed.md")  # Reviewed paper

    # Step 2: Start writing the paper
    paper_content = f"# Survey Paper on {topic}\n\n"
    sections_content = {} 

    with open(paper_path, "w", encoding="utf-8") as f:
        f.write(f"# Survey Paper on {topic}\n\n")

        for section in outline:
            section = section.strip()
            if section:  # Skip empty lines
                logger.info(f"Generating content for section: {section}...")
                section_response = llm.invoke([
                    SystemMessage(content=prompts["WRITER_SYSTEM_PROMPT"].format(section=section, topic=topic)),
                    HumanMessage(content=prompts["SECTION_CONTENT_PROMPT"].format(section=section, topic=topic))
                ])

                # Write each section to the file
                section_content = section_response.content
                sections_content[section] = section_content

                f.write(f"## {section}\n\n{section_content}\n\n")
                paper_content += f"## {section}\n\n{section_content}\n\n"
                logger.info(f"{section} section completed.")

    logger.info("Survey paper generation completed.")
    print(f"Survey paper written to {paper_path}")

    print(len(paper_content))


    logger.info("Starting paper review process...")
    

    max_reviews = 3
    review_count = 0
    
    while review_count < max_reviews:
        

        reviews = await review_paper_with_stages(llm,paper_content,topic,reviewed_paper_path,review_count)
        print(reviews.content)
        review_feedback = reviews.content

        # Rewrite the paper based on the entire review feedback
        logger.info("Processing entire review feedback for rewriting the paper...")

        try:
            # Generate updated paper content based on the entire review feedback
            rewrite_response = llm.invoke([
                SystemMessage(content="You are tasked with rewriting a survey paper based on feedback."),
                HumanMessage(content=f"The original paper content is as follows:\n\n{paper_content}\n\n"
                                    f"The review feedback is as follows:\n\n{review_feedback}\n\n"
                                    f"Rewrite the paper, ensuring all feedback is addressed. Maintain alignment with the topic '{topic}' and ensure clarity, coherence, and originality.")
            ])

            paper_content = rewrite_response.content

            # Save the updated paper content to a new Markdown file
            reviewed_paper_path = reviewed_paper_path.with_name(
                f"survey_paper_dynamic_reviewed_stage_{review_count + 1}.md"
            )

            with open(reviewed_paper_path, "w", encoding="utf-8") as f:
                f.write(rewrite_response.content)

            logger.info(f"Survey paper rewritten and saved for review stage {review_count + 1}.")
            print(f"Updated survey paper saved to {reviewed_paper_path}")

            review_count += 1


        except Exception as e:
            logger.error(f"Error rewriting paper based on feedback: {e}")
            raise


        
    logger.info("Survey paper review and update process completed.")
    print("Final survey paper successfully updated.")


