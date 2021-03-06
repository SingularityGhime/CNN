# -*- coding: utf-8 -*-
"""Greekfile.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dDhlHFL-RTZX-nrV28h5_5Q_k-SOKNDs
"""

#imports
import torch, torchvision
from torch import nn
from torch import optim
from torchvision.transforms import ToTensor
import matplotlib.pyplot as plt
import torch.nn.functional as F
import cv2
import os
import csv
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader

#drive for colab
from google.colab import drive
drive.mount('/gdrive')



#parameters
nb_epoch = 100
lr = 0.01
momentum = 0.5
input_size = 28*28
hidden_layers = 100
log_interval = 5
random_seed = 69
torch.backends.cudnn.enabled = False
torch.manual_seed(random_seed)

#greek image path
Train_Dataset_Path = r"/gdrive/MyDrive/greeksymbol/"
Test_Dataset_Path = r"/gdrive/My Drive/greeksymbol/"

# dataset and loaders
from logging import root
train_transforms = torchvision.transforms.Compose([torchvision.transforms.Grayscale(), torchvision.transforms.Resize((28,28)), torchvision.transforms.functional.invert,torchvision.transforms.ToTensor()],)
train_dataset = torchvision.datasets.ImageFolder(root = Train_Dataset_Path, transform = train_transforms) #imagefolder attribute converts folders with images to datasets
test_dataset = torchvision.datasets.ImageFolder(root = Train_Dataset_Path, transform = train_transforms)

train_loader = torch.utils.data.DataLoader(train_dataset, batch_size = 1, shuffle = True, num_workers = 2)
test_loader = torch.utils.data.DataLoader(train_dataset, batch_size = 27, shuffle = True, num_workers = 2)

#checking dataset
test_dataset[1][0]

#function to extract path of image
def extract_files(path, store):
    for root, __, files in os.walk(path):
      for f in files:
        if f.endswith(".png"):
         store.append(
                     os.path.join(root, f) # add an appropriate reading flag if you want
                     # optional
                     # "foldername": os.path.dirname(root)
                     )
#function to make csv with 784 values
def write_to_csv(storedfiles, test_loader):
    alpha = "alpha"
    beta = "beta"
    gamma = "gamma"
    a_list = list(range(1, 785))
    a_list.insert(0, 'Label')
    with open(f"/gdrive/My Drive/Greekdataset/greek.csv", 'w', newline='') as f:
      the_writer = csv.writer(f)
      the_writer.writerow(a_list)  
      for i in range(len(storedfiles)):
        n = (test_dataset[i][0]).numpy()
        n = n.flatten()
        if alpha in storedfiles[i]:
          m = np.insert(n,0,0)
          m = m.flatten()
          the_writer.writerow(m)
        elif beta in storedfiles[i]: 
          m = np.insert(n,0,1)
          m = m.flatten()
          the_writer.writerow(m)
        elif gamma in storedfiles[i]:
          m = np.insert(n,0,2)
          m = m.flatten()
          the_writer.writerow(m)
#function to make csv with img name and label  
def write_imgnameandlabel(storedfiles):
    alpha = "alpha"
    beta = "beta"
    gamma = "gamma"
    with open(f"/gdrive/My Drive/Greekdataset/greekimgname.csv", 'w', newline='') as g:
      imgname_label = csv.writer(g)
      imgname_list = ['imgpath', 'label']
      imgname_label.writerow(imgname_list)
      for i in range(len(storedfiles)):
        if alpha in storedfiles[i]:
          temp = [storedfiles[i], 0]
          imgname_label.writerow(temp)
        if beta in storedfiles[i]:
          temp = [storedfiles[i], 1]
          imgname_label.writerow(temp)
        if gamma in storedfiles[i]:
          temp = [storedfiles[i], 2]
          imgname_label.writerow(temp)

#writing csv
info = []
extract_files(Train_Dataset_Path, info)
write_to_csv(info, test_loader)
write_imgnameandlabel(info)

#network classes
class myNetwork(nn.Module):
    def __init__(self):
        super(myNetwork, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d(p = 0.5)
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop( self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x)



#initializg network object and optimizing
greeknetwork = myNetwork()
optimizer = optim.SGD(greeknetwork.parameters(), lr=lr,
                      momentum=momentum)
# arrays/list to store losses
train_losses = []
train_counter = []
test_losses = []
test_counter = [i*len(train_loader.dataset) for i in range(nb_epoch + 1)]

#training function
def train(epoch):
  greeknetwork.train()
  for batch_idx, (data, target) in enumerate(train_loader):
    optimizer.zero_grad()
    output = greeknetwork(data)
    loss = F.nll_loss(output, target)   #loss fucntion
    loss.backward()
    optimizer.step()                    #optimizing
    if batch_idx % log_interval == 0:
      print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
        epoch, batch_idx * len(data), len(train_loader.dataset),
        100. * batch_idx / len(train_loader), loss.item()))
      train_losses.append(loss.item())
      train_counter.append(
        (batch_idx*64) + ((epoch-1)*len(train_loader.dataset)))
      #saving models
      torch.save(greeknetwork.state_dict(), r"/gdrive/MyDrive/trainer/model.pth")
      torch.save(optimizer.state_dict(), r"/gdrive/MyDrive/trainer/optimizer.pth")

#test function
def test():
  #setting to eval
  greeknetwork.eval()
  test_loss = 0
  correct = 0
  with torch.no_grad():
    for data, target in test_loader:
      output = greeknetwork(data)
      test_loss += F.nll_loss(output, target, size_average=False).item()  #loss function
      pred = output.data.max(1, keepdim=True)[1]
      correct += pred.eq(target.data.view_as(pred)).sum()
  test_loss /= len(test_loader.dataset)
  test_losses.append(test_loss)
  print('\nTest set: Avg. loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
    test_loss, correct, len(test_loader.dataset),
    100. * correct / len(test_loader.dataset)))

#training the model for 100 epochs even though we get the accuracy needed in 30 epochs
test()
for epoch in range(1, nb_epoch+1):
  train(epoch)
  test()

#loading the model into different object of same network and optimizing it
PATH1 = r"/gdrive/My Drive/trainer/model.pth"
PATH2 = r"/gdrive/My Drive/trainer/optimizer.pth"
subnetwork = myNetwork()
subnetwork.load_state_dict(torch.load(PATH1))
subnetwork.eval()
optimizer = optim.SGD(subnetwork.parameters(), lr=lr,
                      momentum=momentum)
optimizer.load_state_dict(torch.load(PATH2))

examples = enumerate(test_loader)
batch_idx, (example_data, example_targets) = next(examples)
torch.max(example_data[1])

#predicting the dataset
with torch.no_grad():
  output1 = subnetwork(example_data)
  fig = plt.figure()
  for i in range(9):
    plt.subplot(3,3,i+1)
    plt.tight_layout()
    plt.imshow(example_data[i][0], cmap='gray', interpolation='none')
    a = output1.data.max(1, keepdim=True)[1][i].item()
    if a == 0:
      plt.title("Prediction: Alpha")
    if a == 1:
      plt.title("Prediction: Beta")
    if a == 2:
      plt.title("Prediction: Gamma")
    plt.xticks([])
    plt.yticks([])

#declaring an varaible for fc2 weight
layer1weight = greeknetwork.fc2.weight

#new subnetwork
class mysubNetwork(nn.Module):
    def __init__(self):
        super(mysubNetwork, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d(p = 0.5)
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2(x), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        return F.log_softmax(x)

#new object
sub_network = mysubNetwork()
sub_network.load_state_dict(torch.load(PATH1))
sub_network.eval()
optimizer1 = optim.SGD(sub_network.parameters(), lr=lr,
                      momentum=momentum)
optimizer1.load_state_dict(torch.load(PATH2))

examples1 = enumerate(test_loader)
batch_idx1, (example_data1, example_targets1) = next(examples1)

with torch.no_grad():
  testoutput = sub_network(example_data1)

#first image 50 values
testoutput[0]

#creating dataset fucntion from the csv files created above
class MyDataset(Dataset):

  def __init__(self,file_name):
    df = pd.read_csv(file_name)

    x=df.iloc[:,0].values
    y=df.iloc[:,1:].values
    self.n_samples = df.shape[0]
    self.x_train=torch.tensor(x,dtype=torch.float32)
    self.y_train=torch.tensor(y,dtype=torch.float32)
    self.y_train = torch.reshape(self.y_train, (27,1,28,28))
  def __len__(self):
    return self.n_samples
  
  def __getitem__(self,idx):
    return self.y_train[idx],self.x_train[idx]

#creating dataset using the above function and loading
csv_path = r"/gdrive/My Drive/Greekdataset/greek.csv"
dataset = MyDataset(csv_path)

train_loader4 = torch.utils.data.DataLoader(dataset, batch_size = 27, shuffle = False, num_workers = 2)
dataset.y_train.shape

examples2 = enumerate(train_loader4)
batch_idx, (example_data2, example_targets2) = next(examples2)

with torch.no_grad():
  testoutput1 = sub_network(example_data2)

#function to get SSD values
def SSD(a,b,idx):
  c= []
  for i in range(len(a)):
    d = 0
    for j in range(len(a[idx])):
      e = pow((a[idx][j]-b[i][j]).numpy(),2)
      d+=e
    c.append(d)
  return c

#getting index of alpha, beta, gamma images
for i in range(len(example_targets2)):
  if example_targets2[i] == 0:
    alpha_index = i
    continue;
  if example_targets2[i] == 1:
    beta_index = i
    continue;
  if example_targets2[i] == 2:
    gamma_index = i
    break;
print(alpha_index,beta_index, gamma_index)

#calucalting SSD values and printing
alpha_ssd  = SSD(testoutput1,testoutput1, alpha_index)
beta_ssd = SSD(testoutput1, testoutput1, beta_index)
gamma_ssd = SSD(testoutput1, testoutput1, gamma_index)
print("alpha_ssd", alpha_ssd)
print("beta_ssd", beta_ssd)
print("gamma_ssd", gamma_ssd)

#creating dataset from new images which also includes the handwritten alpha/beta/gamma 
dataset_with_newimages = r"/gdrive/MyDrive/Greeksymbolsnew"
newimage_dataset = torchvision.datasets.ImageFolder(root = dataset_with_newimages, transform = train_transforms)
newimage_loader = torch.utils.data.DataLoader(newimage_dataset, batch_size =30, shuffle = False, num_workers = 2)

examples3 = enumerate(newimage_loader)
batch_idx, (example_data3, example_targets3) = next(examples3)

with torch.no_grad():
  testoutput3 = sub_network(example_data3)

#printing out new ssd values of the new alpha, beta, gamma image
new_alpha_ssd = SSD(testoutput3,testoutput3,9)
new_beta_ssd = SSD(testoutput3,testoutput3,19)
new_gamma_ssd = SSD(testoutput3,testoutput3, 29)

print('new_alpha_ssd:', new_alpha_ssd)
print('new beta ssd:', new_beta_ssd)
print('new gamma ssd:', new_gamma_ssd)