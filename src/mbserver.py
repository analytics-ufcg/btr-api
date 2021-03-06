# coding: UTF-8
import urllib

import tornado.escape
import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado.options import define, options, parse_command_line

from handlers.spark_handler import SparkHandler
from handlers.prediction_handler import PredictionHandler
from handlers.bigsea_manager_handler import BigseaManagerHandler
from config import btr_otp_config

define("port", default=8888, help="run on the given port", type=int)


class RoutesPlansHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        # query example: {
        #   "fromPlace": "-25.39211,-49.22613",
        #   "toPlace": "-25.45102,-49.28381",
        #   "mode": "TRANSIT,WALK",
        #   "date": "04/03/2017",
        #   "time": "17:20:00"
        #   }
        request_params = tornado.escape.json_decode(self.request.body)

        query = btr_otp_config.OTP_LINK + urllib.urlencode(request_params)

        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(query)

        otp_data = tornado.escape.json_decode(response.body)

        otp_data_predicted = prediction_handler.get_btr_prediction(otp_data, request_params)

        self.write(otp_data_predicted)

    def get(self):

        spark_handler.updateResources(duration_model_path, crowdedness_model_path, pipeline_path, routes_stops_path)

        self.write('True')


class BigseaHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):

        job = self.get_argument('job')

        result = bigsea_handler.runJob(job)

        self.write(result)

class HealthMonitorHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Everything is fine.")


app = tornado.web.Application([
    (r'/btr_routes_plans', RoutesPlansHandler),
    (r'/run', BigseaHandler),
    (r'/update', RoutesPlansHandler),
    (r'/status', HealthMonitorHandler)
])


def start_up():
    global spark_handler
    global prediction_handler
    global bigsea_handler
    global duration_model_path, crowdedness_model_path, pipeline_path, routes_stops_path
    duration_model_path = btr_otp_config.DURATION_MODEL_PATH
    crowdedness_model_path = btr_otp_config.CROWDEDNESS_MODEL_PATH
    pipeline_path = btr_otp_config.PIPELINE_PATH
    routes_stops_path = btr_otp_config.ROUTES_STOPS_PATH
    app_name = "Best Trip Recommender"
    spark_handler = SparkHandler(app_name, duration_model_path, crowdedness_model_path, pipeline_path, routes_stops_path)
    prediction_handler = PredictionHandler(spark_handler)
    bigsea_handler = BigseaManagerHandler()
    parse_command_line()
    app.listen(options.port)
    print "MBServer started!"
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    start_up()
