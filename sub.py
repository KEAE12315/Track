import os
from func.load import out_bj, out_speed
import pandas as pd
import json


def load_single(track_path):
    """读取单条轨迹

    输入：
        track_path：单条轨迹文件路径

    输出：
        df：dataframe格式
    """

    names = ['lat', 'lng', 'zero', 'alt', 'days', 'date', 'time']
    df = pd.read_csv(track_path, header=6, names=names, index_col=False)

    df.date = df.date+' '+df.time
    df.date = pd.to_datetime(df.date)

    # df = out_bj(df)
    df = out_speed(df)

    df.drop(['zero', 'alt', 'time', 'date'], axis=1, inplace=True)

    return df


def size(filepath):
    sizes = []
    for user in sorted(os.listdir(filepath)):
        dir_user = filepath+user
        size = 0

        for root, dirs, files in os.walk(dir_user, topdown=False):
            for name in files:
                size += os.path.getsize(os.path.join(root, name))
        print(user, end=':')
        print(size/1000000)
        sizes.append(size/1000)

    print(sizes.index(max(sizes)))


def tojson():
    oldpath = '/mnt/c/Users/KEAE/Desktop/轨迹预测/Geolife Trajectories 1.3/Data/'
    newpath = 'dataset/'

    for user in sorted(os.listdir(oldpath)):
        old_dir = oldpath + user
        new_dir = newpath + user
        os.makedirs(new_dir, exist_ok=True)

        for tracj in sorted(os.listdir(old_dir+'/Trajectory/')):
            tracj_path = old_dir+'/Trajectory/'+tracj

            df = load_single(tracj_path)
            df = df.to_json(orient='records')
            df = json.loads(df)

            tracj = tracj.split('.')[0]+'.json'
            with open(new_dir+'/'+tracj, 'w') as f:
                json.dump(df, f, sort_keys=True, indent=4)
    print(user)


if __name__ == '__main__':

    # df = pd.read_json("test.json", encoding="utf-8", orient='records')
    # print(df)

    tojson()
