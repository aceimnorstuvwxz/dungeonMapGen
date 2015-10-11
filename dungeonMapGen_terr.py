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
import time
import math

AGENT_ID_INDEX = 0
RADIO_MINIMAP_LOST = 0.25 #Bigmap内空隙比例。
CNT_BLOCKED = 0
CNT_NON_BLOCKED = 0

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

# 五行标记
EL_METAL = 0
EL_WOOD = 1
EL_WATER = 2
EL_FIRE = 3
EL_EARTH = 4
EL_NONE = 5

BIGMAP_X_EXPAND = 15 #X方向一共31格
BIGMAP_Y_EXPAND = 5  #Y方向一共11格

MINMAP_EXPAND = 5 # 11*11
MINMAP_POS_EXPAND = 2 #每个agentPos绘制5*5像素面积
MINMAP_POS_OFFSET = 3 #各minmap之间的间隙

# 各类型Agent的色彩，现在被用来作为地形的色彩
AgentFillColor = {}
AgentFillColor[AT_3RD_MINE]      = (135, 213, 226, 255) #矿 浅蓝色
AgentFillColor[AT_3RD_STONE]     = (0, 0, 0, 255) #石头 深灰色
AgentFillColor[AT_3RD_TREE]      = (20, 56, 06, 255) #树 深绿色
AgentFillColor[AT_3RD_VOLCANO]   = (102, 000, 000, 255) #火山 红褐色
AgentFillColor[AT_3RD_WATER]     = (000, 051, 153, 255) #水 深蓝色
AgentFillColor[AT_FRIEND_CORE]   = (000, 255, 000, 255) #核心 绿色

COLOR_STEP_MAX = 10
Terrain = {}
#                           距离，radio
Terrain[AT_3RD_MINE]      = (6, 0.1)
Terrain[AT_3RD_STONE]     = (6, 0.3)
Terrain[AT_3RD_TREE]      = (10, 0.1)
Terrain[AT_3RD_VOLCANO]   = (20, 0.1)
Terrain[AT_3RD_WATER]     = (15, 0.1)
Terrain[AT_FRIEND_CORE]   = (20, 0.0)


# 各属性导致的地板底色
ElementBaseColor = {}
ElementBaseColor[EL_METAL] = (53,53,53,255)
ElementBaseColor[EL_WOOD]  = (35,57,35,255)
ElementBaseColor[EL_WATER] = (44,49,71,255)
ElementBaseColor[EL_FIRE]  = (71,50,44,255)
ElementBaseColor[EL_EARTH] = (69,71,44,255)

BASE_COLOR_RADIO = 5
ELEMENT_COLOR_RADIO = 5
BlockedBaseColor = (0,0,0,255)
NonBlockedBaseColor = (67,67,67,255)
BgColor = (20,20,20,255)
ImageWidth = 0
ImageHeight = 0

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
DEFAULT_ACTION_PERIOD = 10;
WATER_ACTION_PERIOD = 10;
VOLCONO_ACTION_PERIOD = 10;
CORE_ACTION_PERIOD = 10;

WATER_CURE_LENGTH_RADIO = 1.0/5;
WATER_CURE_LENGTH_RADIO = 1.0/10;
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
    return wrapPos(pos['x'] + dx, pos['y'] + dy)

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

def calcRandomScopeInt(minmax):
    return int(minmax[0] + (minmax[1] - minmax[0]) * random.random());

def calcRandomScopeFloat(minmax):
    return minmax[0] + (minmax[1] - minmax[0]) * random.random();


def isAgentPosLegeal(agentpos):
    if abs(agentpos["x"]) <=5 and abs(agentpos["y"]) <= 5:
        if abs(agentpos["x"]) == MINMAP_EXPAND and agentpos["y"] == 0:
            return False
        if abs(agentpos["y"]) == MINMAP_EXPAND and agentpos["x"] == 0:
            return False
        return True
    else:
        return False


def isPosEmpty(minmap, agentpos):
    return  minmap["agent_positions"].has_key(encodeAgentPos(agentpos)) == False

def findRandomEmptyAgentPos(minmap):
    while (True):
        pos = wrapPos(random.randint(-MINMAP_EXPAND, MINMAP_EXPAND), random.randint(-MINMAP_EXPAND, MINMAP_EXPAND))
        if isPosEmpty(minmap, pos) and isAgentPosLegeal(pos):
            return pos;

def findContinuesAgentPos(minmap, agentType):
    emptyContinuesPoses = []
    for agentPos in minmap["agents_index"][agentType]:
        pos = posAdd(agentPos, -1, 0)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 1, 0)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 0, -1)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 0, 1)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 1, 1)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, -1, 1)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, 1, -1)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)
        pos = posAdd(agentPos, -1, -1)
        if isAgentPosLegeal(pos) and isPosEmpty(minmap, pos):
            emptyContinuesPoses.append(pos)

    if len(emptyContinuesPoses) > 0:
        return emptyContinuesPoses[random.randint(0, len(emptyContinuesPoses)-1)]
    else:
        return findRandomEmptyAgentPos(minmap)


def nextAgentId():
    global AGENT_ID_INDEX
    ret = AGENT_ID_INDEX
    AGENT_ID_INDEX += 1
    return ret

def genEmptyAgent():
    agent = {}
    agent["aid"] = nextAgentId()
    agent["level"] = 0
    agent["blood"] = 1
    agent["attack"] = 0
    agent["cure"] = 0
    agent["action_distance"] = 0
    agent["action_period"] = DEFAULT_ACTION_PERIOD
    agent["action_period_index"] = DEFAULT_ACTION_PERIOD
    agent["scope"] = 0
    agent["element_type"] = EL_NONE
    agent["mine_capacity"] = 0
    agent["mine_amount"] = 0
    agent["chance_to_relax"] = 0.0
    agent["action_relax_reriod"] = 1
    agent["action_relax_index"] = 0
    agent["nest_chance_to_near"] = 0.0
    agent["nest_chance_to_boss"] = 0.0
    agent["nest_blood"] = 0
    agent["nest_attack"] = 0
    agent["nest_element_type"] = EL_NONE
    agent["nest_attack_distance_near"] = 1
    agent["nest_attack_distance_far"] = 2
    agent["nest_attack_period"] = DEFAULT_ENEMY_ACTION_PERIOD

    return agent

def genAgent(minmap, agentpos, agentType, mapposLength):
    agent = genEmptyAgent()
    agent["pos"] = agentpos
    agent["type"] = agentType
    if agentType == AT_3RD_STONE:
        pass
    elif agentType == AT_3RD_TREE:
        pass
    elif agentType == AT_3RD_WATER:
        agent["blood"] = 1
        agent["attack"] = 0
        agent["cure"] = 1 + int(mapposLength * WATER_CURE_LENGTH_RADIO)
        agent["action_distance"] = 1
        agent["action_period"] = WATER_ACTION_PERIOD
        agent["action_period_index"] = WATER_ACTION_PERIOD
    elif agentType == AT_3RD_VOLCANO:
        agent["blood"] = 1
        agent["attack"] = 1 + int(mapposLength * VOLCONO_ATTACK_LENGTH_RADIO)
        agent["action_distance"] = VOLCONO_ATTACK_DISTANCE
        agent["action_period"] = VOLCONO_ACTION_PERIOD
        agent["action_period_index"] = VOLCONO_ACTION_PERIOD
    elif agentType == AT_3RD_MINE:
        agent["mine_capacity"] = int((MINE_BASE_CAPACITY + MINE_CAPACITY_LENGTH_RADIO * mapposLength) * calcRandomScopeFloat(MineCapacityRadio))
        agent["mine_amount"] = agent["mine_capacity"]
    elif agentType == AT_ENEMY_NEST:
        agent["action_period"] = calcRandomScopeInt(PeriodScopeNestAction)
        agent["action_index"] = agent["action_period"]
        agent["chance_to_relax"] = calcRandomScopeInt(NestChanceToRelaxScope)
        agent["action_relax_period"] = calcRandomScopeInt(NestRelaxPeriodScope)
        agent["action_relax_index"] = 0
        if rand_0_1() < NestChanceToBeNear:
            agent["nest_chance_to_near"] = calcRandomScopeFloat(NestMostNearAsNearScope)
        else:
            agent["nest_chance_to_near"] = calcRandomScopeFloat(NestMostFarAsNearScope)

        if rand_0_1() < NestChanceToHasBoss:
            agent["nest_chance_to_boss"] = calcRandomScopeFloat(NestBossRadioScope)
        else:
            agent["nest_chance_to_boss"] = 0.0

        agent["nest_blood"] = int((NEST_BLOOD_BASE + mapposLength * NEST_BLOOD_LENGTH_RADIO) * calcRandomScopeFloat(NestBloodRadioScope))
        agent["nest_attack"] = int((NEST_ATTACK_BASE + mapposLength * NEST_ATTACK_LENGTH_RADIO) * calcRandomScopeFloat(NestAttackRadioScope))

        if rand_0_1() < rand_0_1() < NEST_CHANCE_AS_MAIN_ELEMENT_TYPE:
            agent["nest_element_type"] = minmap["main_element_type"]
        else:
            agent["nest_element_type"] = minmap["secondary_element_type"]

        agent["nest_attack_distance_near"] = 1
        agent["nest_attack_distance_far"] = int((NEST_ATTACK_DISTANCE_BASE + NEST_ATTACK_DISTANCE_LENGTH_RADIO * mapposLength) * calcRandomScopeFloat(NestAttackDistanceRadioScope))
        agent["nest_attack_period"] = int(DEFAULT_ENEMY_ACTION_PERIOD * calcRandomScopeFloat(DefaultEnemyActionPeriodScope))
    elif agentType == AT_FRIEND_CORE:
        agent["blood"] = 10
        agent["actionDistance"] = 4
        agent["attack"] = 1
        agent["action_period"] = CORE_ACTION_PERIOD
        agent["action_period_index"] = CORE_ACTION_PERIOD
    else:
        print "ERROR invalid type=", agentType

    return agent

def putAgentIn(minmap, mapposLength, agentType):
    continues = calcAgentContinues(Continues[agentType])
    agentpos = {}
    if continues:
        agentpos = findContinuesAgentPos(minmap, agentType)
    else:
        agentpos = findRandomEmptyAgentPos(minmap);

    #print "putAgentIn agentType=", agentType, "continues=", continues, "agentPos=", agentpos

    minmap["agents"].append(genAgent(minmap, agentpos, agentType, mapposLength))
    minmap["agent_positions"][encodeAgentPos(agentpos)] = 1
    minmap["agents_index"][agentType].append(agentpos)

def putAgentDirect(minmap, agentpos, agentType, mapposLength):
    minmap["agents"].append(genAgent(minmap, agentpos, agentType, mapposLength))
    minmap["agent_positions"][encodeAgentPos(agentpos)] = 1
    minmap["agents_index"][agentType].append(agentpos)

def genAgentsOfType(minmap, agentType, mapposLength):
    #print "genAgentsOfType", agentType, "mapposLength", mapposLength
    if calcElementAgentOccurcy(OccurcyRadio[agentType], minmap["main_element_type"]):
        num = calcRandomScopeInt(NumScope[agentType])
        for i in xrange(num):
            putAgentIn(minmap, mapposLength, agentType)

def genMinMap(mappos):
    #print "genMinMap", mappos
    minmap = {}
    global CNT_BLOCKED
    global CNT_NON_BLOCKED

    minmap["pos"] = mappos
    #部分MinMap是空隙，不能进入。
    if rand_0_1() < RADIO_MINIMAP_LOST:
        minmap["blocked"] = 1
        CNT_BLOCKED += 1
        return minmap
    else:
        CNT_NON_BLOCKED += 1
        minmap["blocked"] = 0

    minmap["state"] = 0 #non-active

    minmap["main_element_type"] = random.randint(0, 4)
    minmap["secondary_element_type"] = random.randint(0, 4)

    # 实际以AgentPos作为索引的，agents字典
    minmap['agents'] = []
    minmap['agent_positions'] = {}

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

def genMinMapCore(mappos):
    #print "genMinMap", mappos
    minmap = {}
    global CNT_BLOCKED
    global CNT_NON_BLOCKED

    minmap["pos"] = mappos
    CNT_NON_BLOCKED += 1
    minmap["blocked"] = 0

    minmap["state"] = 1 #active

    minmap["main_element_type"] = random.randint(0, 4)
    minmap["secondary_element_type"] = random.randint(0, 4)

    # 实际以AgentPos作为索引的，agents字典
    minmap['agents'] = []
    minmap['agent_positions'] = {}


    # 各类agent的索引
    minmap["agents_index"] = []
    for at in xrange(AT_MAX):
        minmap["agents_index"].append([])

    mapposLength = abs(mappos["x"]) + abs(mappos["y"])

    putAgentDirect(minmap, wrapPos(0, 0), AT_FRIEND_CORE, 0)

    return minmap

def genMapData():
    mapdata = {}
    mapdata["minmaps"] = []
    for x in xrange(-BIGMAP_X_EXPAND, BIGMAP_X_EXPAND+1):
        for y in xrange(-BIGMAP_Y_EXPAND, BIGMAP_Y_EXPAND+1):
            if x == 0 and y == 0:
                mapdata["minmaps"].append(genMinMapCore(wrapPos(x,y)))
            else:
                mapdata["minmaps"].append(genMinMap(wrapPos(x,y)))

    mapdata["agent_id_index"] = AGENT_ID_INDEX #当前消耗到的AgentId 的MAX
    mapdata["minmap_unblocked_count"] = CNT_NON_BLOCKED
    return mapdata

def calcMinMapCenter(mappos):
    minmapLength = (MINMAP_POS_OFFSET*2 + (MINMAP_EXPAND*2+1)*(MINMAP_POS_EXPAND*2+1));
    x = (mappos["x"] + BIGMAP_X_EXPAND) * minmapLength + MINMAP_EXPAND*(MINMAP_POS_EXPAND*2+1) + MINMAP_POS_OFFSET + MINMAP_POS_EXPAND
    y = (mappos["y"] + BIGMAP_Y_EXPAND) * minmapLength + MINMAP_EXPAND*(MINMAP_POS_EXPAND*2+1) + MINMAP_POS_OFFSET + MINMAP_POS_EXPAND
    return x,y

def drawColorMix(colorRadioCouples):
    radioAll = 0.0
    for couple in colorRadioCouples:
        color, radio = couple
        radioAll += radio
    r = 0.0
    g = 0.0
    b = 0.0
    a = 0.0
    for couple in colorRadioCouples:
        color, radio = couple
        r += radio/radioAll * color[0]
        g += radio/radioAll * color[1]
        b += radio/radioAll * color[2]
        a += radio/radioAll * color[3]

    return (int(r),int(g),int(b),int(a))

def fetchBaseColorByMapPos(minmap):
    if minmap["blocked"] != 0:
        return BlockedBaseColor
    else:
        seco = ElementBaseColor[minmap["main_element_type"]]
        return drawColorMix([(seco, BASE_COLOR_RADIO), (NonBlockedBaseColor, ELEMENT_COLOR_RADIO)])

def slipp(c):
    return int(c/COLOR_STEP_MAX) * COLOR_STEP_MAX

def splipColor(color):
    return (slipp(color[0]), slipp(color[1]), slipp(color[2]), color[3])


def drawHelp(draw, position, color):
    '''解决图片的y坐标与地图的y坐标相反的问题'''
    draw.point((position[0], ImageHeight-position[1]-1), color)#splipColor(color))
    
def getColorHelp(img, position):
    if position[0]>=0 and position[0] < ImageWidth and position[1] >=0 and position[1] < ImageHeight:
        #print ImageWidth,ImageHeight, position, (position[0], ImageHeight-position[1]-1)
        return img.getpixel((position[0], ImageHeight-position[1]-1))
    return (0,0,0,0)

def drawBaseColor(mapdata, draw):
    for minmap in mapdata["minmaps"]:
        mappos = minmap["pos"]
        baseColor = fetchBaseColorByMapPos(minmap)
        cx,cy = calcMinMapCenter(mappos)
        #print cx,cy
        offset = (MINMAP_EXPAND*2+1)*(MINMAP_POS_EXPAND*2+1)/2
        for px in xrange(cx-offset, cx+offset+1):
            for py in xrange(cy-offset, cy+offset+1):
                drawHelp(draw, (px, py), baseColor)


'''
def drawLeakBetweenMinmaps(mapdata, draw):
    for encodedMapPos, minmap in mapdata["minmaps"].items():
        mappos = minmap["pos"]
        ownColor = fetchBaseColorByMapPos(mapdata, mappos)
        topMapPos = wrapPos(mappos["x"], mappos["y"]+1)
        bottomMapPos = wrapPos(mappos["x"], mappos["y"]-1)
        leftMapPos = wrapPos(mappos["x"]-1, mappos["y"])
        rightMapPos = wrapPos(mappos["x"]+1, mappos["y"])

        topColor = fetchBaseColorByMapPos(mapdata, topMapPos)
        bottomColor = fetchBaseColorByMapPos(mapdata, bottomMapPos)

        cx,cy = calcMinMapCenter(mappos)
        offset = (2*MINMAP_EXPAND+1)*(2*MINMAP_POS_EXPAND+1)/2
        for px in xrange(cx-offset, cx+offset+1):
            for ppy in xrange(1, MINMAP_POS_OFFSET+1):
                py = cy+offset+ppy
                drawHelp(draw, (px,py), drawColorMix([(topColor, 1.0/(2*MINMAP_POS_OFFSET - ppy+1)),(ownColor, 1.0/ppy)]))
        for px in xrange(cx-offset, cx+offset+1):
            for ppy in xrange(1, MINMAP_POS_OFFSET+1):
                py = cy-offset-ppy
                drawHelp(draw, (px,py), drawColorMix([(bottomColor, 1.0/(2*MINMAP_POS_OFFSET - ppy+1)),(ownColor, 1.0/ppy)]))
        for px in xrange(cx-offset, cx+offset+1):
            for ppy in xrange(1, MINMAP_POS_OFFSET+1):
                py = cy+offset+ppy
                drawHelp(draw, (px,py), drawColorMix([(topColor, 1.0/(2*MINMAP_POS_OFFSET - ppy+1)),(ownColor, 1.0/ppy)]))
        for px in xrange(cx-offset, cx+offset+1):
            for ppy in xrange(1, MINMAP_POS_OFFSET+1):
                py = cy-offset-ppy
                drawHelp(draw, (px,py), drawColorMix([(bottomColor, 1.0/(2*MINMAP_POS_OFFSET - ppy+1)),(ownColor, 1.0/ppy)]))
'''
def calcAgentCenter(mappos, agentpos):
    x = (mappos["x"]+BIGMAP_X_EXPAND)*((MINMAP_POS_EXPAND*2+1)*(MINMAP_EXPAND*2+1)+2*MINMAP_POS_OFFSET) + MINMAP_POS_OFFSET + (agentpos["x"]+MINMAP_EXPAND)*(MINMAP_POS_EXPAND*2+1) + MINMAP_POS_EXPAND
    y = (mappos["y"]+BIGMAP_Y_EXPAND)*((MINMAP_POS_EXPAND*2+1)*(MINMAP_EXPAND*2+1)+2*MINMAP_POS_OFFSET) + MINMAP_POS_OFFSET + (agentpos["y"]+MINMAP_EXPAND)*(MINMAP_POS_EXPAND*2+1) + MINMAP_POS_EXPAND
    return (x,y)

def encodePixelPos(x, y):
    return y*10000+x

def drawAgents(mapdata, draw):
    '''画agents，先实体，再描边'''
    agentPixelMap = {} #用来帮助描边
    for minmap in mapdata["minmaps"]:
        mappos = minmap["pos"]
        if minmap["blocked"] != 0:
            continue
        for agent in minmap["agents"]:
            agentpos = agent["pos"]
            agentType = agent["type"]
            if agentType == AT_ENEMY_NEST:
                continue
            color = AgentFillColor[agentType]
            cx,cy = calcAgentCenter(mappos, agentpos)
            for px in xrange(cx-MINMAP_POS_EXPAND, cx+MINMAP_POS_EXPAND+1):
                for py in xrange(cy-MINMAP_POS_EXPAND, cy+MINMAP_POS_EXPAND+1):
                    agentPixelMap[encodePixelPos(px,py)] = 1
                    drawHelp(draw, (px,py), color)
    for px in xrange(ImageWidth):
        for py in xrange(ImageHeight):
            if agentPixelMap.has_key(encodePixelPos(px, py)) == False:
                ifdraw = False
                if agentPixelMap.has_key(encodePixelPos(px-1, py-1)) or\
                   agentPixelMap.has_key(encodePixelPos(px-1, py)) or\
                   agentPixelMap.has_key(encodePixelPos(px-1, py+1)) or\
                   agentPixelMap.has_key(encodePixelPos(px, py-1)) or\
                   agentPixelMap.has_key(encodePixelPos(px, py+1)) or\
                   agentPixelMap.has_key(encodePixelPos(px+1, py-1)) or\
                   agentPixelMap.has_key(encodePixelPos(px+1, py)) or\
                   agentPixelMap.has_key(encodePixelPos(px+1, py+1)):
                    drawHelp(draw, (px,py), (0,0,0,255))


def drawTerrainPerAgent(color, length, radio, cx, cy, draw, img):
    for dx in xrange(-length, length+1):
        for dy in xrange(-length, length+1):
            plen = math.sqrt(dx*dx+dy*dy)
            if  plen <= length:
                px = cx + dx
                py = cy + dy
                pradio = (length - plen)/length * radio
                oldColor = getColorHelp(img, (px,py))
                newColor = drawColorMix([(color, pradio),(oldColor, 1.0-pradio)])
                drawHelp(draw, (px,py), newColor)
                    
    
def drawTerrain(mapdata, draw, img):
    for minmap in mapdata["minmaps"]:
        mappos = minmap["pos"]
        if minmap["blocked"] != 0:
            continue
        for agent in minmap["agents"]:
            agentpos = agent["pos"]
            agentType = agent["type"]
            if agentType == AT_ENEMY_NEST:
                continue
            color = AgentFillColor[agentType]
            cx,cy = calcAgentCenter(mappos, agentpos)
            length, radio = Terrain[agentType]
            drawTerrainPerAgent(color, length, radio, cx, cy, draw, img)

def drawBigMap(mapdata, tt):
    '''画背景色，根据主属性'''
    global ImageHeight
    global ImageWidth
    ImageWidth = (BIGMAP_X_EXPAND*2 +1)*(MINMAP_POS_OFFSET*2+(MINMAP_POS_EXPAND*2+1)*(1+2*MINMAP_EXPAND))
    ImageHeight =  (BIGMAP_Y_EXPAND*2 +1)*(MINMAP_POS_OFFSET*2+(MINMAP_POS_EXPAND*2+1)*(1+2*MINMAP_EXPAND))
    print "image width/height=", ImageWidth, ImageHeight
    img = Image.new("RGBA", (ImageWidth,ImageHeight), color=BgColor)
    draw = ImageDraw.Draw(img)
    '''根据主属性绘制底色'''
    drawBaseColor(mapdata, draw)
    '''画MinMap之间的间隙'''
    #drawLeakBetweenMinmaps(mapdata, draw)

    '''画地形'''
    #drawTerrain(mapdata, draw, img)
    
    '''画各agent'''
    #drawAgents(mapdata, draw)
    img.save("bigmap%d.png"%(tt), 'PNG')

def dumpMapData(mapdata, tt):
    #del minmap["agents_index"]
    fn = 'bigmap%d.json'%(tt)
    print "map-data-file-name=", fn
    f = open(fn,'w')
    f.write(json.dumps(mapdata))
    f.close()

if __name__ == "__main__":
    mapdata = genMapData()
    tt = time.time()
    drawBigMap(mapdata, tt)
    dumpMapData(mapdata, tt)
    print "agentNum=", AGENT_ID_INDEX, "blockedMinMap=", CNT_BLOCKED, "blockedRadio=", CNT_BLOCKED * 1.0 / (CNT_BLOCKED + CNT_NON_BLOCKED)
    print 'DONE'
