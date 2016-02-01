from memory import Memory
from importlib import reload

class BotBrain:

    def __init__(self):
        self.memory = Memory()
        self.OPERATORS = {":=" : self.opDefine, "<<" : self.opDefineKeyword, "++" : self.opIncrement}
        self.COMMANDS  = {"remember" : self.comRemember, "quote" : self.comFindQuote, "recall" : self.comFindQuote }
 
    def keepConnection(self):
        self.memory.keepConnection()

    def opDefineKeyword(self, message, sender, STATE):
        print("opDefineKeyword")
        print("Message: %s Sender: %s" % (message, sender))
        message = message.split("<<")
        if(len(message) >= 2):
            keyword = message[0].lower().rstrip().lstrip()
            replacement = message[1].rstrip().lstrip()
            self.memory.addKeyword(sender, keyword, replacement)
            return "Ok %s, remembering %s is a %s" % (sender, replacement, keyword)

    def opDefine(self, message, sender, STATE):
        print("op_define")
        print("Message: %s Sender: %s" % (message, sender))
        message = message.split(":=")
        if(len(message) >= 2):
            trigger = message[0].lower().rstrip().lstrip()
            print ("trigger = ", trigger)
            factoid = message[1].rstrip().lstrip()
            print ("factoid = ", factoid)
            self.memory.addFactoid(sender, trigger, factoid)
            return "Ok %s, remembering %s -> %s" % (sender, trigger, factoid)

    def opIncrement(self, message, sender, STATE):
        print("op_increment")

    def comRemember(self, message, sender, STATE):
        # TODO: All these prints need be using 'logging'
        # of course, half of this output shouldn't be there anyway

        # Should be in format 'remember user quote'
        # First strip the 'remember' out
        message = message[len('remember')+1:].lstrip()
        # extract the username we're looking for
        targetuser = message.split(" ")[0]
        # the rest is the text we'll be looking for:
        targettext = message[len(targetuser):].lstrip().rstrip()
        print ("TARGETUSER %s :: TARGETTEXT %s" % (targetuser, targettext))
        # search the buffer for a matching line
        if(len(STATE['buffer']) > 1):
            buff = STATE['buffer']
            buff.popleft()
            for user, text in buff:
                if(user == targetuser and targettext in text):
                    self.memory.addQuote(sender, user, text)
                    return "Ok %s, remembering that %s said '%s'" % (sender, user, text)
        return "Sorry %s, I couldn't find %s in my logs" % (sender, targettext)

    def comFindQuote(self, message, sender, STATE):
        print ("***** comFindQuote %s" % message)
        trigger = message[len("quote")+1:]
        return self.memory.getQuote(trigger.rstrip().lstrip())

    def findFactoid(self, trigger):
        return self.memory.getFactoid(trigger)    
    
    def findKeyword(self, keyword):
        return self.memory.getKeyword(keyword)    
