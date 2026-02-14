import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def verify_browsers():
    print(" [*] Verifying Playwright Browsers...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            print(" [OK] Chromium launched successfully.")
            return True
    except Exception as e:
        # Use repr() or encode/decode to avoid charmap errors on Windows consoles
        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        try:
            print(f" [X] Playwright Error: {e}")
        except UnicodeEncodeError:
            print(f" [X] Playwright Error: {error_msg}")
            
        print("     Try running 'playwright install' manually in your terminal.")
        return False

def verify_env():
    print(" [*] Verifying Environment Variables...")
    keys = ["GEMINI_API_KEY", "GROQ_API_KEY", "SUPABASE_KEY", "SUPABASE_URL"]
    all_good = True
    for key in keys:
        val = os.getenv(key)
        if not val or val.startswith("your_"):
            print(f" [X] {key} is missing or default.")
            all_good = False
        else:
            print(f" [OK] {key} is set.")
    return all_good

async def main():
    print("=== Verification Tool ===")
    env_ok = verify_env()
    browser_ok = await verify_browsers()
    
    if env_ok and browser_ok:
        print("\n[SUCCESS] Setup seems complete. You can run the main application.")
    else:
        print("\n[WARNING] Setup has issues. Please fix the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
