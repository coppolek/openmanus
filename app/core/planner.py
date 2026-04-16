"""Task planner for breaking down complex tasks into steps."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.logger import logger


class TaskStep(BaseModel):
    """Represents a single step in a task plan."""
    
    step_number: int = Field(description="Step number in sequence")
    description: str = Field(description="Description of what to do")
    tool_hint: Optional[str] = Field(default=None, description="Suggested tool to use")
    dependencies: List[int] = Field(default_factory=list, description="Step numbers this depends on")
    completed: bool = Field(default=False)


class TaskPlan(BaseModel):
    """Represents a complete task plan."""
    
    goal: str = Field(description="Overall goal of the plan")
    steps: List[TaskStep] = Field(default_factory=list)
    current_step: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Planner(BaseModel):
    """Creates and manages task plans."""
    
    max_steps: int = Field(default=10, description="Maximum number of steps in a plan")
    current_plan: Optional[TaskPlan] = Field(default=None)
    
    def create_plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """Create a task plan for the given goal."""
        # Simple heuristic-based planning for now
        steps = []
        
        goal_lower = goal.lower()
        
        if "write" in goal_lower or "create" in goal_lower:
            if "file" in goal_lower:
                steps.append(
                    TaskStep(
                        step_number=1,
                        description="Determine file path and content requirements",
                        tool_hint="ask_human"
                    )
                )
                steps.append(
                    TaskStep(
                        step_number=2,
                        description="Create or edit the file",
                        tool_hint="str_replace_editor",
                        dependencies=[1]
                    )
                )
            elif "code" in goal_lower or "function" in goal_lower:
                steps.append(
                    TaskStep(
                        step_number=1,
                        description="Analyze requirements and design solution",
                        tool_hint="python_execute"
                    )
                )
                steps.append(
                    TaskStep(
                        step_number=2,
                        description="Implement the code",
                        tool_hint="str_replace_editor",
                        dependencies=[1]
                    )
                )
                steps.append(
                    TaskStep(
                        step_number=3,
                        description="Test the implementation",
                        tool_hint="python_execute",
                        dependencies=[2]
                    )
                )
        
        elif "search" in goal_lower or "find" in goal_lower:
            steps.append(
                TaskStep(
                    step_number=1,
                    description="Perform web search",
                    tool_hint="browser_use"
                )
            )
            steps.append(
                TaskStep(
                    step_number=2,
                    description="Extract and summarize results",
                    dependencies=[1]
                )
            )
        
        elif "analyze" in goal_lower:
            steps.append(
                TaskStep(
                    step_number=1,
                    description="Load and prepare data",
                    tool_hint="python_execute"
                )
            )
            steps.append(
                TaskStep(
                    step_number=2,
                    description="Perform analysis",
                    tool_hint="python_execute",
                    dependencies=[1]
                )
            )
            if "visualize" in goal_lower or "plot" in goal_lower:
                steps.append(
                    TaskStep(
                        step_number=3,
                        description="Create visualizations",
                        tool_hint="python_execute",
                        dependencies=[2]
                    )
                )
        
        # Default fallback step if no specific steps were created
        if not steps:
            steps.append(
                TaskStep(
                    step_number=1,
                    description="Execute the requested task"
                )
            )
        
        plan = TaskPlan(
            goal=goal,
            steps=steps,
            metadata=context or {}
        )
        
        self.current_plan = plan
        logger.info(f"Created plan with {len(steps)} steps for goal: {goal}")
        
        return plan
    
    def get_next_step(self) -> Optional[TaskStep]:
        """Get the next uncompleted step in the current plan."""
        if not self.current_plan:
            return None
        
        for step in self.current_plan.steps:
            # Check if dependencies are completed
            deps_completed = all(
                self.current_plan.steps[dep - 1].completed 
                for dep in step.dependencies
            )
            
            if not step.completed and deps_completed:
                return step
        
        return None
    
    def mark_step_completed(self, step_number: int) -> bool:
        """Mark a step as completed."""
        if not self.current_plan:
            return False
        
        for step in self.current_plan.steps:
            if step.step_number == step_number:
                step.completed = True
                logger.info(f"Marked step {step_number} as completed")
                return True
        
        return False
    
    def is_plan_complete(self) -> bool:
        """Check if all steps in the current plan are completed."""
        if not self.current_plan:
            return True
        
        return all(step.completed for step in self.current_plan.steps)
    
    def reset_plan(self) -> None:
        """Reset the current plan."""
        self.current_plan = None
        logger.info("Plan reset")
