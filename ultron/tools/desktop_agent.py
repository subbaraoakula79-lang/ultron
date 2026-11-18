import os
import subprocess
import urllib.request
import urllib.parse
import json
import webbrowser
from typing import Dict, Any, Optional

class DesktopAgent:
    """Automates web searching, booking tickets, and desktop app interactions."""
    def __init__(self):
        pass

    def search_web(self, query: str, open_in_browser: bool = True) -> Dict[str, Any]:
        """Performs a web search, fetches quick answers, and opens results in the browser."""
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        # Try fetching instant summary via DuckDuckGo API (no key needed)
        summary = ""
        try:
            api_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(api_url, headers={"User-Agent": "UltronAgent/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                summary = data.get("AbstractText") or data.get("Heading") or ""
        except Exception:
            pass

        if open_in_browser:
            webbrowser.open(search_url)

        return {
            "success": True,
            "query": query,
            "summary": summary if summary else f"Web search executed for '{query}'. Direct results opened in browser.",
            "url": search_url
        }

    def book_tickets(self, category: str, details: Dict[str, Any], open_in_browser: bool = True) -> Dict[str, Any]:
        """Researches and opens ticket booking engines for flights, trains, movies, and events."""
        cat_lower = category.lower().strip()
        raw_query = details.get("query", "").strip()
        url = ""
        description = ""

        if "flight" in cat_lower or "air" in cat_lower:
            origin = details.get("origin", "")
            dest = details.get("destination", "")
            date = details.get("date", "")
            if raw_query and not (origin and dest):
                query_str = f"flights {raw_query}".strip()
            else:
                query_str = f"flights from {origin} to {dest} {date}".strip()
            url = f"https://www.google.com/travel/flights?q={urllib.parse.quote(query_str)}"
            description = f"Searching flights: {raw_query or (origin + ' -> ' + dest)}"

        elif "train" in cat_lower or "rail" in cat_lower:
            origin = details.get("origin", "")
            dest = details.get("destination", "")
            date = details.get("date", "")
            if raw_query and not (origin and dest):
                query_str = f"trains {raw_query} booking tickets".strip()
            else:
                query_str = f"trains from {origin} to {dest} {date} booking ticket".strip()
            url = f"https://www.google.com/search?q={urllib.parse.quote(query_str)}"
            description = f"Searching train routes: {raw_query or (origin + ' -> ' + dest)}"

        elif "movie" in cat_lower or "cinema" in cat_lower:
            movie = details.get("movie") or details.get("name") or "latest movies"
            location = details.get("city") or details.get("location") or ""
            query_str = f"book movie tickets {movie} {location}".strip()
            url = f"https://www.google.com/search?q={urllib.parse.quote(query_str)}"
            description = f"Searching movie tickets for: '{movie}' ({location})"

        elif "event" in cat_lower or "concert" in cat_lower or "show" in cat_lower:
            event_name = details.get("name") or details.get("event") or "upcoming events"
            url = f"https://www.ticketmaster.com/search?q={urllib.parse.quote(event_name)}"
            description = f"Searching event tickets for: '{event_name}'"

        elif "hotel" in cat_lower or "stay" in cat_lower:
            dest = details.get("destination") or details.get("city") or ""
            url = f"https://www.booking.com/searchresults.html?ss={urllib.parse.quote(dest)}"
            description = f"Searching hotel accommodations in: {dest}"

        else:
            q = details.get("query") or category
            url = f"https://www.google.com/search?q={urllib.parse.quote('book tickets ' + q)}"
            description = f"Searching booking options for: {q}"

        if open_in_browser and url:
            webbrowser.open(url)

        return {
            "success": True,
            "category": category,
            "description": description,
            "booking_url": url
        }

    def open_app(self, app_name: str, target_file: Optional[str] = None) -> Dict[str, Any]:
        """Launches desktop applications on Windows."""
        from pathlib import Path
        local_app = os.environ.get("LOCALAPPDATA", "")
        vscode_exe = Path(local_app) / "Programs" / "Microsoft VS Code" / "Code.exe"
        vscode_path = f'"{vscode_exe}"' if vscode_exe.exists() else "code"

        app_map = {
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "notepad": "notepad.exe",
            "browser": "start chrome",
            "chrome": "start chrome",
            "explorer": "explorer.exe",
            "files": "explorer.exe",
            "terminal": "start powershell",
            "code": vscode_path,
            "vscode": vscode_path,
            "visual studio code": vscode_path,
            "vs code": vscode_path,
            "spotify": "spotify.exe",
            "paint": "mspaint.exe"
        }

        clean_name = app_name.lower().strip()
        cmd = app_map.get(clean_name, clean_name)
        if target_file:
            cmd = f"{cmd} \"{target_file}\""

        try:
            subprocess.Popen(cmd, shell=True)
            return {"success": True, "message": f"Desktop application '{app_name}' launched successfully."}
        except Exception as e:
            return {"success": False, "error": f"Failed to launch '{app_name}': {str(e)}"}
