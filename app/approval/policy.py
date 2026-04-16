from enum import Enum
from typing import Optional, Dict, Any
from datatime import datetime
from pydantic import BaseModel, Field


class ApprovalLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"req_{datetime.now().timestamp()}")
    action: str
    level: ApprovalLevel
    resource: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    def approve(self, approver: str = "system") -> None:
        self.approved = True
        self.approved_by = approver
        self.approved_at = datetime.now()

    def reject(self, rejector: str = "system") -> None:
        self.approved = False
        self.approved_by = rejector
        self.approved_at = datetime.now()


class ApprovalPolicy(BaseModel):
    policies: Dict[str, ApprovalLevel] = Field(default_factory=dict)
    default_level: ApprovalLevel = ApprovalLevel.MEDIUM
    auto_approve_threshold: ApprovalLevel = ApprovalLevel.LOW

    def get_level(self, action: str) -> ApprovalLevel:
        return self.policies.get(action, self.default_level)

    def requires_approval(self, action: str) -> bool:
        level = self.get_level(action)
        return level.value > self.auto_approve_threshold.value

    def create_request(self, action: str, resource: Optional[str] = None, 
                        metadata: Optional[Dict[str, Any]] = None) -> ApprovalRequest:
        return ApprovalRequest(
            action=action,
            level=self.get_level(action),
            resource=resource,
            metadata=metadata or dict()
        )

    def process_request(self, request: ApprovalRequest) -> bool:
        if request.level.value <= self.auto_approve_threshold.value:
            request.approve("auto")
            return True
        return False