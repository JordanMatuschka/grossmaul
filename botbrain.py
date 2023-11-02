from memory import Memory
import logging
import time
import parsedatetime
from importlib import import_module 
from pathlib import Path
from inspect import isclass
from sys import path

path.append('./plugins')
import grossmaulplugin

class BotBrain:

    def __init__(self):
        self.memory = Memory()
        self.OPERATORS = {":=" : self.opDefine, "<<" : self.opDefineKeyword, "@all@" : self.opPublicReminder, "@@" : self.opReminder  }
        self.COMMANDS  = {"remember" : self.comRemember, "recall" : self.comFindQuote, 
                    "evaluate" : self.comEvaluate, "count" : self.comCount, "findfactoid" : self.comFactoidSearch,
                    "findquote" : self.comQuoteSearch, "findkeyword" : self.comKeywordSearch,
                    "delete" : self.comDeleteFactoid, "deletekeyword" : self.comDeleteKeyword,
                    "plugins" : self.comListPlugins }
        self.PROCESSCOMMANDS  = {"remember" :  False, "recall" : False, "evaluate" : True, "count" : False,
                    "findfactoid" : False, "findquote" : False, "findkeyword" : False, "delete" : False,
                    "deletekeyword" : False, "plugins" : False }
        self.PLUGINS = [ ]

        # Look for any installed plugins and add to command/operator dictionaries
        self.loadPlugins()

    def loadPlugins(self):
        path = Path('./plugins')

        dirs = [e for e in path.iterdir() if e.is_dir()]
        for d in dirs:
            # Ignore temp/private directories like __pycache__
            if d.name[0] != '_' and d.name[0] != '.':
                # import the module for testing
                plugin = import_module('plugins.' + d.name + '.' + d.name) 

                for i in vars(plugin):
                    cls = getattr(plugin, i)
                    if isclass(cls):
                        instance = cls()
                        # If instance is subclass to GrossmaulPlugin, it will have COMMANDS, OPERATORS, and PROCESSCOMMANDS, so add those
                        # to our main dictionaries
                        if issubclass(cls, grossmaulplugin.GrossmaulPlugin):
                            self.COMMANDS.update(instance.COMMANDS)
                            self.OPERATORS.update(instance.OPERATORS)
                            self.PROCESSCOMMANDS.update(instance.PROCESSCOMMANDS)
                            if type(instance).__name__ != 'GrossmaulPlugin': 
                                self.PLUGINS.append(type(instance).__name__)
                            instance.setMemory(self.memory)
 
    def keepConnection(self):
        self.memory.keepConnection()

    def opPublicReminder(self, message, sender, STATE, private=False):
        logging.info("opPublicReminder-  Message: %s Sender: %s" % (message, sender))
        # No matter what is passed in, this is now a public reminder
        # (private = False)
        return self.opReminder(message, sender, STATE, False)

    def opReminder(self, message, sender, STATE, private=False):
        """ Set a reminder in the form of {message} @@ {timestamp} """
        logging.info("opReminder-  Message: %s Sender: %s" % (message, sender))
        if ("@all@" in message):
            message = message.split("@all@")
        else:
            message = message.split("@@")
        if(len(message) == 2):
            reminder = message[0].rstrip().lstrip()
            timestamp = message[1].lower().rstrip().lstrip()
            # allow private reminders
            target = None
            if private:
                logging.info("Private reminder to %s" % (sender))
                target = sender
                
            # Attempt to parse timestamp text
            cal = parsedatetime.Calendar()
            when, ret = cal.parse(timestamp)
            # 0 means we can't parse
            if ret > 0:
                isotimestamp = time.strftime('%Y-%m-%dT%H:%M:%S', when)
                self.memory.addReminder("[ " + sender + "] " + reminder, isotimestamp, target)
                return "Ok %s, reminder set for %s" % (sender, isotimestamp)
            else:
                return "I can't make a reminder for %s" % (timestamp)
                


    def opDefineKeyword(self, message, sender, STATE, private=False):
        logging.info("opDefineKeyword-  Message: %s Sender: %s" % (message, sender))
        message = message.split("<<")
        if(len(message) >= 2):
            keyword = message[0].lower().rstrip().lstrip()
            replacement = message[1].rstrip().lstrip()
            self.memory.addKeyword(sender, keyword, replacement)
            return "Ok %s, remembering %s is a %s" % (sender, replacement, keyword)

    def opDefine(self, message, sender, STATE, private=False):
        logging.info("opDefine-  Message: %s Sender: %s" % (message, sender))
        message = message.split(":=")
        if(len(message) >= 2):
            trigger = message[0].lower().rstrip().lstrip()
            factoid = message[1].rstrip().lstrip()
            self.memory.addFactoid(sender, trigger, factoid)
            return "Ok %s, remembering %s -> %s" % (sender, trigger, factoid)

    def comListPlugins (self, message, sender, STATE):
        return str(self.PLUGINS)

    def comDeleteKeyword(self, message, sender, STATE):
        logging.info("comDeleteKeyword-  Message: %s Sender: %s" % (message, sender))
        # strip out command
        message = message[len('deletekeyword')+1:].lstrip()
        return self.memory.deleteKeyword(sender, message, STATE['allow_delete'])

    def comDeleteFactoid(self, message, sender, STATE):
        logging.info("comDeleteFactoid-  Message: %s Sender: %s" % (message, sender))
        # strip out command
        message = message[len('delete')+1:].lstrip()
        return self.memory.deleteFactoid(sender, message, STATE['allow_delete'])


    def comRemember(self, message, sender, STATE):
        logging.info("comRemember-  Message: %s Sender: %s" % (message, sender))
        # Should be in format 'remember user quote'
        # First strip the 'remember' out
        message = message[len('remember')+1:].lstrip()
        # We might need to build a multiline quote:
        quote = ""
        # Split it by spaces, we're looking for user / word pairs
        message = message.split()
        # we'll just say the first one we look up is the 'sender'
        user = message[0]
        # remove the 'remember' command so we don't match
        buff = None
        if(len(STATE['buffer']) > 1):
            buff = STATE['buffer']
            buff.popleft()

        primaryuser = message[0]
        if(primaryuser in STATE['timestamp'].keys()):
            while(len(message) > 1):
                # allow for "remember user word user word user word"
                # extract the username we're looking for
                targetuser = message.pop(0)
                # and the word 
                targettext = message.pop(0)

                # search the buffer for a matching line
                for user, text in buff:
                    if(user == targetuser and targettext in text):
                        # If there's already something there, make it multiline
                        if (len(quote) > 0):
                            quote += '\n' + '<' + targetuser + '> ' + text
                        else:
                            quote = text
                        break # break for

        if (len(quote) > 0):
            # we found something, let's save it                
            self.memory.addQuote(sender, primaryuser, quote)
            return "Ok %s, remembering that %s said '%s'" % (sender, primaryuser, quote)
        else:
            return "Sorry %s, I couldn't find %s in my logs" % (sender, targettext)

    def comEvaluate(self, message, sender, STATE):
        logging.info("comEvaluate-  Message: %s Sender: %s" % (message, sender))
        message = message.rstrip().lstrip()[:255]
        if(len(message.split(" ")) == 2) and (message.split(" ")[1].isnumeric()):
            # If this is a number we're evaluating by id
                return self.memory.getFactoidById(int(message.split(" ")[1]))

        if(len(message.split(" ")) >= 2):
            return ' '.join(message.split(" ")[1:])

        # if no keyword is passed, just return the latest factoid
        return self.memory.getLatestFactoid()

    def comFactoidSearch(self, message, sender, STATE):
        logging.info("comFactoidSearch-  Message: %s Sender: %s" % (message, sender))
        trigger = message[len("findfactoid")+1:]
        query = trigger.rstrip().lstrip()
        if (len(query) > 0):
            return self.memory.findFactoid(query)

    def comKeywordSearch(self, message, sender, STATE):
        logging.info("comKeywordSearch-  Message: %s Sender: %s" % (message, sender))
        trigger = message[len("findkeyword")+1:]
        query = trigger.rstrip().lstrip()
        if (len(query) > 0):
            return self.memory.findKeyword(query)

    def comQuoteSearch(self, message, sender, STATE):
        logging.info("comQuoteSearch-  Message: %s Sender: %s" % (message, sender))
        trigger = message[len("findquote")+1:]
        query = trigger.rstrip().lstrip()
        if (len(query) > 0):
            return self.memory.findQuote(query)

    def comFindQuote(self, message, sender, STATE):
        logging.info("comFindQuote-  Message: %s Sender: %s" % (message, sender))
        trigger = message[len("recall")+1:]
        query = trigger.rstrip().lstrip()
        if (len(query) > 0):
            return self.memory.getQuote(query)
        else:
            return self.memory.getRandomQuote()

    def comCount(self, message, sender, STATE):
        logging.info("comCount-  Message: %s Sender: %s" % (message, sender))
        trigger = message[len("count")+1:]
        query = trigger.rstrip().lstrip()
        if (len(query) > 0):
            if(query[0] == '$'):
                return self.memory.countKeyword(query[1:])
            else:
                return self.memory.countFactoid(query)

    def stripChars(self, string):
        return ''.join([l for l in string if l.isalnum() or l in ' '])

    def findFactoid(self, trigger):
        logging.info("findFactoid-  trigger: %s" % (trigger))
        ret = self.memory.getFactoid(trigger)
        if (ret is not None):
            return ret
        else:
            # if the factoid is not found, strip out punctuation etc and try again
            return self.memory.getFactoid(self.stripChars(trigger))

    def findKeyword(self, keyword):
        logging.info("findKeyword-  keyword: %s" % (keyword))
        return self.memory.getKeyword(keyword)    

    def getMessages(self):
        return self.memory.getMessages()    
