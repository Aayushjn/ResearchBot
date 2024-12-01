import json
import logging
import ssl
from datetime import date
from pathlib import Path
import requests

import httpx
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pypdf import PdfReader
from tqdm import tqdm

import prompts
from dtypes import Cluster
from dtypes import ClusterWithPapers
from dtypes import Paper
from encoder import DataclassJSONEncoder
from semantic_scholar import search_semantic_scholar

import ssl
import httpx
from pathlib import Path
from tqdm import tqdm


def cluster_papers(llm: ChatGoogleGenerativeAI, papers: list[Paper]) -> list[Cluster]:
    gen_config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type_": "ARRAY",
            "description": "Array of clusters",
            "items": {
                "type_": "OBJECT",
                "description": "Cluster",
                "properties": {
                    "name": {"type_": "STRING", "description": "Name of the cluster"},
                    "details": {
                        "type_": "STRING",
                        "description": "Details of the cluster",
                    },
                    "papers": {
                        "type_": "ARRAY",
                        "description": "Array of papers",
                        "items": {"type_": "STRING", "description": "Paper ID"},
                    },
                },
                "required": ["name", "details", "papers"],
            },
        },
    }
    response = llm.invoke(
        prompts.CLUSTER_PAPERS_PROMPT.format(papers=json.dumps(papers, cls=DataclassJSONEncoder)),
        generation_config=gen_config,
    )
    return [Cluster(**c) for c in json.loads(response.content)]


async def download_papers(topic: str, papers: dict[str, Paper]):
    papers_dir = Path.cwd().joinpath("research").joinpath(topic).joinpath("papers")
    # Create a custom SSL context if needed
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with httpx.AsyncClient(http2=True, follow_redirects=True, verify=False) as client:
        for paper in tqdm(
            papers.values(),
            desc=f"Downloading {topic} papers...",
            total=len(papers),
            unit="paper",
            dynamic_ncols=True,
        ):
            dest = papers_dir.joinpath(f"{paper.paper_id}.pdf")
            if dest.exists() and dest.stat().st_size > 0:
                continue

            try:
                r = await client.get(paper.pdf_url)
                if r.status_code == 200:
                    dest.write_bytes(r.content)
                else:
                    print(f"Failed to download {paper.pdf_url} to {dest}: {r.status_code} {r.content}")
            except (httpx.ConnectError, ssl.SSLError) as e:
                print(f"SSL error downloading {paper.pdf_url} to {dest}: {e}")


def get_paper_notes(llm: ChatGoogleGenerativeAI, topic: str, paper_ids: list[str]):
    papers_dir = Path.cwd().joinpath("research").joinpath(topic).joinpath("papers")
    notes_dir = Path.cwd().joinpath("research").joinpath(topic).joinpath("notes")

    llm_prompts = []
    for paper_id in paper_ids:
        pdf = papers_dir.joinpath(f"{paper_id}.pdf")
        notes_file = notes_dir.joinpath(f"{paper_id}.md")
        if not pdf.exists() or pdf.stat().st_size == 0:
            print(f"Skipping empty PDF: {pdf}")
            continue

        if notes_file.exists() and notes_file.stat().st_size > 0:
            continue

        reader = PdfReader(pdf)
        text = "".join((page.extract_text() for page in reader.pages))
        llm_prompts.append(prompts.PAPER_NOTES_PROMPT.format(input_text=text))

    for i, response in tqdm(
        llm.batch_as_completed(llm_prompts),
        desc="Extracting paper notes...",
        total=len(llm_prompts),
        unit="pdf",
        dynamic_ncols=True,
    ):
        notes_dir.joinpath(f"{paper_ids[i]}.md").write_text(response.content,encoding="utf-8")


def get_cluster_notes(llm: ChatGoogleGenerativeAI, topic: str, clusters: list[ClusterWithPapers]):
    notes_dir = Path.cwd().joinpath("research").joinpath(topic).joinpath("notes")
    response = llm.invoke(
        prompts.CLUSTER_NOTES_PROMPT.format(clustered_papers=json.dumps(clusters, cls=DataclassJSONEncoder))
    )
    notes_dir.joinpath("clusters.md").write_text(response.content)


async def perform_research(llm: ChatGoogleGenerativeAI, topic: str):
    logger = logging.getLogger("researcher")
    logger.info("Performing research on %s...", topic)
    # response = llm.invoke(
    #     [
    #         SystemMessage(content=prompts.RESEARCHER_SYSTEM_INSTRUCTION.format(topic=topic)),
    #         HumanMessage(content=prompts.SEMANTIC_SCHOLAR_PROMPT),
    #     ]
    # )
    year = date.today().year
    logger.info("Searching Semantic Scholar...")
    papers = search_semantic_scholar(query=topic, year=(year - 10, year))
    await download_papers(topic, papers)
    get_paper_notes(llm, topic, list(papers.keys()))
    logger.info("Extracted paper notes")
    clusters = [ClusterWithPapers.from_cluster(c, papers) for c in cluster_papers(llm, papers)]
    get_cluster_notes(llm, topic, clusters)
    logger.info("Extracted cluster notes")
    logger.info("Research Complete!")


