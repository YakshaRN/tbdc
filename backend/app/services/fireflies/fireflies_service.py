"""
Fireflies.ai integration service.

Fetches meeting transcripts from Fireflies GraphQL API,
filters by participant email, and returns combined meeting
notes and action items for use in deal analysis.
"""
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger

from app.core.config import settings


class FirefliesService:
    """
    Service to fetch meeting transcript summaries from Fireflies.ai.
    Matches transcripts to deals via the deal Owner's email address.
    """

    def __init__(self):
        self._api_url = settings.FIREFLIES_API_URL
        self._api_key = settings.FIREFLIES_API_KEY

    @property
    def is_enabled(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    # ------------------------------------------------------------------ #
    # GraphQL helpers
    # ------------------------------------------------------------------ #

    def _query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute a synchronous GraphQL POST and return the JSON body."""
        try:
            resp = httpx.post(
                self._api_url,
                headers=self._headers(),
                json={"query": query},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Fireflies API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Fireflies API request failed: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Public methods
    # ------------------------------------------------------------------ #

    def get_transcripts_for_email(self, email: str) -> List[str]:
        """
        Fetch all transcripts from Fireflies and return the IDs
        whose participants list contains the given email.
        """
        if not self.is_enabled:
            return []

        email_lower = email.lower().strip()
        query = '{ transcripts { id participants } }'
        result = self._query(query)

        if not result or "data" not in result:
            logger.warning("No data returned from Fireflies transcripts query")
            return []

        transcripts = result["data"].get("transcripts") or []
        matched_ids: List[str] = []

        for t in transcripts:
            participants = t.get("participants") or []
            if any(p.lower().strip() == email_lower for p in participants):
                matched_ids.append(t["id"])

        logger.info(
            f"Fireflies: {len(matched_ids)} transcripts matched "
            f"for {email} (out of {len(transcripts)} total)"
        )
        return matched_ids

    def get_transcript_summary(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the title, notes, and action_items for a single transcript.
        Returns dict with keys: id, title, notes, action_items.
        """
        if not self.is_enabled:
            return None

        query = (
            '{ transcript(id: "' + transcript_id + '") '
            '{ id title summary { notes action_items } } }'
        )
        result = self._query(query)

        if not result or "data" not in result:
            return None

        transcript = result["data"].get("transcript")
        if not transcript:
            return None

        summary = transcript.get("summary") or {}
        return {
            "id": transcript.get("id", transcript_id),
            "title": transcript.get("title", ""),
            "notes": summary.get("notes", ""),
            "action_items": summary.get("action_items", ""),
        }

    def get_meeting_notes_for_email(self, email: str) -> str:
        """
        High-level method: find all transcripts for the email,
        fetch each summary, and return a single formatted text block
        suitable for appending to an LLM prompt.
        """
        if not self.is_enabled:
            return ""

        transcript_ids = self.get_transcripts_for_email(email)
        if not transcript_ids:
            return ""

        sections: List[str] = []

        for tid in transcript_ids:
            summary = self.get_transcript_summary(tid)
            if not summary:
                continue

            title = summary.get("title") or "Untitled Meeting"
            notes = (summary.get("notes") or "").strip()
            action_items = (summary.get("action_items") or "").strip()

            if not notes and not action_items:
                continue

            parts = [f"### {title}"]
            if notes:
                parts.append(f"Notes:\n{notes}")
            if action_items:
                parts.append(f"Action Items:\n{action_items}")
            sections.append("\n".join(parts))

        if not sections:
            return ""

        combined = "\n\n---\n\n".join(sections)
        logger.info(
            f"Fireflies: compiled {len(sections)} meeting summaries "
            f"({len(combined)} chars) for {email}"
        )
        return combined


# Singleton instance
fireflies_service = FirefliesService()
