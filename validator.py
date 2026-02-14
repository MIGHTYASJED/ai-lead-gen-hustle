import os
import requests
import socket
from dotenv import load_dotenv

load_dotenv()

def validate_inputs(niche: str, location: str, limit: int) -> bool:
    """Validates CLI arguments."""
    if not niche or not isinstance(niche, str):
        print("Error: Niche must be a non-empty string.")
        return False
    if not location or not isinstance(location, str):
        print("Error: Location must be a non-empty string.")
        return False
    if not isinstance(limit, int) or limit <= 0:
        print("Error: Limit must be a positive integer.")
        return False
    return True

def check_connectivity(host="8.8.8.8", port=53, timeout=3):
    """Checks for internet connectivity."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        print("\n[!] No Internet Connection Detected.")
        print("Network Troubleshooting Guide:")
        print("1. Check your Wi-Fi or Ethernet cable.")
        print("2. Ensure you have an active internet plan.")
        print("3. Try pinging google.com manually.")
        return False

def validate_api_keys():
    """Verifies that required API keys are present in environment variables."""
    # Critical keys
    infra_keys = ["SUPABASE_KEY", "SUPABASE_URL"]
    missing_infra = [key for key in infra_keys if not os.getenv(key)]
    
    if missing_infra:
        print("\n[!] Missing Infrastructure Keys:")
        for key in missing_infra:
            print(f" - {key}")
        return False

    # LLM keys (need at least one)
    gemini = os.getenv("GEMINI_API_KEY")
    groq = os.getenv("GROQ_API_KEY")
    
    if not gemini and not groq:
        print("\n[!] Missing LLM Keys: You need at least GEMINI_API_KEY or GROQ_API_KEY.")
        return False
        
    if not gemini:
        print(" [!] Warning: GEMINI_API_KEY is missing. Using Groq only.")
    elif not groq:
        print(" [!] Warning: GROQ_API_KEY is missing. Using Gemini only.")
        
    return True

