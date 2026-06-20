from dataclasses import dataclass

Vector = list[float]


@dataclass(frozen=True)
class EmbeddingInput:
    id: str
    text: str
    metadata: dict


@dataclass(frozen=True)
class EmbeddedText:
    id: str
    text: str
    vector: Vector
    metadata: dict
    model_name: str
    model_version: str
