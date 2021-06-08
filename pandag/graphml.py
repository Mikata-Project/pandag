import re
import networkx as nx
from .nodes import Assert, Inequal, Output, Dummy

label_map = {
    "yes": True,
    "no": False,
    "true": True,
    "false": False,
}


def generate_node_id(node, data):
    """Generates a node ID from the node label, extracts data from: [$ID]."""
    m = re.search(r"\[(?P<node_id>\w+)\]", data["label"])
    if m:
        return m.group("node_id")
    assert m, ("node_id_func must return a valid node ID for each nodes, but "
               f"it didn't for node {node}, {data}")


def load(pandag, path, custom_ids=False, node_id_func=generate_node_id):
    """Loads GraphML into Pandag algo."""
    G = nx.read_graphml(path)
    node_map = {}
    for node, data in G.nodes(data=True):
        node_id = node
        if custom_ids:
            node_id = node_id_func(node, data)
        node_map[node] = node_id
        edges = G.edges(node)
        shape = data.get("shape_type")
        label = data["label"]
        description = data.get("description")
        if not shape:
            continue
        if shape in ("com.yworks.flowchart.start1",
                     "com.yworks.flowchart.start2",
                     "com.yworks.flowchart.terminator"):
            pandag.get_node_id(Dummy(label, _id=node_id))
        if shape == "com.yworks.flowchart.process":
            if description:
                # description can contain a multi-line expression
                expr = description
            else:
                expr = label
            pandag.get_node_id(Output(label, _id=node_id, expr=expr))
        if shape == "com.yworks.flowchart.decision":
            if len(edges) == 2:
                pandag.get_node_id(Assert(label, _id=node_id))
            else:
                pandag.get_node_id(Inequal(label, _id=node_id))
    for src_node_id, dst_node_id in nx.edge_dfs(G):
        edge_data = G.get_edge_data(src_node_id, dst_node_id)
        label = edge_data.get("label")
        if label and label.lower() in label_map:
            label = label_map[label.lower()]
        if label is not None:
            pandag.G.add_edge(node_map[src_node_id], node_map[dst_node_id],
                              label=label)
        else:
            pandag.G.add_edge(node_map[src_node_id], node_map[dst_node_id])
