# messaging/exceptions.py

class RPCError(Exception):
    pass


class RPCTimeoutError(RPCError):
    pass


class ServiceError(RPCError):
    pass