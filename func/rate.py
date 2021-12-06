from itertools import product
import json
from math import exp
import re
from haversine import haversine


def getRate(sps, aeras, phi):
    """对历史轨迹进行评价打分, 越靠近地区越危险, 分越高

    Args:
        -sps: 提取的用户驻足点
        -Aeras: 地区GPS坐标
        -Phi: 距离阈值

    Return:
        -score: 最终评价的风险分数
    """
    aeras = [[p['lat'], p['lng']] for p in aeras]

    N = 0
    for sp, aera in product(sps, aeras):
        distance = haversine(sp, aera)
        if distance <= phi:
            N = N+1

    score = 1/(1+exp(-N/1.5+5))
    print(N)
    return score


if __name__ == "__main__":
    dict = {"a": 1}
    print(json.dumps([1, 2], sort_keys=True, indent=4, separators=(',', ': ')))
