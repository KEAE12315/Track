import os

import pandas as pd
from haversine import haversine


def out_bj(df):
    """
    没找到什么好的判断坐标点是否在北京的方法，粗略在地图上找了边界点。
    上边界lat:42；下边界lat:39；左边界lng:115；右边界lng:118。
    """
    n = 0
    for i, row in df.iterrows():
        if row['lat'] > 42 or row['lat'] < 39 or row['lng'] < 115 or row['lng'] > 118:
            df.drop(index=i, inplace=True)
            n = n+1

    df = df.reset_index(drop=True)
    return df


def out_speed(df):
    """
    剔除速度超过300km/h的点，城市内不可能有这样的速度。
    但是这算法会把跨城旅行的另外一个城市的点全部删除
    """

    lat1 = None
    lng1 = None
    time1 = None
    n = 0
    for index, row in df.iterrows():
        if index == 0:
            lat1 = row['lat']
            lng1 = row['lng']
            time1 = row['days']
            continue

        # distance:km, interval:hour, speed:km/h
        distance = haversine([lat1, lng1], [row['lat'], row['lng']])
        interval = (row['days']-time1)*24
        if interval == 0:
            continue
        speed = distance/interval

        if speed >= 300:
            n = n+1
            df.drop(index, inplace=True)
            continue
        else:
            lat1 = row['lat']
            lng1 = row['lng']
            time1 = row['days']

    df = df.reset_index(drop=True)
    return df


class Load():
    """可迭代容器类，按顺序返回文件夹路径下的所有文件

    输入：
        dir_path：要迭代的文件夹，存放轨迹的json文件。

    输出：
        df：dataframe格式的单条轨迹文件。 
    """

    def __init__(self, dir_path):
        self.dir_path = dir_path

    def __iter__(self):
        for root, dirs, files in os.walk(self.dir_path, topdown=True):
            dirs.sort()
            files.sort()
            for name in files:
                print(os.path.join(root, name))
                df = pd.read_json(os.path.join(root, name))
                # df = out_bj(df)
                # df = out_speed(df)

                df = df.iloc[::12, :]
                df = df.reset_index(drop=True)

                yield df


if __name__ == '__main__':
    load = Load('dataset')
    for i, df in enumerate(load):
        print(df)
        break
