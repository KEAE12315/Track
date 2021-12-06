import numpy as np

from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout
from tensorflow.keras.layers import LSTM
from tensorflow.keras.models import load_model

from haversine import haversine


def NormalizeMult(data, set_range=True):
    '''
    返回归一化后的数据和最大最小值
    '''
    normalize = np.arange(2 * data.shape[1], dtype='float64')
    normalize = normalize.reshape(data.shape[1], 2)

    for i in range(0, data.shape[1]):
        if set_range == True:
            list = data[:, i]
            listlow, listhigh = np.percentile(list, [0, 100])
        else:
            if i == 0:
                listlow = -90
                listhigh = 90
            else:
                listlow = -180
                listhigh = 180

        normalize[i, 0] = listlow
        normalize[i, 1] = listhigh

        delta = listhigh - listlow
        if delta != 0:
            for j in range(0, data.shape[0]):
                data[j, i] = (data[j, i] - listlow) / delta

    return data, normalize


def NormalizeMultUseData(data, normalize):
    """
    使用训练数据的归一化，利用训练时保存到的normalize数据，即横纵坐标的最大最小值
    """
    for i in range(0, data.shape[1]):

        listlow = normalize[i, 0]
        listhigh = normalize[i, 1]
        delta = listhigh - listlow

        if delta != 0:
            for j in range(0, data.shape[0]):
                data[j, i] = (data[j, i] - listlow) / delta

    return data


def create_dataset(data, train_n, pred_n):
    '''
    分割数据，生成训练/测试数据集
    '''

    train_X, train_Y = [], []
    for i in range(data.shape[0] - train_n - pred_n - 1):
        train_X.append(data[i:(i + train_n), :])
        for tmp in data[(i + train_n):(i + train_n + pred_n), :]:
            train_Y.append(tmp)
    train_X = np.array(train_X, dtype='float64')
    train_Y = np.array(train_Y, dtype='float64')

    test_X, test_Y = [], []
    i = data.shape[0] - train_n - pred_n - 1
    test_X.append(data[i:(i + train_n), :])
    for tmp in data[(i + train_n):(i + train_n + pred_n), :]:
        test_Y.append(tmp)
    test_X = np.array(test_X, dtype='float64')
    test_Y = np.array(test_Y, dtype='float64')

    return train_X, train_Y, test_X, test_Y


def trainModel(train_X, train_Y):
    '''
    trainX，trainY: 训练LSTM模型所需要的数据
    '''

    model = Sequential()
    model.add(LSTM(
        120,
        input_shape=(train_X.shape[1], train_X.shape[2]),
        return_sequences=True))
    model.add(Dropout(0.3))

    model.add(LSTM(
        120,
        return_sequences=False))
    model.add(Dropout(0.3))

    model.add(Dense(train_Y.shape[1]))
    model.add(Activation("relu"))

    model.compile(loss='mse', optimizer='adam', metrics=['acc'])
    model.fit(train_X, train_Y, epochs=100, batch_size=64, verbose=1)
    model.summary()

    return model


def reshape_y_hat(y_hat, dim):
    re_y = []
    i = 0
    while i < len(y_hat):
        tmp = []
        for j in range(dim):
            tmp.append(y_hat[i + j])
        i = i + dim
        re_y.append(tmp)
    re_y = np.array(re_y, dtype='float64')
    return re_y


def FNormalizeMult(data, normalize):
    """
    多维反归一化
    """
    data = np.array(data, dtype='float64')
    # 列
    for i in range(0, data.shape[1]):
        listlow = normalize[i, 0]
        listhigh = normalize[i, 1]
        delta = listhigh - listlow
        print("listlow, listhigh, delta", listlow, listhigh, delta)
        # 行
        if delta != 0:
            for j in range(0, data.shape[0]):
                data[j, i] = data[j, i] * delta + listlow

    return data


def rmse(predictions, targets):
    return np.sqrt(((predictions - targets) ** 2).mean())


def mse(predictions, targets):
    return ((predictions - targets) ** 2).mean()


if __name__ == "__main__":
    from serialization import serial
    import folium
    from itertools import islice
    import numpy as np
    from predication import *
    input_n = 7
    output_n = 1

    ss = serial('dataset/001', 'results/landmarks.json', 0.1)
    # ss = islice(ss, 2)
    for df, se in ss:
        data = np.array(se)
        # print(data.shape)
        if len(data) <= 15:
            # print('Inefficent Number of samples: '+str(len(data)))
            continue

        data, normalize = NormalizeMult(data, set_range=True)
        np.savetxt('model/normalize.txt', normalize)

        train_X, train_Y, test_X, test_Y = create_dataset(data, input_n, output_n)
        print(train_X)

        model = trainModel(train_X, train_Y)
        loss, acc = model.evaluate(train_X, train_Y, verbose=2)
        print('Loss : {}, Accuracy: {}'.format(loss, acc * 100))

    model.save('model/track_model.h5')