from dataclasses import dataclass
from pathlib import Path


@dataclass
class CorpusDocument:
    doc_id: str
    citation: str
    source_url: str
    topic: str
    court: str
    kind: str  # "legislation" | "case"
    body: str


def _parse_file(path: Path, kind: str) -> CorpusDocument:
    text = path.read_text()
    header_text, _, body = text.partition("\n\n")

    header: dict[str, str] = {}
    for line in header_text.splitlines():
        key, _, value = line.partition(":")
        header[key.strip()] = value.strip()

    return CorpusDocument(
        doc_id=path.stem,
        citation=header.get("Citation", ""),
        source_url=header.get("Source", ""),
        topic=header.get("Topic", ""),
        court=header.get("Court", ""),
        kind=kind,
        body=body.strip(),
    )


def load_corpus(corpus_dir: Path) -> list[CorpusDocument]:
    docs = [_parse_file(path, "legislation") for path in sorted((corpus_dir / "legislation").glob("*.txt"))]
    docs += [_parse_file(path, "case") for path in sorted((corpus_dir / "cases").glob("*.txt"))]
    return docs
