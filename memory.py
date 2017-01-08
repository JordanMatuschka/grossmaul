from peewee import *
import datetime
import logging

from memoryconfig import db

class Keyword(Model):
    """Datatype to allow simple text replacement"""
    id = IntegerField(primary_key=True)
    # Who submitted the Keyword
    author = CharField()
    # Keyword to find in text
    keyword = CharField()
    # replacement text
    replacement = CharField()
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

    def deleteFactoid(self, username, id):
        logging.info("Memory - deleteFactoid")
        f = Factoid.get(Factoid.id == id)
        if (f is not None):
            ret =  "({}, {}) {} - {}".format(f.author, f.id, f.trigger, f.quote)
            if (f.author == username):
                f.delete_instance()
                return "Deleted: " + ret
            return "Unable to delete factoid: " + ret
        return "Unknown id."

    def deleteKeyword(self, username, id):
        logging.info("Memory - deleteKeyword")
        k = Keyword.get(Keyword.id == id)
        if (k is not None):
            ret =  "({}, {}) {} - {}".format(k.author, k.id, k.keyword, k.replacement)
            if (k.author == username):
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

    def getKeyword(self, keyword):
        logging.info("Memory - getKeyword")
        for k in Keyword.select().where(Keyword.keyword == keyword).order_by(fn.Rand()).limit(1):
            # Return only the replacement text
            return k.replacement

    def countKeyword(self, keyword):
        logging.info("Memory - countKeyword")
        return "%s count: %s" % (keyword, Keyword.select().where(Keyword.keyword == keyword).count())

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

    def findKeyword(self, searchphrase):
        logging.info("Memory - findKeyword")
        for k in Keyword.select().where(Keyword.replacement.contains(searchphrase)).order_by(fn.Rand()).limit(1):
            return "({}, {}) {} - {}".format(k.author, k.id, k.keyword, k.replacement)
        return "I don't have any keywords like %s." % searchphrase

    def findFactoid(self, searchphrase):
        logging.info("Memory - findFactoid")
        for f in Factoid.select().where(Factoid.quote.contains(searchphrase)).order_by(fn.Rand()).limit(1):
            # Update statistics 
            f.timesSeen = f.timesSeen + 1
            f.lastSeen = datetime.datetime.now()
            f.save()
            return "({}, {}) {} - {}".format(f.author, f.id, f.trigger, f.quote)
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
            return "<%s> %s" % (q.trigger, q.quote)
        return "I don't have any quotes for %s." % trigger

    def findQuote(self, searchphrase):
        logging.info("Memory - findQuote")
        for f in Quote.select().where(Quote.quote.contains(searchphrase)).order_by(fn.Rand()).limit(1):
            # Update statistics 
            f.timesSeen = f.timesSeen + 1
            f.lastSeen = datetime.datetime.now()
            f.save()
            return "({}, {}) {} - {}".format(f.author, f.id, f.trigger, f.quote)
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
