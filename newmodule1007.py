import random
import matplotlib.pyplot as plt
import networkx as nx
from getTopologyFromCaida import getTopo
import numpy as np
import time
import environment as en
from Logger import logout

#KEEPALIVE_TIME = 60
KEEPALIVE_TIME = en.KEEPALIVE_TIME
HOLD_TIME = KEEPALIVE_TIME * 3
RUN_TIME = 2000
#
TOLERANCE_FACTOR = en.TOLERANCE_FACTOR
seqnum = en.seqnum

#计算有路径连接的节点对
def link_node(traffic,logic_elist):
    G = nx.Graph()
    G.add_edges_from(logic_elist)
    link_node = []
    for nodes in traffic:
        if not nx.has_path(G, nodes[0], nodes[1]):
            continue
        link_node.append((nodes[0], nodes[1]))
    return link_node

def cacul_traffic(N):
    traffic = []
    for i in range(N):
        for j in range(N):
            if i != j:
                traffic.append([i, j])
    return traffic

def cacul_edge(topology):
    phy_elist = []
    logic_elist = []
    for i in range(len(topology)):
        # for j in range(i+1, len(topology[0])):
        for j in range(i, len(topology[0])):
            if topology[i][j] == 1:
                phy_elist.append((i, j))
                logic_elist.append((i, j))

    return phy_elist,logic_elist

def calcul_load(traffic, phy_elist, logic_elist):
    #starttime1 = time.time()
    #   孤立节点应该不加入计算
    G = nx.Graph()
    G.add_edges_from(logic_elist)

    load = [0 for i in range(len(phy_elist))]
    for nodes in traffic:
        #   判断是否为孤立节点，若是，则不加入计算流量
        if not nx.has_path(G, nodes[0], nodes[1]):
            continue
        path = nx.shortest_path(G, nodes[0], nodes[1])
        for i in range(len(path)-1):
            link_num = (path[i], path[i+1]) if path[i]<=path[i+1] else (path[i+1], path[i])
            idx = phy_elist.index(link_num)
            load[idx] += 1
    return load


def calcul_topology(link_num, link_state, timestep, traffic, phy_elist, logic_elist, load):
    if link_state == 1:
        logout("add_link_num:" + str(link_num))
        #print("add_link_num:", link_num)
        logic_elist.append(link_num)
    elif link_state == -1:
        logout("delete_link_num:"+str(link_num))
        #print("delete_link_num:", link_num)
        if link_num in logic_elist:
            logic_elist.remove(link_num)

    return calcul_load(traffic, phy_elist, logic_elist)

def cacul_faillink(phy_elist, logic_elist):
    return len(phy_elist) - len(logic_elist)

#   node暂时没有很多功能
class Node(object):
    def __init__(self, id):
        self.node_id = id

#   link包含当前负载、额定负载、keepAlive时间（<60, 与失效时间相关）
#   异步应保持每个链路两端的keepAlive时刻相近（暂时设置为<5）  双通好麻烦，单通吧
#   连接状态0、1、-1
class Link(object):
    def __init__(self, load, keepAlive_Timer, link_num):
        self.link_state = 1
        self.link_num = link_num
        self.link_rated_load = load * (1 + TOLERANCE_FACTOR) #   a容忍系数=0.2
        self.link_now_load = load
        self.keepAlive_Timer = keepAlive_Timer  #   timer计时器
        self.holdTime_Timer = keepAlive_Timer
        self.reStart_Timer = 0
        self.readyDown = 0    #   断链标志
        self.readyStart = 0
        self.manual_damage = 0  #   判断是否为故意破坏，是则不会恢复连接

    def update_link(self, timestep, traffic, phy_elist, logic_elist, load):
        #   链路因流量堵塞情况
        if self.link_now_load > self.link_rated_load:
            self.readyDown = 1
        if self.readyDown == 1 and self.link_now_load <= self.link_rated_load and not self.manual_damage:
            self.readyDown = 0
        #   holdtime计时器到期情况
        if self.holdTime_Timer >= HOLD_TIME:
            self.readyDown = 1

        #   破坏链路后经180s才断开连接
        if self.readyDown == 1 and self.holdTime_Timer >= HOLD_TIME:
            self.readyDown = 0
            self.keepAlive_Timer = -1
            self.holdTime_Timer = -1
            self.readyStart = 1
            #   更新edge表
            self.link_state = -1
            load = calcul_topology(self.link_num, self.link_state, timestep, traffic, phy_elist, logic_elist, load)
            self.link_now_load = load[phy_elist.index(self.link_num)]
        elif self.readyDown == 1:
            self.holdTime_Timer += 1
            # 堵塞时照旧发送keepalive，但不再置位holdtimer
            self.keepAlive_Timer = (self.keepAlive_Timer + 1) % KEEPALIVE_TIME

        #   重新建立连接
        if self.readyStart == 1 and self.reStart_Timer == en.reStart_Timer and not self.manual_damage:
            self.readyStart = 0
            self.reStart_Timer = 0
            self.keepAlive_Timer = 0
            self.holdTime_Timer = 0
            #   更新edge表
            self.link_state = 1
            load = calcul_topology(self.link_num, self.link_state, timestep, traffic, phy_elist, logic_elist, load)
            self.link_now_load = load[phy_elist.index(self.link_num)]
        elif self.readyStart == 1:
            self.reStart_Timer += 1

        #   正常通信情况
        if self.readyStart == 0 and self.readyDown == 0:
            #   累计时间步，holdtime到180之前没有keepalive也将触发失效
            self.keepAlive_Timer += 1
            self.holdTime_Timer += 1
            #   每60s交换一次keepalive报文
            if self.keepAlive_Timer >= KEEPALIVE_TIME:
                self.keepAlive_Timer = 0
                self.holdTime_Timer = 0

        #   更新负载
        if self.link_state == 1:
            self.link_now_load = load[phy_elist.index(self.link_num)]

        return load

# def init_topology():
#     topology = getTopo("graph.json")
#
#     topology = [[int(i) for i in j] for j in topology]
#     for i in range(212):
#         for j in range(212):
#             if i == j:
#                 topology[i][j] = 1
#
#     return topology

def init_topology():
    topology = getTopo("graph.json")

    topology = [[int(i) for i in j] for j in topology]
    for i in range(212):
        topology[i][i] = 1
    return topology

def init_network(phy_elist, load):
    #   建立link并赋初值
    links = []
    for e in phy_elist:
        now_load = load[phy_elist.index(e)]
        new_link = Link(now_load, keepAlive_Timer=random.randint(1, KEEPALIVE_TIME), link_num=e)
        links.append(new_link)
    print("initialize successfully!!!")

    return links

def get_action_num(action):
    action = np.array(action)
    b = np.argwhere(action == 1)
    return (b[0][0],b[0][1])
    # num = len(action)
    # for i in range(num):
    #     for j in range(num):
    #         if action[i][j] == 1:
    #             return (i,j)

# def get_topology(logic_elist,load):
#     num = 212
#     topology = []
#     for i in range(num):
#         topology.append([])
#         for j in range(num):
#             if (i,j) in logic_elist:
#                 topology[i].append(load[logic_elist.index((i,j))])
#             else:
#                 topology[i].append(0)
#     return topology

def get_topology(logic_elist,load):
    num = 212
    topology = np.zeros((num,num))
    for (i,j) in logic_elist:
        topology[i,j] = load[logic_elist.index((i,j))]
    return topology

# def get_topology(logic_elist):
#     num = 212
#     topology = []
#     for i in range(num):
#         topology.append([])
#         for j in range(num):
#             if (i,j) in logic_elist:
#                 topology[i].append(1)
#             else:
#                 topology[i].append(0)
#     return topology

def begin_cicle(traffic, phy_elist, logic_elist, load, action, run_time,links):
    #print("run time:", run_time)

    timestep = 0
    action_num = get_action_num(action)

    failload = []
    loadsum = []
    faillink_num = []
    while(timestep < run_time):
        #   开始时先断掉attack link
        if timestep == 0:
            damage_link = links[phy_elist.index(action_num)]
            damage_link.readyDown = 1
            damage_link.manual_damage = 1
        for link in links:
            if link.link_num[0] != link.link_num[1]:
                load = link.update_link(timestep, traffic, phy_elist, logic_elist, load)
        failload.append(sum(load))
        loadsum.append(sum(load))
        faillink_num.append(cacul_faillink(phy_elist, logic_elist))
        timestep += 1

    return get_topology(logic_elist,load),faillink_num,loadsum

def create_attackList(phy_elist):
    listlength = len(phy_elist)
    ran = np.random.randint(1,listlength,seqnum)
    # action_list = []
    # for idx in ran:
    #     action_list.append(phy_elist[idx])
    action_list = [phy_elist[8], phy_elist[44], phy_elist[9], phy_elist[75], phy_elist[96],
                    phy_elist[112], phy_elist[111], phy_elist[141],phy_elist[188],phy_elist[228]]
    print("chose these link:", action_list)

    return action_list

# def create_attackList(phy_elist):
#     # listlength = len(phy_elist)
#     # load_index = [i[0] for i in sorted(enumerate(load), key=lambda x: x[1])]
#     # action_list = []
#     # for i in range(seqnum):
#     #     action_list.append(phy_elist[load_index[listlength-i-1]])
#     action_list = [phy_elist[8], phy_elist[44], phy_elist[9], phy_elist[75], phy_elist[96],
#                    phy_elist[112], phy_elist[111], phy_elist[141],phy_elist[188],phy_elist[228]]
#     print("chose these link:", action_list)
#
#     return action_list



if __name__ == '__main__':
    topology = []  # 拓扑文件,对称矩阵简化为上三角矩阵(算了好像更麻烦
    # topology = [[0]]  跟自己的邻接矩阵应该为1，否则画不出节点
    traffic = []  # 背景流量对，设置为两两互发 n^2
    phy_elist = []  # 边队列(i, j)
    logic_elist = []
    load = []  # load队列，与边一一对应
    links = []  # link队列，与边和load一一对应
    action_list = []    #   失效链路队列
    N = 212  # 节点数量

    #   初始化拓扑
    topology = init_topology()
    # print(topology)

    #   初始化load
    traffic = cacul_traffic(N)
    phy_elist, logic_elist = cacul_edge(topology)

    G = nx.Graph()
    G.add_edges_from(logic_elist)
    pos = nx.circular_layout(G)
    nx.draw(G, pos, with_labels=True)
    plt.show()

    load = [0 for i in range(len(phy_elist))]
    load = calcul_load(traffic, phy_elist, logic_elist, load)
    print(load)

    #   初始化网络
    links = init_network(phy_elist, load)

    #   失效链路选择
    action_list = create_attackList()

    #   开始时间循环
    # begin_cicle(traffic, phy_elist, logic_elist, load, action=action_list[0], run_time=2000)

    print("end")


    # #   失效链路数目变化
    # plt.rcParams['font.sans-serif'] = ['SimHei']  # 添加这条可以让图形显示中文
    # x_axis_data = [i for i in range(RUN_TIME)]
    # y_axis_data = [0] + faillink_num[:RUN_TIME-1]
    # # plot中参数的含义分别是横轴值，纵轴值，线的形状，颜色，透明度,线的宽度和标签
    # plt.plot(x_axis_data, y_axis_data)
    # # 显示标签，如果不加这句，即使在plot中加了label='一些数字'的参数，最终还是不会显示标签
    # plt.legend(loc="upper right")
    # plt.xlabel('x轴数字')
    # plt.ylabel('y轴数字')
    # plt.show()



