from enum import Enum

class conf(Enum):
    set_devices = 'users/{}/nodes/{}/conf/node/set/get/devices'
    get_devices = 'users/{}/nodes/{}/conf/node/get/devices'

class generic(Enum):
    set_generic = 'users/{}/nodes/{}/devices/{}/{}/set/{}'

class lock(Enum):
    set_lockstate = 'users/{}/nodes/{}/devices/locks/{}/set/lockstate'
    get_lockstate = 'users/{}/nodes/{}/devices/locks/{}/get/lockstate'