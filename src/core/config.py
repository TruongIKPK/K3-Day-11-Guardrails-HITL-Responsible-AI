import os


def get_model_name() -> str:
    """Get the central model name configured in environment (.env)."""
    return os.environ.get("MODEL_NAME", os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")).strip()


def setup_api_key():
    """Load API key from environment or prompt based on selected MODEL_NAME."""
    try:
        import dotenv
        dotenv.load_dotenv()
    except ImportError:
        pass

    model_name = get_model_name()
    is_openai = model_name.startswith(("gpt-", "o1-", "o3-", "gpt", "openai"))

    if is_openai:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key or key.startswith("your-openai"):
            os.environ["OPENAI_API_KEY"] = input("Enter OpenAI API Key: ")
    else:
        key = os.environ.get("GOOGLE_API_KEY", "").strip()
        if not key or key.startswith("your-google"):
            os.environ["GOOGLE_API_KEY"] = input("Enter Google API Key: ")

    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
    print(f"API key loaded for model: {model_name}.")


# Allowed banking topics (used by topic_filter)
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Blocked topics (immediate reject)
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling", "bomb", "kill", "steal",
]

