from uuid import uuid4
from pdb2sql import pdb2sql
import numpy as np
from deeprankcore.molstruct.structure import Chain
from deeprankcore.molstruct.atom import Atom
from deeprankcore.molstruct.pair import AtomicContact, ResidueContact
from deeprankcore.molstruct.variant import SingleResidueVariant
from deeprankcore.utils.graph import Edge, Graph
from deeprankcore.utils.buildgraph import get_structure
from deeprankcore.features.contact import add_features
from deeprankcore.domain.aminoacidlist import alanine
from deeprankcore.domain import edgestorage as Efeat



def _get_atom(chain: Chain, residue_number: int, atom_name: str) -> Atom:

    for residue in chain.residues:
        if residue.number == residue_number:
            for atom in residue.atoms:
                if atom.name == atom_name:
                    return atom

    raise ValueError(
        f"Not found: chain {chain.id} residue {residue_number} atom {atom_name}"
    )


def _wrap_in_graph(edge: Edge):
    g = Graph(uuid4().hex)
    g.add_edge(edge)
    return g

def _get_atomiccontact(residue_num1: int, atom_name1: str, residue_num2: int, atom_name2: str):
    pdb_path = "tests/data/pdb/101M/101M.pdb"

    pdb = pdb2sql(pdb_path)
    try:
        structure = get_structure(pdb, "101m")
    finally:
        pdb._close() # pylint: disable=protected-access

    variant = SingleResidueVariant(structure.chains[0].residues[10], alanine)

    contact = AtomicContact(
        _get_atom(structure.chains[0], residue_num1, atom_name1), 
        _get_atom(structure.chains[0], residue_num2, atom_name2)
    )
    edge_obj = Edge(contact)
    add_features(pdb_path, _wrap_in_graph(edge_obj), variant)

    return edge_obj

def test_vanderwaals_positive():
    """MET 0: N - CA, very close. 
    
    Should have positive vanderwaals energy.
    """

    edge_close=_get_atomiccontact(0,"N",0,"CA")
    assert not np.isnan(edge_close.features[Efeat.VANDERWAALS])
    assert edge_close.features[Efeat.VANDERWAALS] > 0.0, edge_close.features[
        Efeat.VANDERWAALS
    ]

def test_vanderwaals_negative():
    """MET 0 N - ASP 27 CB, very far.
    
    Should have negative vanderwaals energy.
    """

    edge_far = _get_atomiccontact(0,"N",27,"CB")
    assert not np.isnan(edge_far.features[Efeat.VANDERWAALS])
    assert edge_far.features[Efeat.VANDERWAALS] < 0.0, edge_far.features[
        Efeat.VANDERWAALS
    ]
    
def test_vanderwaals_morenegative():
    """MET 0 N - PHE 138 CG, intermediate distance.
      
    Should have more negative vanderwaals energy than the war interaction.
    """
    
    edge_intermediate=_get_atomiccontact(0,"N",138,"CG")
    edge_far = _get_atomiccontact(0,"N",27,"CB")
    assert not np.isnan(edge_intermediate.features[Efeat.VANDERWAALS])
    assert (
        edge_intermediate.features[Efeat.VANDERWAALS]
        < edge_far.features[Efeat.VANDERWAALS]
    ), f"{edge_intermediate.features[Efeat.VANDERWAALS]} >= {edge_far.features[Efeat.VANDERWAALS]}"

def test_edge_distance():
    """Check the edge distances.
    """

    edge_close=_get_atomiccontact(0,"N",0,"CA")
    edge_intermediate=_get_atomiccontact(0,"N",138,"CG")
    edge_far = _get_atomiccontact(0,"N",27,"CB")

    assert (
        edge_close.features[Efeat.DISTANCE]
        < edge_intermediate.features[Efeat.DISTANCE]
    ), f"{edge_close.features[Efeat.DISTANCE]} >= {edge_intermediate.features[Efeat.DISTANCE]}"
    assert (
        edge_far.features[Efeat.DISTANCE]
        > edge_intermediate.features[Efeat.DISTANCE]
    ), f"{edge_far.features[Efeat.DISTANCE]} <= {edge_intermediate.features[Efeat.DISTANCE]}"

def test_attractive_electrostatic_close():
    """ARG 139 CZ - GLU 136 OE2, very close attractive electrostatic energy.
    """

    close_attracting_edge = _get_atomiccontact(139,"CZ",136,"OE2")
    assert not np.isnan(close_attracting_edge.features[Efeat.ELECTROSTATIC])
    assert (
        close_attracting_edge.features[Efeat.ELECTROSTATIC] < 0.0
    ), close_attracting_edge.features[Efeat.ELECTROSTATIC]

def test_attractive_electrostatic_far():
    """ARG 139 CZ - ASP 20 OD2, far attractive electrostatic energy.
    """

    far_attracting_edge=_get_atomiccontact(139,"CZ",20,"OD2")
    close_attracting_edge = _get_atomiccontact(139,"CZ",136,"OE2")
    assert not np.isnan(far_attracting_edge.features[Efeat.ELECTROSTATIC])
    assert (
        far_attracting_edge.features[Efeat.ELECTROSTATIC] < 0.0
    ), far_attracting_edge.features[Efeat.ELECTROSTATIC]
    assert (
        far_attracting_edge.features[Efeat.ELECTROSTATIC]
        > close_attracting_edge.features[Efeat.ELECTROSTATIC]
    ), f"{far_attracting_edge.features[Efeat.ELECTROSTATIC]} <= {close_attracting_edge.features[Efeat.ELECTROSTATIC]}"
   
def test_repulsive_electrostatic():
    """GLU 109 OE2 - GLU 105 OE1, repulsive electrostatic energy.
    """

    opposing_edge=_get_atomiccontact(109,"OE2",105,"OE1")
    assert not np.isnan(opposing_edge.features[Efeat.ELECTROSTATIC])
    assert (
        opposing_edge.features[Efeat.ELECTROSTATIC] > 0.0
    ), opposing_edge.features[Efeat.ELECTROSTATIC]

def test_cal_residue_contact():
    pdb_path = "tests/data/pdb/101M/101M.pdb"

    pdb = pdb2sql(pdb_path)
    try:
        structure = get_structure(pdb, "101m")
    finally:
        pdb._close() # pylint: disable=protected-access

    variant = SingleResidueVariant(structure.chains[0].residues[10], alanine)
    
    """Check that we can calculate residue contacts.
    """
    contact = ResidueContact(
        structure.chains[0].residues[0], structure.chains[0].residues[1]
    )
    edge = Edge(contact)
    add_features(pdb_path, _wrap_in_graph(edge), variant)
    assert not np.isnan(edge.features[Efeat.DISTANCE]) > 0.0
    assert edge.features[Efeat.DISTANCE] > 0.0
    assert edge.features[Efeat.DISTANCE] < 1e5

    assert not np.isnan(edge.features[Efeat.ELECTROSTATIC])
    assert edge.features[Efeat.ELECTROSTATIC] != 0.0, edge.features[
        Efeat.ELECTROSTATIC
    ]

    assert not np.isnan(edge.features[Efeat.VANDERWAALS])
    assert edge.features[Efeat.VANDERWAALS] != 0.0, edge.features[
        Efeat.VANDERWAALS
    ]
