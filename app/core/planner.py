"""Planner module for task decomposition and execution planning."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.logger import logger


class TaskNode(BaseModel):
    """Represents a single task in the execution plan."""
    
    id: str
    name: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Represents a complete execution plan."""
    
    id: str
    goal: str
    tasks: List[TaskNode]
    current_task_id: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Planner:
    """Planner for decomposing goals into executable tasks."""
    
    def __init__(self):
        """Initialize the planner."""
        self.current_plan: Optional[ExecutionPlan] = None
        self.plan_history: List[ExecutionPlan] = []
        logger.info("Planner initialized")
    
    async def create_plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """Create an execution plan from a goal.
        
        Args:
            goal: The high-level goal to achieve
            context: Optional context information
            
        Returns:
            ExecutionPlan: The generated execution plan
        """
        logger.info(f"Creating plan for goal: {goal}")
        
        # For now, create a simple single-task plan
        # This will be enhanced with LLM-based decomposition
        plan = ExecutionPlan(
            id=f"plan_{hash(goal) % 10000}",
            goal=goal,
            tasks=[
                TaskNode(
                    id="task_1",
                    name="Execute Goal",
                    description=goal,
                    dependencies=[],
                    status="pending"
                )
            ],
            status="pending",
            metadata=context or {}
        )
        
        self.current_plan = plan
        self.plan_history.append(plan)
        
        logger.info(f"Created plan with {len(plan.tasks)} tasks")
        return plan
    
    async def decompose_task(self, task: TaskNode) -> List[TaskNode]:
        """Decompose a task into subtasks if needed.
        
        Args:
            task: The task to decompose
            
        Returns:
            List[TaskNode]: List of subtasks (or original task if no decomposition needed)
        """
        logger.debug(f"Decomposing task: {task.name}")
        
        # For now, return the task as-is
        # This will be enhanced with intelligent decomposition logic
        return [task]
    
    async def get_next_task(self) -> Optional[TaskNode]:
        """Get the next task to execute from the current plan.
        
        Returns:
            Optional[TaskNode]: The next task to execute, or None if no tasks available
        """
        if not self.current_plan:
            logger.warning("No current plan available")
            return None
        
        # Find the first pending task with all dependencies completed
        for task in self.current_plan.tasks:
            if task.status == "pending":
                # Check if all dependencies are completed
                deps_completed = all(
                    t.status == "completed" 
                    for t in self.current_plan.tasks 
                    if t.id in task.dependencies
                )
                if deps_completed:
                    logger.info(f"Next task: {task.name}")
                    return task
        
        logger.info("No pending tasks available")
        return None
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: str, 
        result: Optional[Any] = None
    ) -> bool:
        """Update the status of a task.
        
        Args:
            task_id: The ID of the task to update
            status: The new status
            result: Optional result data
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if not self.current_plan:
            logger.error("No current plan to update")
            return False
        
        for task in self.current_plan.tasks:
            if task.id == task_id:
                task.status = status
                if result is not None:
                    task.result = result
                logger.info(f"Updated task {task_id} status to {status}")
                
                # Update plan status if needed
                self._update_plan_status()
                return True
        
        logger.error(f"Task {task_id} not found in current plan")
        return False
    
    def _update_plan_status(self):
        """Update the overall plan status based on task statuses."""
        if not self.current_plan:
            return
        
        all_completed = all(t.status == "completed" for t in self.current_plan.tasks)
        any_failed = any(t.status == "failed" for t in self.current_plan.tasks)
        any_running = any(t.status == "running" for t in self.current_plan.tasks)
        
        if all_completed:
            self.current_plan.status = "completed"
            logger.info("Plan completed successfully")
        elif any_failed:
            self.current_plan.status = "failed"
            logger.warning("Plan failed due to task failure")
        elif any_running:
            self.current_plan.status = "running"
        else:
            self.current_plan.status = "pending"
    
    async def replan(self, reason: str) -> Optional[ExecutionPlan]:
        """Create a new plan based on current state.
        
        Args:
            reason: The reason for replanning
            
        Returns:
            Optional[ExecutionPlan]: The new plan, or None if replanning failed
        """
        logger.info(f"Replanning due to: {reason}")
        
        if not self.current_plan:
            logger.error("No current plan to replan from")
            return None
        
        # For now, just mark the current plan as failed and return None
        # This will be enhanced with intelligent replanning logic
        self.current_plan.status = "failed"
        self.current_plan.metadata["replan_reason"] = reason
        
        logger.warning("Replanning not yet fully implemented")
        return None
    
    def get_plan_summary(self) -> Dict[str, Any]:
        """Get a summary of the current plan.
        
        Returns:
            Dict[str, Any]: Summary information about the current plan
        """
        if not self.current_plan:
            return {"status": "no_plan"}
        
        completed_tasks = sum(1 for t in self.current_plan.tasks if t.status == "completed")
        total_tasks = len(self.current_plan.tasks)
        
        return {
            "plan_id": self.current_plan.id,
            "goal": self.current_plan.goal,
            "status": self.current_plan.status,
            "progress": f"{completed_tasks}/{total_tasks}",
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "current_task": self.current_plan.current_task_id
        }
