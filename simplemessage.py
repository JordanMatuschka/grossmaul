import sys
import time
from memory import Memory

memory = Memory()

for line in sys.stdin:
        memory.addReminder(line.rstrip().lstrip(), time.strftime("%Y-%m-%d"))

