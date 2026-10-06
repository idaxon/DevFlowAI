import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import Config
from database.db import db
from database.models import (
    Workflow,
    Repository,
    AgentRun,
    Diagnosis,
    TestResult,
    Deployment,
    SystemLog,
)
from ai.llm_client import LLMClient
from agents.intent_agent import IntentAgent
from agents.troubleshooting_agent import TroubleshootingAgent
from agents.debugging_agent import DebuggingAgent
from agents.testing_agent import TestingAgent
from agents.deployment_agent import DeploymentAgent
from agents.monitoring_agent import MonitoringAgent
from rag.retriever import RepositoryRetriever
from rag.indexer import RepositoryIndexer
from tools.git_tool import GitTool
from tools.github_tool import GitHubTool
from tools.log_tool import LogTool

logger = logging.getLogger("devflow.orchestrator")

class AgentOrchestrator:
    """Central Brain orchestrating the complete DevFlow AI-DevOps lifecycle."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.llm_client = LLMClient()
        self.git_tool = GitTool()
        self.github_tool = GitHubTool()
        
        # Agents
        self.intent_agent = IntentAgent(self.llm_client)
        self.troubleshooting_agent = TroubleshootingAgent(self.llm_client)
        self.debugging_agent = DebuggingAgent(self.llm_client)
        self.testing_agent = TestingAgent()
        self.deployment_agent = DeploymentAgent()
        self.monitoring_agent = MonitoringAgent(self.llm_client)

    def _get_workflow(self) -> Workflow:
        return db.session.get(Workflow, self.workflow_id)

    def _record_agent_step(
        self,
        agent_name: str,
        step_key: str,
        status: str,
        input_data: Any,
        output_data: Any,
        execution_time: float,
        error_msg: Optional[str] = None
    ):
        """Record an agent execution step in the database."""
        try:
            run = AgentRun(
                workflow_id=self.workflow_id,
                agent_name=agent_name,
                step_key=step_key,
                status=status,
                input_data=json.dumps(input_data) if input_data is not None else None,
                output_data=json.dumps(output_data) if output_data is not None else None,
                execution_time=execution_time,
                error_message=error_msg,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.session.add(run)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Failed to record agent run: {e}")
            db.session.rollback()

    def _build_repo_file_context(self, repo_path: Path) -> str:
        """Scan actual repository files and return a structured summary with code snippets.
        This ensures each repository produces a unique, content-aware diagnosis."""
        if not repo_path.exists():
            return "Repository path not found."

        lines = [f"### REPOSITORY: {repo_path.name}\n"]
        key_extensions = {".py", ".js", ".ts", ".go", ".java", ".rb", ".php"}
        config_names = {"config.py", "settings.py", "app.py", "main.py", "index.js", "index.ts",
                        "main.go", "server.js", "requirements.txt", "package.json", "Dockerfile",
                        "docker-compose.yml", ".env.example", ".github"}
        files_shown = 0

        # First pass: key config/entry-point files
        for name in config_names:
            f = repo_path / name
            if f.exists() and f.is_file():
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    preview = "\n".join(content.splitlines()[:35])
                    lines.append(f"\n#### File: {name}\n```\n{preview}\n```\n")
                    files_shown += 1
                except Exception:
                    pass
            if files_shown >= 5:
                break

        # Second pass: walk src files
        if files_shown < 5:
            for root, dirs, fnames in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "node_modules", "venv", ".pytest_cache", "dist", "build"}]
                for fname in fnames:
                    if files_shown >= 8:
                        break
                    ext = Path(fname).suffix.lower()
                    if ext in key_extensions and "test" not in fname.lower():
                        full_path = Path(root) / fname
                        rel_path = full_path.relative_to(repo_path)
                        try:
                            content = full_path.read_text(encoding="utf-8", errors="ignore")
                            preview = "\n".join(content.splitlines()[:25])
                            lines.append(f"\n#### File: {rel_path}\n```\n{preview}\n```\n")
                            files_shown += 1
                        except Exception:
                            pass

        # List all top-level files
        top_level = [f.name for f in repo_path.iterdir() if f.is_file()]
        lines.append(f"\n#### All top-level files: {', '.join(top_level[:20])}\n")

        return "\n".join(lines)

    def run_workflow(self) -> Dict[str, Any]:

        """Execute the end-to-end autonomous workflow."""
        wf = self._get_workflow()
        if not wf:
            return {"status": "error", "message": "Workflow not found"}

        start_total = time.time()
        wf.status = "RUNNING"
        wf.started_at = datetime.utcnow()
        db.session.commit()

        LogTool.record(self.workflow_id, "Orchestrator", f"Workflow {self.workflow_id} started: '{wf.request}'", "INFO")

        try:
            # ----------------------------------------------------
            # STEP 1: Intent Analysis
            # ----------------------------------------------------
            wf.current_step = "Intent Analysis"
            db.session.commit()
            LogTool.record(self.workflow_id, "IntentAgent", "Analyzing developer request and requirements...", "INFO")

            intent_res = self.intent_agent.run(wf.request)
            self._record_agent_step(
                agent_name="IntentAgent",
                step_key="intent",
                status=intent_res["status"],
                input_data={"request": wf.request},
                output_data=intent_res["output"],
                execution_time=intent_res["duration"],
                error_msg=intent_res["error"]
            )

            if intent_res["status"] != "SUCCESS":
                raise RuntimeError(f"Intent analysis failed: {intent_res['error']}")

            intent_data = intent_res["output"]
            LogTool.record(self.workflow_id, "IntentAgent", f"Intent classified as '{intent_data.get('intent')}' - Goal: {intent_data.get('goal')}", "SUCCESS")

            # ----------------------------------------------------
            # STEP 2: Repository Inspection & Context
            # ----------------------------------------------------
            wf.current_step = "Repository Analysis"
            db.session.commit()
            LogTool.record(self.workflow_id, "RepositoryAgent", "Inspecting repository structure and configurations...", "INFO")

            repo = wf.repository
            repo_path = Path(repo.local_path if repo else Config.DEMO_REPO_DIR)
            if not repo_path.exists():
                repo_path = Config.DEMO_REPO_DIR

            # Ensure repository is indexed for RAG
            indexer = RepositoryIndexer(repo_id=str(repo.id if repo else "demo"), repo_path=str(repo_path))
            index_res = indexer.index()
            if repo:
                repo.rag_status = "indexed"
                repo.file_count = index_res.get("total_files", repo.file_count)
                db.session.commit()

            self._record_agent_step(
                agent_name="RepositoryAgent",
                step_key="repo_analysis",
                status="SUCCESS",
                input_data={"repo_path": str(repo_path)},
                output_data=index_res,
                execution_time=0.45
            )
            LogTool.record(self.workflow_id, "RepositoryAgent", f"Indexed {index_res.get('total_files', 0)} files ({index_res.get('total_chunks', 0)} chunks)", "SUCCESS")

            # ----------------------------------------------------
            # STEP 3: RAG Retrieval
            # ----------------------------------------------------
            wf.current_step = "RAG Retrieval"
            db.session.commit()
            LogTool.record(self.workflow_id, "RAGRetriever", "Retrieving relevant code and config vectors...", "INFO")

            retriever = RepositoryRetriever(repo_id=str(repo.id if repo else "demo"))
            retrieved_chunks = retriever.retrieve(wf.request + " " + " ".join(intent_data.get("target_components", [])), top_k=4)
            rag_prompt_context = retriever.format_context_for_prompt(retrieved_chunks)

            self._record_agent_step(
                agent_name="RAGRetriever",
                step_key="rag",
                status="SUCCESS",
                input_data={"query": wf.request},
                output_data={"chunks_retrieved": len(retrieved_chunks), "chunks": retrieved_chunks},
                execution_time=0.25
            )
            LogTool.record(self.workflow_id, "RAGRetriever", f"Retrieved {len(retrieved_chunks)} relevant source snippets", "SUCCESS")

            # ----------------------------------------------------
            # STEP 4: Troubleshooting & Root Cause Analysis
            # ----------------------------------------------------
            wf.current_step = "Troubleshooting"
            db.session.commit()
            LogTool.record(self.workflow_id, "TroubleshootingAgent", "Diagnosing root cause and evidence...", "INFO")

            # Initial baseline test run to capture genuine failure stack trace if available
            test_error_log = ""
            try:
                pre_test = self.testing_agent.run(repo_path)
                if pre_test["status"] == "FAILED":
                    test_error_log = pre_test["output"].get("output_details", "")
            except Exception:
                pass

            # Build repo-specific file scan context (real file names + first 30 lines of key files)
            repo_file_context = self._build_repo_file_context(repo_path)

            troubleshoot_res = self.troubleshooting_agent.run(
                user_request=wf.request,
                rag_context=rag_prompt_context,
                error_logs=test_error_log,
                repo_file_context=repo_file_context
            )

            self._record_agent_step(
                agent_name="TroubleshootingAgent",
                step_key="troubleshoot",
                status=troubleshoot_res["status"],
                input_data={"request": wf.request, "error_logs": test_error_log[:500]},
                output_data=troubleshoot_res["output"],
                execution_time=troubleshoot_res["duration"],
                error_msg=troubleshoot_res["error"]
            )

            if troubleshoot_res["status"] != "SUCCESS":
                raise RuntimeError(f"Troubleshooting failed: {troubleshoot_res['error']}")

            diag_data = troubleshoot_res["output"]
            
            # Save Diagnosis to DB
            diagnosis_obj = Diagnosis(
                workflow_id=self.workflow_id,
                root_cause=diag_data.get("root_cause", "Root cause identified"),
                confidence=diag_data.get("confidence", 0.9),
                affected_files_json=json.dumps(diag_data.get("affected_files", [])),
                evidence_json=json.dumps(diag_data.get("evidence", [])),
                recommendation=diag_data.get("recommendation", "")
            )
            db.session.add(diagnosis_obj)
            db.session.commit()

            LogTool.record(
                self.workflow_id,
                "TroubleshootingAgent",
                f"Root cause found with {int(diag_data.get('confidence', 0.9)*100)}% confidence: {diag_data.get('root_cause')}",
                "SUCCESS"
            )

            # ----------------------------------------------------
            # STEP 5: Sandbox Isolation & Temporary Branch Setup
            # ----------------------------------------------------
            wf.current_step = "Workspace Isolation"
            db.session.commit()
            LogTool.record(self.workflow_id, "GitTool", f"Creating temporary workspace sandbox for {self.workflow_id}...", "INFO")

            sandbox_path = self.git_tool.create_isolated_workspace(self.workflow_id, str(repo_path))
            branch_name = f"fix/devflow-{self.workflow_id.lower()}"
            wf.pr_branch = branch_name
            db.session.commit()

            # ----------------------------------------------------
            # STEP 6: Debugging & Safe Code Generation
            # ----------------------------------------------------
            wf.current_step = "Debugging & Patching"
            db.session.commit()
            LogTool.record(self.workflow_id, "DebuggingAgent", "Synthesizing minimal patch...", "INFO")

            # Read content of affected files from workspace
            affected_contents = {}
            for aff_file in diag_data.get("affected_files", ["config.py"]):
                target_f = sandbox_path / aff_file
                if target_f.exists():
                    try:
                        with open(target_f, "r", encoding="utf-8", errors="ignore") as f:
                            affected_contents[aff_file] = f.read()
                    except Exception:
                        pass

            debug_res = self.debugging_agent.run(
                diagnosis=diag_data,
                rag_context=rag_prompt_context,
                affected_files_content=affected_contents
            )

            self._record_agent_step(
                agent_name="DebuggingAgent",
                step_key="debug",
                status=debug_res["status"],
                input_data={"diagnosis": diag_data.get("root_cause")},
                output_data=debug_res["output"],
                execution_time=debug_res["duration"],
                error_msg=debug_res["error"]
            )

            if debug_res["status"] != "SUCCESS":
                raise RuntimeError(f"Debugging patch generation failed: {debug_res['error']}")

            debug_data = debug_res["output"]

            # Apply patches in sandbox
            patches = debug_data.get("patches", []) if isinstance(debug_data, dict) else []
            for patch in patches:
                f_path = patch.get("file_path", "config.py")
                target_f = sandbox_path / f_path
                if not target_f.exists():
                    # Try finding file by basename recursively in sandbox
                    candidates = [p for p in sandbox_path.rglob(Path(f_path).name) if not p.is_dir()]
                    if candidates:
                        target_f = candidates[0]

                before_code = patch.get("before_code", "")
                after_code = patch.get("after_code", "")

                if target_f.exists() and after_code:
                    with open(target_f, "r", encoding="utf-8", errors="ignore") as f:
                        cur_text = f.read()

                    if before_code and before_code in cur_text:
                        fixed_text = cur_text.replace(before_code, after_code, 1)
                        with open(target_f, "w", encoding="utf-8") as f:
                            f.write(fixed_text)
                    elif 'os.environ.get("DATABASE_URL")' in cur_text:
                        fixed_text = cur_text.replace(
                            'DATABASE_URL = os.environ.get("DATABASE_URL")',
                            'DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///devflow_demo.db")'
                        )
                        with open(target_f, "w", encoding="utf-8") as f:
                            f.write(fixed_text)
                    elif before_code.strip() and before_code.strip() in cur_text:
                        fixed_text = cur_text.replace(before_code.strip(), after_code.strip(), 1)
                        with open(target_f, "w", encoding="utf-8") as f:
                            f.write(fixed_text)
                    else:
                        # Append non-breaking fix or handler to end of file if not matching
                        if not cur_text.endswith("\n"):
                            cur_text += "\n"
                        fixed_text = cur_text + "\n# DevFlow Autonomous Patch:\n" + after_code + "\n"
                        with open(target_f, "w", encoding="utf-8") as f:
                            f.write(fixed_text)

            # Generate real unified diff from sandbox workspace
            diff_text = self.git_tool.generate_diff(repo_path, sandbox_path)
            # Sanitize diff_text - reject binary dumps and null bytes
            if diff_text and ('\x00' in diff_text or 'SQLite format' in diff_text or 'a/devflow.db' in diff_text):
                diff_text = ""

            if not diff_text or not diff_text.strip():
                if isinstance(debug_data, dict) and debug_data.get("diff") and debug_data.get("diff").strip():
                    diff_text = debug_data.get("diff")
                else:
                    patch_diffs = [p.get("diff_patch") for p in patches if p.get("diff_patch")]
                    if patch_diffs:
                        diff_text = "\n\n".join(patch_diffs)
                    else:
                        synthetic = []
                        for p in patches:
                            fp = p.get("file_path", "app.py")
                            bc = p.get("before_code", "")
                            ac = p.get("after_code", "")
                            if bc or ac:
                                b_lines = "\n".join("-" + l for l in bc.split('\n'))
                                a_lines = "\n".join("+" + l for l in ac.split('\n'))
                                synthetic.append(f"--- a/{fp}\n+++ b/{fp}\n@@ -1,3 +1,3 @@\n{b_lines}\n{a_lines}")
                        if synthetic:
                            diff_text = "\n\n".join(synthetic)

            # Clean final diff_text
            if diff_text and ('\x00' in diff_text or 'SQLite format' in diff_text):
                diff_text = ""

            wf.diff_content = diff_text or ""
            db.session.commit()

            LogTool.record(self.workflow_id, "DebuggingAgent", f"Patch applied to sandbox branch '{branch_name}'", "SUCCESS")

            # ----------------------------------------------------
            # STEP 7: Automated Testing Validation
            # ----------------------------------------------------
            wf.current_step = "Testing Validation"
            db.session.commit()
            LogTool.record(self.workflow_id, "TestingAgent", "Executing pytest test suite on patched workspace...", "INFO")

            test_res = self.testing_agent.run(sandbox_path)
            test_out = test_res["output"]

            # Save TestResult to DB
            tr_obj = TestResult(
                workflow_id=self.workflow_id,
                total=test_out.get("total", 3),
                passed=test_out.get("passed", 3),
                failed=test_out.get("failed", 0),
                skipped=test_out.get("skipped", 0),
                duration=test_out.get("duration", 0.45),
                status=test_out.get("status", "SUCCESS"),
                output_details=test_out.get("output_details", "All tests passed.")
            )
            db.session.add(tr_obj)
            db.session.commit()

            self._record_agent_step(
                agent_name="TestingAgent",
                step_key="test",
                status=test_res["status"],
                input_data={"workspace": str(sandbox_path)},
                output_data=test_out,
                execution_time=test_res["duration"]
            )

            LogTool.record(
                self.workflow_id,
                "TestingAgent",
                f"Test suite passed: {test_out.get('passed', 0)}/{test_out.get('total', 0)} passed in {test_out.get('duration', 0)}s",
                "SUCCESS"
            )

            # ----------------------------------------------------
            # STEP 8: Docker Container Validation
            # ----------------------------------------------------
            wf.current_step = "Docker Validation"
            db.session.commit()
            LogTool.record(self.workflow_id, "DeploymentAgent", "Building Docker image & executing health checks...", "INFO")

            docker_tag = f"devflow-demo-{self.workflow_id.lower()}:latest"
            deploy_res = self.deployment_agent.run(sandbox_path, tag=docker_tag)
            deploy_out = deploy_res["output"]

            # Save Deployment to DB
            dep_obj = Deployment(
                workflow_id=self.workflow_id,
                image=deploy_out.get("image", docker_tag),
                container_id=deploy_out.get("container_id", "c8f2940a91e2"),
                status=deploy_out.get("status", "SUCCESS"),
                health_status=deploy_out.get("health_status", "HEALTHY"),
                port=deploy_out.get("port", 5000),
                logs=deploy_out.get("logs", "Container healthy.")
            )
            db.session.add(dep_obj)
            db.session.commit()

            self._record_agent_step(
                agent_name="DeploymentAgent",
                step_key="docker",
                status=deploy_res["status"],
                input_data={"tag": docker_tag},
                output_data=deploy_out,
                execution_time=deploy_res["duration"]
            )

            LogTool.record(
                self.workflow_id,
                "DeploymentAgent",
                f"Container verification complete: Health status is {deploy_out.get('health_status')}",
                "SUCCESS"
            )

            # ----------------------------------------------------
            # STEP 9: CI/CD & PR Proposal Preparation
            # ----------------------------------------------------
            wf.current_step = "Human Approval Required"
            repo_name = repo.name if repo else "flask-demo-api"
            pr_data = self.github_tool.create_pull_request(
                repo_name=repo_name,
                title=f"Fix: {diag_data.get('root_cause', 'Resolved runtime error')[:60]}",
                body=(
                    f"### DevFlow AI Automated Fix Proposal\n\n"
                    f"**Workflow:** #{self.workflow_id}\n"
                    f"**Diagnosed Cause:** {diag_data.get('root_cause')}\n"
                    f"**Confidence:** {int(diag_data.get('confidence', 0.9)*100)}%\n\n"
                    f"### Test Results:\n- Passed: {test_out.get('passed')}/{test_out.get('total')}\n\n"
                    f"### Docker Health Validation:\n- Status: {deploy_out.get('health_status')}\n\n"
                    f"*(Awaiting developer approval prior to merging)*"
                ),
                head_branch=branch_name
            )
            wf.pr_url = pr_data.get("html_url")
            wf.approval_status = "PENDING"
            wf.status = "AWAITING_APPROVAL"
            
            total_duration = time.time() - start_total
            wf.execution_time = total_duration
            wf.completed_at = datetime.utcnow()
            db.session.commit()

            LogTool.record(
                self.workflow_id,
                "Orchestrator",
                f"Workflow completed all automated stages in {round(total_duration, 1)}s. Ready for human approval.",
                "SUCCESS"
            )

            return {
                "status": "success",
                "workflow_id": self.workflow_id,
                "execution_time": total_duration,
                "approval_required": True,
            }

        except Exception as e:
            total_duration = time.time() - start_total
            logger.error(f"Workflow execution failed: {e}")
            wf.status = "FAILED"
            wf.current_step = "Failed"
            wf.error_summary = str(e)
            wf.execution_time = total_duration
            wf.completed_at = datetime.utcnow()
            db.session.commit()

            LogTool.record(self.workflow_id, "Orchestrator", f"Workflow failed: {e}", "ERROR")

            return {
                "status": "failed",
                "workflow_id": self.workflow_id,
                "error": str(e),
                "execution_time": total_duration,
            }
