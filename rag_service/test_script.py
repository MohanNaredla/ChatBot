import json
import sys
import time
import pathlib
import requests #type:ignore


SERVICE_URL = "http://localhost:8000/chat" 
PAUSE_BETWEEN_CALLS = 0.1               


def ask_service(question: str, url: str = SERVICE_URL) -> str:
    """Send a question to the chat endpoint and return the answer text."""
    response = requests.post(url, json={"question": question})
    response.raise_for_status()
    payload = response.json()
    return payload.get("answer", "")

def main() -> None:
    q_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("questions.json")
    a_path = pathlib.Path("answers_cache.json")

    if not q_path.exists():
        sys.exit(f"ERROR: questions file not found: {q_path}")
    questions = json.loads(q_path.read_text(encoding="utf-8"))
    if not isinstance(questions, list):
        sys.exit("ERROR: questions.json must contain a JSON array of strings.")
    print(f"Loaded {len(questions)} questions from {q_path}")

    if a_path.exists():
        cache = json.loads(a_path.read_text(encoding="utf-8"))
        if not isinstance(cache, dict):
            cache = {}
    else:
        cache = {}

    for q in questions:
        if q in cache and cache[q]:
            continue
        try:
            print(f"Asking: {q}")
            cache[q] = ask_service(q)
        except Exception as exc:
            print(f"ERROR for '{q}': {exc}")
            cache[q] = f"ERROR: {exc}"
        time.sleep(PAUSE_BETWEEN_CALLS)

    a_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(cache)} answers to {a_path}")

if __name__ == "__main__":
    main()
