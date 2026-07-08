import operator
from typing import Annotated, TypedDict


class SearchResult(TypedDict):
    source: str
    snippet: str
    kind: str  # "legislation" | "case"


class GraphState(TypedDict):
    query: str
    attempts: int
    results: Annotated[list[SearchResult], operator.add]  # accumulates across search passes
    sufficient: bool
    answer: str | None
    human_approved: bool | None
