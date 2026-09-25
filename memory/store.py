import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from core.config import MEMORY_DIR


class EntityMemoryStore:
    """
    Persistent cross-question knowledge memory store for entities, verified facts,
    and source citations.
    """
    def __init__(self, persistence_file: Optional[Path] = None):
        self.file_path = persistence_file or (MEMORY_DIR / "entity_store.json")
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.access_history: List[Dict[str, Any]] = []
        self.load_from_disk()

    def _normalize(self, name: str) -> str:
        return name.lower().strip()

    def add_entity(self, name: str, aliases: Optional[List[str]] = None, summary: str = ""):
        key = self._normalize(name)
        if key not in self.entities:
            self.entities[key] = {
                "name": name,
                "aliases": [self._normalize(a) for a in (aliases or [])],
                "summary": summary,
                "facts": [],
                "verified_urls": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "hit_count": 0
            }
        self.save_to_disk()

    def add_fact(self, entity_name: str, fact: str, source_url: str = ""):
        key = self._normalize(entity_name)
        if key not in self.entities:
            self.add_entity(entity_name)

        entity = self.entities[key]
        # Check duplicate fact
        for existing in entity["facts"]:
            if existing["fact"].strip().lower() == fact.strip().lower():
                return

        entity["facts"].append({
            "fact": fact,
            "source_url": source_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        if source_url and source_url not in entity["verified_urls"]:
            entity["verified_urls"].append(source_url)
        entity["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save_to_disk()

    def get_entity(self, entity_name: str) -> Optional[Dict[str, Any]]:
        key = self._normalize(entity_name)
        if key in self.entities:
            self.entities[key]["hit_count"] += 1
            self.access_history.append({
                "entity": entity_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "hit"
            })
            return self.entities[key]

        for ent_key, data in self.entities.items():
            if key in data.get("aliases", []):
                data["hit_count"] += 1
                return data
        return None

    def search_entities_for_text(self, text: str) -> List[Dict[str, Any]]:
        """Find stored entities mentioned in the input question/text."""
        found = []
        text_lower = text.lower()
        for key, data in self.entities.items():
            name = data["name"].lower()
            if name in text_lower or any(alias in text_lower for alias in data.get("aliases", [])):
                data["hit_count"] += 1
                found.append(data)
        return found

    def format_memory_context(self, matched_entities: List[Dict[str, Any]]) -> str:
        """Render recalled entity knowledge as structured context for the analyst."""
        if not matched_entities:
            return ""

        lines = ["--- [RECALLED ENTITY MEMORY FROM PREVIOUS SESSIONS] ---"]
        for ent in matched_entities:
            lines.append(f"Entity: {ent['name']}")
            if ent.get("summary"):
                lines.append(f"  Summary: {ent['summary']}")
            if ent.get("facts"):
                lines.append("  Verified Facts:")
                for f in ent["facts"][:8]:  # Up to 8 core facts
                    src = f" (Source: {f['source_url']})" if f.get('source_url') else ""
                    lines.append(f"    - {f['fact']}{src}")
        lines.append("--- [END RECALLED MEMORY: USE TO BYPASS REDUNDANT SEARCHES] ---")
        return "\n".join(lines)

    def save_to_disk(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.entities, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def load_from_disk(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.entities = json.load(f)
            except Exception:
                self.entities = {}
