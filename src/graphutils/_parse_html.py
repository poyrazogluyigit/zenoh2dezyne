import html
import re

# line number is not returned
def _clean_label(label: str):
    clean_label = label.strip('<>').strip('"').strip('<>')
    metadata, code = re.split(r'<BR/>', clean_label, flags=re.IGNORECASE)
    nodeType, _ = metadata.rsplit(',', 1)
    return html.unescape(nodeType.strip()), html.unescape(code.strip())
     

def _prettify_labels(nodes):
        """Parses Joern's raw DOT labels to extract clean code and metadata.
        Unescapes HTML entities and splits metadata from the actual code snippet.
        """
        for _, data in nodes:
            raw_label = data.get('label', '')
            if not raw_label:
                continue

            nodeType, code = _clean_label(raw_label)
            data['node_type'] = nodeType
            data['code'] = code
            if nodeType == "put":
                data['put_target'] = code.split('.')[0]
                if data['put_target'] == "session":
                    data['put_topic'] = code.split('"')[1]
            del data['label']
            

