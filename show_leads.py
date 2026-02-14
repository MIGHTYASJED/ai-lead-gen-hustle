from supabase_client import create_client, SupabaseClient as Client
import os
from dotenv import load_dotenv

load_dotenv()

def show_leads():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    try:
        # Fetch all leads
        response = supabase.table("leads").select("*").execute()
        leads = response.data
        
        print(f"\n--- Discovered Leads ({len(leads)}) ---")
        for lead in leads:
            print(f"[{lead.get('status', 'unknown')}] {lead.get('company_name')} - {lead.get('website_url')}")
            if lead.get('email_draft'):
                print(f"   Draft: {lead.get('email_draft')[:50]}...")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error fetching leads: {e}")

if __name__ == "__main__":
    show_leads()
