timelimit = 100
M = 20
timeStepList = []
attacknum = 10
d = timelimit//M
for i in range(M):
    attacktime = d*i
    timesteps = [attacktime for j in range(attacknum)]
    timeStepList.append(timesteps)
print(timeStepList)
print("test")