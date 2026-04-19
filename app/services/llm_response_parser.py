"""
Normalización y validación de salidas ruidosas del LLM (guardrails).
"""
from __future__ import annotations

import ast
import json
import re
from typing import Any, Dict, Optional


class LlmResponseParser:
    """
    Responsable únicamente de convertir texto del asistente en payload de /v1/notify.
    """

    @staticmethod
    def _strip_markdown_fences(text: str
    ) -> str:
        t = text.strip()
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```$", "", t)
        return t.strip()

    @staticmethod
    def _extract_brace_object(text: str
    ) -> Optional[str]:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None

    @staticmethod
    def _repair_json_loose(text: str
    ) -> str:
        t = re.sub(r",\s*}", "}", text)
        t = re.sub(r",\s*]", "]", t)
        return t

    @staticmethod
    def _regex_unquoted_keys(text: str
    ) -> Optional[Dict[str, str]]:
        to_m = re.search(r"\bto\s*:\s*\"((?:\\.|[^\"\\])*)\"", text, re.IGNORECASE)
        msg_m = re.search(
            r"\bmessage\s*:\s*\"((?:\\.|[^\"\\])*)\"",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        type_m = re.search(r"\btype\s*:\s*\"(email|sms)\"", text, re.IGNORECASE)
        if not (to_m and msg_m and type_m):
            return None
        try:
            return {
                "to": json.loads(json.dumps(to_m.group(1))),
                "message": json.loads(json.dumps(msg_m.group(1))),
                "type": type_m.group(1).lower(),
            }
        except (json.JSONDecodeError, TypeError, IndexError):
            return None

    @staticmethod
    def _regex_triple(text: str
    ) -> Optional[Dict[str, str]]:
        to_m = re.search(
            r'"(?:to|To|TO|recipient|destination)"\s*:\s*"((?:\\.|[^"\\])*)"',
            text,
        )
        msg_m = re.search(
            r'"(?:message|Message|body|text)"\s*:\s*"((?:\\.|[^"\\])*)"',
            text,
            re.DOTALL,
        )
        type_m = re.search(
            r'"(?:type|Type|channel|method)"\s*:\s*"(email|sms)"',
            text,
            re.IGNORECASE,
        )
        if not (to_m and msg_m and type_m):
            return None
        try:
            return {
                "to": json.loads(json.dumps(to_m.group(1))),
                "message": json.loads(json.dumps(msg_m.group(1))),
                "type": type_m.group(1).lower(),
            }
        except (json.JSONDecodeError, TypeError, IndexError):
            return None

    @staticmethod
    def _normalize_payload(raw: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        if not isinstance(raw, dict):
            return None
        lowered: Dict[str, Any] = {}
        for k, v in raw.items():
            if isinstance(k, str):
                lowered[k.lower()] = v

        to_val = (
            lowered.get("to")
            or lowered.get("recipient")
            or lowered.get("destination")
        )
        msg_val = lowered.get("message") or lowered.get("body") or lowered.get("text")
        typ_val = lowered.get("type") or lowered.get("channel") or lowered.get("method")

        if to_val is None or msg_val is None or typ_val is None:
            return None
        to_s = str(to_val).strip()
        msg_s = str(msg_val).strip()
        typ_s = str(typ_val).strip().lower()
        if typ_s not in ("email", "sms") or not to_s or not msg_s:
            return None
        return {"to": to_s, "message": msg_s, "type": typ_s}

    def parse(self, content: str
    ) -> Optional[Dict[str, str]]:
        if not content or not content.strip():
            return None
        text = self._strip_markdown_fences(content.strip())

        candidates: list[str] = []
        if text.lstrip().startswith("{"):
            candidates.append(text)
        brace = self._extract_brace_object(text)
        if brace and brace not in candidates:
            candidates.append(brace)

        for cand in candidates:
            repaired = self._repair_json_loose(cand)
            for fragment in {cand, repaired}:
                try:
                    data = json.loads(fragment)
                    norm = self._normalize_payload(data)
                    if norm:
                        return norm
                except json.JSONDecodeError:
                    pass
                try:
                    data = ast.literal_eval(fragment)
                    norm = self._normalize_payload(data)
                    if norm:
                        return norm
                except (ValueError, SyntaxError, TypeError):
                    pass

        rx = self._regex_triple(text)
        if rx:
            return rx
        uq = self._regex_unquoted_keys(text)
        if uq:
            return uq
        return None
