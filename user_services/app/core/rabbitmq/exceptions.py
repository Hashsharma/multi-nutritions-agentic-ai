class RabbitMQError(Exception):
    pass

class ConnectionError(RabbitMQError):
    pass

class HandlerNotFoundError(RabbitMQError):
    pass

class MessageProcessingError(RabbitMQError):
    pass