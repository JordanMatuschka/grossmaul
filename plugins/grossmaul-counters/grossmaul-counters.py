from grossmaulplugin import GrossmaulPlugin
import logging # TODO centralize this

class CountersPlugin(GrossmaulPlugin):
    def __init__(self):
        self.OPERATORS = { '++' : self.opIncrement, '+=' : self.opIncrement, '--' : self.opDecrement, '-=' : self.opDecrement }
        self.COMMANDS = {'vardump' : self.comVardump }
        self.PROCESSCOMMANDS = { 'vardump' : False }


    def getCountersByUser(self, user):
        logging.info("CountersPlugin - getCountersByUser - %s" % user)
        ret = {}
        #for counter in KV.select().where(KV.usr == usr, KV.app == COUNTERAPP):
        counters = self.get(None, user)
        for key in counters:
            ret[str(key)] = int(counters[key])
        return ret

    def getCounterValue(self, k, usr):
        logging.info("CountersPlugin - getCounterValue")
        counter = self.get(k, usr)
        if counter is not None:
            return int(counter)
        return None
        

    def comVardump(self, message, sender, STATE):
        logging.info("comVardump-  Message: %s Sender: %s" % (message, sender))
        # Look for a target parameter
        message = message.split()
        if(len(message) == 2):
            user = message[1]
            logging.info("Looking for %s in kv" % user)
            counters = self.getCountersByUser(user)
            if (counters):
                return "%s" % counters
            else:
                # if we can't find by user, let's look by key
                counters = self.get(message[1])
                if (counters):
                    return "%s" % counters
                else: 
                    return "I can't find any counters for %s" % user
        else:
            # If nothing else, return the sender's state
            return "%s" % self.getCountersByUser(sender)

    def opIncrement(self, message, sender, STATE, private=False):
        logging.info("opIncrement-  Message: %s Sender: %s" % (message, sender))
        if ("++" in message):
            delim = "++"
        else:
            delim = "+="
        logging.info("delim - %s" % (delim))

        if(delim == "++" and len(message.split("++")[1]) > 0):
            return

        # there shouldn't be any tokens before the counter + delim for valid use
        if len(message.split(delim)[0].split()) > 1:
            return

        if (delim == "+="):
            inc = int(message.split(delim)[1].strip())
            message = message.split(delim)[0].strip()
        else:
            inc = 1
            message = message.split(delim)[0].strip()

        # Allow 'targeting' counters with dot notation
        if ("." in message):
            sender = message.split(".")[0]
            message = message.split(".")[1]

        logging.info("inc - %s" % (repr(inc)))
        logging.info("message - %s" % (repr(message)))

        counter = self.getCounterValue(message, sender)
        
        if(counter):
            counter += inc
        else:
            counter = inc

        self.setValue(message, sender, int(counter))
        return "%s has a %s count of %i" % (sender, message, counter)

    def opDecrement(self, message, sender, STATE, private=False):
        logging.info("opDecrement-  Message: %s Sender: %s" % (message, sender))
        if ("--" in message):
            delim = "--"
        else:
            delim = "-="
        logging.info("delim - %s" % (delim))

        if (delim == '--' and len(message.split("--")[1]) > 0):
            return

        # there shouldn't be any tokens before the counter + delim for valid use
        if len(message.split(delim)[0].split()) > 1:
            return

        if (delim == "-="):
            dec = int(message.split(delim)[1].strip())
            message = message.split(delim)[0].strip()
        else:
            dec = 1
            message = message.split(delim)[0].strip()


        # Allow 'targeting' counters with dot notation
        if ("." in message):
            sender = message.split(".")[0]
            message = message.split(".")[1]

        logging.info("dec - %s" % (repr(dec)))
        logging.info("message - %s" % (repr(message)))

        counter = self.getCounterValue(message, sender)
        if(counter):
            counter -= dec
            if(counter <= 0):
                # Remove from list if we go to 0
                self.delete(message, sender)
                return "Counter removed."
            else:
                self.setValue(message, sender, counter)
                return "%s has a %s count of %i" % (sender, message, counter)
        else:
            return "I can't find that counter."

