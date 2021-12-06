import math
import json

import numpy as np
import pandas as pd
from haversine import haversine

from sklearn.cluster import DBSCAN


def get_centermost_point(cluster):
    """获取每个坐标点簇中，最接近簇中心的坐标点
    """
    from shapely.geometry import MultiPoint
    from geopy.distance import great_circle

    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    centermost_point = min(cluster, key=lambda point: great_circle(point, centroid).m)
    return tuple(centermost_point)


class StayPoint:
    """从轨迹中提取驻足点，并聚类成重要位置。
    """

    def __init__(self, df, roh=0.8, delta=0.1, phi=5) -> None:
        """
        Args：
            df：待处理轨迹数据，dataframe格式。
            roh：直接一致性相关阈值。
            delta：距离因子，用于放缩。
            phi：判断根节点的个数阈值，如果一个点跟多个点直接一致性相关就是根节点。
        """
        self.df = df
        df[['root', 'visited', 'clusterID']] = pd.DataFrame([[0, 0, 0]], index=df.index)

        self.roh = roh
        self.delta = delta
        self.phi = phi

    def _coh(self, p, q) -> bool:
        """计算两个坐标点之间的区域一致性，直接一致相关返回True，反之Flase。
        """
        # 距离km，时间h，速度km/h
        distance = haversine([p.lat, p.lng], [q.lat, q.lng])
        duration = abs((p.days-q.days)*24)
        speed = distance/duration

        a = distance/self.delta
        b = speed
        c = math.exp(-a-b)
        if c >= self.roh:
            return True
        else:
            return False

    def _cohs(self):
        """根节点列表，邻接字典。
        """
        n = self.df.shape[0]

        roots = []
        adjac = {x: [] for x in range(n)}

        for i in range(n):
            if i % 1000 == 0:
                print(i, end=',')
            n_link = 0
            n_far = 0

            # 往前推十个点
            foward = i-10
            if foward < 0:
                foward = 0

            for j in range(foward, n):
                if i == j:
                    continue
                p = self.df.loc[i]
                q = self.df.loc[j]
                if self._coh(p, q):
                    # cohs[i, j] = 1
                    # cohs[j, i] = 1
                    adjac[i].append(j)
                    n_link += 1
                else:
                    n_far += 1

                # 如果跟节点i直接一致相关的点数超过阈值，设i为根节点
                if n_link >= self.phi:
                    self.df.loc[i, 'root'] = 1
                    roots.append(i)
                # 如果连续两个点都不跟i相连，停止对后面的迭代
                if n_far >= 2:
                    break

        return roots, adjac

    def _cluster(self, roots, adjac):
        def DFS(i, clusterID):
            for j in adjac[i]:
                if int(self.df.loc[j, 'visited']) == 1 or j in roots:
                    continue
                self.df.loc[j, 'visited'] = 1
                self.df.loc[j, 'clusterID'] = clusterID
                if adjac[j]:
                    DFS(j, clusterID)

        # 聚类
        clusterID = 1
        for i in roots:
            if self.df.loc[i, 'visited'] == 1:
                continue
            self.df.loc[i, 'visited'] = 1
            self.df.loc[i, 'clusterID'] = clusterID
            if len(adjac[i]) > 0:
                DFS(i, clusterID)

            clusterID += 1

        num_cluster = clusterID-1
        clusters = {x: [] for x in range(num_cluster)}
        for n in range(num_cluster):
            tmp = self.df.loc[self.df.clusterID == n+1, ['lat', 'lng']]
            tmp = tmp.values.tolist()
            clusters[n].append(tmp[0])

        return clusters

    def ex_sp(self):
        # 求根节点和邻接字典
        print('计算cohs', end=': ')
        roots, adjac = self._cohs()

        # 聚类求簇
        print('\n聚类求簇')
        clusters = self._cluster(roots, adjac)
        clusters = pd.Series(clusters)

        # 对每个簇求中心，即驻足点
        print('求驻足点')
        sp = []
        centermost_points = clusters.map(get_centermost_point)
        lats, lngs = zip(*centermost_points)
        sp = pd.DataFrame({'lng': lngs, 'lat': lats})
        sp.to_json('results/stay points.json', orient='records')

        return sp
        # return sp.to_json(orient='records')


def landmark(sp, eps=10, minPts=5):
    """将提取出来的驻足点用DBSCAN算法聚类为重要位置。

    由于一个人不同时间都可能经过相同的地方，已经提取出来的驻足点会有重复。通过空间上的再次聚类，消灭这种重复。

    Args：
        sp：已经提取出来的驻足点
        eps：这里为比例
        minPts：数量阈值

    Retrun：
        cluster：分类的集合。
        lm：驻足点，为每个轨迹簇的位置中心。
    """
    print('开始求landmark')
    # sp = json.loads(sp)
    # sp = [[p['lat'], p['lng']] for p in sp]
    coords = np.array(sp)
    kms_per_radian = 6371.0088
    epsilng = 0.5/kms_per_radian

    db = DBSCAN(eps=epsilng/eps, min_samples=minPts,
                algorithm='ball_tree', metric='haversine').fit(np.radians(coords))

    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels)-set([-1]))

    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])

    # 获取每个簇中 最接近簇中心的 坐标点
    print('正在求中心点')
    centermost_points = clusters.map(get_centermost_point)
    lats, lngs = zip(*centermost_points)
    lm = pd.DataFrame({'lng': lngs, 'lat': lats})
    lm.to_json('results/landmarks.json', orient='records')

    return lm


if __name__ == '__main__':
    pass
