from Source import interface
interface = interface.ListenerInterface()

while interface.running:
    interface.update()

