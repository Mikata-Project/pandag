"""Main module."""

import uuid
import networkx as nx
from pandag.nodes import Node, Output
from pandag import plot, graphml
import more_itertools


class FakeDiGraph(nx.DiGraph):
    """This is to make dag.plot._graphviz_layout think it's not a DiGraph and
    execute to_dict_of_dicts, so a correct dot file is created."""
    pass


class Pandag:
    def __init__(self, path_column='path'):
        self.path_column = path_column
        self.next_node_id = 0
        self.nodes = {}
        self.node_ids = {}
        self.G = FakeDiGraph()
        self.uuid = str(uuid.uuid4())

    def load_algo(self, algo, local_dict=None, global_dict=None):
        """Creates the DAG from a python data structure."""
        self.create_graph(algo, local_dict=local_dict, global_dict=global_dict)

    def load_graphml(self, path, local_dict=None, global_dict=None, **kwargs):
        """Load an algo from a GraphML file located at `path`."""
        graphml.load(self, path, local_dict=local_dict,
                     global_dict=global_dict, **kwargs)

    def get_node_id(self, node):
        """Return node ID for a given node.

        Args:
            node (pandag.Node): The pandag node.

        Returns:
            (str, int): The node ID.

        """
        if node not in self.nodes:
            if getattr(node, 'id', None) is not None:
                # we've node IDs in the nodes, use them instead of dynamically
                # created ones and require their uniqueness
                assert node.id not in self.node_ids, "User-specified node ids must be unique!"
                self.nodes[node] = node.id
                self.node_ids[node.id] = node
            else:
                # store the dynamic ID in the `id` attribute, so we can get it
                # during plotting
                setattr(node, 'id', self.next_node_id)
                self.nodes[node] = self.next_node_id
                self.node_ids[self.next_node_id] = node
                self.next_node_id += 1
            self.G.add_node(self.nodes[node], node=node)
        return self.nodes[node]

    def get_node(self, node_id):
        """Return the node for a given node ID.

        Args:
            node_id (str, int): Node ID.

        Returns:
            pandag.Node: Node for the given node ID.

        """
        return self.node_ids[node_id]

    def create_graph(self, sub, parent=None, local_dict=None, global_dict=None):
        """Generate NetworkX graph object.

        Args:
            sub (dict): The sub graph to parse.
            parent (pandag.Node): Parent for this subgraph.

        Returns:
            None

        """
        for k, v in sub.items():
            if isinstance(k, Node):
                # add local/global dicts to the node if specified
                if local_dict:
                    k.local_dict = local_dict
                if global_dict:
                    k.global_dict = global_dict
                # create nodes and add an edge between them if there's a parent
                k_id = self.get_node_id(k)
                if parent:
                    self.G.add_edge(self.get_node_id(parent), k_id)
                if isinstance(v, Node):
                    self.G.add_edge(self.get_node_id(k), self.get_node_id(v))
                if isinstance(v, dict):
                    self.create_graph(v,
                                      parent=k,
                                      local_dict=local_dict,
                                      global_dict=global_dict)
            elif isinstance(v, (Node, tuple, list)):
                # having a list on this level means they will be daisy-chained
                prev_node = None
                for node in more_itertools.always_iterable(v):
                    if isinstance(node, dict):
                        self.create_graph(node,
                                          parent=parent,
                                          local_dict=local_dict,
                                          global_dict=global_dict)
                        continue
                    node_id = self.get_node_id(node)
                    if prev_node:
                        self.G.add_edge(self.get_node_id(prev_node), node_id)
                    elif parent:
                        self.G.add_edge(self.get_node_id(parent), node_id, label=k)
                    prev_node = node
            elif isinstance(v, dict):
                # if the value is a dict and we have a parent, add edges between it
                # and the dict's keys with the given label
                if parent:
                    for node in v.keys():
                        self.G.add_edge(self.get_node_id(parent),
                                        self.get_node_id(node), label=k)
                self.create_graph(v,
                                  parent=parent,
                                  local_dict=local_dict,
                                  global_dict=global_dict)

    def eval(self, df):
        """Evaluate a Pandas DataFrame with the graph.

        Args:
            df (pandas.DataFrame): The DataFrame to be evaluated.

        Returns:
            pandas.DataFrame: Resulting DataFrame.

        """
        # generate a unique column name
        node_col = f'{self.uuid}_curr_node'
        for src_node_id, dst_node_id in nx.edge_dfs(self.G):
            if node_col not in df.columns:
                # this is the first node we're visiting, add its id to the
                # `node_col` column as the current node ID for each rows
                df[node_col] = src_node_id

                # initialize the path column with the first node id as string, so
                # we can later append new node IDs with a vectorized operation
                if self.path_column is not None:
                    df[self.path_column] = str(src_node_id)
            edge_data = self.G.get_edge_data(src_node_id, dst_node_id)
            src_node = self.get_node(src_node_id)
            dst_node = self.get_node(dst_node_id)
            if isinstance(dst_node, Output):
                dst_node.update(df, df[node_col] == src_node_id)
            flt = (df[node_col] == src_node_id) & (src_node.eval(df, edge_data))
            if self.path_column:
                # store the path which touched these rows
                df.loc[flt, self.path_column] = df[self.path_column] + f',{dst_node_id}'
            # update the matching rows' curr_node column to the next node,
            # we'll use this to select the source rows for running the
            # edge pointing from this node to the next
            df.loc[flt, node_col] = dst_node_id

        # remove the temporary current node column
        df = df.drop(node_col, axis=1)
        return df

    def draw(self, **kwargs):
        """Draw the graph.

        Args:
            See pandag.plot.plot_dag

        Returns:
            None

        """
        plot.plot_dag(self.G, **kwargs)
