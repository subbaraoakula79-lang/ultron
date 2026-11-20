import json
from typing import Any, Dict, List, Optional
from ultron.ai.model_manager import ModelManager
from ultron.agent.tool_registry import ToolRegistry
from ultron.agent.tool_executor import ToolExecutor
from ultron.agent.permission_manager import PermissionManager
from ultron.agent.planner import TaskPlanner
from ultron.agent.conversation_manager import ConversationManager
from ultron.agent.response_handler import ResponseHandler
from ultron.persona import SYSTEM_PROMPT


class UltronAgent:
    """The central intelligent agent orchestrator for ULTRON.

    Executes the standard pipeline:
    User Input -> Intent/Planner -> Context -> Ollama Native Tool Calling ->
    Permission Verification -> Tool Execution -> Result Validation -> Response.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        tool_registry: ToolRegistry,
        permission_manager: PermissionManager,
        max_tool_iterations: int = 5
    ):
        self.model_manager = model_manager
        self.registry = tool_registry
        self.permissions = permission_manager
        self.executor = ToolExecutor(self.registry, self.permissions)
        self.planner = TaskPlanner()
        self.conversation = ConversationManager()
        self.response_handler = ResponseHandler()
        self.max_tool_iterations = max_tool_iterations

    def process(self, user_input: str, confirmation_token: Optional[str] = None) -> str:
        """Processes a user instruction end-to-end."""
        # 1. Check for manual confirmation token
        if not confirmation_token:
            detected_token = self.planner.detect_confirmation(user_input)
            if detected_token:
                confirmation_token = detected_token

        # If user is confirming a pending high-risk action
        if confirmation_token and confirmation_token in self.permissions.pending_confirmations:
            pending = self.permissions.pending_confirmations[confirmation_token]
            tool_name = pending["tool"]
            args = pending["args"]
            exec_res = self.executor.execute(tool_name, args, confirmation_token=confirmation_token)
            return self.response_handler.format_final_response(
                f"Confirmation verified for action '{tool_name}'.",
                [exec_res]
            )

        self.conversation.add_user_message(user_input)
        provider = self.model_manager.get_active_provider()
        execution_results: List[Dict[str, Any]] = []

        # 2. Native Ollama Tool Calling Loop (if Ollama is online)
        if provider.is_available():
            schemas = self.registry.get_ollama_schemas()
            iteration = 0

            while iteration < self.max_tool_iterations:
                iteration += 1
                messages = self.conversation.get_messages()

                chat_res = provider.chat(
                    messages=messages,
                    tools=schemas if schemas else None,
                    system_prompt=SYSTEM_PROMPT
                )

                if not chat_res.get("success"):
                    # Fallback to deterministic planner if Ollama fails mid-run
                    break

                msg = chat_res.get("message", {})
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls", [])

                # If no tool calls were requested, model provided direct conversational reply
                if not tool_calls:
                    self.conversation.add_assistant_message(content)
                    return self.response_handler.format_final_response(content, execution_results)

                # Process requested native tool calls
                self.conversation.add_assistant_message(content, tool_calls=tool_calls)

                for call in tool_calls:
                    fn = call.get("function", {})
                    name = fn.get("name")
                    raw_args = fn.get("arguments", {})

                    # Parse arguments if returned as JSON string
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except Exception:
                            args = {}
                    else:
                        args = raw_args

                    exec_res = self.executor.execute(name, args, confirmation_token=confirmation_token)
                    execution_results.append(exec_res)

                    # Append tool result to conversation history
                    obs_str = json.dumps(exec_res.get("observation", exec_res))
                    self.conversation.add_tool_message(obs_str, tool_name=name)

                    # If blocked by permission check, immediately stop and ask user for confirmation
                    if exec_res.get("blocked"):
                        return self.response_handler.format_final_response(
                            content,
                            execution_results
                        )

            # Max iterations reached or final summary
            final_summary = self.response_handler.format_final_response(
                "Tasks concluded.",
                execution_results
            )
            return final_summary

        # 3. Deterministic Planner Fallback (when local Ollama is offline or not yet installed)
        plan = self.planner.plan_steps(user_input)
        if plan:
            for step in plan:
                if step.get("type") == "confirmation":
                    continue
                tool = step.get("tool")
                args = step.get("args", {})
                exec_res = self.executor.execute(tool, args, confirmation_token=confirmation_token)
                execution_results.append(exec_res)

            fallback_text = (
                "Ultron Local Heuristic Core active. (Ollama daemon offline on port 11434). "
                "Executing matched deterministic plan."
            )
            return self.response_handler.format_final_response(fallback_text, execution_results)

        # Conversational fallback
        return (
            "Ultron Core Online. Local Ollama is currently offline on port 11434.\n"
            "To enable full neural inference, start Ollama (`ollama run qwen3.5:2b-q4_K_M`).\n"
            "Direct system directives (apps, hardware status, files) remain fully operational."
        )
