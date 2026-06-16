from dataclasses import dataclass, field
from ..graphutils import JoernCFG


@dataclass
class MainThread:
    cfg: JoernCFG

    @property
    def name(self):
        return "main"


@dataclass
class Subscriber:
    """A subscription: a callback thread bound to an incoming topic.

    ``name`` is the callback identifier (used as the Dezyne thread name),
    ``topic`` the normalized key it subscribes to, ``cfg`` the callback's CFG.
    """
    name: str
    topic: str
    cfg: JoernCFG


@dataclass
class Publisher:
    """An outgoing publication: a handle/variable name and the topic it publishes."""
    symbol: str
    topic: str


@dataclass
class TranslationUnit:
    file_name: str
    main_thread: MainThread
    callback_threads: list[Subscriber] = field(default_factory=list)
    publishers: list[Publisher] = field(default_factory=list)
