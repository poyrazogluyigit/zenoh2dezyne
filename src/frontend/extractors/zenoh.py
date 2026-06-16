"""Zenoh middleware extractor."""
from ...datatypes import Publisher, Subscriber
from ...graphutils import JoernCFG
from .base import BaseExtractor


class ZenohExtractor(BaseExtractor):
    name = "zenoh"
    publish_call_names = frozenset({"put"})

    def extract_publishers(self, client, file: str) -> list[Publisher]:
        publishers: list[Publisher] = []
        # declare_publisher handles
        var_pubs = client.run_query(f'''cpg.call.name("declare_publisher")
        .where(_.file.name("{file}"))
        .map {{ c =>
        (c.inAssignment.target.code.head, c.argument(1).code)
        }}''')
        for item in var_pubs:
            for symbol, topic in item.items():
                publishers.append(Publisher(symbol=symbol, topic=topic))
        # session.put topics (inner put query scoped to this file)
        sess = client.run_query(f'''cpg.call.code(".*zenoh::Session::open\\\\(.*")
        .where(_.file.name("{file}"))
        .inAssignment.target.code.map {{
            sessionVar =>
            val putArgs = cpg.call.name("put")
                .where(_.file.name("{file}"))
                .where(_.argument(0).codeExact(sessionVar))
                .argument(1).code.l
            (sessionVar, putArgs)
        }}.toMap''')
        for item in sess:
            for session_var, topics in item.items():
                publishers.extend(Publisher(symbol=session_var, topic=t) for t in topics)
        return publishers

    def extract_subscribers(self, client, file: str) -> list[Subscriber]:
        data = client.run_query(f"""cpg.call("declare_subscriber").where(_.file.name("{file}")).map {{ subCall =>
        val topic = subCall.argument(1).code
        val cbArgCode = subCall.argument(2).code

        val cbVarName = cbArgCode.replace("&", "").trim

                val resolvedMethods = {{
                    val directMethods = cpg.method.name(cbVarName).l
                    if (directMethods.nonEmpty) directMethods
                    else {{
                        cpg.assignment
                        .where(_.argument(1).codeExact(cbVarName))
                        .argument(2)
                        .ast.isMethodRef
                        .filter(_.refOut.nonEmpty)
                        .referencedMethod
                        .l
                    }}
                }}

                val resolved = resolvedMethods.headOption
                val dotGraph = resolved
                    .map(_.dotCfg.headOption.getOrElse("CFG resolution failed"))
                    .getOrElse("CFG resolution failed")

                Map(
                        "topic"     -> topic,
                        "callback"  -> cbVarName,
                        "dotGraph"  -> dotGraph
                )
            }}""")
        return [
            Subscriber(name=d["callback"], topic=d["topic"], cfg=JoernCFG(d["dotGraph"]))
            for d in data
        ]

    def resolve_publish_topic(self, node_code: str, publishers: list[Publisher]) -> str | None:
        """Resolve a Zenoh ``put`` CFG node's code to a topic.

        ``session.put("topic", ...)`` → the literal first argument.
        ``handle.put(...)`` → the topic the handle was declared with.
        """
        receiver = node_code.split(".")[0].strip()
        if receiver == "session":
            parts = node_code.split('"')
            return parts[1] if len(parts) > 1 else None
        match = next((p for p in publishers if p.symbol == receiver), None)
        return match.topic if match else None
