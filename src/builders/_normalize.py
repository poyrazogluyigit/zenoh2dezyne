"""Middleware-neutral CFG annotation.

Tags each publish call node with a neutral ``comm_op='publish'`` and a resolved
``topic``, using the extractor's ``publish_call_names`` and
``resolve_publish_topic``. After this pass, codegen reads only neutral
attributes and never needs middleware knowledge.
"""
from ..graphutils import JoernCFG


def normalize_publish_nodes(cfg: JoernCFG, extractor, publishers) -> None:
    for node_id in cfg:
        if cfg.get_type(node_id) in extractor.publish_call_names:
            code = cfg.get_data(node_id, "code") or ""
            cfg.set_data(node_id, "comm_op", "publish")
            cfg.set_data(node_id, "topic", extractor.resolve_publish_topic(code, publishers))
