import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar
from uuid import UUID, uuid4
import traceback

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)
agent_name_var: ContextVar[Optional[str]] = ContextVar("agent_name", default=None)