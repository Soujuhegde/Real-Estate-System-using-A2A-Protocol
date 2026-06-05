"""
Shared A2A (Agent-to-Agent) Protocol Models
Based on Google's A2A specification
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
import uuid


class A2APart(BaseModel):
    text: str


class A2AMessage(BaseModel):
    role: str  # "user" | "agent"
    parts: List[A2APart]

    @classmethod
    def user(cls, text: str) -> "A2AMessage":
        return cls(role="user", parts=[A2APart(text=text)])

    @classmethod
    def agent(cls, text: str) -> "A2AMessage":
        return cls(role="agent", parts=[A2APart(text=text)])

    def text(self) -> str:
        return " ".join(p.text for p in self.parts)


class A2ATaskRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: A2AMessage
    metadata: Optional[Dict[str, Any]] = None


class A2ATaskStatus(BaseModel):
    state: str  # "submitted" | "working" | "completed" | "failed"
    message: Optional[A2AMessage] = None
    error: Optional[str] = None


class A2AArtifact(BaseModel):
    name: str
    parts: List[A2APart]
    metadata: Optional[Dict[str, Any]] = None


class A2ATaskResponse(BaseModel):
    id: str
    status: A2ATaskStatus
    artifacts: Optional[List[A2AArtifact]] = None


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    input_schema: Optional[Dict] = None


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: Dict[str, bool] = {"streaming": False, "pushNotifications": False}
    skills: List[AgentSkill] = []
