import json, threading, time
from support import mosquitoauthdb, passwordgen, bnbhome, mqttclient
from enum import Enum


default_reg = 'register'
default_register_status = default_reg + '/@status'
default_register = default_reg + '/+'


class server_endpoints(Enum):
    nodes_get_registered = 'nodes/{}/get/registered'
    nodes_set_registered = 'nodes/{}/set/registered'

    nodes_get_status = 'nodes/{}/get/status'

def check_return(return_value):
    return True

def register_node(client, userdata, msg):
    if msg.topic != default_register_status:
        topics = msg.topic.split('/')
        if topics.__len__() == 2 and topics[1] == 'node':
            registration_details = json.loads(msg.payload.decode('ascii'))
            if registration_details['type'] == 'node' and check_return(registration_details['return']):
                node_id = db.generate_nodeid()
                db.append_node(node_id, registration_details['password'])
                if db.check_user(node_id):
                    sendback = {
                        'status' : 'OKAY',
                        'nodeid' : node_id
                    }
                    sendback = json.dumps(sendback)
                    callback_address = '{}/node/{}'.format(default_reg, registration_details['return'])
                    mqtt.outgoing.broadcast_message(callback_address, sendback)

def nodes_nodeid_set_registered(client, userdata, msg):
    msg_topics = msg.topic.split('/')
    target_node = msg_topics[1]

    node_test = db.check_registered(target_node)
    if node_test:
        node_details = db.get_node_conf_defatils(target_node)
        return_value = json.dumps({
            'username' : node_details[0],
            'nodename' : node_details[1]
        })
    elif not node_test:
        return_value = 0
    else:
        return_value = -1
    print(return_value)
    mqtt.outgoing.broadcast_message(server_endpoints.nodes_set_registered.value.format(target_node), return_value)

def nodes_get_status(client, userdata, msg):
    msg_topics = msg.topic.split('/')
    found = False
    watching_nodes_temp = dict(watching_nodes)
    for mesg in watching_nodes_temp:
        if msg_topics[1] == mesg:
            watching_nodes[mesg] = int(time.time())
            found = True
            break
    if not found:
        watching_nodes[msg_topics[1]] = int(time.time())
    print(watching_nodes)

def register_status():
    return 1


if __name__ == '__main__':
    authdb_address = 'localhost'
    authdb_db = 'bnblock'
    authdb_username = 'mosquitto'
    authdb_password = 'EAmyFuWVJEgTMhKMt2hGVnrL'
    db = mosquitoauthdb.Connect(authdb_address, authdb_db, authdb_username, authdb_password)

    mqtt_address = 'auth.bnbwithme.com'
    mqtt_port = 8883

    username = "mosquitto_admin"
    password = passwordgen.random_len(250, set=2)
    db.remove_superusers()
    db.append_superuser(username, password)

    watching_nodes = dict()

    #mqtt thread
    mqtt = mqttclient.Connect(username, password, mqtt_address, port=mqtt_port)
    mqtt.outgoing.frequency = 5

    mqtt.outgoing.set_broadcast(default_register_status, register_status, 'status')
    mqtt.incoming.set_callback(default_register, register_node)
    mqtt.incoming.set_callback(server_endpoints.nodes_get_registered.value.format('+'), nodes_nodeid_set_registered)
    mqtt.incoming.set_callback(server_endpoints.nodes_get_status.value.format('+'), nodes_get_status)


    #flask thread
    homecon = bnbhome.Connect(db, mqtt, watching_nodes)
    homecon.run()
    mqtt.stop()