import json
from typing import Any, Dict, List, Optional


class ResponseHandler:
    """Formats final responses adhering to Ultron's analytical, confident, and direct persona."""

    def format_final_response(
        self,
        assistant_text: str,
        execution_results: List[Dict[str, Any]],
        language: str = "en"
    ) -> str:
        """Assembles verified execution outputs with Ultron's persona tone."""
        output_parts = []

        if assistant_text and assistant_text.strip():
            output_parts.append(assistant_text.strip())

        if execution_results:
            for item in execution_results:
                tool = item.get("tool")
                success = item.get("success")

                if item.get("blocked"):
                    output_parts.append(f"\n[SECURITY PROTOCOL ENGAGED]\n{item.get('message')}")
                    continue

                if success:
                    obs = item.get("observation", {})
                    # Clean representation
                    formatted_obs = json.dumps(obs, indent=2)
                    output_parts.append(f"\n[Execution Verified ({tool})]:\n{formatted_obs}")
                else:
                    err = item.get("error", "Unknown anomaly during execution.")
                    output_parts.append(f"\n[Execution Alert ({tool})]: Action did not conclude successfully: {err}")

        # Add brief persona sign-off
        if execution_results and all(x.get("success") for x in execution_results if not x.get("blocked")):
            if language == "te":
                output_parts.append('\n"పని పూర్తయింది. సిస్టమ్ స్థిరంగా ఉంది."')
            else:
                output_parts.append('\n"Directive executed. All parameters verified."')

        return "\n".join(output_parts)
