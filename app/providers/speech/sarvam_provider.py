import logging
import os
import time

import httpx

from app.providers.speech.base import BaseSpeechProvider, merge_turns

log = logging.getLogger("mom.sarvam")


class SarvamProvider(BaseSpeechProvider):
    """Sarvam AI batch job API, strong on Indian languages and code-mixed speech.

    The direct endpoint caps audio at 30 seconds, so meetings always go through
    the batch pipeline: create job, upload, start, poll, download.
    """

    name = "sarvam"
    label = "Sarvam AI"
    BASE_URL = "https://api.sarvam.ai"
    POLL_INTERVAL = 10
    MAX_WAIT = 7200

    def transcribe(self, audio_path: str) -> str:
        filename = os.path.basename(audio_path)
        with httpx.Client(timeout=60, headers=self._auth()) as client:
            job_id, storage = self._create_job(client)
            self._upload(audio_path, self._upload_url(client, job_id, filename), storage)
            _check(client.post(f"{self.BASE_URL}/speech-to-text/job/v1/{job_id}/start", json={}), "start job")
            output = self._wait(client, job_id, filename)
            return _parse(_download(self._download_url(client, job_id, output)))

    def check(self) -> str:
        with httpx.Client(timeout=30, headers=self._auth()) as client:
            self._create_job(client)
        return "Sarvam AI accepted the request."

    def _auth(self) -> dict:
        return {"api-subscription-key": self._require_key("sarvam_api_key", "Sarvam AI")}

    def _create_job(self, client: httpx.Client) -> tuple[str, str]:
        model = self._setting("sarvam_model", "saaras:v3")
        parameters = {
            "model": model,
            "language_code": self.language or "unknown",
            "with_diarization": self.diarize,
        }
        if model.startswith("saaras"):
            parameters["mode"] = "transcribe"

        response = client.post(f"{self.BASE_URL}/speech-to-text/job/v1", json={"job_parameters": parameters})
        _check(response, "create job")
        data = response.json()
        return data["job_id"], data.get("storage_container_type", "")

    def _upload_url(self, client: httpx.Client, job_id: str, filename: str) -> str:
        response = client.post(
            f"{self.BASE_URL}/speech-to-text/job/v1/upload-files",
            json={"job_id": job_id, "files": [filename]},
        )
        _check(response, "request upload URL")
        return _presigned(response.json().get("upload_urls", {}), filename, "upload")

    def _download_url(self, client: httpx.Client, job_id: str, filename: str) -> str:
        response = client.post(
            f"{self.BASE_URL}/speech-to-text/job/v1/download-files",
            json={"job_id": job_id, "files": [filename]},
        )
        _check(response, "request download URL")
        return _presigned(response.json().get("download_urls", {}), filename, "download")

    @staticmethod
    def _upload(audio_path: str, url: str, storage: str) -> None:
        headers = {"x-ms-blob-type": "BlockBlob"} if "azure" in storage.lower() else {}
        with open(audio_path, "rb") as handle:
            response = httpx.put(url, content=handle.read(), headers=headers, timeout=1800)
        if response.status_code not in (200, 201, 204):
            raise RuntimeError(f"Uploading the recording to Sarvam failed with HTTP {response.status_code}.")

    def _wait(self, client: httpx.Client, job_id: str, filename: str) -> str:
        deadline = time.monotonic() + self.MAX_WAIT
        while time.monotonic() < deadline:
            response = client.get(f"{self.BASE_URL}/speech-to-text/job/v1/{job_id}/status")
            _check(response, "read job status")
            data = response.json()
            state = data.get("job_state", "")
            log.debug("Sarvam job %s is %s", job_id, state)

            if state == "Completed":
                return _output_filename(data, filename)
            if state == "Failed":
                raise RuntimeError(f"Sarvam job failed: {data.get('error_message') or 'no reason given'}")
            time.sleep(self.POLL_INTERVAL)
        raise RuntimeError(f"Sarvam job {job_id} did not finish within {self.MAX_WAIT // 60} minutes.")


def _output_filename(status: dict, input_filename: str) -> str:
    for detail in status.get("job_details", []):
        if not any(i.get("file_name") == input_filename for i in detail.get("inputs", [])):
            continue
        if detail.get("state") not in ("Success", ""):
            raise RuntimeError(
                f"Sarvam could not transcribe the recording: "
                f"{detail.get('error_message') or detail.get('state')}"
            )
        outputs = detail.get("outputs", [])
        if outputs:
            return outputs[0].get("file_name") or outputs[0].get("file_id", "")
    return os.path.splitext(input_filename)[0] + ".json"


def _presigned(urls: dict, filename: str, kind: str) -> str:
    info = urls.get(filename) or {}
    if not info.get("file_url"):
        raise RuntimeError(f"Sarvam did not return a {kind} URL for '{filename}'.")
    return info["file_url"]


def _download(url: str):
    response = httpx.get(url, timeout=300)
    if response.status_code != 200:
        raise RuntimeError(f"Downloading the Sarvam transcript failed with HTTP {response.status_code}.")
    try:
        return response.json()
    except ValueError:
        return {"transcript": response.text}


def _parse(data) -> str:
    if isinstance(data, list):
        return merge_turns(_segments(data))
    if not isinstance(data, dict):
        return ""

    diarized = data.get("diarized_transcript") or data.get("diarized_output")
    entries = diarized.get("entries", []) if isinstance(diarized, dict) else diarized
    if isinstance(entries, list) and entries:
        text = merge_turns(_segments(entries))
        if text:
            return text
    return (data.get("transcript") or "").strip()


def _segments(entries: list):
    for entry in entries:
        speaker = entry.get("speaker") or entry.get("speaker_id") or entry.get("speaker_label")
        yield speaker, entry.get("transcript") or entry.get("text") or ""


def _check(response: httpx.Response, action: str) -> None:
    if response.status_code in (200, 201, 202):
        return
    try:
        message = response.json().get("error", {}).get("message") or response.text
    except ValueError:
        message = response.text
    raise RuntimeError(f"Sarvam API error while trying to {action}: HTTP {response.status_code} — {message}")
