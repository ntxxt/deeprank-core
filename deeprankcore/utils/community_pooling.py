import warnings
import community
import torch
import matplotlib.pyplot as plt
import numpy as np
import markov_clustering as mc
import networkx as nx
from torch_scatter import scatter_max, scatter_mean
from torch_geometric.nn.pool.pool import pool_edge, pool_batch
from torch_geometric.nn.pool.consecutive import consecutive_cluster
from torch_geometric.data import Batch, Data


def plot_graph(graph, cluster):

    pos = nx.spring_layout(graph, iterations=200)
    nx.draw(graph, pos, node_color=cluster)
    plt.show()


def get_preloaded_cluster(cluster, batch):

    nbatch = torch.max(batch) + 1
    for ib in range(1, nbatch):
        cluster[batch == ib] += torch.max(cluster[batch == ib - 1]) + 1
    return cluster


def community_detection_per_batch( # pylint: disable=too-many-locals
    edge_index, batch, num_nodes: int, edge_attr=None, method: str = "mcl"
):
    """Detects clusters of nodes based on the edge attributes (distances)

    Args:
        edge_index (Tensor): Edge index.
        num_nodes (int): Number of nodes.
        edge_attr (Tensor, optional): Edge attributes. Defaults to None.
        method (str, optional): Method. Defaults to "mcl".

    Raises:
        ValueError: Requires a valid clustering method ('mcl' or 'louvain')

    Returns:
        cluster Tensor
    """

    # make the networkX graph
    g = nx.Graph()
    g.add_nodes_from(range(num_nodes))

    for iedge, (i, j) in enumerate(edge_index.transpose(0, 1).tolist()):
        if edge_attr is None:
            g.add_edge(i, j)
        else:
            g.add_edge(i, j, weight=edge_attr[iedge])

    num_batch = max(batch) + 1
    all_index = range(num_nodes)
    cluster, ncluster = [], 0

    for ib in range(num_batch):

        index = torch.tensor(all_index)[batch == ib].tolist()
        subg = g.subgraph(index)

        # detect the communities using Louvain method
        if method == "louvain":
            c = community.best_partition(subg)
            cluster += [v + ncluster for k, v in c.items()]
            ncluster = max(cluster)

        # detect communities using MCL
        elif method == "mcl":
            matrix = nx.to_scipy_sparse_array(subg)
            # run MCL with default parameters
            result = mc.run_mcl(matrix)
            mc_clust = mc.get_clusters(result)  # get clusters

            index = np.zeros(subg.number_of_nodes()).astype("int")
            for ic, c in enumerate(mc_clust):
                index[list(c)] = ic + ncluster
            cluster += index.tolist()
            ncluster = max(cluster)

        else:
            raise ValueError(f"Clustering method {method} not supported")
    # return
    device = edge_index.device
    return torch.tensor(cluster).to(device)


<<<<<<< HEAD
def community_detection(edge_index, num_nodes, edge_attr=None, method="mcl"): # pylint: disable=too-many-locals
    """Detects clusters of nodes based on the edge attributes (distances)
=======
def community_detection(edge_index, num_nodes: int, edge_attr=None, method: str = "mcl"): # pylint: disable=too-many-locals
    """Detects clusters of nodes based on the edge attributes (distances).
>>>>>>> main

    Args:
        edge_index (Tensor): Edge index.
        num_nodes (int): Number of nodes.
        edge_attr (Tensor, optional): Edge attributes. Defaults to None.
        method (str, optional): Method. Defaults to "mcl".

    Raises:
        ValueError: Requires a valid clustering method ('mcl' or 'louvain')

    Returns:
        cluster Tensor


    Examples:

        >>> import torch
        >>> from torch_geometric.data import Data, Batch
        >>> edge_index = torch.tensor([[0, 1, 1, 2, 3, 4, 4, 5],
        >>>                            [1, 0, 2, 1, 4, 3, 5, 4]], dtype=torch.long)
        >>> x = torch.tensor([[0], [1], [2], [3], [4], [5]],
        >>>                  dtype=torch.float)
        >>> data = Data(x=x, edge_index=edge_index)
        >>> data.pos = torch.tensor(np.random.rand(data.num_nodes, 3))
        >>> c = community_detection(data.edge_index, data.num_nodes)
    """
    # make the networkX graph
    g = nx.Graph()
    g.add_nodes_from(range(num_nodes))

    for iedge, (i, j) in enumerate(edge_index.transpose(0, 1).tolist()):
        if edge_attr is None:
            g.add_edge(i, j)
        else:
            g.add_edge(i, j, weight=edge_attr[iedge])

    # get the device
    device = edge_index.device

    # detect the communities using Louvain detection
    if method == "louvain":
        cluster = community.best_partition(g)
        return torch.tensor([v for k, v in cluster.items()]).to(device)

    # detect the communities using MCL detection
    if method == "mcl":

        matrix = nx.to_scipy_sparse_array(g)

        # run MCL with default parameters
        result = mc.run_mcl(matrix)

        clusters = mc.get_clusters(result)  # get clusters

        index = np.zeros(num_nodes).astype("int")
        for ic, c in enumerate(clusters):
            index[list(c)] = ic

        return torch.tensor(index).to(device)

    raise ValueError(f"Clustering method {method} not supported")


def community_pooling(cluster, data):
    """Pools features and edges of all cluster members

    All cluster members are pooled into a single node that is assigned:
    - the max cluster value for each feature
    - the average cluster nodes position

    Args:
        cluster: Clusters.
        data: Features tensor.

    Returns:
        pooled features tensor


    Example:
        >>> import torch
        >>> from torch_geometric.data import Data, Batch
        >>> edge_index = torch.tensor([[0, 1, 1, 2, 3, 4, 4, 5],
        >>>                            [1, 0, 2, 1, 4, 3, 5, 4]], dtype=torch.long)
        >>> x = torch.tensor([[0], [1], [2], [3], [4], [5]],
        >>>                  dtype=torch.float)
        >>> data = Data(x=x, edge_index=edge_index)
        >>> data.pos = torch.tensor(np.random.rand(data.num_nodes, 3))
        >>> c = community_detection(data.edge_index, data.num_nodes)
        >>> batch = Batch().from_data_list([data, data])
        >>> cluster = community_detection(batch.edge_index, batch.num_nodes)
        >>> new_batch = community_pooling(cluster, batch)
    """

    # determine what the batches has as attributes
    has_internal_edges = hasattr(data, "internal_edge_index")
    has_pos2d = hasattr(data, "pos2d")
    has_pos = hasattr(data, "pos")
    has_cluster = hasattr(data, "cluster0")

    if has_internal_edges:
        warnings.warn(
            """Internal edges are not supported anymore.
            You should probably prepare the hdf5 file with
            a more up to date version of this software.""", DeprecationWarning)

    cluster, perm = consecutive_cluster(cluster)
    cluster = cluster.to(data.x.device)

    # pool the node infos
    x, _ = scatter_max(data.x, cluster, dim=0)

    # pool the edges
    edge_index, edge_attr = pool_edge(cluster, data.edge_index, data.edge_attr)

    # pool the pos
    if has_pos:
        pos = scatter_mean(data.pos, cluster, dim=0)
    if has_pos2d:
        pos2d = scatter_mean(data.pos2d, cluster, dim=0)

    if has_cluster:
        c0, c1 = data.cluster0, data.cluster1

    # pool batch
    if hasattr(data, "batch"):
        batch = None if data.batch is None else pool_batch(perm, data.batch)
        data = Batch(
            batch=batch, x=x, edge_index=edge_index, edge_attr=edge_attr, pos=pos
        )

        if has_cluster:
            data.cluster0 = c0
            data.cluster1 = c1

    else:
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, pos=pos)

        if has_pos2d:
            data.pos2d = pos2d

        if has_cluster:
            data.cluster0 = c0
            data.cluster1 = c1

    return data
