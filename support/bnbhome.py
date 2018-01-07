from flask import Flask
from flask_restful import Resource, Api, reqparse, abort
import json, threading, time
from support.devices import callbacks
from support import mqttclient

class Connect():

    def __init__(self, db, mqtt, node_listen):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.db = db
        self.mqtt = mqtt
        self.__node_listen = node_listen
        self.api.add_resource(self.UserRegistration, '/user/registration', resource_class_kwargs={'db':self.db})
        self.api.add_resource(self.NodeRegistration, '/node/registration', resource_class_kwargs={'db':self.db})
        self.api.add_resource(self.NodeCheckStatus, '/node/check_status', resource_class_kwargs={'db':self.db})
        self.api.add_resource(self.UserNodesDevices, '/user/nodes_devices', resource_class_kwargs={'db':self.db, 'listen': self.__node_listen, 'mqtt': self.mqtt})
        self.api.add_resource(self.UserExecuteMQTT, '/user/execute_mqtt', resource_class_kwargs={'db':self.db, 'listen': self.__node_listen, 'mqtt': self.mqtt})




        for resource in self.api.resources:
            print(type(resource))

    class NodeCheckStatus(Resource):
        def __init__(self, **kwargs):
            self.db = kwargs['db']
        def get(self):
            parser = reqparse.RequestParser()
            parser.add_argument('nodeid', type=str, required=True, location='args')

            args = parser.parse_args()
            print(args)
            try:
                response = self.db.check_registered(args['nodeid'])
                if response == -1:
                    return {
                        'status' : 'OKAY',
                        'node_status' : 'BAD'
                    }
                elif response:
                    return {
                        'status' : 'OKAY',
                        'node_status' : 'REGISTERED',
                    }
                elif not response:
                    return {
                        'status' : 'OKAY',
                        'node_status' : 'UNREGISTERED'
                    }
            except:
                return {
                    'STATUS' : 'FAIL'
                }
    class NodeRegistration(Resource):
        def __init__(self, **kwargs):
            self.db = kwargs['db']
        def put(self):
            parser = reqparse.RequestParser()
            parser.add_argument('userid', type=str, required=True, location='json')
            parser.add_argument('node_name', type=str, required=True, location='json')
            parser.add_argument('nodeid', type=str, required=True, location='json')

            args = parser.parse_args()
            response = self.db.append_user_node(args['userid'], args['nodeid'], args['node_name'])
            if response:
                return {'status' : 'OKAY'}
            elif not response:
                return {'status' : 'FAIL'}
            return {'status' : 'FAIL'}
        def get(self):
            return 1
    class UserRegistration(Resource):
        def __init__(self, **kwargs):
            self.db = kwargs['db']
        def put(self):
            parser = reqparse.RequestParser()
            parser.add_argument('username', type=str, required=True, location='json')
            parser.add_argument('password', type=str, required=True, location='json')
            parser.add_argument('name', type=str, required=True, location='json')

            args = parser.parse_args()
            response = self.db.append_user(args['username'], args['password'], args['name'])
            if response:
                return {
                    'status' : 'OKAY',
                    'userid' : response
                }
            else:
                return {
                    'status' : 'FAIL',
                    'message' : 'likely there is already a user with the same name on the network.'
                }
        def get(self):
            return 'hi'
    class UserNodesDevices(Resource):
        def __init__(self, **kwargs):
            self.db = kwargs['db']
            self.listen = kwargs['listen']
            self.mqtt = kwargs['mqtt']
#            self.mqtt = mqttclient.Connect()
            self.timeout = 3
        def get(self):
            parser = reqparse.RequestParser()
            parser.add_argument('userid', type=str, required=True, location='args')
            args = parser.parse_args()
            user_nodes = self.db.get_user_nodes(args['userid'])
            username = self.db.get_user(args['userid'])
            target_nodes = list()
            for node in user_nodes:
                try:
                    time_stamp = self.listen[node[1]]
                except KeyError:
                    time_stamp = 0
                current_time = int(time.time())
                if current_time - time_stamp <= 35:
                    target_nodes.append(node)
            out_object = dict()
            out_object_nodes = dict()
            out_object['nodes'] = out_object_nodes

            for node in target_nodes:
                address_store = callbacks.conf.get_devices.value.format(username, node[1])
                broadcast = callbacks.conf.set_devices.value.format(username, node[1])
                self.mqtt.incoming.set_address_store(address_store)
                self.mqtt.outgoing.broadcast_message(broadcast, 1)
                time.sleep(.2)
                for x in range(self.timeout):
                    if self.mqtt.incoming.get_address_store(address_store) != None:
                        out_object_node = dict()
                        out_object_node['name'] = node[2]
                        out_object_node['devices'] = json.loads(self.mqtt.incoming.get_address_store(address_store)[0].payload.decode('ascii'))
                        out_object_nodes[node[1]] = out_object_node

                        break
                    time.sleep(2)
            return out_object

    class UserExecuteMQTT(Resource):
        def __init__(self, **kwargs):
            self.db = kwargs['db']
            self.listen = kwargs['listen']
            self.mqtt = kwargs['mqtt']
            #            self.mqtt = mqttclient.Connect()

            self.timeout = 3

        def put(self):
            parser = reqparse.RequestParser()
            parser.add_argument('userid', type=str, required=True, location='json')
            parser.add_argument('node', type=str, required=True, location='json')
            parser.add_argument('device_type', type=str, required=True, location='json')
            parser.add_argument('device_id', type=str, required=True, location='json')
            parser.add_argument('target_endpoint', type=str, required=True, location='json')
            parser.add_argument('payload', type=str, required=True, location='json')
            args = parser.parse_args()

            user_nodes = self.db.get_user_nodes(args['userid'])
            username = self.db.get_user(args['userid'])

            found = False

            for node in user_nodes:
                if node[1] == args['node']:
                    found = True

            if found:
                topic =  callbacks.generic.set_generic.value.format(username, args['node'], args['device_type'], args['device_id'], args['target_endpoint'])
                print(topic)
                self.mqtt.outgoing.broadcast_message(topic, args['payload'])

    def run(self):
        self.app.run(host='0.0.0.0', port=5000, debug=False)