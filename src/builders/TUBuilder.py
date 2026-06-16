import logging

from ..frontend import JoernClient, MiddlewareExtractor
from ..datatypes import MainThread, TranslationUnit
from ..graphutils import JoernCFG

from ._normalize import normalize_publish_nodes

logger = logging.getLogger(__name__)


class TUBuilder:
    """Assembles neutral TranslationUnits from a JoernClient + a middleware extractor.

    Orchestration is framework-agnostic: the extractor supplies publishers,
    subscribers and services; this builder fetches CFGs, normalizes their
    publish nodes, and packages everything into TranslationUnits.
    """

    def __init__(self, client: JoernClient, extractor: MiddlewareExtractor):
        self.client = client
        self.extractor = extractor

    def build(self) -> list[TranslationUnit]:
        units: list[TranslationUnit] = []
        for file_name in self.client.get_files():
            publishers = self.extractor.extract_publishers(self.client, file_name)
            subscribers = self.extractor.extract_subscribers(self.client, file_name)
            services = self.extractor.extract_services(self.client, file_name)

            main_cfg = JoernCFG(self.client.get_cfg_as_dot(file_name, "main")[0])
            normalize_publish_nodes(main_cfg, self.extractor, publishers)
            for sub in subscribers:
                normalize_publish_nodes(sub.cfg, self.extractor, publishers)

            units.append(TranslationUnit(
                file_name=file_name,
                main_thread=MainThread(cfg=main_cfg),
                callback_threads=subscribers,
                publishers=publishers,
                services=services,
            ))
        return units
