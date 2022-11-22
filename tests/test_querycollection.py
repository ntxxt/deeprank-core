from tempfile import mkdtemp
from shutil import rmtree
from os.path import join
import h5py
from deeprankcore.features import surfacearea
from deeprankcore.query import SingleResidueVariantResidueQuery, QueryCollection, Query
from deeprankcore.domain.aminoacidlist import alanine, phenylalanine
from tests._utils import PATH_TEST


def querycollection_tester(n_queries, n_cpus, combine_files, feature_modules):
    """
    Generic function to test QueryCollection class.

    Args:
        n_queries: number of queries to be generated.
        
        n_cpus: number of cpus to be used during the queries processing.

        combine_files: boolean for combining the hdf5 files generated by the subprocesses.
            By default, the hdf5 files generated are combined into one, and then deleted.

        feature_modules: list of feature modules (from .deeprankcore.features) to be passed to process.
            If "all", all available modules in deeprankcore.features are used to generate the features.
    """

    output_directory = mkdtemp()
    prefix = join(output_directory, "test-process-queries")
    collection = QueryCollection()

    try:
        for number in range(1, n_queries + 1):
            collection.add(SingleResidueVariantResidueQuery(
                str(PATH_TEST / "data/pdb/101M/101M.pdb"),
                "A",
                number,
                None,
                alanine,
                phenylalanine,
                pssm_paths={"A": str(PATH_TEST / "data/pssm/101M/101M.A.pdb.pssm")},
                ))

        output_paths = collection.process(prefix, n_cpus, combine_files, feature_modules)
        assert len(output_paths) > 0

        graph_names = []
        for path in output_paths:
            with h5py.File(path, "r") as f5:
                graph_names += list(f5.keys())

        for query in collection.queries:
            query_id = query.get_query_id()
            assert query_id in graph_names, f"missing in output: {query_id}"
    except Exception as e:
        print(e)

    return collection, output_directory, output_paths


def test_querycollection_process():
    """
    Tests processing method of QueryCollection class.
    """

    n_queries = 10
    n_cpus = 3
    combine_files = True
    feature_modules = "all"

    collection, output_directory, _ = querycollection_tester(n_queries, n_cpus, combine_files, feature_modules)
    
    assert type(collection.queries) == list
    assert len(collection.queries) == n_queries
    for query in collection.queries:
        assert issubclass(type(query), Query)

    rmtree(output_directory)


def test_querycollection_process_single_feature_module():
    """
    Tests processing for generating a single feature.
    """

    n_queries = 10
    n_cpus = 3
    combine_files = True
    feature_modules = [surfacearea]

    _, output_directory, _ = querycollection_tester(n_queries, n_cpus, combine_files, feature_modules)

    rmtree(output_directory)


def test_querycollection_process_all_features_modules():
    """
    Tests processing for generating all features.
    """

    n_queries = 10
    n_cpus = 3
    combine_files = True
    feature_modules = "all"

    _, output_directory, _ = querycollection_tester(n_queries, n_cpus, combine_files, feature_modules)

    rmtree(output_directory)


def test_querycollection_process_combine_files_true():
    """
    Tests processing for combining hdf5 files into one.
    """

    n_queries = 10
    n_cpus = 3
    combine_files = True
    feature_modules = "all"

    _, output_directory, output_paths = querycollection_tester(n_queries, n_cpus, combine_files, feature_modules)

    assert len(output_paths) == 1

    rmtree(output_directory)


def test_querycollection_process_combine_files_false():
    """
    Tests processing for keeping all generated hdf5 files .
    """

    n_queries = 10
    n_cpus = 3
    combine_files = False
    feature_modules = "all"

    _, output_directory, output_paths = querycollection_tester(n_queries, n_cpus, combine_files, feature_modules)

    assert len(output_paths) == n_cpus

    rmtree(output_directory)
