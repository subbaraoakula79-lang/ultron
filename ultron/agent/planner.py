import re
from typing import Any, Dict, List, Optional


class TaskPlanner:
    """Understands user intents in English & Telugu, breaks complex instructions into steps."""

    def __init__(self):
        # Intent patterns in English & Telugu (Romanized & Script)
        self.intent_patterns = {
            "desktop_app": [
                r"open\s+(vscode|code|notepad|calc|calculator|chrome|browser)",
                r"(vscode|notepad|calculator|chrome)\s+(open|launch|start|చెయ్యి|ఓపెన్)"
            ],
            "system_status": [
                r"(system|pc|cpu|ram|memory|computer)\s+(status|health|usage|info|check)",
                r"(సిస్టమ్|ర్యామ్|సీపీయూ)\s+(స్టేటస్|చెక్)"
            ],
            "search_web": [
                r"search\s+(for\s+)?(.+)",
                r"look\s+up\s+(.+)",
                r"google\s+(.+)",
                r"(.+)\s+గురించి\s+(వెతుకు|సెర్చ్)"
            ],
            "phone_status": [
                r"(phone|mobile|android)\s+(status|battery|check)",
                r"(ఫోన్|మొబైల్)\s+(స్టేటస్|చెక్)"
            ],
            "clean_temp": [
                r"clean\s+(temp|temporary|cache)",
                r"(టెంప్|కాష్)\s+(క్లీన్|డిలీట్)"
            ],
            "artemis_status": [
                r"(artemis|android\s+automation)\s+(status|check)",
                r"ఆర్టెమిస్\s+(స్టేటస్)"
            ]
        }

    def detect_confirmation(self, text: str) -> Optional[str]:
        """Detects if user is responding with a confirmation token (e.g. 'confirm CONFIRM-delete_file-1234')."""
        match = re.search(r"confirm\s+(CONFIRM-[A-Za-z0-9_\-]+)", text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def plan_steps(self, prompt: str) -> List[Dict[str, Any]]:
        """Decomposes a complex prompt into planned tool invocations."""
        prompt_lower = prompt.lower().strip()
        steps = []

        # Check for confirmation token
        token = self.detect_confirmation(prompt)
        if token:
            steps.append({"type": "confirmation", "token": token})
            return steps

        # Match known intents for deterministic recovery
        for intent, patterns in self.intent_patterns.items():
            for pat in patterns:
                m = re.search(pat, prompt_lower)
                if m:
                    if intent == "desktop_app":
                        app_name = m.group(1)
                        if "code" in app_name or "vscode" in app_name:
                            app_name = "code"
                        elif "calc" in app_name:
                            app_name = "calc"
                        steps.append({"tool": "desktop_app", "args": {"app": app_name}})
                    elif intent == "system_status":
                        steps.append({"tool": "system_status", "args": {}})
                    elif intent == "search_web":
                        query = m.group(2) if len(m.groups()) >= 2 and m.group(2) else m.group(1)
                        steps.append({"tool": "search_web", "args": {"query": query.strip()}})
                    elif intent == "phone_status":
                        steps.append({"tool": "phone_status", "args": {}})
                    elif intent == "clean_temp":
                        steps.append({"tool": "clean_temp", "args": {"older_than_days": 1.0}})
                    elif intent == "artemis_status":
                        steps.append({"tool": "artemis_status", "args": {}})
                    return steps

        return steps
