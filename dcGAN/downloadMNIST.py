import torchvision.datasets as datasets

datasets.MNIST(root='./data', train=True, download=True, transform=None)