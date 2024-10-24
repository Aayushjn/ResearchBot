from dataclasses import dataclass


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    pdf_url: str


@dataclass
class Cluster:
    name: str
    details: str
    papers: list[str]


@dataclass
class ClusterList:
    clusters: list[Cluster]


@dataclass
class ClusterWithPapers:
    name: str
    details: str
    papers: list[Paper]

    @classmethod
    def from_cluster(cls, cluster: Cluster, paper_dict: dict[str, Paper]) -> "ClusterWithPapers":
        return cls(
            name=cluster.name,
            details=cluster.details,
            papers=[paper_dict[paper_id] for paper_id in cluster.papers if paper_id in paper_dict],
        )
