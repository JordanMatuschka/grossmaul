# All plugins inherit from this

class GrossmaulPlugin:
        def __init__(self):
                self.OPERATORS = { }
                self.COMMANDS = { }
                self.PROCESSCOMMANDS = { }

        def setMemory(self, memory):
            self.memory = memory

        def getMessageById(self, id):
                return self.memory.getMessageById(id)
