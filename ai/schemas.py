from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IntentOutput(BaseModel):
    intent: str = Field(description="Classified intent (e.g. troubleshooting, debugging, deployment, testing, optimization)")
    goal: str = Field(description="Concise description of the user's objective")
    repository_required: bool = Field(default=True, description="Whether repository inspection is needed")
    logs_required: bool = Field(default=True, description="Whether logs analysis is needed")
    testing_required: bool = Field(default=True, description="Whether automated tests need to be run")
    deployment_required: bool = Field(default=True, description="Whether Docker validation/deployment is requested")
    target_components: List[str] = Field(default_factory=list, description="Specific endpoints or modules mentioned (e.g. /users, database)")

class CauseHypothesis(BaseModel):
    cause: str
    probability: float
    description: str

class TroubleshootingOutput(BaseModel):
    root_cause: str = Field(description="Primary diagnosed root cause")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    potential_causes: List[CauseHypothesis] = Field(default_factory=list, description="Ranked list of alternative causes")
    affected_files: List[str] = Field(default_factory=list, description="List of file paths contributing to or affected by the bug")
    evidence: List[str] = Field(default_factory=list, description="List of factual observations proving the root cause")
    recommendation: str = Field(description="Actionable guidance on how to fix the issue")

class CodeFilePatch(BaseModel):
    file_path: str
    before_code: str
    after_code: str
    diff_patch: str
    explanation: str

class DebuggingOutput(BaseModel):
    summary: str = Field(description="Summary of the code changes applied")
    patches: List[CodeFilePatch] = Field(default_factory=list, description="List of patches for affected files")
    diff: str = Field(description="Unified git-style diff")
    new_dependencies: List[str] = Field(default_factory=list, description="Any new packages or env keys required")

class TestingOutput(BaseModel):
    status: str = Field(description="SUCCESS or FAILED")
    total: int = Field(default=0)
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    skipped: int = Field(default=0)
    duration: float = Field(default=0.0)
    failures: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = Field(default="")

class DeploymentOutput(BaseModel):
    status: str = Field(description="SUCCESS, FAILED, or SIMULATED")
    image_tag: str = Field(default="devflow-test:latest")
    container_id: Optional[str] = None
    health_status: str = Field(default="HEALTHY")
    port: int = Field(default=5000)
    logs_sample: str = Field(default="")
    checks_passed: List[str] = Field(default_factory=list)

class MonitoringOutput(BaseModel):
    health_score: float = Field(default=1.0)
    recurring_errors: List[str] = Field(default_factory=list)
    active_services: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = Field(default="")
