async def review_paper_with_stages(llm, paper_content, topic, output_file_path, review_count):
    """
    Function to review a research paper using staged prompts to refine the document iteratively.
    
    Args:
    - llm: Language model for invoking reviews
    - paper_content: Content of the research paper
    - topic: Research topic
    - output_file_path: File path to save the revised paper
    - max_reviews: Maximum number of review stages
    
    Returns:
    - None (The revised paper is saved to the output file)
    """
    # Define the review prompts for each stage
    review_prompts = [
        f"Please review the paper on '{topic}' as a cohesive document. Analyze its structure, logical flow, and coherence from section to section. Specifically, check for instances of hallucinations where the content may be fabricated or unsupported by research. Evaluate if the content is original and free of plagiarism by identifying any areas of duplication or unoriginal material. Provide section-wise feedback, including section names, and suggest specific improvements to enhance clarity, alignment with the research topic, and depth of coverage.",
        
       f"Following the initial review, the paper has been revised. Please assess the updated document for logical consistency and alignment with the topic. Confirm if the revised content addresses earlier feedback and remains accurate, original, and free of hallucinations or fabricated information. Evaluate if the sections now effectively support the main arguments and highlight any lingering gaps or areas needing improvement. Provide detailed, section-wise feedback, including the section names, and offer actionable suggestions for refinement.",
        
        f"This is the final review stage for the paper on '{topic}'. Please verify that the document is free of hallucinations and plagiarism, and confirm that all sections are cohesive, logically structured, and contribute meaningfully to the research topic. Ensure that earlier revisions have resolved prior issues, and evaluate if the paper is now ready for submission or publication. Provide concise, section-wise feedback, highlighting any remaining concerns or confirming that no further revisions are needed."
    ]


    review_promt = review_prompts[review_count]

    review_response = llm.invoke([review_promt + "\n\n" + paper_content])
    return review_response





