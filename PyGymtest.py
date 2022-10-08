import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from collections import OrderedDict
from WEBNET import WEBNET
from WEBNET import Storage
import random
import environment as en
import matplotlib.pyplot as plt
import time as time
from Logger import logout


# 超参数
BATCH_SIZE = en.BATCH_SIZE
MEMORY_CAPACITY = en.MEMORY_CAPACITY
LR = 0.01
EPSILON = 0.9  # 随机选取的概率，如果概率小于这个随机数，就采取greedy的行为
GAMMA = 0.9
TARGET_REPLACE_ITER = en.TARGET_REPLACE_ITER

num = 10
action = np.zeros((num, num))
n_actions = len(action)
state = np.zeros((n_actions, n_actions))

env = WEBNET(state,action)
node = env.node  # 打击的节点
state_action = node * node * 2 # 实验环境的状态

#时间限制
timelimit = en.timelimit



class Net(nn.Module):
    i = 0
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 1, 3)
        self.fc1 = nn.Linear((node - 2) * (node - 2), 1000)
        self.fc1.weight.data.normal_(0, 0.1)  # initialization
        self.fc2 = nn.Linear(1000, 100)
        self.fc2.weight.data.normal_(0, 0.1)  # initialization
        self.fc = nn.Linear(2, 100)
        self.out = nn.Linear(200, timelimit)
        self.out.weight.data.normal_(0, 0.1)  # initialization


    def forward(self, x,y):
        x = F.relu(self.conv1(x))
        x = x.view(-1, (node - 2) * (node - 2))
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x= F.relu(x)
        y = y.view(-1, 2)
        y = self.fc(y)
        out = torch.cat((x, y), dim=0)
        out = out.view(-1,200)
        actions_value = self.out(out)
        return actions_value


class DQN(object):
    def __init__(self):
        # DQN是Q-Leaarning的一种方法，但是有两个神经网络，一个是eval_net一个是target_net
        # 两个神经网络相同，参数不同，是不是把eval_net的参数转化成target_net的参数，产生延迟的效果
        self.eval_net, self.target_net = Net(), Net()

        self.learn_step_counter = 0  # 学习步数计数器
        self.memory_counter = 0  # 记忆库中位值的计数器
        self.memory = list()  # 初始化记忆库
        # 记忆库初始化为全0，存储两个state的数值加上一个a(action)和一个r(reward)的数值
        self.optimizer = torch.optim.Adam(self.eval_net.parameters(), lr=LR)
        self.loss_func = nn.MSELoss()  # 优化器和损失函数

    # 接收环境中的观测值，并采取动作
    def choose_time(self, state,action):
        # sa为状态和动作
        time = 0
        if np.random.uniform() < EPSILON:
            # 随机值得到的数有百分之九十的可能性<0.9,所以该if成立的几率是90%
            # 90%的情况下采取actions_value高的作为最终动作
            time_value = self.eval_net.forward(state,action)
            time = torch.max(time_value, 1)[1].data.numpy()
            time = time[0].tolist()  # return the argmax index
        else:
            time = random.randint(1,timelimit-1)
        return time

        # 记忆库，存储之前的记忆，学习之前的记忆库里的东西

    def store_transition(self, stor):
        # 如果记忆库满了, 就覆盖老数据
        if self.memory_counter > MEMORY_CAPACITY:
            index = self.memory_counter % MEMORY_CAPACITY
            self.memory[index] = stor
        else:
            self.memory.append(stor)
        self.memory_counter += 1

    # 抽取记忆库中的批数据
    def get_store(self, memory, index):

        b_memory = np.array(memory)[index]
        lenth = len(b_memory)

        ls = list()
        la = list()
        lreward = list()
        lnexts= list()
        lnexta = list()
        lt = list()
        for i in range(0,lenth):
            ls.append(torch.FloatTensor(b_memory[i].state))
            la.append(torch.FloatTensor(b_memory[i].action))
            lnexts.append(torch.FloatTensor(b_memory[i].next_state))
            lnexta.append(torch.FloatTensor(b_memory[i].next_action))
            lreward.append(torch.tensor(b_memory[i].reward))
            lt.append(torch.tensor(b_memory[i].time))
        b_s = torch.stack(ls,dim=0)
        b_a = torch.stack(la, dim=0)
        b_nexts = torch.stack(lnexts, dim=0)
        b_nexta = torch.stack(lnexta,dim=0)
        b_reward = torch.stack(lreward,dim=0)
        b_time = torch.stack(lt,dim=0)

        return b_s,b_a,b_nexts,b_nexta,b_reward,b_time

    def Learn(self):
        # target net 参数更新,每隔TARGET_REPLACE_ITE更新一下
        if self.learn_step_counter % TARGET_REPLACE_ITER == 0:
            self.target_net.load_state_dict(self.eval_net.state_dict())
        self.learn_step_counter += 1
        # targetnet是时不时更新一下，evalnet是每一步都更新

        # 抽取记忆库中的批数据
        sample_index = np.random.choice(MEMORY_CAPACITY, BATCH_SIZE)
        b_s,b_a,b_nexts,b_nexta,b_reward,b_time = self.get_store(self.memory,sample_index)
        b_time = b_time.view(BATCH_SIZE,1)
        # 针对做过的动作b_a, 来选 q_eval 的值, (q_eval 原本有所有动作的值)
        q_next = self.target_net(b_nexts,b_nexta).detach()  # q_next 不进行反向传递误差, 所以 detach
        q_eval = self.eval_net(b_s,b_a).gather(1, b_time)  # shape (batch, 1)
        a = q_next.max(1)
        b = a[0]
        q_target = b_reward + GAMMA * q_next.max(1)[0]  # shape (batch, 1)
        q_target = q_target.view(BATCH_SIZE,-1).to(torch.float32)
        q_eval = q_eval.to(torch.float32)
        loss = self.loss_func(q_eval, q_target)

        # 计算, 更新 eval net
        self.optimizer.zero_grad()
        loss.backward()  # 误差反向传播
        self.optimizer.step()

def main():
    #训练长度限制
    seqnum = 100
    dqn = DQN()
    rewardlist = []
    for i_episode in range(seqnum):
        #print("epoch begin:", i_episode)
        sa = env.reset()  # 得到环境的反馈，现在的状态
        print("----------------------reset over-----------------------------")
        print("-------------------------------------------------------------")
        done = False
        reward = 0
        i = 0
        ep_reward = []
        while not done:
            i += 1
            action = np.argwhere(sa[1] == 1)[0]
            action = torch.tensor(action, dtype=torch.float)
            state = torch.tensor(sa[0], dtype=torch.float)
            state = torch.unsqueeze(state, 0)
            t = dqn.choose_time(state,action)  # 根据dqn来接受现在的状态，得到一个行为
            nextsa,reward,linkrewardper,loadrewardper,done = env.step(sa,t)  # 根据环境的行为，给出一个反馈
            next_action = np.argwhere(nextsa[1] == 1)[0]
            next_action = torch.tensor(next_action, dtype=torch.float)
            next_state = torch.tensor(nextsa[0], dtype=torch.float)
            next_action = torch.tensor(next_action, dtype=torch.float)
            next_state = torch.tensor(next_state, dtype=torch.float)
            next_state = torch.unsqueeze(next_state, 0)
            stor = Storage(state,action, reward, next_state,next_action, t)
            dqn.store_transition(stor)  # dqn存储现在的状态，行为，反馈，和环境导引的下一个状态
            logout('Ep: ', i_episode, '| ActionNum: ', i ,"/",en.seqnum-1,' | Time:', t, ' | Reward: ', reward, ' | LinkRewardPer: ', linkrewardper, ' | LoadRewardPer: ', loadrewardper)
            if dqn.memory_counter > MEMORY_CAPACITY:
                #print("---------------Learn episod:",i_episode,"------------------")
                dqn.Learn()
            #将下一个阶段的状态和动作更新上去
            sa = nextsa
            ep_reward.append(reward)
        rewardlist.append(ep_reward)
    rewardlist = np.array(rewardlist,dtype=object)

    x = [i for i in range(seqnum)]
    y = []
    for i in range(seqnum):
        y.append(rewardlist[i][-1])

    plt.plot(x,y)
    #第3步：显示图形
    plt.show()
    time1 = time.strftime('%Y%m%d%H%M', time.localtime())
    numpydata = 'reward'+time1+'.npy'
    modeldata = './model'+time1+'.pkl'
    np.save(numpydata,rewardlist)
    pathmodel = modeldata
    torch.save(dqn.eval_net, pathmodel)


if __name__ == '__main__':
    main()