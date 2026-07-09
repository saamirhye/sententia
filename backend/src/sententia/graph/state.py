import operator
from typing import Annotated, TypedDict


class SearchResult(TypedDict):
    source: str
    text: str
    kind: str  # "legislation" | "case"


class GraphState(TypedDict):
    query: str
    attempts: int
    results: Annotated[list[SearchResult], operator.add]  # accumulates across search passes
    relevant: bool | None
    sufficient: bool
    answer: str | None
    human_approved: bool | None
    follow_up_questions: list[str]
