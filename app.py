# app.py — simple text chatbot that calls your FastAPI recommender
import requests

API_URL = "http://localhost:8000"

def recommend(user_id: int, k: int = 5):
    r = requests.get(f"{API_URL}/recommend/{user_id}", timeout=5)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    print(f"\nRecommendations for user {data.get('user', user_id)}: {items}\n")

def help_msg():
    print(
        "Commands:\n"
        "  /help                Show commands\n"
        "  /recommend <user>    Get top items for a user (e.g., /recommend 1)\n"
        "  exit                 Quit\n"
    )

def main():
    print("Recommendation Chat — type /help for commands (Ctrl+C to quit)")
    help_msg()
    while True:
        try:
            text = input("> ").strip()
            if not text:
                continue
            if text.lower() in {"exit", "quit"}:
                break
            if text.startswith("/help"):
                help_msg()
                continue
            if text.startswith("/recommend"):
                parts = text.split()
                user = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                recommend(user)
                continue
            print("I didn't understand. Try /help")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"(error) {e}")

if __name__ == "__main__":
    main()
