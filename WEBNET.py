import numpy as np
import newmodule
import networkx as nx
import environment as en
from Logger import logout

num = 212
rewardfactor = en.rewardfactor
class WEBNET:
    #state是否能够输入一个二维数组，数组的横和列代表节点，值代表当前的流量
    #action就是节点，输入这个action代表打击这个节点
    def __init__(self,states,action):
        self.node = num
        self.action = np.zeros((self.node, self.node))
        self.state = np.zeros((self.node, self.node))
        self.sa = np.stack([self.state,self.action],axis=2)
        #网络构建参数
        self.topology = []  # 拓扑文件, 跟自己的邻接矩阵(0, 0)应该为1，否则画不出节点
        self.traffic = []  # 背景流量对,设置为两两互发 n^2
        self.phy_elist = []  # 边队列(i, j)
        self.logic_elist = []
        self.load = [0 for i in range(num)]  # load队列,与边一一对应
        self.links = []  # link队列存放link对象,与边和load一一对应
        self.action_list = []  # 失效链路队列
        # 用来进行加权
        self.line = np.sum(self.state)
        self.loadsum = np.sum(self.load)
        self.allline = np.sum(self.state)

    #将当前状态写入
    def reset(self):
        #这里可以写成从某个函数里面取得，action中可用的链路为1，不可用的为0
        # self.sa = np.random.random((self.node,self.node,2))
        newmodule.reset()
        self.topology = newmodule.init_topology()
        self.phy_elist, self.logic_elist = newmodule.cacul_edge(self.topology)
        self.traffic = newmodule.cacul_traffic(self.logic_elist)
        self.traffic,self.load = newmodule.calcul_load(self.traffic, self.phy_elist, self.logic_elist)
        self.links = newmodule.init_network(self.phy_elist, self.load)
        self.action_list = newmodule.create_attackList(self.phy_elist)
        self.state = self.topology
        self.action = self.creat_action_matrix()
        #self.action_list = newmodule.create_attackList(self.phy_elist, self.load)
        self.sa = np.stack([self.state,self.action],axis=0)

        self.line = np.sum(self.state)
        self.loadsum = np.sum(self.load)
        self.allline = np.sum(self.state)
        #返回状态和可用的链路
        return self.sa

    #当前行为执行完之后会给的反馈，返回状态state,执行完成后的奖励，以及是否结束
    def step(self,state_action,time):
        # 是否结束
        done = False
        action = newmodule.get_action_num(self.action)
        self.state,faillink,loadnum= newmodule.begin_cicle(self.traffic, self.phy_elist, self.logic_elist, self.load, action, time,self.links)
        if len(self.action_list) > 0:
            self.action = self.creat_action_matrix()

        if len(self.action_list) == 0:
            done = True

        # 修改后所有流量之和
        newpath = np.sum(self.load)
        #修改后的所有可用链路数
        newline = np.sum(self.state)

        #权重设置
        #pathweight = 0.5
        #nodeweight = 0.5

        faillink_sum = 0
        failload_sum = 0
        length = len(faillink)
        if length > 10:
            calcmean = 10
        else:
            calcmean = length
        for i in range(length-calcmean,length):
            faillink_sum = faillink_sum + faillink[i]
            failload_sum = failload_sum + (self.loadsum-loadnum[i])
        if calcmean == 0:
            calcmean = 1
        faillink_mean = faillink_sum/calcmean
        failload_mean = failload_sum/calcmean
        linkrewardper = faillink_mean/len(self.phy_elist)
        loadrewardper = failload_mean/self.loadsum
        reward = faillink_mean
        self.sa = np.stack([self.state,self.action],axis=0)

        if linkrewardper > en.rewardfactor:
            done = True
        return self.sa,reward,linkrewardper,loadrewardper,done

    def creat_action_matrix(self):
        #   输入action_list中的action二元组, 返回一个n*n的action矩阵
        if len(self.action_list) > 0:
            action_num = self.action_list.pop(0)

        logout("attack link:", action_num)
        logout("other links:",self.action_list)

        action = np.zeros((num,num))
        action[action_num[0],action_num[1]] = 1
        #action = []
        # for i in range(num):
        #     action.append([])
        #     for j in range(num):
        #         if action_num[0] == i and action_num[1] == j:
        #             action[i].append(1)
        #         else:
        #             action[i].append(0)
        return action

class Storage:
    #用来存储状态s在动作a下获得的reward和达成的结果
    def __init__(self, state,action,reward,next_state,next_action,time):
        self.state = state
        self.action = action
        self.next_state = next_state
        self.next_action = next_action
        self.reward = reward
        self.time = time


