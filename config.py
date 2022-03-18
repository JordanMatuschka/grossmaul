# Database Setup
from peewee import *
db = MySQLDatabase('DATABASE', user='sqluser', password='PASSWORD')

# Connection Settings
CHAN = "#thetestening"
NICK = "BeerRobot"
HOST = "irc.libera.chat"
PORT = 6697

# If your server uses SASL, set the below to true and enter the user to authenticate as
SASL = True
SASL_USER = 'authuser'
SASL_PASS = 'PASSWORD'

# Misc settings
LULL = 900 

