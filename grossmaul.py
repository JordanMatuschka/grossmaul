import pydle
import logging
import collections
import random
from botbrain import BotBrain
from types import FunctionType
from importlib import reload

# Modify these for your own nefarious purposes
CHAN = "#thehoppening"
#CHAN = "#thetestening"
NICK = "BeerRobot"
HOST = "chat.freenode.net"
PORT = 6697

STATE = {
'counters':  {"__startup":True},
'buffer': collections.deque(maxlen = 1000),
}

#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GrossmaulBot(pydle.Client):
    """  """
    botbrain = None

    def sendMessage(self, target, message, processing = True):
        """Customize message sending to allow for keyword parsing"""
        # Look for a $ that indicates keywords
        if processing:
            if '$' in message:
                # split into words
                words = message.split()
                for word in words:
                    if word.count('$') == 2:
                        # If there are two $s, keyword is embedded
                        # eg Abso-$keyword$-lutely!
                        keyword = word.split('$')[1]
                        replacement = self.botbrain.findKeyword(keyword.lower())
                        if (replacement is not None):
                            message = message.replace('$' + keyword + '$', replacement, 1)
                    elif word[0] is '$':
                        # parse into only alphanumeric characters (+ some others)
                        keyword = ''
                        for char in word:
                            if char.isalnum() or char in "-_": keyword += (char)
                        replacement = self.botbrain.findKeyword(keyword.lower())
                        if (replacement is not None):
                            message = message.replace('$' + keyword, replacement, 1)
        
        # If the message starts with /me it is an action, treat accordingly        
        if message.lower().startswith("/me"):
            self.action(target, message[3:].lstrip())
        else:
            #otherwise simply sent the message
            self.message(target, message)

    def action(self, target, message):
        # send a CTCP message that will be interpreted as an action
        self.ctcp(target, "ACTION", message)


    def on_connect(self):
        """Callback when client has successfully connected. Client will attempt to connect to db and join CHAN."""
        logging.info("Connected to %s" % HOST)    
        self.botbrain = BotBrain()
        self.join(CHAN)

    def on_join(self, channel, user):
        """Called when any user (including this client) joins the channel."""
        global STATE
        global NICK
        logging.info("%s has joined %s" % (user, channel))
        # Detect if the client is using a backup name and if so change NICK
        # If "__startup" is still in STATE['counters'], we will use user as the new NICK
        if("__startup" in STATE['counters']):
            del STATE['counters']["__startup"]
            if (NICK != user):
                NICK = user
                logging.info("Changing internal NICK to %s" % NICK)
        

    def on_unknown(self, message):
        """Callback when client receives unknown data"""
        logging.warning("Client received unknown data: %s" % message)

    def on_message(self, channel, sender, message):
        """Callback called when the client received a message."""
        global STATE 

        # make sure the username is initialized for counter use
        if(sender not in STATE['counters'].keys()): 
            logging.info("Adding %s key to STATE['counters']" % sender)
            STATE['counters'][sender] = {}

        # Filter out private messages, those will be handled in on_private_message
        if(channel == NICK): return

        # Add all messages to a deque to allow for quoting user's messages
        # Store as a tuple to allow searching by user, append left for easy iteration
        STATE['buffer'].appendleft( (sender, message) )

        logging.info("Message received, channel: %s, sender: %s, message: %s" % (channel, sender, message))
        # For now, make sure that the message is addressed to this bot
        if(message[0] == '!' or (len(message) > len(NICK) and NICK.lower() == message[:len(NICK)].lower())):
            # remove the bot name/bang from the message
            if(message[0] == '!'):
                message = message[1:]
            else:
                message = message[len(NICK)+1:]

            # Parse for special operators
            is_op = False
            is_command = False
            for op in self.botbrain.OPERATORS.keys():
                if(op in message):
                    logging.info("Operator: %s" % op)
                    # call the appropriate function in the function dictionary
                    retval = self.botbrain.OPERATORS[op](message, sender, STATE)
                    if (retval is not None):
                        # Send message without processing on operators
                        self.sendMessage(CHAN, retval, False)
                    is_op = True

            # If it's not an operator, look for a command
            if(not is_op):
                # extract the command from the message
                command = message.split()[0]
                command = command.lower()
                logging.info("Looking for command: %s" % command)
                if(command in self.botbrain.COMMANDS):
                    is_command = True
                    logging.info("Command: %s" % command)
                    retval = self.botbrain.COMMANDS[command](message, sender, STATE)
                    if (retval is not None):
                        # Send message without processing on commands 
                        self.sendMessage(CHAN, retval, False)
                else:
                    logging.info("Can't find %s()" % command)

            # If it's not an operator and not a command, let's see if there are any factoids on the topic
            if(not is_op and not is_command):
                logging.info("Looking for factoid: %s" % message)
                factoid = self.botbrain.findFactoid(message.lower().rstrip().lstrip())
                if(factoid is not None):
                    self.sendMessage(CHAN, self.preprocess_message(sender, factoid))
                else:
                    # If it's not an operator, command, or factoid, look for a __confused response
                    factoid = self.botbrain.findFactoid("__confused")
                    if(factoid is not None):
                        self.sendMessage(CHAN, factoid)


        # If the message is not addressed to the bot, let's look for a factoid
        else:
            if(len(message) > 2):
                logging.info("Looking for factoid: %s" % message)
                factoid = self.botbrain.findFactoid(message.lower().rstrip().lstrip())
                if(factoid is not None):
                    self.sendMessage(CHAN, self.preprocess_message(sender, factoid))

    def preprocess_message(self, sender, message):
        """ Allow use of $nick and $user keywords in factoids etc """
        global STATE
        # First allow the bot to address who it's responding to via $nick
        message = message.replace("$nick", sender)        
        # replace any instances of $user with a random username from STATE 
        message = message.replace("$user", random.choice(list(STATE['counters'].keys())))
        return message

    def on_private_message(self, sender, message):
        global STATE
        logging.info("Message received: sender: %s, message: %s" % (sender, message))


        # Allow the use of operators in private messages
        for op in self.botbrain.OPERATORS.keys():
            if(op in message):
                logging.info("Operator: %s" % op)
                # call the appropriate function in the function dictionary
                retval = self.botbrain.OPERATORS[op](message, sender, STATE)
                if (retval is not None):
                    self.sendMessage(sender, retval)

    def on_raw(self, message):
        """Called on raw message (almost anything). We don't want to handle most things here."""
        # Look for pings. TODO: idle processing stuff here.
        if("PING" in "%s" % message): 
            logging.info("PING!")
            # make sure db stays available
            if self.botbrain is not None: 
                self.botbrain.keepConnection()
            
        # Let the base client handle the raw stuff
        super(GrossmaulBot, self).on_raw(message)

# Start and connect the bot
client = GrossmaulBot(NICK, fallback_nicknames=[NICK[:-1]+"1", NICK[:-1]+"2"])
logging.info("Connecting to %s:%s" % (HOST, PORT))
client.connect(HOST, PORT, tls=True, tls_verify=False)
client.handle_forever()

