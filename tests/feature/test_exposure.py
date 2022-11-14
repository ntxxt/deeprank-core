import numpy
from pdb2sql import pdb2sql
from deeprankcore.features.exposure import add_features
from deeprankcore.models.graph import build_residue_graph
from deeprankcore.models.pdb import get_structure, get_residue_contact_pairs
from deeprankcore.domain import nodefeatures


def test_add_features():
    pdb_path = "tests/data/pdb/1ATN/1ATN_1w.pdb"

    pdb = pdb2sql(pdb_path)
    try:
        structure = get_structure(pdb, "1ATN_1w")
    finally:
        pdb._close() # pylint: disable=protected-access

    residues = set([])
    for residue1, residue2 in get_residue_contact_pairs(
        pdb_path, structure, "A", "B", 8.5
    ):
        residues.add(residue1)
        residues.add(residue2)

    graph = build_residue_graph(residues, "1ATN-1w", 8.5)

    add_features(pdb_path, graph)

    assert numpy.any(
        node.features[nodefeatures.HSE] != 0.0 for node in graph.nodes
    )

    assert numpy.any(
        node.features[nodefeatures.RESDEPTH] != 0.0 for node in graph.nodes
    )
