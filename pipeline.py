import os
import google.generativeai as genai
from supabase_client import create_client, SupabaseClient as Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
from groq import Groq

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

def generate_email(lead_data: dict) -> Optional[str]:
    """
    Generates a personalized cold email (<125 words) using Gemini (primary) or Groq (fallback).
    """
    prompt = f"""
    Write a cold email to {lead_data.get('company_name')} (Niche: {lead_data.get('niche')}).
    
    Context:
    - We visited their website: {lead_data.get('website_url')}
    - We identified a problem: {lead_data.get('problem')}
    - We have an AI solution: {lead_data.get('ai_solution')}
    
    Constraints:
    1. Access the recipient as "Hi [Name]" (if unknown, use "Hi there").
    2. Start with a specific compliment about their site content (be genuine).
    3. Mention the problem briefly and pivot to the solution.
    4. Keep it under 125 words.
    5. Tone: Professional, helpful, not salesy.
    6. Sign off with "Best, [Your Name]".
    
    Output only the email body.
    """

    # 1. Try Gemini
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f" [!] Email Generation (Gemini) Failed: {e}")

    # 2. Try Groq (Fallback)
    try:
        if groq_client:
            print(" [!] Switching to Groq for email generation...")
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            return chat_completion.choices[0].message.content.strip()
        else:
             print(" [!] Groq client not available for fallback.")
    except Exception as e:
        print(f" [!] Email Generation (Groq) Failed: {e}")
        
    return None

def update_lead_record(lead_id: int, analysis_data: dict, email_draft: str):
    """Updates the existing lead record with analysis and email draft."""
    try:
        data = {
            "problem_identified": analysis_data.get("problem"),
            "ai_solution_idea": analysis_data.get("ai_solution"),
            "email_draft": email_draft,
            "status": "processed",
            # We preserve original engine_used regarding discovery, 
            # but maybe we should log intelligence engine too? 
            # The schema has one 'engine_used'. We can append or overwrite.
            # Let's overwrite or keep it simple.
        }
        
        supabase.table("leads").update(data).eq("id", lead_id).execute()
        print(f" [+] Lead {lead_id} updated with analysis and draft.")
    except Exception as e:
        print(f" [!] Database Update Error: {e}")

def get_discovered_leads(limit: int):
    """Fetches leads with status 'discovered' from Supabase."""
    try:
        response = supabase.table("leads").select("*").eq("status", "discovered").limit(limit).execute()
        return response.data
    except Exception as e:
        print(f" [!] Error fetching discovered leads: {e}")
        return []

if __name__ == "__main__":
    # Test
    pass

