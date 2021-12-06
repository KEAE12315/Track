import os
import json
import pandas as pd

import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from gevent.pywsgi import WSGIServer
from flask_restplus import Api, Resource, Namespace
from flask import Flask, request, jsonify

from func.predication import *
from func.serialization import serial

# 实例化
app = Flask(__name__)
api = Api(app, version='1.1', title='Extract Stay Points and Predication')

# 创建命名空间
ex = Namespace('extraction', description='从轨迹文件中提取驻足点并聚类成重要位置')
pr = Namespace('predication', description='训练lstm模型并预测轨迹')
ay = Namespace('analyze', description='轨迹数据分析')
api.add_namespace(ex)
api.add_namespace(pr)
api.add_namespace(ay)

print('Start serving...')


def _extraction():
    """提取驻足点和重要位置"""
    try:
        user_path = request.json["user_path"]
        roh = request.json["sp_roh"]
        phi = request.json["sp_phi"]
        eps = request.json["lm_eps"]
        minPts = request.json["lm_minPts"]
    except KeyError:
        raise KeyError

    from func.load import Load
    load = Load(user_path)
    try:
        df = pd.concat([d for d in load], ignore_index=True)
    except ValueError:
        raise ValueError

    print('Track points: '+str(df.shape[0]))

    from func.extraction import StayPoint
    extraction = StayPoint(df, roh, phi)
    sp = extraction.ex_sp()

    from func.extraction import landmark
    lm = landmark([[lat, lng] for [lng, lat] in sp.values],
                  eps, minPts)

    return sp, lm


@ex.route('/')
class ExtractSP(Resource):
    @ex.doc('轨迹提取')
    @ex.response(200, 'SUCCESS: Complete the calculation!')
    @ex.response(500, 'ERROR: ')
    def post(self):
        """获取驻足点和重要位置"""
        try:
            sp, lm = _extraction()
        except ValueError:
            return jsonify(status=500,
                           msg="Error: incorrect file format.",
                           results=['Null'])
        except KeyError:
            return jsonify(status=500,
                           msg="Error: Insufficient parameters.",
                           results=['Null'])

        return jsonify(status=200,
                       msg='SUCCESS: Complete the calculation!',
                       results={"stay points": json.loads(sp.to_json(orient='records')),
                                "landmarks": json.loads(lm.to_json(orient='records'))})


@ay.route('/')
class Analyze(Resource):
    @ay.doc('轨迹分析')
    @ay.response(200, 'SUCCESS: Complete the calculation!')
    @ay.response(500, 'ERROR: ')
    def post(self):
        try:
            with open(request.json['landmarks_path'], 'r')as f:
                lm = json.load(f)
            lm = [[p['lat'], p['lng']] for p in lm]
        except KeyError:
            try:
                _, lm = self._extraction()
                lm = [[lat, lng]for [lng, lat] in lm.values]
            except ValueError:
                return jsonify(status=500,
                                msg="Error: The path to the landmarks does not exist, and insufficient parameters for extraction of landmarks",
                                results=['Null'])

        scores = {}
        from func.rate import getRate
        try:
            dangerAeras = request.json['dangerAeras']
            dangerPhi = request.json['dangerPhi']
            scores['score of danger aeras'] = getRate(lm, dangerAeras, dangerPhi)
        except KeyError:
            scores['score of danger aeras'] = "Null"

        try:
            activityAeras = request.json['activityAeras']
            activityPhi = request.json['activityPhi']
            scores['score of activity aeras'] = getRate(lm, activityAeras, activityPhi)
        except KeyError:
            scores['score of activity aeras'] = "Null"

        return jsonify(status=200,
                        msg='SUCCESS: Complete the calculation!',
                        results=scores)


@pr.route('/')
class Predication(Resource):
    @pr.doc('轨迹预测')
    # 响应内容
    @pr.response(200, 'SUCCESS: Complete the calculation!')
    @pr.response(500, 'ERROR: Folder does not exist or Folder is empty or Incorrect data format')
    def post(self):
        print(request.json)

        user_path = request.json["user_path"]
        lm_path = request.json['landmarks_path']
        input_n = request.json["input_n"]
        output_n = request.json["output_n"]

        if not os.path.exists(user_path):
            msg = "Error: Folder does not exist."
            return jsonify(status=500, msg=msg, results=['Null'])

        ss = serial(user_path, lm_path, 0.2)
        for _, se in ss:
            data = np.array(se)
            if len(data) <= 15:
                continue

            data, normalize = NormalizeMult(data, set_range=True)
            np.savetxt('model/normalize.txt', normalize)

            train_X, train_Y, _, _ = create_dataset(data, input_n, output_n)
            model = trainModel(train_X, train_Y)
            loss, acc = model.evaluate(train_X, train_Y, verbose=2)
            print('Loss : {}, Accuracy: {}'.format(loss, acc * 100))

        model.save('model/track_model.h5')

        msg = 'SUCCESS: Complete the calculation!'
        return jsonify(status=200, msg=msg, results=['Null'])

    def get(self):
        print(request.json)
        x = request.json['data']
        x = np.array(x)

        # 归一化
        normalize = np.loadtxt('model/normalize.txt')
        x = NormalizeMultUseData(x, normalize)

        # 使用训练好的模型进行预测
        model = load_model('model/track_model.h5')
        test_X = x.reshape(1, x.shape[0], x.shape[1])
        y_hat = model.predict(test_X)
        y_hat = y_hat.reshape(y_hat.shape[1])
        y_hat = reshape_y_hat(y_hat, 2)

        # 反归一化
        y_hat = FNormalizeMult(y_hat, normalize)

        msg = 'SUCCESS: Complete the calculation!'
        return jsonify(status=200, msg=msg, results=y_hat.tolist())


if __name__ == '__main__':
    WSGIServer(('127.0.0.1', 5000), application=app).serve_forever()
    # app.run(debug=True)
