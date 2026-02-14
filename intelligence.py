import os
import requests
import google.generativeai as genai
from groq import Groq
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

from typing import Optional

from playwright.async_api import async_playwright

async def extract_text_from_url(url: str) -> Optional[str]:
    """Fetches and extracts text content from a URL using Playwright."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                # context = await browser.new_context(user_agent="Mozilla/5.0 ...")
                page = await browser.new_page()
                try:
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                except Exception:
                    # Retry or ignore timeout if some content loaded
                    pass
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()
                    
                text = soup.get_text()
                
                # Clean chunks
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text[:10000]
            finally:
                await browser.close()
    except Exception as e:
        print(f" [!] Error fetching {url}: {e}")
        return None

def call_gemini(prompt: str) -> Optional[str]:
    """Calls Gemini 1.5 Pro with fallback logic handled by caller."""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f" [!] Gemini Error: {e}")
        return None

def call_groq(prompt: str) -> Optional[str]:
    """Calls Groq (Llama-3.3-70b) as fallback."""
    try:
        if not groq_client:
            print(" [!] Groq Client not initialized.")
            return None
            
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f" [!] Groq Error: {e}")
        return None

async def analyze_site(url: str, niche: str) -> Optional[dict]:
    """
    Analyzes a website to identify core service, problems, and AI solutions.
    Uses Gemini first, falls back to Groq.
    """
    print(f" [*] Analyzing {url}...")
    
    # Removed unused start_time
    website_content = await extract_text_from_url(url)
    
    if not website_content:
        return None

    prompt = f"""
    Analyze the following website content for a {niche} business.
    Website URL: {url}
    Content:
    {website_content}
    
    Identify the following:
    1. Core Service: What is their main offering?
    2. Problem: Identify one major operational hole, missing feature, or inefficiency visible on the site (e.g., no online booking, generic text, slow load, no chatbot, outdated design).
    3. AI Improvement Idea: Propose a specific AI automation or tool to fix this problem.
    
    Output strictly in JSON format:
    {{
        "core_service": "...",
        "problem": "...",
        "ai_solution": "..."
    }}
    """
    
    result_text = None
    engine_used = "Gemini 1.5 Pro"
    
    # Try Gemini
    result_text = call_gemini(prompt)
    
    # Fallback to Groq
    if not result_text:
        print(" [!] Gemini failed. Switching to Groq...")
        engine_used = "Groq Llama-3.3-70b"
        result_text = call_groq(prompt)
        
    if not result_text:
        print(" [!] intelligence analysis failed on both engines.")
        return None

    # Parse JSON
    # LLMs might add markdown backticks
    try:
        import json
        clean_text = result_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        data['engine_used'] = engine_used
        return data
    except json.JSONDecodeError:
        print(f" [!] Error parsing JSON from LLM: {result_text}")
        return None

if __name__ == "__main__":
    # Test
    # print(analyze_site("https://example.com", "software"))
    pass

