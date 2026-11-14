import os
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from config.settings import GROQ_API_KEY, GOOGLE_API_KEY, MODEL_OPTIONS
from utils.logger import logger

class MultimodalService:
    """
    Direct REST-native adapter for Groq Cloud and Google Gemini.
    Provides robust Chat Completion, Vision Understanding, and Audio Transcription
    without fragile third-party wrapper dependencies.
    """

    @staticmethod
    def get_supported_models() -> Dict[str, Any]:
        return MODEL_OPTIONS

    @staticmethod
    def check_provider_health(provider: str, test_connectivity: bool = False) -> Dict[str, Any]:
        provider = provider.lower()
        if provider == "groq":
            configured = bool(GROQ_API_KEY)
            status = "unconfigured"
            error = None
            if configured:
                if test_connectivity:
                    try:
                        # Genuine minimal chat completion request to verify configured model availability
                        probe_model = MODEL_OPTIONS["groq"]["chat_models"][0]
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        probe_payload = json.dumps({
                            "model": probe_model,
                            "messages": [{"role": "user", "content": "ping"}],
                            "max_tokens": 1
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            url,
                            data=probe_payload,
                            headers={
                                "Authorization": f"Bearer {GROQ_API_KEY}",
                                "Content-Type": "application/json",
                                "User-Agent": "OmniMind-AI-Backend/2.0"
                            }
                        )
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                status = "online"
                            else:
                                status = "degraded"
                    except urllib.error.HTTPError as e:
                        # If the primary model encounters account permissions, try the fallback model
                        try:
                            fallback_model = MODEL_OPTIONS["groq"]["chat_models"][1]
                            probe_payload = json.dumps({
                                "model": fallback_model,
                                "messages": [{"role": "user", "content": "ping"}],
                                "max_tokens": 1
                            }).encode("utf-8")
                            req = urllib.request.Request(
                                url,
                                data=probe_payload,
                                headers={
                                    "Authorization": f"Bearer {GROQ_API_KEY}",
                                    "Content-Type": "application/json",
                                    "User-Agent": "OmniMind-AI-Backend/2.0"
                                }
                            )
                            with urllib.request.urlopen(req, timeout=5) as resp:
                                if resp.status == 200:
                                    status = "online"
                                else:
                                    status = "degraded"
                        except Exception as inner_e:
                            status = "unreachable"
                            error = str(inner_e)
                    except Exception as e:
                        status = "unreachable"
                        error = str(e)
                else:
                    status = "configured"

            res = {
                "provider": "Groq Cloud",
                "configured": configured,
                "status": status,
                "chat_models": MODEL_OPTIONS["groq"]["chat_models"],
                "vision_models": MODEL_OPTIONS["groq"]["vision_models"],
                "audio_models": MODEL_OPTIONS["groq"]["audio_models"]
            }
            if error:
                res["error"] = error
            return res

        elif provider == "gemini":
            configured = bool(GOOGLE_API_KEY)
            status = "unconfigured"
            error = None
            if configured:
                if test_connectivity:
                    try:
                        # Direct minimal generation check to ensure model ID is genuinely reachable and active
                        model = MODEL_OPTIONS["gemini"]["chat_models"][0]
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"
                        test_payload = json.dumps({
                            "contents": [{"parts": [{"text": "ping"}]}],
                            "generationConfig": {"maxOutputTokens": 1}
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            url,
                            data=test_payload,
                            headers={"Content-Type": "application/json", "User-Agent": "OmniMind-AI-Backend/2.0"}
                        )
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                status = "online"
                            else:
                                status = "degraded"
                    except urllib.error.HTTPError as e:
                        # If primary model is unavailable or capacity exhausted, try fallback stable model
                        try:
                            fallback_model = MODEL_OPTIONS["gemini"]["chat_models"][1]
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/{fallback_model}:generateContent?key={GOOGLE_API_KEY}"
                            req = urllib.request.Request(
                                url,
                                data=test_payload,
                                headers={"Content-Type": "application/json", "User-Agent": "OmniMind-AI-Backend/2.0"}
                            )
                            with urllib.request.urlopen(req, timeout=5) as resp:
                                if resp.status == 200:
                                    status = "online"
                                else:
                                    status = "degraded"
                        except Exception as inner_e:
                            status = "unreachable"
                            error = str(inner_e)
                    except Exception as e:
                        status = "unreachable"
                        error = str(e)
                else:
                    status = "configured"

            res = {
                "provider": "Google Gemini",
                "configured": configured,
                "status": status,
                "chat_models": MODEL_OPTIONS["gemini"]["chat_models"],
                "vision_models": MODEL_OPTIONS["gemini"]["vision_models"],
                "audio_models": MODEL_OPTIONS["gemini"]["audio_models"]
            }
            if error:
                res["error"] = error
            return res
        else:
            return {
                "provider": provider,
                "configured": False,
                "status": "unsupported",
                "error": f"Provider '{provider}' is not supported"
            }

    @staticmethod
    def _is_transient_or_capacity_error(http_code: int, err_text: str) -> bool:
        """
        Identifies transient rate limits, capacity exhaustion, model-not-found/unsupported,
        or gateway/server timeouts. Never treats 401/403 auth errors or 422 malformed schema as fallbackable.
        """
        if http_code in (404, 429, 500, 502, 503, 504):
            return True
        if http_code == 400:
            err_lower = err_text.lower()
            if any(term in err_lower for term in [
                "does not exist", "not have access", "unsupported model",
                "model_capacity_exhausted", "capacity_exhausted", "overloaded", "quota"
            ]):
                return True
        return False

    @staticmethod
    def chat_completion(
        messages: List[Dict[str, Any]],
        provider: str = "gemini",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        provider = provider.lower()

        if provider == "groq":
            if not GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not configured on the backend server.")

            available_options = list(MODEL_OPTIONS["groq"]["chat_models"])
            if model:
                models_to_try = [model] + [m for m in available_options if m != model]
            else:
                models_to_try = available_options
            last_err = None

            for attempt_idx, selected_model in enumerate(models_to_try):
                url = "https://api.groq.com/openai/v1/chat/completions"
                payload = {
                    "model": selected_model,
                    "messages": messages,
                    "temperature": max(0.0, min(temperature, 1.5)),
                    "max_tokens": max_tokens
                }

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "OmniMind-AI-Backend/2.0"
                    }
                )

                try:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        text = res_json["choices"][0]["message"]["content"]
                        usage = res_json.get("usage", {})
                        return {
                            "text": text,
                            "model": selected_model,
                            "provider": "groq",
                            "usage": usage
                        }
                except urllib.error.HTTPError as e:
                    err = e.read().decode("utf-8", errors="replace")
                    logger.warning(f"Groq API HTTP Error {e.code} on model {selected_model}: {err}")
                    last_err = RuntimeError(f"Groq API Error ({e.code}): {err}")
                    if attempt_idx < len(models_to_try) - 1 and MultimodalService._is_transient_or_capacity_error(e.code, err):
                        logger.info(f"Attempting Groq runtime fallback from {selected_model} to {models_to_try[attempt_idx + 1]}")
                        continue
                    raise last_err
                except Exception as e:
                    logger.warning(f"Groq API connection error on model {selected_model}: {e}")
                    last_err = e
                    if attempt_idx < len(models_to_try) - 1:
                        continue
                    raise last_err

        elif provider == "gemini":
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not configured on the backend server.")

            available_options = list(MODEL_OPTIONS["gemini"]["chat_models"])
            if model:
                models_to_try = [model] + [m for m in available_options if m != model]
            else:
                models_to_try = available_options
            last_err = None

            # Convert standard messages to Gemini contents structure
            contents = []
            system_instruction = None

            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "system":
                    system_instruction = {"parts": [{"text": content}]}
                elif role == "assistant":
                    contents.append({"role": "model", "parts": [{"text": content}]})
                else:
                    contents.append({"role": "user", "parts": [{"text": content}]})

            payload: Dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            if system_instruction:
                payload["systemInstruction"] = system_instruction

            for attempt_idx, selected_model in enumerate(models_to_try):
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={GOOGLE_API_KEY}"
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "OmniMind-AI-Backend/2.0"
                    }
                )

                try:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        candidates = res_json.get("candidates", [])
                        if not candidates:
                            raise ValueError("Gemini returned empty candidate choices.")
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return {
                            "text": text,
                            "model": selected_model,
                            "provider": "gemini",
                            "usage": res_json.get("usageMetadata", {})
                        }
                except urllib.error.HTTPError as e:
                    err = e.read().decode("utf-8", errors="replace")
                    logger.warning(f"Gemini API HTTP Error {e.code} on model {selected_model}: {err}")
                    last_err = RuntimeError(f"Google Gemini API Error ({e.code}): {err}")
                    if attempt_idx < len(models_to_try) - 1 and MultimodalService._is_transient_or_capacity_error(e.code, err):
                        logger.info(f"Attempting Gemini runtime fallback from {selected_model} to {models_to_try[attempt_idx + 1]}")
                        continue
                    raise last_err
                except Exception as e:
                    logger.warning(f"Gemini API connection error on model {selected_model}: {e}")
                    last_err = e
                    if attempt_idx < len(models_to_try) - 1:
                        continue
                    raise last_err

        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    @staticmethod
    def analyze_image(
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        prompt: str = "Analyze this image and describe its key elements, objects, and any visible text in detail.",
        provider: str = "gemini",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        provider = provider.lower()
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        if provider == "gemini":
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not configured on the backend server.")

            available_options = list(MODEL_OPTIONS["gemini"]["vision_models"])
            if model:
                models_to_try = [model] + [m for m in available_options if m != model]
            else:
                models_to_try = available_options
            last_err = None

            for attempt_idx, selected_model in enumerate(models_to_try):
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={GOOGLE_API_KEY}"

                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": prompt},
                                {
                                    "inlineData": {
                                        "mimeType": mime_type,
                                        "data": b64_image
                                    }
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.4,
                        "maxOutputTokens": 1024
                    }
                }

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "OmniMind-AI-Backend/2.0"}
                )

                try:
                    with urllib.request.urlopen(req, timeout=40) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                        return {
                            "description": text,
                            "provider": "gemini",
                            "model": selected_model,
                            "mime_type": mime_type
                        }
                except urllib.error.HTTPError as e:
                    err = e.read().decode("utf-8", errors="replace")
                    logger.warning(f"Gemini Vision HTTP Error {e.code} on model {selected_model}: {err}")
                    last_err = RuntimeError(f"Google Gemini Vision Error ({e.code}): {err}")
                    if attempt_idx < len(models_to_try) - 1 and MultimodalService._is_transient_or_capacity_error(e.code, err):
                        logger.info(f"Attempting Gemini vision fallback from {selected_model} to {models_to_try[attempt_idx + 1]}")
                        continue
                    raise last_err
                except Exception as e:
                    logger.warning(f"Gemini Vision connection error on model {selected_model}: {e}")
                    last_err = e
                    if attempt_idx < len(models_to_try) - 1:
                        continue
                    raise last_err

        elif provider == "groq":
            if not GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not configured on the backend server.")

            available_options = list(MODEL_OPTIONS["groq"]["vision_models"])
            if model:
                models_to_try = [model] + [m for m in available_options if m != model]
            else:
                models_to_try = available_options
            last_err = None
            data_url = f"data:{mime_type};base64,{b64_image}"

            for attempt_idx, selected_model in enumerate(models_to_try):
                url = "https://api.groq.com/openai/v1/chat/completions"
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ]

                payload = {
                    "model": selected_model,
                    "messages": messages,
                    "max_tokens": 1024
                }

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "OmniMind-AI-Backend/2.0"
                    }
                )

                try:
                    with urllib.request.urlopen(req, timeout=40) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        text = res_json["choices"][0]["message"]["content"]
                        return {
                            "description": text,
                            "provider": "groq",
                            "model": selected_model,
                            "mime_type": mime_type
                        }
                except urllib.error.HTTPError as e:
                    err = e.read().decode("utf-8", errors="replace")
                    logger.warning(f"Groq Vision HTTP Error {e.code} on model {selected_model}: {err}")
                    last_err = RuntimeError(f"Groq Vision Error ({e.code}): {err}")
                    if attempt_idx < len(models_to_try) - 1 and MultimodalService._is_transient_or_capacity_error(e.code, err):
                        logger.info(f"Attempting Groq vision fallback from {selected_model} to {models_to_try[attempt_idx + 1]}")
                        continue
                    raise last_err
                except Exception as e:
                    logger.warning(f"Groq Vision connection error on model {selected_model}: {e}")
                    last_err = e
                    if attempt_idx < len(models_to_try) - 1:
                        continue
                    raise last_err
        else:
            raise ValueError(f"Vision not supported for provider '{provider}'")

    @staticmethod
    def transcribe_audio(
        audio_bytes: bytes,
        filename: str = "audio.wav",
        provider: str = "groq",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribes speech using Groq's high-speed Whisper Large v3 endpoint.
        """
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required for audio transcription with Whisper.")

        selected_model = model or MODEL_OPTIONS["groq"]["audio_models"][0]
        url = "https://api.groq.com/openai/v1/audio/transcriptions"

        # Construct multipart/form-data
        boundary = "----OmniMindBoundary9876543210"
        body = bytearray()

        # model field
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
        body.extend(f"{selected_model}\r\n".encode("utf-8"))

        # response_format
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(b'Content-Disposition: form-data; name="response_format"\r\n\r\n')
        body.extend(b"verbose_json\r\n")

        # file field
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
        body.extend(audio_bytes)
        body.extend(b"\r\n")

        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(
            url,
            data=bytes(body),
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return {
                    "text": res_json.get("text", "").strip(),
                    "language": res_json.get("language", "auto"),
                    "duration": res_json.get("duration", 0.0),
                    "model": selected_model,
                    "provider": "groq",
                    "segments": res_json.get("segments", [])
                }
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            logger.error(f"Whisper Transcription Error ({e.code}): {err}")
            raise RuntimeError(f"Audio transcription error ({e.code}): {err}")
