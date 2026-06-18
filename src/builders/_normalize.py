"""Middleware-neutral CFG annotation.

Tags each publish call node with a neutral ``comm_op='publish'`` and a resolved
``topic``, using the extractor's ``publish_call_names`` and
``resolve_publish_topic``. After this pass, codegen reads only neutral
attributes and never needs middleware knowledge.
"""
import logging

from ..graphutils import JoernCFG

logger = logging.getLogger(__name__)


def normalize_publish_nodes(cfg: JoernCFG, extractor, publishers) -> None:
    for node_id in cfg:
        if cfg.get_type(node_id) in extractor.publish_call_names:
            code = cfg.get_data(node_id, "code") or ""
            topic = extractor.resolve_publish_topic(code, publishers)
            if topic is None:
                # Statically unresolvable topic (e.g. non-literal advertise, or a
                # publish on a non-trivial receiver). Drop it rather than emit a
                # None topic, which would crash codegen's topic mangling.
                logger.warning("dropping publish with unresolved topic: %s", code.strip())
                continue
            cfg.set_data(node_id, "comm_op", "publish")
            cfg.set_data(node_id, "topic", topic)
