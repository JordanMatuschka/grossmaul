# All plugins inherit from this

class GrossmaulPlugin:
        # TODO Fix init to include memory reference
        # TODO pass in KV from memory.py
        def __init__(self):
            self.OPERATORS = { }
            self.COMMANDS = { }
            self.PROCESSCOMMANDS = { }

        def setMemory(self, memory):
            self.memory = memory

        def getClass(self):
            return type(self).__name__
            # or should this be self.__class__.__name__

        def getMessageById(self, id):
            return self.memory.getMessageById(id)

        # def addMessage(self, message, timestamp):

        def get(self, key = None, usr = None):
            # Parse out missing values to determine what we're getting from the KV
            app = self.getClass()
            if key is None and usr is None:
                return false

            if key is None:
                return self.getValuesAppUser(app, usr)

            if usr is None:
                return self.getValuesAppKey(app, key)
            
            # All 'targeting' values, get a single value
            return self.getValueAppKeyUser(app, key, usr)

        def delete(self, key, usr):
            app = self.getClass()
            return self.memory.delete(app, key, usr)

        def getValueAppKeyUser(self, app, key, usr):
            return self.memory.getValueAppKeyUser(app, key, usr)
        
        def getValuesAppKey(self, app, key):
            return self.memory.getValuesAppKey(app, key)

        def getValuesAppUser(self, app, usr):
            return self.memory.getValuesAppUser(app, usr)

        def setValue(self, key, usr, value):
            app = self.getClass()
            return self.memory.setValue(app, key, usr, value)

