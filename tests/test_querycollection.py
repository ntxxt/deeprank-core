from tempfile import mkdtemp
from shutil import rmtree
from os.path import join
import h5py
from deeprankcore.features import surfacearea
from deeprankcore.query import QueryCollection, Query, SingleResidueVariantResidueQuery, ProteinProteinInterfaceResidueQuery
from deeprankcore.domain.aminoacidlist import alanine, phenylalanine
from . import PATH_TEST

def _querycollection_tester( # pylint: disable = too-many-locals
    query_type: str = 'ppi',
    n_queries: int = 10, 
    feature_modules = None, 
    cpu_count: int = 1, 
    combine_output: bool = True,
):
    """
    Generic function to test QueryCollection class.

    Args:
        query_type (str): query type to be generated. It accepts only 'ppi' (ProteinProteinInterface) or 'var' (SingleResidueVariant).
            Defaults to 'ppi'.
        n_queries (int): number of queries to be generated.
        feature_modules: module or list of feature modules (from .deeprankcore.features) to be passed to process.
            If None, all available modules in deeprankcore.features are used to generate the features.
        cpu_count (int): number of cpus to be used during the queries processing.
        combine_output (bool): boolean for combining the hdf5 files generated by the processes.
            By default, the hdf5 files generated are combined into one, and then deleted.
    """

    if query_type == 'ppi':
        queries = [ProteinProteinInterfaceResidueQuery(
                        str("tests/data/pdb/3C8P/3C8P.pdb"),
                        "A",
                        "B",
                        pssm_paths={"A": str(PATH_TEST / "data/pssm/3C8P/3C8P.A.pdb.pssm"), "B": str(PATH_TEST / "data/pssm/3C8P/3C8P.B.pdb.pssm")},
                    ) for _ in range(n_queries)]
    elif query_type == 'var':
        queries = [SingleResidueVariantResidueQuery(
                        str(PATH_TEST / "data/pdb/101M/101M.pdb"),
                        "A",
                        None, # placeholder
                        insertion_code= None,
                        wildtype_amino_acid= alanine,
                        variant_amino_acid= phenylalanine,
                        pssm_paths={"A": str(PATH_TEST / "data/pssm/101M/101M.A.pdb.pssm")},
                    ) for _ in range(n_queries)]
    else:
        raise ValueError("Please insert a valid type (either ppi or var).")

    output_directory = mkdtemp()
    prefix = join(output_directory, "test-process-queries")
    collection = QueryCollection()

    for idx in range(n_queries):
        if query_type == 'var':
            queries[idx]._residue_number = idx + 1 # pylint: disable=protected-access
            collection.add(queries[idx])
        else:
            collection.add(queries[idx], warn_duplicate=False)

    output_paths = collection.process(prefix, feature_modules, cpu_count, combine_output)
    assert len(output_paths) > 0

    graph_names = []
    for path in output_paths:
        with h5py.File(path, "r") as f5:
            graph_names += list(f5.keys())

    for query in collection.queries:
        query_id = query.get_query_id()
        assert query_id in graph_names, f"missing in output: {query_id}"

    return collection, output_directory, output_paths


def test_querycollection_process():
    """
    Tests processing method of QueryCollection class.
    """

    for query_type in ['ppi', 'var']:
        n_queries = 5

        collection, output_directory, _ = _querycollection_tester(query_type, n_queries=n_queries)
        
        assert isinstance(collection.queries, list)
        assert len(collection.queries) == n_queries
        for query in collection.queries:
            assert issubclass(type(query), Query)

        rmtree(output_directory)


def test_querycollection_process_single_feature_module():
    """
    Tests processing for generating a single feature.
    """

    for query_type in ['ppi', 'var']:

        # test with single feature in list
        _, output_directory, _ = _querycollection_tester(query_type, feature_modules=[surfacearea])
        rmtree(output_directory)

        # test with single feature NOT in list
        _, output_directory, _ = _querycollection_tester(query_type, feature_modules=surfacearea)
        rmtree(output_directory)


def test_querycollection_process_all_features_modules():
    """
    Tests processing for generating all features.
    """

    for query_type in ['ppi', 'var']:

        _, output_directory, _ = _querycollection_tester(query_type)

        rmtree(output_directory)


def test_querycollection_process_combine_output_true():
    """
    Tests processing for combining hdf5 files into one.
    """

    for query_type in ['ppi', 'var']:

        _, output_directory_t, output_paths_t = _querycollection_tester(query_type)

        _, output_directory_f, output_paths_f = _querycollection_tester(query_type, combine_output = False, cpu_count=2)

        assert len(output_paths_t) == 1

        keys_t = {}
        with h5py.File(output_paths_t[0],'r') as file_t:
            for key, value in file_t.items():
                keys_t[key] = value

        keys_f = {}
        for output_path in output_paths_f:
            with h5py.File(output_path,'r') as file_f:
                for key, value in file_f.items():
                    keys_f[key] = value

        assert keys_t == keys_f

        rmtree(output_directory_t)
        rmtree(output_directory_f)


def test_querycollection_process_combine_output_false():
    """
    Tests processing for keeping all generated hdf5 files .
    """

    for query_type in ['ppi', 'var']:

        cpu_count = 2
        combine_output = False

        _, output_directory, output_paths = _querycollection_tester(query_type, cpu_count = cpu_count, combine_output = combine_output)

        assert len(output_paths) == cpu_count

        rmtree(output_directory)
