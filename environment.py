#DQN网络记忆容量
MEMORY_CAPACITY = 100
BATCH_SIZE = 32

#打击序列长度
seqnum = 10

#target网络隔多久进行更新
TARGET_REPLACE_ITER = 20

#reward达到该值时停止计算
rewardfactor = 0.2
#时间限制
timelimit = 50
#容忍参数
TOLERANCE_FACTOR = 0.4
#恢复时间
reStart_Timer = 50

KEEPALIVE_TIME = 10