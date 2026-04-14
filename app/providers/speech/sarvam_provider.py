import os
import time
import logging
import httpx
from app.providers.speech.base import BaseSpeechProvider

logger = logging.getLogger(__name__)


class SarvamProvider(BaseSpeechProvider):
    """
    Speech-to-text via Sarvam AI Batch Job API (saarika:v2.5 / saaras:v3).

    The direct /speech-to-text endpoint only accepts up to 30 seconds of audio.
    For meeting recordings we use the batch job pipeline which has no duration limit.

    Pipeline (7 steps):
      1. Initiate job  → POST /speech-to-text/job/v1
      2. Get upload URL → POST /speech-to-text/job/v1/upload-files
      3. Upload file    → PUT <presigned_url>  (Azure needs x-ms-blob-type header)
      4. Start job      → POST /speech-to-text/job/v1/{job_id}/start
      5. Poll status    → GET  /speech-to-text/job/v1/{job_id}/status
      6. Get download URL → POST /speech-to-text/job/v1/download-files
      7. Download & parse → GET <presigned_url>
    """

    provider_name = "sarvam"
    BASE_URL = "https://api.sarvam.ai"

    POLL_INTERVAL_SEC = 10          # seconds between status checks
    MAX_POLL_SECONDS  = 3600        # 1-hour ceiling for very long meetings

    def transcribe_file(self, audio_path: str) -> str:
        if not self.validate_key():
            raise RuntimeError("Sarvam AI API key is not configured.")

        filename = os.path.basename(audio_path)
        auth = {"api-subscription-key": self.api_key}

        with httpx.Client(timeout=60) as client:
            # ── 1. Initiate job ────────────────────────────────────────────
            job_id, storage_type = self._initiate_job(client, auth)
            logger.debug("Sarvam job initiated: %s (storage: %s)", job_id, storage_type)

            # ── 2. Get presigned upload URL ────────────────────────────────
            upload_url = self._get_upload_url(client, auth, job_id, filename)

            # ── 3. Upload audio file ───────────────────────────────────────
            self._upload_file(audio_path, upload_url, storage_type)
            logger.debug("Sarvam: uploaded %s", filename)

            # ── 4. Start job ───────────────────────────────────────────────
            self._start_job(client, auth, job_id)
            logger.debug("Sarvam job started: %s", job_id)

            # ── 5. Poll until complete ─────────────────────────────────────
            output_filename = self._poll_until_complete(client, auth, job_id, filename)
            logger.debug("Sarvam job completed. Output file: %s", output_filename)

            # ── 6. Get presigned download URL ──────────────────────────────
            download_url = self._get_download_url(client, auth, job_id, output_filename)

            # ── 7. Download and parse transcript ───────────────────────────
            return self._download_and_parse(download_url)

    # ── Step implementations ────────────────────────────────────────────────

    def _initiate_job(self, client: httpx.Client, auth: dict) -> tuple[str, str]:
        resp = client.post(
            f"{self.BASE_URL}/speech-to-text/job/v1",
            headers=auth,
            json={
                "job_parameters": {
                    "model": "saarika:v2.5",
                    "language_code": "unknown",   # auto-detect language
                    "with_diarization": True,     # speaker identification
                }
            },
        )
        _raise(resp, "initiate job")
        data = resp.json()
        return data["job_id"], data.get("storage_container_type", "")

    def _get_upload_url(
        self, client: httpx.Client, auth: dict, job_id: str, filename: str
    ) -> str:
        resp = client.post(
            f"{self.BASE_URL}/speech-to-text/job/v1/upload-files",
            headers=auth,
            json={"job_id": job_id, "files": [filename]},
        )
        _raise(resp, "get upload URL")
        data = resp.json()
        file_info = data.get("upload_urls", {}).get(filename)
        if not file_info or not file_info.get("file_url"):
            raise RuntimeError(
                f"Sarvam did not return an upload URL for '{filename}'. "
                f"Response: {data}"
            )
        return file_info["file_url"]

    @staticmethod
    def _upload_file(audio_path: str, presigned_url: str, storage_type: str) -> None:
        """
        PUT audio bytes to the presigned URL.
        Azure Blob Storage (storage_type = 'Azure' or 'Azure_V1') requires the
        x-ms-blob-type header; other providers (GCS, local) do not need it.
        """
        upload_headers: dict = {}
        if "azure" in storage_type.lower():
            upload_headers["x-ms-blob-type"] = "BlockBlob"

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        resp = httpx.put(
            presigned_url,
            content=audio_bytes,
            headers=upload_headers,
            timeout=600,    # large files can take a while
        )
        if resp.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"Audio upload to presigned URL failed: HTTP {resp.status_code}"
            )

    def _start_job(self, client: httpx.Client, auth: dict, job_id: str) -> None:
        resp = client.post(
            f"{self.BASE_URL}/speech-to-text/job/v1/{job_id}/start",
            headers=auth,
            json={},
        )
        _raise(resp, "start job")

    def _poll_until_complete(
        self,
        client: httpx.Client,
        auth: dict,
        job_id: str,
        input_filename: str,
    ) -> str:
        """
        Poll the job status until it reaches a terminal state.
        Returns the output transcript filename (e.g. 'meeting.json').

        Docs recommend >= 5 ms between polls; we use 10 s to be courteous.
        """
        deadline = time.monotonic() + self.MAX_POLL_SECONDS

        while time.monotonic() < deadline:
            resp = client.get(
                f"{self.BASE_URL}/speech-to-text/job/v1/{job_id}/status",
                headers=auth,
            )
            _raise(resp, "get job status")
            data = resp.json()
            state = data.get("job_state", "")

            logger.debug("Sarvam job %s → %s", job_id, state)

            if state == "Completed":
                # Locate the output filename from per-file task details
                for detail in data.get("job_details", []):
                    inputs  = detail.get("inputs", [])
                    outputs = detail.get("outputs", [])
                    task_state = detail.get("state", "")
                    if any(inp.get("file_name") == input_filename for inp in inputs):
                        if task_state not in ("Success", ""):
                            err = detail.get("error_message") or task_state
                            raise RuntimeError(
                                f"Sarvam transcription failed for '{input_filename}': {err}"
                            )
                        if outputs:
                            # Prefer file_name; fall back to file_id
                            out = outputs[0]
                            return out.get("file_name") or out.get("file_id", "")
                # Fallback: Sarvam names outputs as <stem>.json
                return os.path.splitext(input_filename)[0] + ".json"

            if state == "Failed":
                err = data.get("error_message") or "Unknown error"
                raise RuntimeError(f"Sarvam job {job_id} failed: {err}")

            time.sleep(self.POLL_INTERVAL_SEC)

        raise RuntimeError(
            f"Sarvam job {job_id} did not complete within {self.MAX_POLL_SECONDS}s. "
            "Consider increasing SarvamProvider.MAX_POLL_SECONDS for very long recordings."
        )

    def _get_download_url(
        self, client: httpx.Client, auth: dict, job_id: str, output_filename: str
    ) -> str:
        resp = client.post(
            f"{self.BASE_URL}/speech-to-text/job/v1/download-files",
            headers=auth,
            json={"job_id": job_id, "files": [output_filename]},
        )
        _raise(resp, "get download URL")
        data = resp.json()
        file_info = data.get("download_urls", {}).get(output_filename)
        if not file_info or not file_info.get("file_url"):
            raise RuntimeError(
                f"Sarvam did not return a download URL for '{output_filename}'. "
                f"Response: {data}"
            )
        return file_info["file_url"]

    @staticmethod
    def _download_and_parse(presigned_url: str) -> str:
        resp = httpx.get(presigned_url, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download Sarvam transcript: HTTP {resp.status_code}"
            )
        try:
            data = resp.json()
        except Exception:
            # Some presigned URLs may return plain text
            text = resp.text.strip()
            if text:
                return text
            raise RuntimeError("Sarvam transcript download returned empty or non-JSON response")
        return SarvamProvider._parse_result(data)

    # ── Transcript parsing ──────────────────────────────────────────────────

    @staticmethod
    def _parse_result(data) -> str:
        """
        Parse the output JSON downloaded from Sarvam.

        Tries (in order):
          1. Diarized list  – list of {"speaker_id": "...", "transcript": "...", ...}
          2. Diarized dict  – {"diarized_transcript": {"entries": [...]}}
          3. Diarized list  – {"diarized_transcript": [...]}
          4. Plain field    – {"transcript": "..."}
        """
        if isinstance(data, list):
            # Top-level list of segments (unlikely but defensive)
            return SarvamProvider._build_diarized(data)

        if isinstance(data, dict):
            # Check for diarized transcript in the Sarvam response format:
            #   {"diarized_transcript": {"entries": [...]}}   ← actual Sarvam format
            #   {"diarized_transcript": [...]}                 ← potential variant
            diarized = data.get("diarized_transcript") or data.get("diarized_output")
            if isinstance(diarized, dict):
                entries = diarized.get("entries", [])
                if entries and isinstance(entries, list):
                    return SarvamProvider._build_diarized(entries)
            elif isinstance(diarized, list) and diarized:
                return SarvamProvider._build_diarized(diarized)

            transcript = data.get("transcript", "").strip()
            if transcript:
                return transcript

        raise RuntimeError(
            f"Unrecognised Sarvam transcript format: {type(data).__name__}"
        )

    @staticmethod
    def _build_diarized(segments: list) -> str:
        """
        Collapse diarized speaker segments into labelled turns.

        Input segment keys may vary; we try common field names.
        Consecutive same-speaker turns are merged.
        Falls back to plain text when only one speaker is detected.
        """
        collapsed: list[tuple[str, list[str]]] = []
        current_speaker: str | None = None
        current_parts: list[str] = []

        for seg in segments:
            speaker = (
                seg.get("speaker")
                or seg.get("speaker_id")
                or seg.get("speaker_label")
                or "Speaker"
            )
            text = (
                seg.get("transcript")
                or seg.get("text")
                or ""
            ).strip()

            if not text:
                continue

            if speaker != current_speaker:
                if current_parts:
                    collapsed.append((current_speaker, current_parts))
                current_speaker = speaker
                current_parts = [text]
            else:
                current_parts.append(text)

        if current_parts:
            collapsed.append((current_speaker, current_parts))

        if not collapsed:
            return ""

        unique_speakers = {s for s, _ in collapsed if s != "Speaker"}
        if len(unique_speakers) > 1:
            return "\n\n".join(
                f"[{spk}]: {' '.join(parts)}" for spk, parts in collapsed
            )
        return " ".join(" ".join(parts) for _, parts in collapsed)


# ── Helper ───────────────────────────────────────────────────────────────────

def _raise(resp: httpx.Response, operation: str) -> None:
    """Raise a RuntimeError with a clean message for non-2xx responses."""
    if resp.status_code in (200, 201, 202):
        return
    try:
        err = resp.json().get("error", {})
        msg = err.get("message") or resp.text
    except Exception:
        msg = resp.text
    raise RuntimeError(
        f"Sarvam API error during '{operation}': "
        f"HTTP {resp.status_code} — {msg}"
    )
