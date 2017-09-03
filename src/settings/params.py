from configparser import ConfigParser
import os

config = ConfigParser()
print('dir ' + os.path.dirname(os.path.realpath(__file__)))
config.read_file(open(os.path.dirname(os.path.realpath(__file__)) + '/config.ini'))


def get_config(section, key):
    global config
    return config[section][key].replace('"', '')
