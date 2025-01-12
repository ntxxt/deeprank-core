# DeeprankCore

| Badges | |
|:----:|----|
| **fairness** |  [![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F-green)](https://fair-software.eu) [![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/6403/badge)](https://bestpractices.coreinfrastructure.org/projects/6403) |
| **package** |  [![PyPI version](https://badge.fury.io/py/deeprankcore.svg)](https://badge.fury.io/py/deeprankcore) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/f3f98b2d1883493ead50e3acaa23f2cc)](https://app.codacy.com/gh/DeepRank/deeprank-core?utm_source=github.com&utm_medium=referral&utm_content=DeepRank/deeprank-core&utm_campaign=Badge_Grade) |
| **docs** | [![Documentation Status](https://readthedocs.org/projects/deeprankcore/badge/?version=latest)](https://deeprankcore.readthedocs.io/en/latest/?badge=latest) [![DOI](https://zenodo.org/badge/450496579.svg)](https://zenodo.org/badge/latestdoi/450496579) |
| **tests** | [![Build Status](https://github.com/DeepRank/deeprank-core/actions/workflows/build.yml/badge.svg)](https://github.com/DeepRank/deeprank-core/actions) ![Linting status](https://github.com/DeepRank/deeprank-core/actions/workflows/linting.yml/badge.svg?branch=main) [![Coverage Status](https://coveralls.io/repos/github/DeepRank/deeprank-core/badge.svg?branch=main)](https://coveralls.io/github/DeepRank/deeprank-core?branch=main) |
| **license** |  [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)  |


## Overview

![alt-text](./deeprankcore.png)

DeeprankCore is a deep learning framework for data mining Protein-Protein Interactions (PPIs) using Graph Neural Networks. 

DeeprankCore contains useful APIs for pre-processing PPIs data, computing features and targets, as well as training and testing GNN models.

Main features:
- Predefined atom-level and residue-level PPI feature types
  - e.g. atomic density, vdw energy, residue contacts, PSSM, etc.
- Predefined target type
  - e.g. binary class, CAPRI categories, DockQ, RMSD, FNAT, etc.
- Flexible definition of both new features and targets
- Graphs feature mapping
- Efficient data storage in HDF5 format
- Support both classification and regression (based on PyTorch and PyTorch Geometric)

DeeprankCore documentation can be found here : https://deeprankcore.rtfd.io/.

## Table of contents

- [DeeprankCore](#deeprankcore)
  - [Overview](#overview)
  - [Table of contents](#table-of-contents)
  - [Installation](#installation)
    - [Dependencies](#dependencies)
    - [Deeprank-Core Package](#deeprank-core-package)
  - [Documentation](#documentation)
  - [Quick start](#quick-start)
    - [Graphs generation](#graphs-generation)
    - [Dataset](#dataset)
    - [Training](#training)
      - [Custom GNN](#custom-gnn)
  - [h5x support](#h5x-support)
  - [Package development](#package-development)

## Installation

### Dependencies

Before installing deeprankcore you need to install:

 * [reduce](https://github.com/rlabduke/reduce): follow the instructions in the README of the reduce repository.
    * **How to build it without sudo privileges on a Linux machine**. After having run `make` in the reduce/ root directory, go to reduce/reduce_src/Makefile and modify `/usr/local/` to a folder in your home directory, such as `/home/user_name/apps`. Note that such a folder needs to be added to the PATH in the `.bashrc` file. Then run `make install` from reduce/. 
 * [msms](https://ssbio.readthedocs.io/en/latest/instructions/msms.html): `conda install -c bioconda msms`. *For MacOS with M1 chip users*: you can follow [these instructions](https://ssbio.readthedocs.io/en/latest/instructions/msms.html).
 * [pytorch](https://pytorch.org/get-started/locally/): `conda install pytorch torchvision torchaudio cpuonly -c pytorch` or `conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia`, for taking advantage of GPUs.
 * [pytorch-geometric](https://pytorch-geometric.readthedocs.io/en/latest/notes/installation.html): `conda install pyg -c pyg`
 * [Dependencies for pytorch geometric from wheels](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html#installation-from-wheels): `pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-${TORCH}+${CUDA}.html`. 
    - Here, `${TORCH}` and `${CUDA}` should be replaced by the pytorch and CUDA versions installed. You can find these using:
      - `python -c "import torch; print(torch.__version__)"` and
      - `python -c "import torch; print(torch.version.cuda)"`
    - For example: `https://data.pyg.org/whl/torch-2.0.0+cpu.html`
 * Only if you have a MacOS with M1 chip, additional steps are needed:
    * `conda install pytables`
    * See [this](https://stackoverflow.com/questions/30145751/python3-cant-find-and-import-pyqt5) solution to install PyQt5 or run `conda install pyqt`

### Deeprank-Core Package

Once the dependencies installed, you can install the latest release of deeprankcore using the PyPi package manager:

```
pip install deeprankcore
```

You can get all the new developments by cloning the repo and installing the code with

```
git clone https://github.com/DeepRank/deeprank-core
cd deeprank-core
pip install -e ./
```

## Documentation

More extensive and detailed documentation can be found [here](https://deeprankcore.rtfd.io/).

## Quick start

### Graphs generation

The process of generating graphs takes as input `.pdb` files representing protein-protein structural complexes and the correspondent Position-Specific Scoring Matrices (PSSMs) in the form of `.pssm` files. Query objects describe how the graphs should be built.

```python
from deeprankcore.query import QueryCollection, ProteinProteinInterfaceResidueQuery

queries = QueryCollection()

# Append data points
queries.add(ProteinProteinInterfaceResidueQuery(
    pdb_path = "1ATN_1w.pdb",
    chain_id1 = "A",
    chain_id2 = "B",
    targets = {
        "binary": 0
    },
    pssm_paths = {
        "A": "1ATN.A.pdb.pssm",
        "B": "1ATN.B.pdb.pssm"
    }
))
queries.add(ProteinProteinInterfaceResidueQuery(
    pdb_path = "1ATN_2w.pdb",
    chain_id1 = "A",
    chain_id2 = "B",
    targets = {
        "binary": 1
    },
    pssm_paths = {
        "A": "1ATN.A.pdb.pssm",
        "B": "1ATN.B.pdb.pssm"
    }
))
queries.add(ProteinProteinInterfaceResidueQuery(
    pdb_path = "1ATN_3w.pdb",
    chain_id1 = "A",
    chain_id2 = "B",
    targets = {
        "binary": 0
    },
    pssm_paths = {
        "A": "1ATN.A.pdb.pssm",
        "B": "1ATN.B.pdb.pssm"
    }
))

# Generate graphs and save them in hdf5 files
output_paths = queries.process("<output_folder>/<prefix_for_outputs>")

```

The user is free to implement his/her own query class. Each implementation requires the `build` method to be present.


### Dataset

Data can be split in sets implementing custom splits according to the specific application. Utility splitting functions are currently under development.

Assuming that the training, validation and testing ids have been chosen (keys of the hdf5 file), then the corresponding graphs can be saved in hdf5 files containing only references (external links) to the original one. For example:

```python
from deeprankcore.dataset import save_hdf5_keys

save_hdf5_keys("<original_hdf5_path.hdf5>", train_ids, "<train_hdf5_path.hdf5>")
save_hdf5_keys("<original_hdf5_path.hdf5>", valid_ids, "<val_hdf5_path.hdf5>")
save_hdf5_keys("<original_hdf5_path.hdf5>", test_ids, "<test_hdf5_path.hdf5>")
```

Now the GraphDataset objects can be defined:

```python
from deeprankcore.dataset import GraphDataset

node_features = ["bsa", "res_depth", "hse", "info_content", "pssm"]
edge_features = ["distance"]
target = "binary"

# Creating GraphDataset objects
dataset_train = GraphDataset(
    hdf5_path = "<train_hdf5_path.hdf5>",
    node_features = node_features,
    edge_features = edge_features,
    target = target
)
dataset_val = GraphDataset(
    hdf5_path = "<val_hdf5_path.hdf5>",
    node_features = node_features,
    edge_features = edge_features,
    target = target

)
dataset_test = GraphDataset(
    hdf5_path = "<test_hdf5_path.hdf5>",
    node_features = node_features,
    edge_features = edge_features,
    target = target
)
```

### Training

Let's define a Trainer instance, using for example of the already existing GNNs, GINet:

```python
from deeprankcore.trainer import Trainer
from deeprankcore.ginet import GINet

trainer = Trainer(
    GINet,
    dataset_train,
    dataset_val,
    dataset_test
)

```

By default, the Trainer class creates the folder `./output` for storing predictions information collected later on during training and testing. `HDF5OutputExporter` is the exporter used by default, but the user can specify any other implemented exporter or implement a custom one.

Optimizer (`torch.optim.Adam` by default) and loss function can be defined by using dedicated functions:

```python
import torch

trainer.configure_optimizers(torch.optim.Adamax, lr = 0.001, weight_decay = 1e-04)

```

Then the Trainer can be trained and tested, and the model can be saved:

```python
trainer.train(nepoch = 50, batch_size = 64, validate = True)
trainer.test()
trainer.save_model(filename = "<output_model_path.pth.tar>")

```

#### Custom GNN

It is also possible to define new network architectures:

```python
import torch 

def normalized_cut_2d(edge_index, pos):
    row, col = edge_index
    edge_attr = torch.norm(pos[row] - pos[col], p=2, dim=1)
    return normalized_cut(edge_index, edge_attr, num_nodes=pos.size(0))

class CustomNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = SplineConv(d.num_features, 32, dim=2, kernel_size=5)
        self.conv2 = SplineConv(32, 64, dim=2, kernel_size=5)
        self.fc1 = torch.nn.Linear(64, 128)
        self.fc2 = torch.nn.Linear(128, 1)

    def forward(self, data):
        data.x = F.elu(self.conv1(data.x, data.edge_index, data.edge_attr))
        weight = normalized_cut_2d(data.edge_index, data.pos)
        cluster = graclus(data.edge_index, weight)
        data = max_pool(cluster, data)

        data.x = F.elu(self.conv2(data.x, data.edge_index, data.edge_attr))
        weight = normalized_cut_2d(data.edge_index, data.pos)
        cluster = graclus(data.edge_index, weight)
        x, batch = max_pool_x(cluster, data.x, data.batch)

        x = scatter_mean(x, batch, dim=0)
        x = F.elu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        return F.log_softmax(self.fc2(x), dim=1)

trainer = Trainer(
    CustomNet,
    dataset_train,
    dataset_val,
    dataset_test
)

trainer.train(nepoch=50, batch_size = 64)

```

## h5x support

After installing  `h5xplorer`  (https://github.com/DeepRank/h5xplorer), you can execute the python file `deeprankcore/h5x/h5x.py` to explorer the connection graph used by deeprankcore. The context menu (right click on the name of the structure) allows to automatically plot the graphs using `plotly`.

## Package development

- Branching
  - When creating a new branch, please use the following convention: `<issue_number>_<description>_<author_name>`.
- Pull Requests
  - When creating a pull request, please use the following convention: `<type>: <description>`. Example _types_ are `fix:`, `feat:`, `build:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, and others based on the [Angular convention](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines).
- Software release
  - Before creating a new package release, make sure to have updated all version strings in the source code. An easy way to do it is to run `bump2version [part]` from command line after having installed [bump2version](https://pypi.org/project/bump2version/) on your local environment. Instead of `[part]`, type the part of the version to increase, e.g. minor. The settings in `.bumpversion.cfg` will take care of updating all the files containing version strings. 
