from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunContext:
    """Single source of truth for all input/output paths of one run."""
    input_dir: Path
    output_dir: Path

    @property
    def project_name(self) -> str:
        return self.input_dir.name

    @property
    def amalgamated_dir(self) -> Path:
        return self.output_dir / "amalgamated"

    @property
    def models_dir(self) -> Path:
        return self.output_dir / "models"

    def mkdirs(self) -> None:
        for p in (self.amalgamated_dir, self.models_dir):
            p.mkdir(parents=True, exist_ok=True)
