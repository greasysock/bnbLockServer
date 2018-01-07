import MySQLdb, time
from support import hashing_passwords, passwordgen
import _mysql_exceptions
from enum import Enum

tables = [("mqtt_users", "username TEXT, password TEXT, super BIT, userid TEXT"),
          ("acls", "username TEXT, topic TEXT, rw INT, userid TEXT, nodeid TEXT"),
          ("users", "username TEXT, userid TEXT, name TEXT, password TEXT"),
          ("nodes", "userid text, nodeid text, name TEXT, streetnumber TEXT, street TEXT, state TEXT, zip TEXT, city TEXT")]

wilds = [('register/@status', 1)]

class data_type(Enum):
    mqtt_users = 'mqtt_users'
    users = 'users'

class Connect():
    def __init__(self, address, db, username, password):
        self.__db = db
        self.__conn = MySQLdb.connect(host=address, user=username, passwd=password, db=db)
        self.__c = self.__conn.cursor()
    def save(self):
        self.__conn.commit()
    def close(self):
        self.__conn.close()
    def check_user(self, username, check=data_type.mqtt_users):
        values = self.__c.execute("SELECT * FROM {} WHERE username = '{}'".format(check.value,username))
        numrows = self.__c.rowcount
        out_test = list()
        for x in range (0, numrows):
            row = self.__c.fetchone()
            out_test.append(out_test)
        if out_test.__len__() > 0:
            return True
        else:
            return False
    def check_userid(self, userid, check=data_type.users):
        self.__c.execute("SELECT * FROM {} WHERE userid = '{}'".format(check.value, userid))
        numrows = self.__c.rowcount
        out_test = list()
        for x in range (0, numrows):
            row = self.__c.fetchone()
            out_test.append(row)
        if out_test.__len__() > 0:
            return True
        else:
            return False
    def check_registered(self, nodeid):
        if self.check_user(nodeid):
            self.__c.execute("SELECT * FROM nodes WHERE nodeid = '{}'".format(nodeid))
            numrows = self.__c.rowcount
            for x in range(0, numrows):
                row = self.__c.fetchone()
                if row[0] == 'UNREGISTERED' or not self.check_userid(row[0], check=data_type.users):
                    return False
                elif self.check_user(row[0], check=data_type.users):
                    return True
        return -1
    def get_userid(self, username):
        self.__c.execute("SELECT * FROM users WHERE username = '{}'".format(username))
        numrows = self.__c.rowcount
        out_val = str()
        for x in range (0, numrows):
            row = self.__c.fetchone()
            out_val = row[1]
        return out_val
    def get_user(self, userid):
        self.__c.execute("SELECT * FROM users WHERE userid = '{}'".format(userid))
        numrows = self.__c.rowcount
        out_val = str()
        for x in range (0, numrows):
            row = self.__c.fetchone()
            out_val = row[0]
            return out_val
    def get_node_conf_defatils(self, nodeid):
        nodedetails = self.get_node(nodeid)
        username = self.get_user(nodedetails[0])
        return username, nodedetails[2]
    def generate_userid(self):
        first_id = passwordgen.random_len(6, set=2)
        while self.check_userid(first_id):
            first_id = passwordgen.random_len(6, set=2)
        return first_id
    def generate_nodeid(self):
        first_id = passwordgen.random_len(6, set=2)
        while self.check_user(first_id):
            first_id = passwordgen.random_len(6, set=2)
        return first_id
    def get_acls(self):
        out_list = list()
        self.__c.execute("SELECT * FROM acls")
        numrows = self.__c.rowcount
        for x in range (0, numrows):
            row = self.__c.fetchone()
            out_list.append(row)
        return out_list
    def get_users(self):
        out_list = list()
        self.__c.execute("SELECT * FROM mqtt_users")
        numrows = self.__c.rowcount
        for x in range(0, numrows):
            row = self.__c.fetchone()
            out_list.append(row)
        return out_list
    def append_wild_acl(self, topic, rw):
        self.__c.execute("INSERT INTO acls VALUES ('@', '{}', '{}', 'WILD', 'WILD')".format(topic, rw))
    def append_acl(self, username, topic, rw, userid, nodeid = ''):
        if self.check_user(username):
            self.__c.execute("INSERT INTO acls VALUES ('{}','{}', '{}', '{}', '{}')".format( username, topic, rw, userid, nodeid))
        return -1
    def append_superuser(self, username, password):
        if not self.check_user(username):
            hash_pass = hashing_passwords.make_hash(password)
            self.__c.execute("INSERT INTO mqtt_users VALUES ('{}', '{}', 1, '1')".format(username,hash_pass))
            self.save()
    def append_node_conf(self):
        if not self.check_userid('CONFUSER', check=data_type.mqtt_users):
            username = passwordgen.random_len(100)
            password = passwordgen.random_len(100)
            hash_pass = hashing_passwords.make_hash(password)
            self.__c.execute("INSERT INTO mqtt_users VALUES ('{}', '{}', b'0', '{}')".format(username, hash_pass, 'CONFUSER'))
            self.append_acl(username, topic='register/node', rw=2, userid='CONFUSER')
            self.append_acl(username, topic='register/node/+', rw=1, userid='CONFUSER')

            return username, password
        else:
            return -1
    def remove_mqtt_user(self, username):
        self.__c.execute("DELETE FROM mqtt_users WHERE username = \"{}\"".format(username))
        self.save()
    def remove_bnblock_user(self, username):
        if self.check_user(username):
            userid = self.get_userid(username)
            self.__c.execute("DELETE FROM users WHERE userid = '{}'".format(userid))
            self.__c.execute("DELETE FROM mqtt_users WHERE userid = '{}'".format(userid))
            self.__c.execute("DELETE FROM nodes WHERE userid = '{}'".format(userid))
            self.__c.execute("DELETE FROM acls WHERE userid = '{}'".format(userid))
    def remove_bnblock_node(self, nodeid):
        if self.check_user(nodeid):
            self.__c.execute("DELETE FROM mqtt_users WHERE username = '{}'".format(nodeid))
            self.__c.execute("DELETE FROM nodes WHERE nodeid = '{}'".format(nodeid))
            self.__c.execute("DELETE FROM acls WHERE nodeid = '{}'".format(nodeid))
    def remove_superusers(self):
        self.__c.execute("DELETE FROM mqtt_users WHERE super = 1")
        self.save()
    def append_user(self, username, password, name):
        if not self.check_user(username):
            hash_pass = hashing_passwords.make_hash(password)
            userid = self.generate_userid()
            self.__c.execute("INSERT INTO users VALUES ('{}', '{}', '{}', '{}')".format(username, userid, name, hash_pass))
            self.__c.execute("INSERT INTO mqtt_users VALUES ( '{}', '{}', b'0', '{}')".format(username, hash_pass, userid))
            self.append_acl(username, 'register/{}'.format(username),2, userid)
            self.append_acl(username, 'register/{}/+'.format(username), 1, userid)
            self.append_acl(username, 'users/{}/info/set/#'.format(username), 2, userid)
            self.append_acl(username, 'users/{}/info/get/#'.format(username), 1, userid)
            self.save()
            return userid
        return False
    def update_node_info(self, set=0, **kwargs):
        if set==0:
            self.__c.execute("UPDATE nodes SET userid='{}', name='{}' WHERE nodeid = '{}'".format(kwargs['userid'], kwargs['name'], kwargs['nodeid']))
    def append_user_node(self, userid, nodeid, node_name):
        if self.check_userid(userid) and self.check_user(nodeid, check=data_type.mqtt_users):
            username = self.get_user(userid)
            self.update_node_info(userid=userid,name=node_name, nodeid=nodeid)
            self.save()
            topic_scope = 'users/{}/nodes/{}'.format(username, nodeid)

            #User ACL Config
            self.append_acl(username,topic_scope+'/conf/set/#',2,userid,nodeid=nodeid)
            self.append_acl(username,topic_scope+'/conf/get/#',1,userid,nodeid=nodeid)

            self.append_acl(username,topic_scope+'/devices/+/set/#', 2,userid,nodeid=nodeid)
            self.append_acl(username,topic_scope+'/devices/+/get/#', 1,userid,nodeid=nodeid)

            #Node ACL Config
            self.append_acl(nodeid,topic_scope, 2, userid, nodeid=nodeid)
            self.append_acl(nodeid,topic_scope+'/#', 2, userid, nodeid=nodeid)

            self.save()
            return True


        return False
    def get_node(self, nodeid):
        self.__c.execute("SELECT * FROM nodes WHERE nodeid = '{}'".format(nodeid))
        numrows = self.__c.rowcount
        for x in range (0, numrows):
            row = self.__c.fetchone()
            return row
    def get_user_nodes(self, userid):
        self.__c.execute("SELECT * FROM nodes WHERE userid = '{}'".format(userid))
        out_list = list()
        numrows = self.__c.rowcount
        for x in range (0, numrows):
            row = self.__c.fetchone()
            out_list.append(row)
        return out_list
    def append_node(self, username, password, **kwargs):
        if not self.check_user(username):
            time.sleep(2)
            self.__c.execute("INSERT INTO mqtt_users VALUES ('{}', '{}', 0, '{}')".format(username, password, 'NODECONF'))
            #Node acl configuration

            self.append_acl(username, 'nodes/{}/get/#'.format(username), 2, 'NODECONF',nodeid=username)
            self.append_acl(username, 'nodes/{}/set/#'.format(username), 1, 'NODECONF',nodeid=username)

            #User acl configuration

            self.__c.execute("INSERT INTO nodes VALUES"
                             "('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format('UNREGISTERED', username,
                                                                                       '',
                                                                                       '',
                                                                                       '',
                                                                                       '',
                                                                                       '',
                                                                                       ''))
            self.save()
def setup_database(address, username, password, db, admin='admin', tables=tables):
    conn = MySQLdb.connect(host=address, user=username, passwd=password, db=db)
    c = conn.cursor()
    for table, values in tables:
        print("CREATE TABLE '{}' ({})".format(table, values))
        try:
            c.execute("CREATE TABLE {} ({})".format(table, values))
        except _mysql_exceptions.OperationalError:
            print('Table {} already exists. Skipping.'.format(table))
    for_conn = Connect(address,db, username, password)
    conf_details = for_conn.append_node_conf()
    if conf_details != -1:
        print('Configuration Username/Password. Please store this information in a safe place.')
        print('Username: {}'.format(conf_details[0]))
        print('Password: {}'.format(conf_details[1]))
    for wild in wilds:
        for_conn.append_wild_acl(*wild)
    for_conn.save()