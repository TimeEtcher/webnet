# Time:2022 2022/3/1 17:20
# Author: Jasmay
# -*- coding: utf-8 -*-
import time
import logging
from Logger import logout
import numpy as np

re = np.load("reward202210072206.npy",allow_pickle=True)
length = len(re)
result = []
for i in range(length):
    result.append(re[i][-1])

print(result)
print(result[-1])
print(np.max(result))

