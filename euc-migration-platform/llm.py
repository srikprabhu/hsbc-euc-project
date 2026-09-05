import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "LLM-APIs.txt", override=False)

_clients = {}


def _configured_key(primary: str) -> str | None:
    value = os.getenv(primary)
    if not value:
        value = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not value:
        return None
    return value.strip().strip('"\'') or None


# ============================================================
# RESPONSE WRAPPER
# ============================================================

class GeminiResponse:
    def __init__(
        self,
        text,
        usage_metadata=None,
    ):
        self.content = text
        self.usage_metadata = usage_metadata


# ============================================================
# GEMINI LLM
# ============================================================

class GeminiLLM:

    def __init__(self, step=None):

        self.step = step

        # ----------------------------------------------------
        # Select API key
        # ----------------------------------------------------

        if step in (3, 4):

            api_key = _configured_key("GEMINI_API_KEY_1")

            model = os.getenv(
                "GEMINI_MODEL_1",
                "gemini-3.6-flash",
            )

            key_name = "GEMINI_API_KEY_1"

        elif step == 5:

            api_key = _configured_key("GEMINI_API_KEY_2")

            model = os.getenv(
                "GEMINI_MODEL_2",
                "gemini-3.6-flash",
            )

            key_name = "GEMINI_API_KEY_2"

        else:

            # Backward compatibility:
            # if some existing code calls get_llm()
            # without a step, use Key 1.

            api_key = _configured_key("GEMINI_API_KEY_1")

            model = os.getenv(
                "GEMINI_MODEL_1",
                "gemini-3.6-flash",
            )

            key_name = "GEMINI_API_KEY_1"

        # ----------------------------------------------------
        # Validate API key
        # ----------------------------------------------------

        if not api_key:

            raise RuntimeError(
                f"{key_name} is not configured in .env"
            )

        self.model = model
        self.key_name = key_name

        # ----------------------------------------------------
        # Reuse Gemini client
        # ----------------------------------------------------

        if key_name not in _clients:

            _clients[key_name] = genai.Client(
                api_key=api_key
            )

        self.client = _clients[key_name]

    # ========================================================
    # INVOKE
    # ========================================================

    def invoke(self, prompt):

        max_retries = int(
            os.getenv(
                "GEMINI_MAX_RETRIES",
                "3",
            )
        )

        retry_seconds = float(
            os.getenv(
                "GEMINI_RETRY_SECONDS",
                "3",
            )
        )

        last_error = None

        for attempt in range(
            1,
            max_retries + 1,
        ):

            try:

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                    )
                )

                # ------------------------------------------------
                # Gemini usage metadata
                # ------------------------------------------------

                usage_metadata = getattr(
                    response,
                    "usage_metadata",
                    None,
                )

                # ------------------------------------------------
                # Debug information
                # ------------------------------------------------

                if usage_metadata:

                    input_tokens = getattr(
                        usage_metadata,
                        "prompt_token_count",
                        0,
                    )

                    output_tokens = getattr(
                        usage_metadata,
                        "candidates_token_count",
                        0,
                    )

                    total_tokens = getattr(
                        usage_metadata,
                        "total_token_count",
                        0,
                    )

                    print(
                        f"[LLM] Step {self.step} | "
                        f"{self.key_name} | "
                        f"Input: {input_tokens} | "
                        f"Output: {output_tokens} | "
                        f"Total: {total_tokens}"
                    )

                return GeminiResponse(
                    response.text or "",
                    usage_metadata=usage_metadata,
                )

            except Exception as exc:

                last_error = exc

                print(
                    f"[LLM] Gemini request failed "
                    f"(attempt {attempt}/{max_retries}): "
                    f"{type(exc).__name__}: {exc}"
                )

                if attempt < max_retries:

                    time.sleep(
                        retry_seconds
                    )

        raise last_error


# ============================================================
# FACTORY
# ============================================================

def get_llm(step=None):

    return GeminiLLM(
        step=step
    )