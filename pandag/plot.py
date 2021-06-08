"""Plotting utilities."""
import networkx as nx
import matplotlib.pyplot as plt

from .nodes import Node


def _get_node_colors(nodes, path, colors):
    """For each node, assign color based on membership in path."""
    node_colors = []
    for x in nodes:
        if x in path:
            node_colors.append(colors['active'])
        else:
            node_colors.append(colors['inactive_node'])
    return node_colors


def _get_edge_colors(G, path, colors):
    """For each edge, assign color based on membership in path_edges."""
    path_edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
    edge_colors = []
    for x in G.edges:
        if x in path_edges:
            edge_colors.append(colors['active'])
        else:
            edge_colors.append(colors['inactive_edge'])
    return edge_colors


def _graphviz_layout(G):
    """
    Hack because even though FakeDiGraph is subclassed from nx.DiGraph,
    nx.nx_pydot.graphviz_layout() doesn't like it.
    """
    if type(G) != nx.classes.digraph.DiGraph:
        G = nx.from_dict_of_dicts(nx.to_dict_of_dicts(G))
    return nx.nx_pydot.graphviz_layout(G, prog='dot')


def _draw_node_shapes(G, node_map, path, pos, colors, node_size):
    """
    Hack to draw node shapes because nx.draw() does not accept a list for
    `node_shape`.
    """
    for node_type in Node.get_subclasses():
        node_list = {ix for ix, node in node_map.items()
                     if isinstance(node, node_type)}
        node_colors = _get_node_colors(node_list, path, colors)
        nx.draw_networkx_nodes(
            G,
            pos,
            node_shape=node_type.plot_shape,
            node_size=node_size,
            node_color=node_colors,
            nodelist=node_list,
        )


# TODO: add legend for active vs. inactive node colors
def plot_dag(G, title=None, show_ids=False, path=None, pos=None, figsize=(20, 24), fpath=None):
    """
    Generate Matplotlib rendering of graph structure.

    Args:
        title: plot title
        show_ids: if True, prefix node labels with node ID
        path: array of node indices representing a path through the graph
        pos: map of node indices to (x, y) coordinates for the plot
        figsize: figure size
        fpath: file path to save plot
    """
    colors = {
        'active': 'lightskyblue',
        'inactive_node': 'thistle',
        'inactive_edge': 'black',
    }

    path = path or []

    plt.figure(figsize=figsize)
    plt.title(title)

    pos = pos or _graphviz_layout(G)

    node_map = {ix: data['node'] for ix, data in G.nodes(data=True)}

    if show_ids:
        node_labels = {ix: f'({node.id}) {node.label}' for ix,
                       node in node_map.items()}
    else:
        node_labels = {ix: node.label for ix, node in node_map.items()}

    edge_colors = _get_edge_colors(G, path, colors)

    node_size = 4000
    plt_config = {
        'pos': pos,
        'width': 1.5,
        'font_size': 10,
        'font_color': 'black',
        'edge_color': edge_colors,
        # making invisible nodes so edges draw correctly,
        # then nodes are drawn later
        'node_size': node_size + 200,
        'node_color': 'white',
        'node_shape': 's',
        'labels': node_labels,
        # https://matplotlib.org/stable/gallery/userdemo/connectionstyle_demo.html
        'connectionstyle': 'arc3,rad=0.',
    }
    nx.draw(G, **plt_config)

    _draw_node_shapes(G, node_map, path, pos, colors, node_size)

    edge_labels = {
        'false': {k: v for k, v in nx.get_edge_attributes(G, 'label').items() if not v},
        'true': {k: v for k, v in nx.get_edge_attributes(G, 'label').items() if v},
    }

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels['false'],
        font_color='red',
    )
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels['true'],
        font_color='green',
    )

    if fpath:
        plt.savefig(fpath)
    else:
        plt.show()
