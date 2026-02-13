"""
Fireflies.ai integration service.

Fetches meeting transcripts from Fireflies GraphQL API,
filters by participant email, and returns combined meeting
notes and action items for use in deal analysis.
"""
from typing import List, Dict, Any, Optional
import json
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
        logger.info(f"[Fireflies] Sending GraphQL request to {self._api_url}")
        logger.debug(f"[Fireflies] GraphQL query: {query}")
        try:
            resp = httpx.post(
                self._api_url,
                headers=self._headers(),
                json={"query": query},
                timeout=30.0,
            )
            logger.info(f"[Fireflies] Response status: {resp.status_code}")
            resp.raise_for_status()
            body = resp.json()
            logger.debug(f"[Fireflies] Response body: {json.dumps(body, default=str)[:2000]}")
            return body
        except httpx.HTTPStatusError as e:
            logger.error(f"[Fireflies] API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException as e:
            logger.error(f"[Fireflies] API request timed out after 30s: {e}")
            return None
        except Exception as e:
            logger.error(f"[Fireflies] API request failed: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Public methods
    # ------------------------------------------------------------------ #

    def get_transcripts_for_email(self, email: str) -> List[str]:
        """
        Fetch all transcripts from Fireflies and return the IDs
        whose participants list contains the given email.
        """
        logger.info(f"[Fireflies] get_transcripts_for_email called with email: {email}")
        if not self.is_enabled:
            logger.warning("[Fireflies] Service not enabled (no API key), returning empty list")
            return []

        email_lower = email.lower().strip()
        query = '{ transcripts { id participants } }'
        logger.info(f"[Fireflies] Fetching all transcripts to match against email: {email_lower}")
        result = self._query(query)

        if not result or "data" not in result:
            logger.warning("[Fireflies] No data returned from Fireflies transcripts query")
            return []

        transcripts = result["data"].get("transcripts") or []
        logger.info(f"[Fireflies] Total transcripts fetched: {len(transcripts)}")
        matched_ids: List[str] = []

        for t in transcripts:
            participants = t.get("participants") or []
            if any(p.lower().strip() == email_lower for p in participants):
                matched_ids.append(t["id"])
                logger.debug(f"[Fireflies] Transcript {t['id']} matched (participants: {participants})")

        logger.info(
            f"[Fireflies] {len(matched_ids)} transcripts matched "
            f"for {email} (out of {len(transcripts)} total)"
        )
        if matched_ids:
            logger.info(f"[Fireflies] Matched transcript IDs: {matched_ids}")
        return matched_ids

    def get_transcript_summary(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the title, notes, and action_items for a single transcript.
        Returns dict with keys: id, title, notes, action_items.
        """
        logger.info(f"[Fireflies] get_transcript_summary called for transcript_id: {transcript_id}")
        if not self.is_enabled:
            logger.warning("[Fireflies] Service not enabled, returning None")
            return None

        query = (
            '{ transcript(id: "' + transcript_id + '") '
            '{ id title summary { notes action_items } } }'
        )
        result = self._query(query)

        if not result or "data" not in result:
            logger.warning(f"[Fireflies] No data returned for transcript {transcript_id}")
            return None

        transcript = result["data"].get("transcript")
        if not transcript:
            logger.warning(f"[Fireflies] Transcript {transcript_id} not found in response")
            return None

        summary = transcript.get("summary") or {}
        title = transcript.get("title", "")
        notes = summary.get("notes", "")
        action_items = summary.get("action_items", "")
        logger.info(
            f"[Fireflies] Transcript {transcript_id} summary - "
            f"title: '{title}', notes: {len(notes)} chars, action_items: {len(action_items)} chars"
        )
        return {
            "id": transcript.get("id", transcript_id),
            "title": title,
            "notes": notes,
            "action_items": action_items,
        }

    def get_meeting_notes_for_email(self, email: str) -> str:
        """
        High-level method: find all transcripts for the email,
        fetch each summary, and return a single formatted text block
        suitable for appending to an LLM prompt.
        """
        logger.info(f"[Fireflies] get_meeting_notes_for_email called for email: {email}")
        if not self.is_enabled:
            logger.warning("[Fireflies] Service not enabled, returning empty string")
            return ""

        transcript_ids = self.get_transcripts_for_email(email)
        if not transcript_ids:
            logger.info(f"[Fireflies] No transcripts found for {email}, returning empty string")
            return ""

        logger.info(f"[Fireflies] Fetching summaries for {len(transcript_ids)} transcripts...")
        sections: List[str] = []

        for i, tid in enumerate(transcript_ids, 1):
            logger.info(f"[Fireflies] Fetching summary {i}/{len(transcript_ids)} (transcript_id: {tid})")
            summary = self.get_transcript_summary(tid)
            if not summary:
                logger.warning(f"[Fireflies] No summary returned for transcript {tid}, skipping")
                continue

            title = summary.get("title") or "Untitled Meeting"
            notes = (summary.get("notes") or "").strip()
            action_items = (summary.get("action_items") or "").strip()

            if not notes and not action_items:
                logger.debug(f"[Fireflies] Transcript {tid} ('{title}') has no notes or action items, skipping")
                continue

            parts = [f"### {title}"]
            if notes:
                parts.append(f"Notes:\n{notes}")
            if action_items:
                parts.append(f"Action Items:\n{action_items}")
            sections.append("\n".join(parts))
            logger.info(f"[Fireflies] Included transcript {tid} ('{title}')")

        if not sections:
            logger.info(f"[Fireflies] No usable meeting summaries found for {email}")
            return ""

        combined = "\n\n---\n\n".join(sections)
        logger.info(
            f"[Fireflies] Compiled {len(sections)} meeting summaries "
            f"({len(combined)} chars) for {email}"
        )
        logger.debug(f"[Fireflies] Combined meeting notes:\n{combined[:1000]}...")
        return combined


# Singleton instance
fireflies_service = FirefliesService()
