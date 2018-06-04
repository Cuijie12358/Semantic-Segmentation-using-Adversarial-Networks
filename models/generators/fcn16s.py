import os,sys

import chainer
import chainer.functions as F
import chainer.links as L
import numpy as np

sys.path.append(os.path.split(os.path.split(os.getcwd())[0])[0])
import functions as f


class FCN16s(chainer.Chain):
    """Fully Convolutional Network 16s"""

    def __init__(self, n_class=21):
        self.train=True
        super(FCN16s, self).__init__(
            conv1_1=L.Convolution2D(3, 64, 3, stride=1, pad=100),
            conv1_2=L.Convolution2D(64, 64, 3, stride=1, pad=1),
            conv2_1=L.Convolution2D(64, 128, 3, stride=1, pad=1),
            conv2_2=L.Convolution2D(128, 128, 3, stride=1, pad=1),
            conv3_1=L.Convolution2D(128, 256, 3, stride=1, pad=1),
            conv3_2=L.Convolution2D(256, 256, 3, stride=1, pad=1),
            conv3_3=L.Convolution2D(256, 256, 3, stride=1, pad=1),
            conv4_1=L.Convolution2D(256, 512, 3, stride=1, pad=1),
            conv4_2=L.Convolution2D(512, 512, 3, stride=1, pad=1),
            conv4_3=L.Convolution2D(512, 512, 3, stride=1, pad=1),
            conv5_1=L.Convolution2D(512, 512, 3, stride=1, pad=1),
            conv5_2=L.Convolution2D(512, 512, 3, stride=1, pad=1),
            conv5_3=L.Convolution2D(512, 512, 3, stride=1, pad=1),
            fc6=L.Convolution2D(512, 4096, 7, stride=1, pad=0),
            fc7=L.Convolution2D(4096, 4096, 1, stride=1, pad=0),
            score_fr=L.Convolution2D(4096, n_class, 1, stride=1, pad=0,
                nobias=True, initialW=np.zeros((n_class, 4096, 1, 1))),
            score_pool4=L.Convolution2D(512, n_class, 1, stride=1, pad=0,
                nobias=True, initialW=np.zeros((n_class, 512, 1, 1))),
            upscore2=L.Deconvolution2D(n_class, n_class, 4, stride=2,
                nobias=True, initialW=f.bilinear_interpolation_kernel(n_class, n_class, ksize=4),),
            upscore16=L.Deconvolution2D(n_class, n_class, 32, stride=16,
                nobias=True, initialW=f.bilinear_interpolation_kernel(n_class, n_class, ksize=32),),
        )

    def __call__(self, x):
        h = F.relu(self.conv1_1(x))
        h = F.relu(self.conv1_2(h))
        h = F.max_pooling_2d(h, 2, stride=2, pad=0)
        h = F.relu(self.conv2_1(h))
        h = F.relu(self.conv2_2(h))
        h = F.max_pooling_2d(h, 2, stride=2, pad=0)
        h = F.relu(self.conv3_1(h))
        h = F.relu(self.conv3_2(h))
        h = F.relu(self.conv3_3(h))
        h = F.max_pooling_2d(h, 2, stride=2, pad=0)
        h = F.relu(self.conv4_1(h))
        h = F.relu(self.conv4_2(h))
        h = F.relu(self.conv4_3(h))
        pool4 = F.max_pooling_2d(h, 2, stride=2, pad=0)
        h = F.relu(self.conv5_1(pool4))
        h = F.relu(self.conv5_2(h))
        h = F.relu(self.conv5_3(h))
        h = F.max_pooling_2d(h, 2, stride=2, pad=0)
        h = F.relu(self.fc6(h))
        h = F.dropout(h, ratio=.5)
        h = F.relu(self.fc7(h))
        h = F.dropout(h, ratio=.5)
        score_fr = self.score_fr(h)

        upscore2 = self.upscore2(score_fr)
        score_pool4 = self.score_pool4(pool4)
        score_pool4c = f.crop_to_target(score_pool4, target=upscore2)
        fuse_pool4 = upscore2 + score_pool4c

        upscore16 = self.upscore16(fuse_pool4)
        score = f.crop_to_target(upscore16, target=x)

        return score
