from peewee import *
import datetime
import logging

from config import db
COUNTERAPP = "counters"

class Keyword(Model):
    """Datatype to allow simple text replacement"""
    id = IntegerField(primary_key=True)
    # Who submitted the Keyword
    author = CharField()
    # Keyword to find in text
    keyword = CharField()
    # replacement text
    replacement = CharField()
    # ------------ Defaults below
    # When was this added?
    timeAdded = DateTimeField(default=datetime.datetime.now)
    class Meta:
        global db
        database = db

class Message(Model):
    id = IntegerField(primary_key=True)
    # Message to be sent to channel
    message = CharField()
    # Did a user of the channel send this?
    sender = CharField()
    # Should we evaluate this like a normal message?
    evaluate = BooleanField()
    # When should it be displayed
    triggerTime = DateTimeField(default=datetime.datetime.now)
    timesSeen = IntegerField(default = 0)
    # Who to send the message to. If null, send to channel
    target = CharField(null = True)
    class Meta:
        global db
        database = db

class KV(Model):
    """Simple model that stores key-value pairs per user, per app
    lookups require usr / k and return value
    usr may be overridden to be applications or plugins with prefixes for extensibility
    value is varchar but may be interpreted as other types
    """
    id = IntegerField(primary_key=True)
    usr = CharField()
    k = CharField()
    value = CharField()
    app = CharField()
    class Meta:
        global db
        database = db

class Factoid(Model):
    id = IntegerField(primary_key=True)
    # Who submitted the factoid
    author = CharField()
    # What will bring up this factoid
    trigger = CharField()
    # quote data to display to the channel
    quote = CharField()
    # ------------ Defaults below
    # When was this added?
    timeAdded = DateTimeField(default=datetime.datetime.now)
    # How many times have we seen this factoid?
    timesSeen = IntegerField(default = 0)
    # When last has this come up in the channel?
    lastSeen = DateTimeField(default=datetime.datetime.now)
    class Meta:
        global db
        database = db

# At the moment, Quotes are just factoids kept seperately and treated slightly different
# This may change when multiline quotes come about
class Quote(Model):
    id = IntegerField(primary_key=True)
    # Who submitted the quote
    author = CharField()
    # What will bring up this quote
    trigger = CharField()
    # quote data to display to the channel
    quote = CharField()
    # ------------ Defaults below
    # When was this added?
    timeAdded = DateTimeField(default=datetime.datetime.now)
    # How many times have we seen this quote?
    timesSeen = IntegerField(default = 0)
    # When last has this come up in the channel?
    lastSeen = DateTimeField(default=datetime.datetime.now)
    class Meta:
        global db
        database = db

class Memory:
    def __init__(self):
        logging.info("Memory connecting to MySql")
        self.db = db
        self.db.connect()
        logging.info("Memory Connected!")

    def keepConnection(self):
        # More like renew connection, now
        self.db.close()
        self.db.connect()

    def deleteFactoid(self, username, id, allow_delete=[]):
        logging.info("Memory - deleteFactoid")
        f = Factoid.get(Factoid.id == id)
        if (f is not None):
            ret =  "({}, {}) {} - {}".format(f.author, f.id, f.trigger, f.quote)
            if (f.author == username or f.author in allow_delete):
                f.delete_instance()
                return "Deleted: " + ret
            return "Unable to delete factoid: " + ret
        return "Unknown id."

    def deleteKeyword(self, username, id, allow_delete=[]):
        logging.info("Memory - deleteKeyword")
        k = Keyword.get(Keyword.id == id)
        if (k is not None):
            ret =  "({}, {}) {} - {}".format(k.author, k.id, k.keyword, k.replacement)
            if (k.author == username or f.author in allow_delete):
                k.delete_instance()
                return "Deleted: " + ret
            return "Unable to delete keyword: " + ret
        return "Unknown id."

    def addFactoid(self, author, trigger, quote):
        logging.info("Memory - addFactoid")
        f = Factoid(author=author, trigger=trigger, quote=quote)
        f.save()    

    def addKeyword(self, author, keyword, replacement):
        logging.info("Memory - addKeyword")
        k = Keyword(author=author, keyword=keyword, replacement=replacement)
        k.save()    

    def addReminder(self, message, timestamp, sender=None):
        logging.info("Memory - addReminder")
        r = Message(message=message, triggerTime=timestamp, timesSeen=0, target=sender)
        r.save()    

    def getKeyword(self, keyword):
        logging.info("Memory - getKeyword")
        for k in Keyword.select().where(Keyword.keyword == keyword).order_by(fn.Rand()).limit(1):
            # Return only the replacement text
            return k.replacement

    def countKeyword(self, keyword):
        logging.info("Memory - countKeyword")
        return "%s count: %s" % (keyword, Keyword.select().where(Keyword.keyword == keyword).count())

    def getCountersByUser(self, usr):
        global COUNTERAPP # fix this shit
        logging.info("Memory - getCountersByUser")
        ret = {}
        for counter in KV.select().where(KV.usr == usr, KV.app == COUNTERAPP):
            logging.info("Loading %s - %s" % (str(counter.k), str(counter.value)))
            ret[str(counter.k)] = int(counter.value)
        return ret 

    # All db API should follow App, Key, User order, some will be missing

# Abstract this one even futrher, it should call get KVA and just return the value
    def getValueAppKeyUser(self, app, k, usr):
        logging.info("Memory - getValueAppKeyUser")
        for kva in KV.select().where(
                (KV.usr == usr) & 
                (KV.k == k) &
                (KV.app == app)
            ):
            logging.info("KVA id = %i" % kva.id)
            return kva
        return None

    def getValuesAppKey(self, app, k):
        logging.info("Memory - getValuesAppKey")
        ret = {}
        for val in KV.select().where(KV.app == app, KV.k == k):
            logging.info("Found %s - %s" % (str(val.k), str(val.value)))
            # 
            ret[str(val.usr)] = val.value
        return ret 

    def getValuesAppUser(self, app, usr):
        logging.info("Memory - getValuesAppUser")
        ret = {}
        for val in KV.select().where(KV.usr == usr, KV.app == app):
            logging.info("Found %s - %s" % (str(val.k), str(val.value)))
            # 
            ret[str(val.k)] = val.value
        return ret 

    def getKVAppKeyUser(self, app, k, usr):
        logging.info("Memory - getValueAppKeyUser")
        for kva in KV.select().where(
                (KV.usr == usr) & 
                (KV.k == k) &
                (KV.app == app)
            ):
            logging.info("KVA id = %i" % kva.id)
            return kva
        return None

    def setValue(self, app, k, usr, value):
        logging.info("Memory - setValue")
        counter = self.getValueAppKeyUser(app, k, usr)
        if not counter:
            # counter does not exist, simply create the object
            counter = KV(usr = usr, k = k, value = value, app = app)
        else:
            counter.value = value

        counter.save()

    def delete(self, app, usr, k):
        logging.info("Memory - delete")
        c = self.getKVAppKeyUser(app, usr, k)
        if (c is not None):
            c.delete_instance()

    def getCounter(self, usr, k):
        global COUNTERAPP # fix this shit
        logging.info("Memory - getCounter")
        return self.getValueAppKeyUser(COUNTERAPP, k, usr)

    def getCounterValue(self, usr, k):
        logging.info("Memory - getCounterValue")
        counter = self.getCounter(usr, k)
        return int(counter.value)
        
# TODO do the rest of these guys like this
    def deleteCounter(self, usr, k):
        global COUNTERAPP # fix this shit
        logging.info("Memory - deleteCounter")
        c = self.getCounter(usr, k)
        if (c is not None):
            c.delete_instance()
        

    def getMessageById(self, id):
        logging.info("Memory - getMessageById")

        m = Message.get(Message.id == id)
        if (m is not None):
            return m
        return "Unknown id."

    def getMessages(self):
        logging.info("Memory - getMessages")

        messages = []
        for m in Message.select().where(
                (Message.timesSeen == 0) & 
                (Message.triggerTime < datetime.datetime.now())
            ):
            # Update statistics 
            m.timesSeen = m.timesSeen + 1
            m.save()
            # Return only the message
            messages.append((m.message, m.target, m.sender, m.evaluate))
             
        return messages

    def getLatestFactoid(self):
        logging.info("Memory - getLatestFactoid")
        # Honestly this isn't prettier than just writing SQL
        for f in Factoid.select().order_by(Factoid.id.desc()).limit(1):
            # Update statistics 
            f.timesSeen = f.timesSeen + 1
            f.lastSeen = datetime.datetime.now()
            f.save()
            # Return only the text of the factoid
            return f.quote

    def countFactoid(self, trigger):
        logging.info("Memory - countFactoid")
        return "%s count: %s" % (trigger, Factoid.select().where(Factoid.trigger == trigger).count())

    def getFactoid(self, trigger):
        logging.info("Memory - getFactoid")
        # Honestly this isn't prettier than just writing SQL
        for f in Factoid.select().where(Factoid.trigger == trigger).order_by(fn.Rand()).limit(1):
            # Update statistics 
            f.timesSeen = f.timesSeen + 1
            f.lastSeen = datetime.datetime.now()
            f.save()
            # Return only the text of the factoid
            return f.quote

    def getFactoidById(self, id):
        logging.info("Memory - getFactoid")
        # Honestly this isn't prettier than just writing SQL
        f = Factoid.get(Factoid.id == id)
        if (f is not None):
            # Update statistics 
            f.timesSeen = f.timesSeen + 1
            f.lastSeen = datetime.datetime.now()
            f.save()
            # Return only the text of the factoid
            return f.quote
        return "I don't have a factoid with that id."

    def findKeyword(self, searchphrase):
        logging.info("Memory - findKeyword")
        for k in Keyword.select().where(Keyword.replacement.contains(searchphrase)).order_by(fn.Rand()).limit(1):
            return "({}, {}, {}) {} - {}".format(k.author, k.id, k.timeAdded, k.keyword, k.replacement)
        return "I don't have any keywords like %s." % searchphrase

    def findFactoid(self, searchphrase):
        logging.info("Memory - findFactoid")
        for f in Factoid.select().where(Factoid.quote.contains(searchphrase)).order_by(fn.Rand()).limit(1):
            return "({}, {}, {}, seen {} times) {} - {}".format(f.author, f.id, f.timeAdded, f.timesSeen, f.trigger, f.quote)
        return "I don't have any quotes for %s." % searchphrase

    def addQuote(self, author, trigger, quote):
        logging.info("Memory - addQuote")
        q = Quote(author=author, trigger=trigger, quote=quote)
        q.save()    

    def getQuote(self, trigger):
        logging.info("Memory - getQuote")
        for q in Quote.select().where(Quote.trigger == trigger).order_by(fn.Rand()).limit(1):
            # Update statistics 
            q.timesSeen = q.timesSeen + 1
            q.lastSeen = datetime.datetime.now()
            q.save()
            # Return the formatted quote
            ret = []
            ret_string = "<%s> %s" % (q.trigger, q.quote)
            if '\n' not in ret_string:
                if '> /me' in ret_string:
                    ret_string = ret_string.replace('> /me', '', 1)
                    ret_string = ret_string.replace('<', '* ', 1)
                return ret_string
            # otherwise check each line for strings indicating /me
            for line in ret_string.split('\n'):
                if '> /me' in line:
                    line = line.replace('> /me', '', 1)
                    line = line.replace('<', '* ', 1)
                logging.info("Line - " + line)
                ret.append(line)
            return '\\n'.join(ret)
                    
                
        return "I don't have any quotes for %s." % trigger

    def findQuote(self, searchphrase):
        logging.info("Memory - findQuote")
        for f in Quote.select().where(Quote.quote.contains(searchphrase)).order_by(fn.Rand()).limit(1):
            return "({}, {}, {}, seen {} times) {} - {}".format(f.author, f.id, f.timeAdded, f.timesSeen, f.trigger, f.quote)
        return "I don't have any quotes for %s." % searchphrase

    def getRandomQuote(self):
        logging.info("Memory - getRandomQuote")
        for q in Quote.select().order_by(fn.Rand()).limit(1):
            # Update statistics 
            q.timesSeen = q.timesSeen + 1
            q.lastSeen = datetime.datetime.now()
            q.save()
            # Return the formatted quote
            return "<%s> %s" % (q.trigger, q.quote)
        return "No quotes found."
