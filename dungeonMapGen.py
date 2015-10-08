#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
(C) 2015 Turnro.com ScatOrc工作室
'''

import sys
from pylab import*
from scipy.io import wavfile
from PIL import Image, ImageDraw
import json
import random

# Agent 类型，与DDAgent.h内同步。
AT_3RD_MINE = 0
AT_3RD_STONE = 1
AT_3RD_TREE = 2
AT_3RD_WATER = 3
AT_3RD_VOLCANO = 4
AT_ENEMY_FAR = 5
AT_ENEMY_NEAR = 6
AT_ENEMY_NEST = 7
AT_FRIEND_ARROW_TOWER = 8
AT_FRIEND_CONNON_TOWER = 9
AT_FRIEND_CORE = 10
AT_FRIEND_CURE_TOWER = 11
AT_FRIEND_LIGHT_TOWER = 12
AT_FRIEND_MAGIC_TOWER = 13
AT_FRIEND_MINER = 14
AT_FRIEND_WALL = 15
AT_MAX = 16

BIGMAP_X_EXPAND = 15 #X方向一共31格
BIGMAP_Y_EXPAND = 5  #Y方向一共11格

MINMAP_EXPAND = 5 # 11*11

# 各元素在不同属性下出现的概率
OccurcyRadio = {}
#                                  金    木   水   火    土
OccurcyRadio[AT_3RD_STONE]      = [0.5, 0.5, 0.5, 0.5, 0.8] #石头
OccurcyRadio[AT_3RD_TREE]       = [0.2, 0.9, 0.7, 0.3, 0.6] #树
OccurcyRadio[AT_3RD_WATER]      = [0.2, 0.5, 0.8, 0.2, 0.5] #水潭
OccurcyRadio[AT_3RD_VOLCANO]    = [0.6, 0.2, 0.2, 0.8, 0.3] #火山
OccurcyRadio[AT_3RD_MINE]       = [0.9, 0.5, 0.5, 0.5, 0.6] #矿
OccurcyRadio[AT_ENEMY_NEST]     = [1.0, 1.0, 1.0, 1.0, 1.0] #母巢

# 各元素在出现时出现的个数
NumScope = {}
#                          最小/最大
NumScope[AT_3RD_STONE]    = [2,15]
NumScope[AT_3RD_TREE]     = [2,15]
NumScope[AT_3RD_WATER]    = [1,15]
NumScope[AT_3RD_VOLCANO]  = [1,2]
NumScope[AT_3RD_MINE]     = [2,10]
NumScope[AT_ENEMY_NEST]   = [0,4]

# 各元素的连续性
Continues = {}
Continues[AT_3RD_STONE]   = 0.5
Continues[AT_3RD_TREE]    = 0.7
Continues[AT_3RD_WATER]   = 0.5
Continues[AT_3RD_VOLCANO] = 0.0
Continues[AT_3RD_MINE]    = 0.5
Continues[AT_ENEMY_NEST]  = 0.0

# 一些配置项
WATER_ACTION_PERIOD = 10;
VOLCONO_ACTION_PERIOD = 10;

WATER_CURE_LENGTH_RADIO = 1.0/5;
VOLCONO_ATTACK_LENGTH_RADIO = 1.0/5;
VOLCONO_ATTACK_DISTANCE = 5;

MINE_BASE_CAPACITY = 30;
MINE_CAPACITY_LENGTH_RADIO = 5;
MineCapacityRadio = [0.5, 2.0];

PeriodScopeNestAction = [10,50];
NestChanceToRelaxScope = [0.01,0.1];
NestRelaxPeriodScope = [50,1000];

NestChanceToHasBoss = 0.5;
NestBossRadioScope = [0.05,0.25];

NestChanceToBeNear = 0.5;
NestMostNearAsNearScope = [0.8,1];
NestMostFarAsNearScope = [0, 0.2];

NEST_BLOOD_BASE = 1;
NEST_ATTACK_BASE = 1;
NEST_BLOOD_LENGTH_RADIO = 1.0/2;
NestBloodRadioScope = [1.0, 1.5];
NEST_ATTACK_LENGTH_RADIO = 1.0/2;
NestAttackRadioScope = [1.0, 1.5];
NEST_CHANCE_AS_MAIN_ELEMENT_TYPE = 0.75;

NEST_ATTACK_DISTANCE_BASE = 2;
NEST_ATTACK_DISTANCE_LENGTH_RADIO = 1.0/5;
NestAttackDistanceRadioScope = [1.0,1.5];

DEFAULT_ENEMY_ACTION_PERIOD = 10;
DefaultEnemyActionPeriodScope = [1.0,1.5];
DEFAULT_FRIEND_ACTION_PERIOD = 10;

def wrapPos(x,y):
    return {"x":x, "y":y}

def posAdd(pos, dx, dy):
    return wrapPos(pos.x + dx, pos.y + dy)

def encodeMapPos(mappos):
    x,y = mappos['x'], mappos['y']
    return (y+BIGMAP_Y_EXPAND)*100 + (x+BIGMAP_X_EXPAND)
def encodeAgentPos(agentpos):
    x,y = agentpos["x"], agentpos["y"]
    return (y+MINMAP_EXPAND)*100 + (x+MINMAP_EXPAND)

def rand_0_1():
    return random.random()

def calcAgentContinues(radio):
    return random.random() < radio;

def calcElementAgentOccurcy(occradio, elementType):
    radio = occradio[elementType];
    return random.random() < radio;

def calcRandomScope(minmax):
    return int(minmax[0] + (minmax[1] - minmax[0]) * random.random());

def isPosEmpty(minmap, agentpos):
    return  minmap["agents"].has_key(encodeAgentPos(agentpos))

def findRandomEmptyAgentPos(minmap):
    while (True):
        print "findRandomEmptyAgentPos"
        pos = wrapPos(random.randint(-MINMAP_EXPAND, MINMAP_EXPAND), random.randint(-MINMAP_EXPAND, MINMAP_EXPAND))
        if isPosEmpty(minmap, pos):
            return pos;
    
def findContinuesAgentPos(minmap, agentType):
    emptyContinuesPoses = []
    print agentType
    for agentPos in minmap["agents_index"][agentType]:
        pos = posAdd(agentPos, -1, 0)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 1, 0)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 0, -1)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 0, 1)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 1, 1)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, -1, 1)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 1, -1)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, -1, -1)
        if isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
    
    if len(emptyContinuesPoses) > 0:
        return emptyContinuesPoses[random.randint(0, len(emptyContinuesPoses)-1)]
    else:
        return findRandomEmptyAgentPos(minmap)

AGENT_ID_INDEX = 0

def nexAgentId():
    ret = AGENT_ID_INDEX
    AGENT_ID_INDEX += 1
    return ret

def putAgentIn(minmap, mapposLength, agentType):
    continues = calcAgentContinues(Continues[agentType])
    agentpos = {}
    if continues:
        agentpos = findContinuesAgentPos(minmap, agentType)
    else:
        agentpos = findRandomEmptyAgentPos(minmap);
    
    print "putAgentIn agentType=", agentType, "continues=", continues, "agentPos=", agentpos

    minmap.agents[encodeAgentPos(agentpos)] = {}#genAgent(minmap, agentpos, agentType, mapposLength)
    minmap.agents_index[agentType].append(agentpos)

def genAgentsOfType(minmap, agentType, mapposLength):
    print "genAgentsOfType", agentType, "mapposLength", mapposLength
    if calcElementAgentOccurcy(OccurcyRadio[agentType], minmap["main_element_type"]):
        num = calcRandomScope(NumScope[agentType])
        print "num", num
        for i in xrange(num):
            putAgentIn(minmap, mapposLength, agentType)

def genMinMap(mappos):
    print "genMinMap", mappos
    minmap = {}
    minmap["pos"] = mappos
    minmap["state"] = 0 #non-active
    
    minmap["main_element_type"] = random.randint(0, 4)
    minmap["secondary_element_type"] = random.randint(0, 4)
    
    # 实际以AgentPos作为索引的，agents字典
    minmap['agents'] = {}
    
    # 各类agent的索引
    minmap["agents_index"] = []
    for at in xrange(AT_MAX):
        minmap["agents_index"].append([])

    mapposLength = abs(mappos["x"]) + abs(mappos["y"])

    genAgentsOfType(minmap, AT_3RD_STONE, mapposLength)
    genAgentsOfType(minmap, AT_3RD_TREE, mapposLength)
    genAgentsOfType(minmap, AT_3RD_WATER, mapposLength)
    genAgentsOfType(minmap, AT_3RD_VOLCANO, mapposLength)
    genAgentsOfType(minmap, AT_3RD_MINE, mapposLength)
    genAgentsOfType(minmap, AT_ENEMY_NEST, mapposLength)

    return minmap

def genMapData():
    mapdata = {}
    for x in xrange(-BIGMAP_X_EXPAND, BIGMAP_X_EXPAND+1):
        for y in xrange(-BIGMAP_Y_EXPAND, BIGMAP_Y_EXPAND+1):
            mapdata[encodeMapPos(x, y)] = genMinMap(wrapPos(x,y))
            
    mapdata["agent_id_index"] = AGENT_ID_INDEX #当前消耗到的AgentId 的MAX
    return mapdata

def drawBigMap(mapdata):
    pass

def dumpMapData(mapdata):
    #del minmap["agents_index"] 
    print json.dumps(mapdata)
    pass

if __name__ == "__main__":
    mapdata = genMapData()
    drawBigMap(mapdata)
    dumpMapData(mapdata)
    print 'DONE'
