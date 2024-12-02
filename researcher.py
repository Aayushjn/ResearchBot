import json
import logging
import ssl
from datetime import date
from pathlib import Path

import google.generativeai as genai
import httpx
from tqdm import tqdm

import prompts
from dtypes import Cluster
from dtypes import ClusterWithPapers
from dtypes import Paper
from encoder import DataclassJSONEncoder
from llm import create_llm
from semantic_scholar import search_semantic_scholar


class Researcher:
    llm: genai.GenerativeModel
    session: genai.ChatSession
    uploaded_papers: dict[str, genai.types.File]

    topic: str
    research_dir: Path
    paper_ids: list[str]

    logger: logging.Logger

    def __init__(self, topic: str, research_dir: Path):
        self.topic = topic
        self.research_dir = research_dir
        self.logger = logging.getLogger("researcher")

        self.llm = create_llm(system_instruction=prompts.RESEARCHER_SYSTEM_INSTRUCTION.format(topic=topic))
        self.session = self.llm.start_chat()

    def cluster_papers(self, papers: list[Paper]) -> list[Cluster]:
        response = self.session.send_message(
            prompts.CLUSTER_PAPERS_PROMPT.format(papers=json.dumps(papers, cls=DataclassJSONEncoder)),
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=list[Cluster]
            ),
        )
        return [Cluster(**c) for c in json.loads(response.text)]

    async def download_papers(self, papers: dict[str, Paper]):
        papers_dir = self.research_dir.joinpath("papers")
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with httpx.AsyncClient(http2=True, follow_redirects=True, verify=False) as client:
            for paper in tqdm(
                papers.values(),
                desc=f"Downloading {self.topic} papers...",
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

    def get_paper_notes(self, paper_ids: list[str]):
        papers_dir = self.research_dir.joinpath("papers")
        notes_dir = self.research_dir.joinpath("notes")

        self.uploaded_papers = {
            paper_id: file for file in genai.list_files() if (paper_id := file.display_name.split(".")[0]) in paper_ids
        }

        for paper_id in tqdm(
            paper_ids,
            desc="Extracting paper notes...",
            total=len(paper_ids),
            unit="pdf",
            dynamic_ncols=True,
        ):
            if paper_id not in self.uploaded_papers:
                pdf = papers_dir.joinpath(f"{paper_id}.pdf")
                notes_file = notes_dir.joinpath(f"{paper_id}.md")
                if not pdf.exists() or pdf.stat().st_size == 0:
                    print(f"Skipping empty PDF: {pdf}")
                    continue

                if notes_file.exists() and notes_file.stat().st_size > 0:
                    continue

                self.uploaded_papers[paper_id] = genai.upload_file(
                    pdf, mime_type="application/pdf", display_name=f"{paper_id}.pdf"
                )

            file = self.uploaded_papers[paper_id]

            dest = notes_dir.joinpath(f"{paper_id}.md")
            if dest.exists() and dest.stat().st_size > 0:
                continue

            dest.write_text(self.session.send_message([file, prompts.PAPER_NOTES_PROMPT]).text)

    def get_cluster_notes(self, clusters: list[ClusterWithPapers]):
        self.research_dir.joinpath("notes").joinpath("clusters.md").write_text(
            self.session.send_message(
                prompts.CLUSTER_NOTES_PROMPT.format(clustered_papers=json.dumps(clusters, cls=DataclassJSONEncoder))
            ).text
        )

    async def perform_research(self):
        logger = logging.getLogger("researcher")
        logger.info("Performing research on %s...", self.topic)
        # response = self.session.send_message(prompts.SEMANTIC_SCHOLAR_PROMPT)
        year = date.today().year
        logger.info("Searching Semantic Scholar...")
        papers = search_semantic_scholar(query=self.topic, year=(year - 10, year))
        await self.download_papers(papers)
        self.get_paper_notes(list(papers.keys()))
        logger.info("Extracted paper notes")

        cluster_notes_path = self.research_dir.joinpath("notes").joinpath("clusters.md")
        if not cluster_notes_path.exists() or cluster_notes_path.stat().st_size <= 0:
            clusters = [ClusterWithPapers.from_cluster(c, papers) for c in self.cluster_papers(papers)]
            self.get_cluster_notes(clusters)
        logger.info("Extracted cluster notes")
        logger.info("Research Complete!")
