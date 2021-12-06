from haversine import haversine
from func.load import Load
import json


class serial():
    def __init__(self, user_path, lm_path, phi=0.2) -> None:
        self.user_path = user_path
        self.lm_path = lm_path
        self.phi = phi

    def __iter__(self):
        with open(self.lm_path, 'r')as f:
            lm = json.load(f)

        load = Load(self.user_path)
        for df in load:
            df = [[lat, lng] for lat, lng in zip(df['lat'].values, df['lng'].values)]
            sequence = []
            flag = None
            for p in df:
                for q in lm:
                    if haversine([p[0], p[1]], [q['lat'], q['lng']]) <= self.phi:
                        if flag == q:
                            break
                        else:
                            sequence.append([q['lat'], q['lng']])
                            flag = q
                            break
            yield df, sequence
