"""Tests for GraphML support."""

import pathlib
import os
import re
import pytest
import pandas as pd
import numpy as np

from pandag import Pandag
from pandag.graphml import generate_node_id


@pytest.fixture
def sample_df():
    """Sample DataFrame."""
    size = 100
    df = pd.DataFrame({'x': np.repeat(range(size), size),
                       'y': list(range(size)) * size})
    return df


def get_file(fn):
    path = os.path.join(pathlib.Path(__file__).parent.absolute(),
                        "files", fn)
    return path


def test_load():
    """Test GraphML import."""
    dag = Pandag()
    dag.load_graphml(get_file("box.graphml"))
    assert set(dag.G.nodes) == {0, 1, 2, 3, 4, 5, 6, 7}
    assert set(dag.G.edges) == {(0, 1), (1, 2), (1, 3), (2, 7), (3, 2), (3, 4),
                                (4, 2), (4, 5), (5, 6), (5, 2), (6, 7)}


def test_coords_type():
    """Test GraphML coordinates to be floats."""
    dag = Pandag()

    dag.load_graphml(get_file("box.graphml"))
    for node, data in dag.G.nodes(data=True):
        isinstance(getattr(data["node"], "_x", None), float)


def test_extract_ids():
    """Test GraphML import with custom node IDs."""
    dag = Pandag()
    dag.load_graphml(get_file("box.graphml"), custom_ids=True)
    assert set(dag.G.nodes) == {'0', '1', '6', '2', '3', '4', '5', '7'}
    assert set(dag.G.edges) == {('0', '1'), ('1', '6'), ('1', '2'), ('6', '7'),
                                ('2', '6'), ('2', '3'), ('3', '6'), ('3', '4'),
                                ('4', '5'), ('4', '6'), ('5', '7')}


def test_custom_id_func():
    """Test GraphML import with custom node IDs and extract method."""
    def id_extract(node, data):
        """Extract and return the node ID as integer."""
        pat = r"\[(?P<node_id>\w+)\]"
        m = re.search(pat, data["label"])
        if m:
            return (int(m.group("node_id")),
                    re.sub(pat, '', data["label"]).strip())

    dag = Pandag()
    dag.load_graphml(get_file("box.graphml"), custom_ids=True, node_id_func=id_extract)
    assert set(dag.G.nodes) == {0, 1, 6, 2, 3, 4, 5, 7}
    assert set(dag.G.edges) == {(0, 1), (1, 6), (1, 2), (6, 7),
                                (2, 6), (2, 3), (3, 6), (3, 4),
                                (4, 5), (4, 6), (5, 7)}


def test_labels():
    """Test decision labels."""
    dag = Pandag()
    dag.load_graphml(get_file("box.graphml"), custom_ids=True)

    assert dag.G.get_edge_data("0", "1").get("label") is None
    assert dag.G.get_edge_data("1", "6").get("label") is True
    assert dag.G.get_edge_data("2", "3").get("label") is False


def test_eval(sample_df):
    """Test eval and its results."""
    dag = Pandag()
    dag.load_graphml(get_file("box.graphml"), custom_ids=True)
    res = dag.eval(sample_df)

    query = "x>=60"
    assert all(res.query(query)["color"] == "red")
    assert all(res.query(query)["path"] == "0,1,6,7")

    query = "x>=60 and x<40"
    assert all(res.query(query)["color"] == "red")
    assert all(res.query(query)["path"] == "0,1,2,6,7")

    query = "x>=60 and x<40 and y>=60"
    assert all(res.query(query)["color"] == "red")
    assert all(res.query(query)["path"] == "0,1,2,3,6,7")

    query = "x>=60 and x<40 and y>=60 and y<40"
    assert all(res.query(query)["color"] == "red")
    assert all(res.query(query)["path"] == "0,1,2,3,4,6,7")

    query = "~x>=60 and ~x<40 and ~y>=60 and ~y<40"
    assert all(res.query(query)["color"] == "black")
    assert all(res.query(query)["path"] == "0,1,2,3,4,5,7")


def test_c4():
    """Test C4 algo."""
    def node_id_gen(node, data):
        """Convert string node IDs to int."""
        node_id, label = generate_node_id(node, data)
        return int(node_id), label

    c4_target = 0.9
    outrigger_target = 1.1
    outrigger_min = 1
    num_grace_days = 14

    dag = Pandag(path_column="dag_path")
    dag.load_graphml(get_file("c4.graphml"),
                     custom_ids=True,
                     local_dict=locals(),
                     node_id_func=node_id_gen)
    df = pd.read_pickle(get_file("c4.df.pickle"))
    df = df[["target_roas_old", "days_since_last_change"]]
    res = dag.eval(df)

    for idx, row in res.iterrows():
        if row.target_roas_old == c4_target:  # n0
            if row.days_since_last_change >= num_grace_days:  # n1
                assert row.target_roas_target == outrigger_target, f"index: {idx} failed"  # n3
            else:
                assert row.target_roas_target == row.target_roas_old, f"index: {idx} failed"  # n4
        else:
            assert row.target_roas_target == c4_target, f"index: {idx} failed"  # n2
        if row.target_roas_old >= outrigger_min:  # n6
            assert row.target_roas_rec == row.target_roas_old, f"index: {idx} failed" # n7
        else:
            assert row.target_roas_rec == row.target_roas_target, f"index: {idx} failed"  # n5
