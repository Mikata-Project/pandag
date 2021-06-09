"""Tests for GraphML support."""

import pathlib
import os
import re
import pytest
import pandas as pd
import numpy as np

from pandag import Pandag


@pytest.fixture
def sample_df():
    """Sample DataFrame."""
    size = 100
    df = pd.DataFrame({'x': np.repeat(range(size), size),
                       'y': list(range(size))*size})
    return df


@pytest.fixture
def box_file():
    path = os.path.join(pathlib.Path(__file__).parent.absolute(),
                        "files", "box.graphml")
    return path


def test_load(box_file):
    """Test GraphML import."""
    dag = Pandag()

    dag.load_graphml(box_file)
    assert set(dag.G.nodes) == {'n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7'}
    assert set(dag.G.edges) == {('n0', 'n1'), ('n1', 'n2'), ('n1', 'n3'),
                                ('n2', 'n7'), ('n3', 'n2'), ('n3', 'n4'),
                                ('n4', 'n2'), ('n4', 'n5'), ('n5', 'n6'),
                                ('n5', 'n2'), ('n6', 'n7')}


def test_extract_ids(box_file):
    """Test GraphML import with custom node IDs."""
    dag = Pandag()
    dag.load_graphml(box_file, custom_ids=True)
    assert set(dag.G.nodes) == {'0', '1', '6', '2', '3', '4', '5', '7'}
    assert set(dag.G.edges) == {('0', '1'), ('1', '6'), ('1', '2'), ('6', '7'),
                                ('2', '6'), ('2', '3'), ('3', '6'), ('3', '4'),
                                ('4', '5'), ('4', '6'), ('5', '7')}


def test_custom_id_func(box_file):
    """Test GraphML import with custom node IDs and extract method."""
    def id_extract(node, data):
        """Extract and return the node ID as integer."""
        pat = r"\[(?P<node_id>\w+)\]"
        m = re.search(pat, data["label"])
        if m:
            return (int(m.group("node_id")),
                    re.sub(pat, '', data["label"]).strip())

    dag = Pandag()
    dag.load_graphml(box_file, custom_ids=True, node_id_func=id_extract)
    assert set(dag.G.nodes) == {0, 1, 6, 2, 3, 4, 5, 7}
    assert set(dag.G.edges) == {(0, 1), (1, 6), (1, 2), (6, 7),
                                (2, 6), (2, 3), (3, 6), (3, 4),
                                (4, 5), (4, 6), (5, 7)}


def test_labels(box_file):
    """Test decision labels."""
    dag = Pandag()
    dag.load_graphml(box_file, custom_ids=True)

    assert dag.G.get_edge_data("0", "1").get("label") is None
    assert dag.G.get_edge_data("1", "6").get("label") is True
    assert dag.G.get_edge_data("2", "3").get("label") is False


def test_eval(box_file, sample_df):
    """Test eval and its results."""
    dag = Pandag()
    dag.load_graphml(box_file, custom_ids=True)
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
