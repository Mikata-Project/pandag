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
    """Generate a node ID from the node label, extracts data from: [$ID].

    Return the extracted node ID and the label, without the ID part, so
    it can be the expression if one isn't specified in the description."""
    pat = r"\[(?P<node_id>\w+)\]"
    m = re.search(pat, data["label"])
    if m:
        return m.group("node_id"), re.sub(pat, '', data["label"]).strip()
    assert m, ("node_id_func must return a valid node ID for each nodes, but "
               f"it didn't for node {node}, {data}")


def load(pandag, path, local_dict=None, global_dict=None,
         custom_ids=False, node_id_func=generate_node_id):
    """Loads GraphML into Pandag algo."""
    G = nx.read_graphml(path)
    next_node_id = 0
    node_map = {}
    for node, data in G.nodes(data=True):
        node_id = node
        if custom_ids:
            node_id, custom_expr = node_id_func(node, data)
        else:
            node_id = next_node_id
            next_node_id += 1
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
            pandag.get_node_id(Dummy(label,
                                     _id=node_id,
                                     _x=data.get("x"),
                                     _y=data.get("y")))
        if custom_ids:
            expr = custom_expr
        else:
            expr = label
        if shape == "com.yworks.flowchart.process":
            if description:
                # description can contain a multi-line expression
                expr = description
            pandag.get_node_id(Output(label,
                                      _id=node_id,
                                      _x=data.get("x"),
                                      _y=data.get("y"),
                                      expr=expr,
                                      local_dict=local_dict,
                                      global_dict=global_dict))
        if shape == "com.yworks.flowchart.decision":
            if len(edges) == 2:
                pandag.get_node_id(Assert(expr,
                                          _label=label,
                                          _id=node_id,
                                          _x=data.get("x"),
                                          _y=data.get("y"),
                                          local_dict=local_dict,
                                          global_dict=global_dict))
            else:
                pandag.get_node_id(Inequal(_label=label,
                                           _id=node_id,
                                           _x=data.get("x"),
                                           _y=data.get("y"),
                                           local_dict=local_dict,
                                           global_dict=global_dict))
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
