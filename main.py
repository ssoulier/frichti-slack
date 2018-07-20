from commandHandler import CommandHandler, ResponseLayer
from dbLayer import dbLayer

dblayer = dbLayer()
responseLayer = ResponseLayer()


def endpoint(event, context):

    commandHandler = CommandHandler(event, dbLayer, responseLayer)

    return commandHandler.parseCommand()