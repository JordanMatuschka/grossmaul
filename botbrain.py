from memory import Memory
from importlib import reload

class BotBrain:

    def __init__(self):
        self.memory = Memory()
        self.OPERATORS = {":=" : self.opDefine, "<<" : self.opDefineKeyword, "++" : self.opIncrement}
        self.COMMANDS  = {"remember" : self.comRemember, "recall" : self.comFindQuote, "evaluate" : self.comEvaluate }
        self.PROCESSCOMMANDS  = {"remember" :  False, "recall" : False, "evaluate" : True }
 
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
        while(len(message) > 1):
            # allow for "remember user word user word user word"
            # extract the username we're looking for
            targetuser = message.pop(0)
            # and the word 
            targettext = message.pop(0)

            print ("TARGETUSER %s :: TARGETTEXT %s" % (targetuser, targettext))
            # search the buffer for a matching line
            for user, text in buff:
                if(user == targetuser and targettext in text):
                    print ("found %s" % targettext)
                    # If there's already something there, make it multiline
                    if (len(quote) > 0):
                        quote += '\n' + '<' + targetuser + '> ' + text
                    else:
                        quote = text
        if (len(quote) > 0):
            # we found something, let's save it                
            self.memory.addQuote(sender, user, quote)
            return "Ok %s, remembering that %s said '%s'" % (sender, user, quote)
        else:
            return "Sorry %s, I couldn't find %s in my logs" % (sender, targettext)

    def comEvaluate(self, message, sender, STATE):
#        if(len(message.split(" ") >= 2)):
#            return 
        return self.memory.getLatestFactoid()

    def comFindQuote(self, message, sender, STATE):
        print ("***** comFindQuote %s" % message)
        trigger = message[len("recall")+1:]
        query = trigger.rstrip().lstrip()
        if (len(query) > 0):
            return self.memory.getQuote(query)
        else:
            return self.memory.getRandomQuote()

    def stripChars(self, string):
        return ''.join([l for l in string if l.isalnum() or l in ' '])

    def findFactoid(self, trigger):
        ret = self.memory.getFactoid(trigger)
        if (ret is not None):
            return ret
        else:
            # if the factoid is not found, strip out punctuation etc and try again
            return self.memory.getFactoid(self.stripChars(trigger))

    def findKeyword(self, keyword):
        return self.memory.getKeyword(keyword)    
