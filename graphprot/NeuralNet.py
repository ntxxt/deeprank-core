import numpy as np
from tqdm import tqdm

# torch import
import torch
import torch.nn as nn
from torch.nn import MSELoss
import torch.nn.functional as F

# torch_geometric import
from torch_scatter import scatter_mean
from torch_geometric.data import DataLoader
from torch_geometric.nn import max_pool_x

# community pooling import
from .community_pooling import *

# graphprot import
from .DataSet import HDF5DataSet, DivideDataSet
from .ginet import GINet


class Net(torch.nn.Module):

    def __init__(self,input_shape):
        super(Net, self).__init__()

        self.conv1 = GINet(input_shape, 16)
        self.conv2 = GINet(16 , 32)

        self.fc1 = torch.nn.Linear(32, 64)
        self.fc2 = torch.nn.Linear(64, 1)

    def forward(self, data):

        act = nn.Tanhshrink()
        act = F.relu
        #act = nn.LeakyReLU(0.25)

        # first conv block
        data.x = act(self.conv1(data.x, data.edge_index,data.edge_attr))
        cluster = community_detection_per_batch(data.internal_edge_index,data.batch,data.num_nodes)
        data = community_pooling(cluster, data)

        # second conv block
        data.x = act(self.conv2(data.x, data.edge_index,data.edge_attr))
        cluster = community_detection_per_batch(data.internal_edge_index,data.batch,data.num_nodes)
        x, batch = max_pool_x(cluster, data.x, data.batch)

        # FC
        x = scatter_mean(x, batch, dim=0)
        x = act(self.fc1(x))
        x = self.fc2(x)
        #x = F.dropout(x, training=self.training)

        return x
        #return F.relu(x)

class NeuralNet(object):

    def __init__ (self, database, Net, node_feature = ['type','polarity','bsa'],
                        edge_feature = ['dist'], target = 'irmsd',
                        batch_size = 32, nepoch = 100, percent = [0.8,0.2],index=None):

        # dataset
        dataset = HDF5DataSet(root='./',database=database,index=index,
                              node_feature=node_feature,edge_feature=edge_feature, target=target)

        train_dataset, valid_dataset = DivideDataSet(dataset,percent=percent)

        # dataloader
        self.train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
        self.valid_loader = DataLoader(valid_dataset, batch_size=batch_size, shuffle=False)

        # get the device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # put the model
        self.model = Net(dataset.get(0).num_features).to(self.device)

        # optimizer/loss/epoch
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        self.loss = MSELoss()
        self.nepoch = nepoch


    def train(self,validate=False):

        self.model.train()
        for epoch in range(1, self.nepoch):
            loss = self._epoch(epoch)

            if validate:
                _, val_loss = self.eval(self.valid_loader)
                print ('Epoch [%04d] : train loss %e | valid loss %e' %(epoch,loss, val_loss))
            else:
                print ('Epoch [%04d] : train loss %e' %(epoch,loss))

    def eval(self,loader):

        self.model.eval()

        loss_func, loss_val = self.loss, 0
        out = []
        for data in loader:
            data = data.to(self.device)
            pred = self.model(data).reshape(-1)
            loss_val += loss_func(pred,data.y)
            out += pred.reshape(-1).tolist()
        return out, loss_val


    def _epoch(self,epoch):
        running_loss = 0
        for data in self.train_loader:
            data = data.to(self.device)
            self.optimizer.zero_grad()
            out = self.model(data).reshape(-1)
            loss = self.loss(out, data.y)
            running_loss += loss.data.item()
            loss.backward()
            self.optimizer.step()
        return running_loss


    def plot_scatter(self):

        import matplotlib.pyplot as plt

        self.model.eval()

        pred, truth = {'train':[], 'valid':[]}

        for data in self.train_loader:
            data = data.to(self.device)
            truth['train'] += data.y.tolist()
            pred['train'] += self.model(data).reshape(-1).tolist()


        for data in self.valid_loader:
            data = data.to(device)
            truth['valid'] += data.y.tolist()
            pred['valid'] += model(data).reshape(-1).tolist()

        plt.scatter(truth['train'],pred['train'],c='blue')
        plt.scatter(truth['valid'],pred['valid'],c='red')
        plt.show()