# Time:2022 2022/3/1 17:20
# Author: Jasmay
# -*- coding: utf-8 -*-
import time
import logging
filename = time.strftime('%Y-%m-%d %H.%M', time.localtime(time.time()))
filename = "./log/" + filename + ".log"
# 第一步：创建日志器对象，默认等级为warning
logger = logging.getLogger()
logging.basicConfig(
                    level    = logging.DEBUG,
                    format   = '%(asctime)s\tFile \"%(filename)s\",line %(lineno)s\t%(levelname)s: %(message)s',
                    #datefmt  = '%a, %d %b %Y %H:%M:%S',
                    filemode = 'w')

# 第二步：创建控制台日志处理器+文件日志处理器
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler(filename,mode="a",encoding="utf-8")

# 第三步：设置控制台日志的输出级别,需要日志器也设置日志级别为info；----根据两个地方的等级进行对比，取日志器的级别
console_handler.setLevel(level="WARNING")

# 第四步：设置控制台日志和文件日志的输出格式
file_fmt = "%(asctime)s--->%(message)s"
fmt1 = logging.Formatter('LINE %(lineno):%(levelname)-8s %(message)s')
fmt2 = logging.Formatter(file_fmt)

console_handler.setFormatter(fmt = fmt1)
file_handler.setFormatter(fmt = fmt2)

# 第五步：将控制台日志器、文件日志器，添加进日志器对象中
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def logout(*messages):
    re = ""
    for message in messages:
        re = re + str(message)

    logger.info(re)

