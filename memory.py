from peewee import *
import datetime
import logging

from memoryconfig import db

class Keyword(Model):
    """Datatype to allow simple text replacement"""
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

    def addFactoid(self, author, trigger, quote):
        f = Factoid(author=author, trigger=trigger, quote=quote)
        f.save()    

    def addKeyword(self, author, keyword, replacement):
        k = Keyword(author=author, keyword=keyword, replacement=replacement)
        k.save()    

    def getKeyword(self, keyword):
        for k in Keyword.select().where(Keyword.keyword == keyword).order_by(fn.Rand()).limit(1):
            # Return only the replacement text
            return k.replacement

    def getFactoid(self, trigger):
        # Honestly this isn't prettier than just writing SQL
        for f in Factoid.select().where(Factoid.trigger == trigger).order_by(fn.Rand()).limit(1):
            # Update statistics 
            f.timesSeen = f.timesSeen + 1
            f.lastSeen = datetime.datetime.now()
            f.save()
            # Return only the text of the factoid
            return f.quote

    def addQuote(self, author, trigger, quote):
        q = Quote(author=author, trigger=trigger, quote=quote)
        q.save()    

    def getQuote(self, trigger):
        for q in Quote.select().where(Quote.trigger == trigger).order_by(fn.Rand()).limit(1):
            # Update statistics 
            q.timesSeen = q.timesSeen + 1
            q.lastSeen = datetime.datetime.now()
            q.save()
            # Return the formatted quote
            return "<%s> %s" % (q.trigger, q.quote)
        return "I don't have any quotes for %s." % trigger

    def getRandomQuote(self):
        for q in Quote.select().order_by(fn.Rand()).limit(1):
            # Update statistics 
            q.timesSeen = q.timesSeen + 1
            q.lastSeen = datetime.datetime.now()
            q.save()
            # Return the formatted quote
            return "<%s> %s" % (q.trigger, q.quote)
        return "No quotes found."
