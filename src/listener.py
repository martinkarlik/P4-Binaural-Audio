from src import interface
interface = interface.ListenerInterface()

while interface.running:
    interface.update()
