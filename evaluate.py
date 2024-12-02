# import logging
# from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# from langchain_community.vectorstores import FAISS
# from pathlib import Path
# from PyPDF2 import PdfReader
# #Extract Text from PDFs
# # Initialize logger
# logger = logging.getLogger("text_extractor")
# logging.basicConfig(level=logging.INFO)
# paper_path= r"D:\BITS PILANI\3rdsem\llm project\ResearchBot\research\image classification\papers"
# def extract_text_from_papers(paper_path: str):
#     """
#     Extract text from all PDF files in the given directory.
#     Args:
#         paper_path (str): Path to the directory containing PDF files.
#     Returns:
#         dict: A dictionary where keys are paper filenames (without extension)
#               and values are the extracted text.
#     """
#     logger.info("Extracting text from downloaded papers...")
#     paper_dir = Path(paper_path)
#     extracted_texts = {}
#     if not paper_dir.exists() or not paper_dir.is_dir():
#         logger.error(f"Provided path '{paper_path}' is not a valid directory.")
#         return extracted_texts
#     # Iterate through all PDF files in the directory
#     for pdf_file in paper_dir.glob("*.pdf"):
#         logger.info(f"Processing file: {pdf_file.name}")
#         try:
#             reader = PdfReader(pdf_file)
#             # Extract text from all pages of the PDF
#             extracted_text = "".join((page.extract_text() for page in reader.pages))
#             # Use the filename (without extension) as the key
#             extracted_texts[pdf_file.stem] = extracted_text
#             logger.info(f"Successfully extracted text from {pdf_file.name}")
#         except Exception as e:
#             logger.error(f"Failed to process {pdf_file.name}: {e}")
#     logger.info("Text extraction completed.")
#     return extracted_texts
# # Function to create vector store for plagiarism detection
# def create_vector_store(extracted_texts: dict, vector_store_path: Path):
#     embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key="AIzaSyAjCvq3WBzO628A-hNvQDXCo4ESzmNCVY4")
#     # Prepare texts and metadata
#     texts = list(extracted_texts.values())  # All paper texts
#     metadata = [{"paper_id": paper_id} for paper_id in extracted_texts.keys()]  # Paper IDs as metadata
#     # Create vector store using FAISS
#     vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadata)
#     vector_store.save_local(str(vector_store_path))
#     return vector_store
# # Function to evaluate the generated survey paper
# def evaluate_generated_paper(generated_paper_text: str, vector_store_path: Path, llm: ChatGoogleGenerativeAI):
#     # Load the vector store from disk
#     vector_store = FAISS.load_local(str(vector_store_path))
#     # Create embedding for the generated paper
#     embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
#     paper_embedding = embeddings.embed_query(generated_paper_text)
#     # Retrieve similar documents (potential plagiarism check)
#     similar_papers = vector_store.similarity_search(paper_embedding, k=5)  # Top 5 similar papers
#     logger = logging.getLogger("evaluator")
#     # Build the context for hallucination check
#     context = "\n".join([f"{doc.metadata['paper_id']}: {doc.page_content}" for doc in similar_papers])
#     # Generate prompt for hallucination detection
#     prompt = f"""
#     Based on the following context from related research papers:
#     {context}
#     Review the generated survey paper content below. Does it contain any hallucinated or fabricated information?
#     Generated survey paper content:
#     {generated_paper_text}
#     """
#     # Ask Gemini to evaluate hallucinations
#     logger.info("Evaluating for hallucinations...")
#     response = llm.invoke([{
#         "role": "system",
#         "content": "You are tasked with detecting any hallucinations or inconsistencies in a survey paper based on the context of related research."
#     }, {
#         "role": "user",
#         "content": prompt
#     }])
#     hallucination_check = response.content  # Hallucination evaluation response
#     # Check plagiarism based on similarity search
#     logger.info("Checking for potential plagiarism...")
#     plagiarism_check = f"Plagiarism check: Similar documents found: {', '.join([doc.metadata['paper_id'] for doc in similar_papers])}"
#     # Generate a final report with hallucination and plagiarism results
#     report = generate_report(hallucination_check, plagiarism_check)
#     return report
# # Function to review and evaluate the dynamically generated survey paper
# async def review_and_evaluate_paper(llm: ChatGoogleGenerativeAI, topic: str, research_dir: Path):
#     logger = logging.getLogger("reviewer")
#     # Path to the generated paper
#     paper_path = research_dir.joinpath("survey_paper_dynamic.md")
#     if not paper_path.exists():
#         logger.error("Generated paper not found.")
#         return
#     # Read the generated paper content
#     with open(paper_path, "r", encoding="utf-8") as f:
#         generated_paper_text = f.read()
#     # call for extracted paper texts
#     extracted_texts= extract_text_from_papers(paper_path)
#     # Step 1: Create or load the vector store for extracted papers
#     vector_store_path = research_dir.joinpath("vector_store")
#     vector_store = create_vector_store(extracted_texts, vector_store_path)
#     # Step 2: Evaluate the generated paper for hallucination and plagiarism
#     evaluation_report = evaluate_generated_paper(generated_paper_text, vector_store_path, llm)
#     logger.info(f"Evaluation report: {evaluation_report}")
#     # Step 3: Generate the final report
#    # logger.info("Generating the final report...")
#     #generate_report(evaluation_report)
# using chroma code
import logging
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from PyPDF2 import PdfReader

# Initialize logger
logger = logging.getLogger("text_extractor")
logging.basicConfig(level=logging.INFO)


# Extract Text from PDFs
def extract_text_from_papers(paper_path: str):
    """
    Extract text from all PDF files in the given directory.

    Args:
        paper_path (str): Path to the directory containing PDF files.

    Returns:
        dict: A dictionary where keys are paper filenames (without extension)
              and values are the extracted text.
    """
    logger.info("Extracting text from downloaded papers...")
    paper_dir = Path(paper_path)
    extracted_texts = {}

    if not paper_dir.exists() or not paper_dir.is_dir():
        logger.error(f"Provided path '{paper_path}' is not a valid directory.")
        return extracted_texts

    for pdf_file in paper_dir.glob("*.pdf"):
        logger.info(f"Processing file: {pdf_file.name}")
        try:
            reader = PdfReader(pdf_file)
            extracted_text = "".join((page.extract_text() for page in reader.pages))
            extracted_texts[pdf_file.stem] = extracted_text
            logger.info(f"Successfully extracted text from {pdf_file.name}")
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")

    logger.info("Text extraction completed.")
    return extracted_texts


# Function to create vector store for plagiarism detection using Chroma
def create_vector_store(extracted_texts: dict, vector_store_path: Path):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", google_api_key="AIzaSyAjCvq3WBzO628A-hNvQDXCo4ESzmNCVY4"
    )

    texts = list(extracted_texts.values())  # All paper texts
    metadata = [{"paper_id": paper_id} for paper_id in extracted_texts.keys()]  # Metadata for papers

    # Create Chroma vector store
    vector_store = Chroma.from_texts(
        texts=texts, embedding=embeddings, metadatas=metadata, persist_directory=str(vector_store_path)
    )
    vector_store.persist()  # Save the vector store to disk
    return vector_store


# Function to evaluate the generated survey paper
def evaluate_generated_paper(generated_paper_text: str, vector_store_path: Path, llm: ChatGoogleGenerativeAI):
    # Load the Chroma vector store from disk
    vector_store = Chroma(persist_directory=str(vector_store_path))

    # Create embedding for the generated paper
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    paper_embedding = embeddings.embed_query(generated_paper_text)

    # Retrieve similar documents (potential plagiarism check)
    similar_papers = vector_store.similarity_search_by_vector(paper_embedding, k=5)  # Top 5 similar papers
    logger = logging.getLogger("evaluator")

    # Build the context for hallucination check
    context = "\n".join([f"{doc['metadata']['paper_id']}: {doc['text']}" for doc in similar_papers])

    # Generate prompt for hallucination detection
    prompt = f"""
    Based on the following context from related research papers:

    {context}

    Review the generated survey paper content below. Does it contain any hallucinated or fabricated information?
    Generated survey paper content:
    {generated_paper_text}
    """

    # Ask Gemini to evaluate hallucinations
    logger.info("Evaluating for hallucinations...")
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "You are tasked with detecting any hallucinations or inconsistencies in a survey paper based on the context of related research.",
            },
            {"role": "user", "content": prompt},
        ]
    )

    hallucination_check = response.content  # Hallucination evaluation response

    # Check plagiarism based on similarity search
    logger.info("Checking for potential plagiarism...")
    plagiarism_check = f"Plagiarism check: Similar documents found: {', '.join([doc['metadata']['paper_id'] for doc in similar_papers])}"

    # Generate a final report with hallucination and plagiarism results
    report = generate_report(hallucination_check, plagiarism_check)

    return report


# Function to generate the final evaluation report
def generate_report(hallucination_check: str, plagiarism_check: str) -> str:
    """
    Generate a detailed report based on hallucination and plagiarism checks.

    Args:
        hallucination_check (str): Results of the hallucination evaluation.
        plagiarism_check (str): Results of the plagiarism check.

    Returns:
        str: A detailed evaluation report.
    """
    report = f"""
    Evaluation Report:
    -------------------
    
    1. Hallucination Check:
       {hallucination_check}

    2. Plagiarism Check:
       {plagiarism_check}

    Conclusion:
       The paper was evaluated for hallucinations and plagiarism. Please review the results and make necessary edits.
    """
    logger.info("Report generated successfully.")
    return report


# Function to review and evaluate the dynamically generated survey paper
async def review_and_evaluate_paper(llm: ChatGoogleGenerativeAI, topic: str, research_dir: Path):
    logger = logging.getLogger("reviewer")

    # Path to the generated paper
    paper_path = research_dir.joinpath("survey_paper_dynamic.md")

    if not paper_path.exists():
        logger.error("Generated paper not found.")
        return

    # Read the generated paper content
    with open(paper_path, "r", encoding="utf-8") as f:
        generated_paper_text = f.read()

    # Call for extracted paper texts
    paper_texts = extract_text_from_papers(paper_path)

    # Step 1: Create or load the vector store for extracted papers
    vector_store_path = research_dir.joinpath("vector_store")
    create_vector_store(paper_texts, vector_store_path)

    # Step 2: Evaluate the generated paper for hallucination and plagiarism
    evaluation_report = evaluate_generated_paper(generated_paper_text, vector_store_path, llm)
    logger.info(f"Evaluation report: {evaluation_report}")
