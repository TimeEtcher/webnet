import json
import random
import re

import ijson
import networkx as nx
import numpy as np
from scipy.stats import stats


def random_int_list(start, stop, length):
    start, stop = (int(start), int(stop)) if start <= stop else (int(stop), int(start))
    length = int(abs(length)) if length else 0
    random_list = []
    for i in range(length):
        random_list.append(random.randint(start, stop))
    return random_list

def getNodeNumber(filePath):
    with open(filePath) as gr:
        dict1 = json.load(gr)
        node_nums = dict1['property']['n_nodes']
    return node_nums

def getLinkNumber(filePath):
    with open(filePath) as gr:
        dict1 = json.load(gr)
        link_nums = dict1['property']['n_links']
    return link_nums

def getSource(filePath):
    source = []
    with open(filePath) as gr:
        dict1 = json.load(gr)
        for i in range(dict1['property']['n_links']):
            source.append(dict1['links'][i]['source'])
    return source

def getTarget(filePath):
    target = []
    with open(filePath) as gr:
        dict1 = json.load(gr)
        for i in range(dict1['property']['n_links']):
            target.append(dict1['links'][i]['target'])
    return target

def getTopo(filePath):
    node_nums = getNodeNumber(filePath)
    source = getSource(filePath)
    target = getTarget(filePath)
    with open(filePath) as gr:
        dict1 = json.load(gr)
        topo = np.zeros((node_nums, node_nums))
        for i in range(dict1['property']['n_links']):
            topo[source[i]][target[i]] = 1
    return topo

def createIPv4Config(filePath):

    source = getSource(filePath)
    target = getTarget(filePath)
    node_nums = getNodeNumber(filePath)
    topo = getTopo(filePath)
    A = [0] * 300
    with open("./IPv4Config.xml", "w") as f:
        f.write("<config>\n")
        for i in range(len(source)):
            if (i < 246):
                f.write("\t<interface hosts='A" + str(source[i]) + "' names='ppp" + str(
                    A[source[i]]) + "' address='10.10." + str(i + 10) +
                        ".1' netmask='255.255.255.0' groups='224.0.0.1 224.0.0.2 224.0.0.5' metric='1'/>\n")
                f.write("\t<interface hosts='A" + str(target[i]) + "' names='ppp" + str(
                    A[target[i]]) + "' address='10.10." + str(i + 10) +
                        ".2' netmask='255.255.255.0' groups='224.0.0.1 224.0.0.2 224.0.0.5' metric='1'/>\n")
                A[source[i]] += 1
                A[target[i]] += 1
            else:
                f.write("\t<interface hosts='A" + str(source[i]) + "' names='ppp" + str(
                    A[source[i]]) + "' address='10.11." + str(i - 236) +
                        ".1' netmask='255.255.255.0' groups='224.0.0.1 224.0.0.2 224.0.0.5' metric='1'/>\n")
                f.write("\t<interface hosts='A" + str(target[i]) + "' names='ppp" + str(
                    A[target[i]]) + "' address='10.11." + str(i - 236) +
                        ".2' netmask='255.255.255.0' groups='224.0.0.1 224.0.0.2 224.0.0.5' metric='1'/>\n")
                A[source[i]] += 1
                A[target[i]] += 1

        f.write("\n")
        for i in range(node_nums):
            if (i < 246):
                f.write("\t<interface hosts='A" + str(i) + "' names='eth0' address='172." + str(
                    i + 10) + ".4.255' netmask='255.255.255.0' metric='1'/>\n")
            else:
                f.write("\t<interface hosts='A" + str(i) + "' names='eth0' address='173." + str(
                    i - 236) + ".4.255' netmask='255.255.255.0' metric='1'/>\n")
        for i in range(node_nums):
            if (i < 246):
                f.write("\t<interface hosts='HA" + str(i) + "' names='eth0' address='172." + str(
                    i + 10) + ".4.1' netmask='255.255.255.0' mtu='1500' metric='1'/>\n")
            else:
                f.write("\t<interface hosts='HA" + str(i) + "' names='eth0' address='173." + str(
                    i - 236) + ".4.1' netmask='255.255.255.0' mtu='1500' metric='1'/>\n")
        f.write("\n")
        f.write("\t<route hosts='H*' destination='*' netmask='*' interface='eth0'/>\n")
        f.write("\t<route hosts='R*' destination='*' netmask='0.0.0.0' interface='ppp0'/>\n")
        f.write("\n")

        f.write("</config>\n")

def getBetweenness(filePath):
    betweenness = []
    with open(filePath, "r") as gr:
        dict1 = json.load(gr)
        for i in range(dict1['property']['n_links']):
            betweenness.append(dict1['links'][i]['betweenness'])
    return betweenness

def createBgpConfig(filePath,conRetryTime = 180,holdTime = 60,keepAliveTime = 120,startDelay = 12):
    node_nums = getNodeNumber(filePath)
    source = getSource(filePath)
    target = getTarget(filePath)
    with open("./BGPConfig.xml", "w") as f:
        f.write("<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n")
        f.write("<BGPConfig xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n")
        f.write("\t\t  xsi:schemaLocation=\"BGP.xsd\">\n")
        f.write("\n")
        f.write("\t<TimerParams>\n")
        f.write("\t\t<connectRetryTime> " + str(conRetryTime)+ " </connectRetryTime>\n")
        f.write("\t\t<holdTime>" + str(holdTime) + "</holdTime>\n")
        f.write("\t\t<keepAliveTime>" + str(keepAliveTime)+ "</keepAliveTime>\n")
        f.write("\t\t<startDelay> " + str(startDelay)+ " </startDelay>\n")
        f.write("\t</TimerParams>\n")
        f.write("\n")
        f.write("\n")
        for i in range(node_nums):
            if (i < 246):
                f.write("\t<AS id=\"" + str(60010 + i) + "\">\n")
                f.write("\t\t<Router interAddr=\"172." + str(10 + i) + ".4.255\"/> <!--router A" + str(i) + "-->\n")
                f.write("\t</AS>\n")
                f.write("\n")
            else:
                f.write("\t<AS id=\"" + str(60010 + i) + "\">\n")
                f.write("\t\t<Router interAddr=\"173." + str(i - 236) + ".4.255\"/> <!--router A" + str(i) + "-->\n")
                f.write("\t</AS>\n")
                f.write("\n")

        for i in range(len(source)):
            f.write("\t<Session id=\"" + str(i) + "\">\n")
            if (i < 246):
                f.write("\t\t<Router exterAddr=\"10.10." + str(i + 10) + ".1\" > </Router> <!--Router A" + str(
                    source[i]) + "-->\n")
                f.write("\t\t<Router exterAddr=\"10.10." + str(i + 10) + ".2\" > </Router> <!--Router A" + str(
                    target[i]) + "-->\n")
            else:
                f.write("\t\t<Router exterAddr=\"10.11." + str(i - 236) + ".1\" > </Router> <!--Router A" + str(
                    source[i]) + "-->\n")
                f.write("\t\t<Router exterAddr=\"10.11." + str(i - 236) + ".2\" > </Router> <!--Router A" + str(
                    target[i]) + "-->\n")
            f.write("\t</Session>\n")

        f.write("\n")
        f.write("</BGPConfig>\n")

def createOspfConfig(filePath):
    node_nums = getNodeNumber(filePath)
    with open("./OSPFConfig.xml", "w") as f:
        f.write("<?xml version=\"1.0\"?>\n")
        f.write(
            "<OSPFASConfig xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"OSPF.xsd\">\n")

        f.write("\n")

        for i in range(node_nums):
            if (i < 246):
                f.write("\t<Area id=\"0.0.0." + str(i + 1) + "\">\n")
                f.write("\t\t<AddressRange address=\"172." + str(
                    i + 10) + ".4.0\" mask=\"255.255.255.0\" status=\"Advertise\" />\n")
                f.write("\t</Area>\n")
                f.write("\n")
            else:
                f.write("\t<Area id=\"0.0.0." + str(i + 1) + "\">\n")
                f.write("\t\t<AddressRange address=\"173." + str(
                    i - 236) + ".4.0\" mask=\"255.255.255.0\" status=\"Advertise\" />\n")
                f.write("\t</Area>\n")
                f.write("\n")

        for i in range(node_nums):
            f.write("\t<Router name=\"A" + str(i) + "\" RFC1583Compatible=\"true\">\n")
            f.write("\t\t<BroadcastInterface ifName=\"eth0\" areaID=\"0.0.0." + str(
                i + 1) + "\" interfaceOutputCost=\"10\" routerPriority=\"1\" />\n")
            f.write("\t</Router>\n")
            f.write("\n")
        f.write("</OSPFASConfig>\n")

def getCoreNode(filePath):
    with open(filePath) as gr:
        dict1 = json.load(gr)
        core_nums = 0
        for i in range(getNodeNumber(filePath)):
            if dict1['nodes'][i]['degree'] > 1:
                core_nums = core_nums + 1
    return  core_nums

def getG(filePath):
    topo = getTopo(filePath)
    G = nx.Graph()
    for i in range(len(topo)):
        for j in range(len(topo)):
            if topo[i][j]:
                G.add_edge(i, j)
    return G

def createIni(filePath,simulationTime,startTime,isPossion = False):

    coreNodeNumber = getCoreNode(filePath)
    betweeness = []
    with open(filePath, "r") as gr:
        dict2 = json.load(gr)
        for i in range(dict2['property']['n_nodes']):
            if dict2['nodes'][i]['degree'] > 1:
                tup = (i, dict2['nodes'][i]['degree'])
                betweeness.append(tup)

        sortedList = sorted(betweeness, key=lambda s: s[1], reverse=True)
        sortedList.remove((41, 2))
        sortedNode = []
        for i in range(len(sortedList)):
            sortedNode.append(sortedList[i][0])
        random.shuffle(sortedNode)

        t_source = []
        t_target = []
        for i in range(coreNodeNumber // 2):  # 49对点对点（度>=2）
            t_source.append(sortedNode[i])
            t_target.append(sortedNode[i + coreNodeNumber // 2])
        # by wb 210705
        shortest_path = []
        for i in range(len(t_source)):
            path = nx.dijkstra_path(getG(filePath), source=t_source[i], target=t_target[i])
            for j in range(len(path) - 1):
                shortest_path.append([path[j], path[j + 1]])
        for i in range(len(shortest_path)):
            if shortest_path[i][0] > shortest_path[i][1]:
                shortest_path[i][0], shortest_path[i][1] = shortest_path[i][1], shortest_path[i][0]

        np_spath = np.array(shortest_path)
        np_spath = np_spath[np.lexsort(np_spath[:, ::-1].T)]  # 按照首列排序

        np_spath = np_spath.tolist()

        map = {}
        for i in np_spath:
            s = str(i)
            if s in map.keys():
                map[s] = map[s] + 1
            else:
                map[s] = 1
        test = []
        j = 0
        for key in map.keys():
            test.append([np_spath[j][0], np_spath[j][1], map[key]])
            j = j + map[key]
        for i in range(dict2['property']['n_links']):
            dict2['links'][i]['betweenness'] = 0
            for j in range(len(test)):
                if ((dict2['links'][i]['source'] == test[j][0]) and (dict2['links'][i]['target'] == test[j][1])):
                    dict2['links'][i]['betweenness'] = test[j][2]
        with open("./graph_change.json", "w") as fo:
            fo.write(json.dumps(dict2, indent=4))

        a = 100
        str1 = ""

        with open("./omnetpp.ini", "w") as f1:
            f1.write("[General]\n")
            f1.write("\n")
            f1.write("description = \"Multi OSPF routing test + BGP\"\n")
            f1.write("sim-time-limit = " + str(simulationTime)+ "s\n")
            f1.write("network = BgpNetwork\n")
            f1.write("output-scalar-file = results.sca\n")
            f1.write("output-vector-file = results.vec\n")
            f1.write("output-scalar-precision = 2\n")

            f1.write("**.app[0].**.scalar-recording = true\n")
            f1.write("**.scalar-recording = true\n")
            f1.write("**.vector-recording = true\n")
            # f1.write("**.vector-recording-intervals =")
            while a < simulationTime:
                # f1.write(str(a-100)+".."+str(a)+", ")
                str1 = str1 + str(a - 10) + ".." + str(a) + ","
                a = a + 200

            f1.write("**.vector-recording-intervals =" + str(str1[:-1]) + "\n")
            # ip settings
            f1.write("**.rsvp.procDelay = 1us\n")

            # tcp settings
            f1.write("**.tcp.typename = \"Tcp\"\n")
            f1.write("**.tcp.mss = 1024\n")
            f1.write("**.tcp.advertisedWindow = 14336\n")
            f1.write("**.tcp.tcpAlgorithmClass = \"TcpReno\"\n")

            # OSPF configuration
            f1.write("**.ospfConfig = xmldoc(\"OSPFConfig.xml\")\n")

            # scenariomanager
            f1.write("*.scenarioManager.script = xmldoc(\"scenario.xml\")\n")

            # Visualizer settings
            f1.write("*.visualizer.interfaceTableVisualizer.displayInterfaceTables = true\n")

            # bgp settings
            f1.write("**.bgpConfig = xmldoc(\"BGPConfig.xml\")\n")

            f1.write("**.bgp.redistributeOspf = \"E2\"\n")

            # router setting
            f1.write("**.ppp[*].ppp.queue.typename = \"DropTailQueue\"\n")
            f1.write("**.ppp[*].ppp.queue.packetCapacity = 20\n")
            f1.write("**.ppp[*].ppp.queue.dataCapacity = 102400b\n")
            if isPossion == False:
                for i in range(len(t_source)):
                    f1.write("**.HA" + str(t_source[i]) + ".numApps = 1\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[*].typename = \"UdpBasicApp\"\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].startTime = " + str(startTime) + "s\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].localPort = 1234\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].destPort = 5678\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].messageLength = 1024 bytes\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].sendInterval = 3 ms\n")
                    if (t_target[i] < 246):
                        f1.write(
                            "**.HA" + str(t_source[i]) + ".app[0].destAddresses = \"172." + str(
                                t_target[i] + 10) + ".4.1\"\n")
                    else:
                        f1.write("**.HA" + str(t_source[i]) + ".app[0].destAddresses = \"173." + str(
                            t_target[i] - 236) + ".4.1\"\n")
                    f1.write("\n")
                    f1.write("**.HA" + str(t_target[i]) + ".numApps = 1\n")
                    f1.write("**.HA" + str(t_target[i]) + ".app[*].typename = \"UdpSink\"\n")
                    f1.write("**.HA" + str(t_target[i]) + ".app[0].localPort = 5678\n")
                    f1.write("\n")
            else:
                for i in range(len(t_source)):
                    f1.write("**.HA" + str(t_source[i]) + ".numApps = 1\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[*].typename = \"TcpSessionApp\"\n")
                    if (t_source[i] < 246):
                        f1.write("**.HA" + str(t_source[i]) + ".app[0].localAddresses = \"127." + str(
                            t_source[i] + 10) + ".4.1\"\n")
                    else:
                        f1.write("**.HA" + str(t_source[i]) + ".app[0].localAddresses = \"173." + str(
                            t_source[i] - 236) + ".4.1\"\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].localPort = 1234\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].connectPort = 1234\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].tOpen = 1.0s\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].tSend = 0\n")
                    f1.write("**.HA" + str(t_source[i]) + ".app[0].sendBytes = 0\n")
                    str2 = ''
                    k = range(0, 12)
                    temp = int(simulationTime / 12)

                    y = stats.poisson.pmf(k, 4)
                    for i in range(len(y)):
                        str2 = str2 + str(temp) + " " + str(int(y[i] * 10000)) + ";"
                        temp = temp + int(simulationTime / 12)

                    f1.write("**.HA" + str(t_source[i]) + ".app[0].sendScript = " + str(str2[:-1]) + "\n")
                    if (t_target[i] < 246):
                        f1.write(
                            "**.HA" + str(t_source[i]) + ".app[0].connectAddress = \"172." + str(
                                t_target[i] + 10) + ".4.1\"\n")
                    else:
                        f1.write("**.HA" + str(t_source[i]) + ".app[0].connectAddress = \"173." + str(
                            t_target[i] - 236) + ".4.1\"\n")
                    f1.write("\n")
                    f1.write("**.HA" + str(t_target[i]) + ".numApps = 1\n")
                    f1.write("**.HA" + str(t_target[i]) + ".app[*].typename = \"TcpEchoApp\"\n")
                    f1.write("**.HA" + str(t_target[i]) + ".app[0].localPort = 1234\n")
                    f1.write("**.HA" + str(t_target[i]) + ".app[0].localAddress = \"172." + str(
                        t_target[i] + 10) + ".4.1\"\n")
                    f1.write("\n")

def createScenario(filePath,simulationTime:int,simulationMode = 1):
    try:
        link_nums = getLinkNumber(filePath)
        source = getSource("./graph_change.json")
        target = getTarget("./graph_change.json")
        betweenness = getBetweenness("./graph_change.json")
        link = []
        pppg = [0] * 300

        for i in range(len(source)):
            link.append([source[i], target[i], betweenness[i], pppg[source[i]], pppg[target[i]]])
            pppg[source[i]] += 1
            pppg[target[i]] += 1
        link_sorted = sorted(link, key=(lambda link: link[2]), reverse=True)
        with open("./scenario.xml", "w") as f:
            f.write("<scenario>\n")
            time = simulationTime / 10
            start_time = simulationTime + 100  # 间隔设置为200s，初始时间为110s
            if (simulationMode == 1):# mode = 1 策略仿真, mode = 0 随机仿真
                # 策略选择
                for i in range(5):
                    f.write("\t<at t=\"" + str(start_time) + "\">\n")
                    f.write("\t\t<set-channel-param src-module=\"A" + str(
                        link_sorted[i][0]) + "\" src-gate=\"pppg[" + str(
                        link_sorted[i][3]) + "]\" dest-gate=\"A" + str(
                        link_sorted[i][1]) + "\" par=\"datarate\" value=\"10bps\"/>\n")
                    f.write("\t\t<set-channel-param src-module=\"A" + str(
                        link_sorted[i][1]) + "\" src-gate=\"pppg[" + str(
                        link_sorted[i][4]) + "]\" dest-gate=\"A" + str(
                        link_sorted[i][0]) + "\" par=\"datarate\" value=\"10bps\"/>\n")
                    f.write("\t</at>\n")
                    start_time = start_time + time
            else:
                random_list = random_int_list(0, link_nums - 1, 5)

                for i in range(5):
                    f.write("\t<at t=\"" + str(start_time) + "\">\n")
                    f.write("\t\t<set-channel-param src-module=\"A" + str(
                        link_sorted[random_list[i]][0]) + "\" src-gate=\"pppg[" + str(
                        link_sorted[random_list[i]][3]) + "]\" dest-gate=\"A" + str(
                        link_sorted[random_list[i]][1]) + "\" par=\"datarate\" value=\"10bps\"/>\n")
                    f.write("\t\t<set-channel-param src-module=\"A" + str(
                        link_sorted[random_list[i]][1]) + "\" src-gate=\"pppg[" + str(
                        link_sorted[random_list[i]][4]) + "]\" dest-gate=\"A" + str(
                        link_sorted[random_list[i]][0]) + "\" par=\"datarate\" value=\"10bps\"/>\n")

                    f.write("\t</at>\n")
                    start_time = start_time + time

            f.write("</scenario>\n")
    except:
        print("Create failed! Please create scenario last")

def getDegree(filePath):
    degree = []
    with open(filePath) as gr:
        dict1 = json.load(gr)
        for i in range(getNodeNumber(filePath)):
            degree.append(dict1['nodes'][i]['degree'])
    return degree

def createNed(filePath):
    try:
        target = getTarget(filePath)
        source = getSource(filePath)
        G = getG(filePath)
        pos = nx.spring_layout(G)
        bet = []
        degree = getDegree(filePath)
        with open("./graph_change.json", "r") as gr:
            dict1 = json.load(gr)
            for i in range(dict1['property']['n_links']):
                bet.append(dict1['links'][i]['betweenness'])

            A = [0] * 300
            for i in pos.keys():
                pos[i][0] = (pos[i][0] + 1) * 2000
                pos[i][1] = (pos[i][1] + 1) * 2000

            with open("./network.ned", "w") as f:
                f.write("import inet.common.misc.ThruputMeteringChannel;\n")
                f.write("import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;\n")
                f.write("import inet.node.bgp.BgpRouter;\n")
                f.write("import inet.node.ethernet.EtherSwitch;\n")
                f.write("import inet.node.inet.StandardHost;\n")
                f.write("import inet.node.ospfv2.OspfRouter;\n")
                f.write("import inet.visualizer.integrated.IntegratedCanvasVisualizer;\n")
                f.write("import inet.common.scenario.ScenarioManager;\n")
                f.write("\n")
                f.write("network BgpNetwork\n")
                f.write("{\n")
                f.write("\ttypes:\n")

                link_exist = [0] * 1000
                for i in range(dict1['property']['n_links']):
                    if (link_exist[bet[i]] != 0):
                        continue
                    link_exist[bet[i]] = 1
                    if bet[i] == 0:
                        f.write("\t\tchannel LINK_" + str(bet[i]) + " extends ThruputMeteringChannel\n")
                        f.write("\t\t{\n")
                        f.write("\t\t\tparameters:\n")
                        f.write("\t\t\t\tdelay = 50us;\n")
                        f.write("\t\t\t\tdatarate = 10Mbps;\n")
                        f.write("\t\t\t\tdisplayAsTooltip = true;\n")
                        f.write("\t\t\t\tthruputDisplayFormat = \"#N\";\n")
                        f.write("\t\t}\n")
                    else:
                        f.write("\t\tchannel LINK_" + str(bet[i]) + " extends ThruputMeteringChannel\n")
                        f.write("\t\t{\n")
                        f.write("\t\t\tparameters:\n")
                        f.write("\t\t\t\tdelay = 50us;\n")
                        f.write("\t\t\t\tdatarate = " + str(bet[i] * 10) + "Mbps;\n")
                        f.write("\t\t\t\tdisplayAsTooltip = true;\n")
                        f.write("\t\t\t\tthruputDisplayFormat = \"#N\";\n")
                        f.write("\t\t}\n")

                f.write("\t\tchannel LINK_100 extends ThruputMeteringChannel\n")
                f.write("\t\t{\n")
                f.write("\t\t\tparameters:\n")
                f.write("\t\t\t\tdelay = 50us;\n")
                f.write("\t\t\t\tdatarate = 100Mbps;\n")
                f.write("\t\t\t\tdisplayAsTooltip = true;\n")
                f.write("\t\t\t\tthruputDisplayFormat = \"#N\";\n")
                f.write("\t\t}\n")

                f.write("\tsubmodules:\n")
                f.write("\t\tvisualizer: IntegratedCanvasVisualizer {\n")
                f.write("\t\t\tparameters:\n")
                f.write("\t\t\t\t@display(\"p=100,100;is=s\");\n")
                f.write("\t\t}\n")
                f.write("\t\tconfigurator: Ipv4NetworkConfigurator {\n")
                f.write("\t\t\tparameters:\n")
                f.write("\t\t\t\t@display(\"p=100,200;is=s\");\n")
                f.write("\t\t\t\tconfig = xmldoc(\"IPv4Config.xml\");\n")
                f.write("\t\t\t\taddStaticRoutes = false;\n")
                f.write("\t\t\t\taddDefaultRoutes = false;\n")
                f.write("\t\t\t\taddSubnetRoutes = false;\n")
                f.write("\t\t}\n")

                for i in pos.keys():
                    f.write("\t\tA" + str(i) + ":BgpRouter{\n")
                    f.write("\t\t\tparameters:\n")
                    f.write("\t\t\t\t@display(\"p=" + str(pos[i][0]) + "," + str(pos[i][1]) + "\");\n")
                    f.write("\t\t\tgates:\n")
                    f.write("\t\t\t\tpppg[" + str(degree[i]) + "];\n")
                    f.write("\t\t\t\tethg[1];\n")
                    f.write("\t\t}\n")

                for i in pos.keys():
                    f.write("\t\tHA" + str(i) + ": StandardHost {\n")
                    f.write("\t\t\tparameters:\n")
                    f.write(
                        "\t\t\t\t@display(\"p=" + str(pos[i][0] + 30) + "," + str(
                            pos[i][1] + 30) + ";i=device/pc\");\n")
                    f.write("\t\t\tgates:\n")
                    f.write("\t\t\t\tethg[1];\n")
                    f.write("\t\t}\n")
                for i in pos.keys():
                    f.write("\t\tPA" + str(i) + ": EtherSwitch {\n")
                    f.write("\t\t\tparameters:\n")
                    f.write("\t\t\t\t@display(\"p=" + str(pos[i][0] + 15) + "," + str(pos[i][1] + 15) + "\");\n")
                    f.write("\t\t\tgates:\n")
                    f.write("\t\t\t\tethg[2];\n")
                    f.write("\t\t}\n")
                f.write("\tconnections:\n")

                for i in range(len(source)):
                    f.write(
                        "\t\tA" + str(source[i]) + ".pppg[" + str(A[source[i]]) + "] <--> " + "LINK_" + str(
                            bet[i]) + " <--> A" + str(
                            target[i]) + ".pppg[" + str(A[target[i]]) + "];\n")
                    A[source[i]] += 1
                    A[target[i]] += 1

                for i in pos.keys():
                    f.write("\t\tA" + str(i) + ".ethg[0] <--> LINK_100 <--> PA" + str(i) + ".ethg[0];\n")
                    f.write("\t\tPA" + str(i) + ".ethg[1] <--> LINK_100 <--> HA" + str(i) + ".ethg[0];\n")
                f.write("}\n")
    except:
        print("Create failed! Please create ini before create ned")



def getNodeResult(filePath,resultPath,time):
    change_row = []
    txState = {}
    change = []
    numbers = {}  # 存放非正常结束路由器的端口号与路由器号
    list2 = []
    node_nums = getNodeNumber(filePath)

    with open(resultPath) as ts:
        obj = list(ijson.items(ts, ""))
        dict0 = obj[0]
        for a in dict0.keys():
            temp = a
        for i in range(len(dict0[temp]['vectors'])):
            endtime = dict0[temp]['vectors'][i]['time'][-1]
            host = dict0[temp]['vectors'][i]['module']
            txState[host] = endtime
    # 查找非正常结束传输的端口，存入change
    for key, value in txState.items():
        if value < time:
            change.append(key)

    # 提取出非正常结束传输端口的路由器号
    host_string = ",".join(change)
    host_number_string = re.findall(r"\d+", host_string)
    host_number = list(map(int, host_number_string))
    for i in range(len(host_number)):
        if i % 2 == 1:
            numbers['post_number' + str(int(i / 2))] = host_number[i]
        else:
            numbers['host_number' + str(int(i / 2))] = host_number[i]

    # 打开graph。json，将网络链接信息存在矩阵中
    # 获取非正常结束路由器链路另一端路由器号
    topo = getTopo(filePath)
    for i in range(node_nums):
        for j in range(i, node_nums):
            topo[j][i] = topo[i][j]

    not_zero = np.nonzero(topo)
    line = not_zero[0].tolist()
    row = not_zero[1].tolist()
    for i in range(len(line)):
        list2.append((line[i], row[i]))

    for i in range(len(numbers) // 2):
        change_row.append(line.index(numbers['host_number' + str(i)]) + numbers['post_number' + str(i)])
    # 修改拓扑
    for i in range(len(change_row)):
        topo[numbers['host_number' + str(i)]][row[change_row[i]]] = 0

    graph = getG(filePath)
    if list(nx.connected_components(graph)):
        largest_graphy = max(nx.connected_components(graph), key=len)
        return len(largest_graphy)
    else:
        return 0



def getLinkResult(filePath,resultPath,time):
    change_row = []
    txState = {}
    change = []
    numbers = {}  # 存放非正常结束路由器的端口号与路由器号
    list2 = []
    link_nums = getLinkNumber(filePath)
    node_nums = getNodeNumber(filePath)

    with open(resultPath) as ts:
        obj = list(ijson.items(ts, ""))
        dict0 = obj[0]
        for a in dict0.keys():
            temp = a
        for i in range(len(dict0[temp]['vectors'])):
            endtime = dict0[temp]['vectors'][i]['time'][-1]
            host = dict0[temp]['vectors'][i]['module']
            txState[host] = endtime
    # 查找非正常结束传输的端口，存入change
    for key, value in txState.items():
        if value < time:
            change.append(key)

    # 提取出非正常结束传输端口的路由器号
    host_string = ",".join(change)
    host_number_string = re.findall(r"\d+", host_string)
    host_number = list(map(int, host_number_string))
    for i in range(len(host_number)):
        if i % 2 == 1:
            numbers['post_number' + str(int(i / 2))] = host_number[i]
        else:
            numbers['host_number' + str(int(i / 2))] = host_number[i]

    # 打开graph。json，将网络链接信息存在矩阵中
    # 获取非正常结束路由器链路另一端路由器号
    topo = getTopo(filePath)
    for i in range(node_nums):
        for j in range(i, node_nums):
            topo[j][i] = topo[i][j]

    not_zero = np.nonzero(topo)
    line = not_zero[0].tolist()
    row = not_zero[1].tolist()
    for i in range(len(line)):
        list2.append((line[i], row[i]))

    for i in range(len(numbers) // 2):
        change_row.append(line.index(numbers['host_number' + str(i)]) + numbers['post_number' + str(i)])
    # 修改拓扑
    for i in range(len(change_row)):
        topo[numbers['host_number' + str(i)]][row[change_row[i]]] = 0

    graph = getG(filePath)
    failure_edges = link_nums - len(graph.edges())
    return failure_edges






