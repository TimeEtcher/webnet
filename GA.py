import random
import newmodule
import numpy as np
from Logger import logout
import matplotlib.pyplot as plt
# 获取最开始的时间步
def get_timestep(M,attacknum, timelimit):
    timeStepList = []
    # for i in range(M):
    #     timesteps = list()
    #     for j in range(attacknum):
    #         timesteps.append(random.randint(10, timelimit))
    #     timeStepList.append(timesteps)
    d = timelimit//M
    for i in range(M):
        attacktime = d*i
        timesteps = [attacktime for j in range(attacknum)]
        timeStepList.append(timesteps)
    return timeStepList

# 适应度函数，利用最后的reward当作适应度的值，适应度值越高越好
def fitness(num,attacknum,timesteps,traffic,phy_elist,logic_elist,load,action_list,links):
    reward = 0
    for i in range(attacknum):
        time = timesteps[i]
        action_num = action_list[i]
        #logout("attack"+str(action_num))
        _, faillink, _ = newmodule.begin_cicle(traffic, phy_elist,logic_elist, load,
                                                         action_num, time, links)
    faillink_sum = 0
    length = len(faillink)
    if length > 10:
        calcmean = 10
    else:
        calcmean = length
    for i in range(length - calcmean, length):
        faillink_sum = faillink_sum + faillink[i]
    if calcmean == 0:
        calcmean = 1
    faillink_mean = faillink_sum / calcmean
    reward = faillink_mean
    #将reward作为适应度，reward越高适应度越好
    return reward


def creat_action_matrix(action_list,logic_elist,num):
    #   输入action_list中的action二元组, 返回一个n*n的action矩阵
    while len(action_list) > 0:
        action_num = action_list.pop(0)
        if action_num in logic_elist:
            break
    print("attack link:", action_num)
    print("other links:",action_list)

    action = np.zeros((num,num))
    action[action_num[0],action_num[1]] = 1
    return action

def select(num,attacknum,population):
    """
    :param population:种群，规模为M
    :return:返回选择后的种群
    """
    # 按照population顺序存放其适应度
    all_fitness = []
    i = 0
    for timesteps in population:
        # 每次都要重新初始化网络系统
        traffic, phy_elist, logic_elist, load, action_list, links = init_network()
        logout('time:',i,'----------------------------timesteps:'+str(timesteps))
        fit = fitness(num,attacknum,timesteps,traffic,phy_elist,logic_elist,load,action_list,links)
        logout('fitness:'+str(fit))
        all_fitness.append(fit)
        i = i + 1
    # 适应度函数的总和
    sum_fitness = sum(all_fitness)
    # 以第一个个体为0号，计算每个个体轮盘开始的位置，position的位置和population是对应的
    all_position = []
    for i in range(0, len(all_fitness)):
        all_position.append(sum(all_fitness[:i + 1]) / sum_fitness)
    # 轮盘赌进行选择
    # 经过选择后的新种群
    next_population = []
    for i in range(0, len(population)):
        # 生成0-1之间的随机小数
        ret = random.random()
        for j in range(len(all_position)):
            # 根据轮盘赌规则进行选择
            if all_position[j] > ret:
                next_population.append(population[j])
                break
    return next_population,all_fitness

def cross(M,Pc,attacknum,population):
    """
    :param M: 种群规模
    :param Pc: 交叉概率
    :param population:选择后的种群
    :param attacknum:打击链路总数
    :return:交叉后的种群
    """
    num = M * Pc
    # 计数器，判断是否交换次数达到num次
    count = 0
    i = 0
    # # 交叉后的种群
    # next_population2 = []
    # 由于选择后的种群本来就是随机的，所以让相邻两组做交叉，从第一组开始直到达到交叉概率停止
    while (i < M-1):
        # while(count < num):
        # 随机产生交叉点
        position = random.randrange(0, attacknum - 1)
        # print(position)
        # print(position)
        # 将两个个体从交叉点断开
        tmp11 = population[i][:position]
        tmp12 = population[i][position:]
        tmp21 = population[i + 1][:position]
        tmp22 = population[i + 1][position:]
        # 重新组合成新的个体
        # print(next_population1[i])
        population[i] = tmp11 + tmp22
        # print(next_population1[i])
        population[i + 1] = tmp21 + tmp12
        i += 1
    return population

def variation(M, Pm,attacknum,population,timelimit):
    """
    :param M:种群规模
    :param Pm:变异概率
    :param population:选择后的种群
    :param attacknum:打击链路总数
    :param timelimit:时间步的时间限制
    :return:变异后的种群
    """
    for i in range(M):
        ret = random.random()
        # 生成0-1的随机数，如果随机数
        if ret < Pm:
            # 随机产生变异点
            position = random.randrange(0, attacknum)
            population[i][position] = random.randint(10, timelimit)

    return population

def search(attacknum,population):
    # 按照population顺序存放其适应度
    all_fitness = []
    for timesteps in population:
        # 初始化网络系统
        traffic, phy_elist, logic_elist, load, action_list, links = init_network()
        all_fitness.append(fitness(attacknum,timesteps,traffic,phy_elist,logic_elist,load,action_list,links))
    #获取所有fitness中的最大值
    return max(all_fitness),all_fitness.index(max(all_fitness))

def init_network():
    newmodule.reset()
    topology = newmodule.init_topology()
    phy_elist, logic_elist = newmodule.cacul_edge(topology)
    traffic = newmodule.cacul_traffic(logic_elist)
    traffic,load = newmodule.calcul_load(traffic, phy_elist, logic_elist)
    links = newmodule.init_network(phy_elist, load)
    action_list = newmodule.create_attackList(phy_elist)
    return traffic,phy_elist,logic_elist,load,action_list,links

def main(M,T,attacknum,timelimit,Pm,Pc):
    """
        :param M: 种群规模
        :param T: 遗传运算的终止进化代数
        :param attacknum: 进行打击的链路数目
        :param timelimit: 单步最长等待时间
        :param Pm: 变异概率
        :param Pc: 交叉概率
        :return:
        """
    # 初始化网络状态，获取各项网络参数
    num = 212

    #第一次随机选择种群，规模为M
    population = get_timestep(M,attacknum,timelimit)
    fitnesslist = []
    populationlist = []
    for i in range(T):
        logout("------------ epoch:",i,"-----------")
        # 进行选择操作
        population,allFitness = select(num,attacknum,population)
        populationlist.append(population)
        logout("------------",i,"/",T,"---------FailLinkNum:",max(allFitness),"-----------")
        fitnesslist.append(allFitness)
        # 进行交叉操作
        population = cross(M,Pc,attacknum,population)
        # 进行变异操作
        population = variation(M,Pm,attacknum,population,timelimit)
    # 最优个体
    #maxvalue,index = search(attacknum,population)
    logout("populationlist:",populationlist)
    logout("fitnesslist:",fitnesslist)
    #print(population[index],'----------------',maxvalue)
    x = [i for i in range(T)]

    plt.plot(x, fitnesslist)
    # 第3步：显示图形
    plt.show()


if __name__ == '__main__':

    #M = 10
    M = 10
    T = 10
    attacknum = 10
    timelimit = 50
    Pm = 0.2
    Pc = 0.5
    main(M,T,attacknum,timelimit,Pm,Pc)
