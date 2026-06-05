import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from .a2a_models import (
    A2AMessage, A2ATaskRequest, A2ATaskResponse,
    A2ATaskStatus, A2AArtifact, AgentCard, AgentSkill, A2APart
)
from .a2a_client import A2AClient
from . import config
