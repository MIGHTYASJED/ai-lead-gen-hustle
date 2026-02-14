import argparse
import asyncio
from tqdm import tqdm
from validator import validate_inputs, check_connectivity, validate_api_keys
from discovery import search_leads
from intelligence import analyze_site
from pipeline import get_discovered_leads, generate_email, update_lead_record

async def main():
    parser = argparse.ArgumentParser(description="LeadGen-Nexus V2 CLI")
    parser.add_argument("--niche", type=str, required=True, help="Business niche (e.g., 'dentist')")
    parser.add_argument("--location", type=str, required=True, help="Location (e.g., 'New York')")
    parser.add_argument("--limit", type=int, required=True, help="Number of leads to find")
    
    args = parser.parse_args()
    
    print("\n=== LeadGen-Nexus V2 ===")
    
    # 1. Validation
    if not validate_inputs(args.niche, args.location, args.limit):
        return
        
    if not validate_api_keys():
        return
        
    if not check_connectivity():
        return

    # 2. Discovery
    print(f"\n[Phase 1] Discovery: Finding {args.limit} leads for '{args.niche}' in '{args.location}'...")
    try:
        await search_leads(args.niche, args.location, args.limit)
    except Exception as e:
        print(f" [!] Discovery Failed: {e}")
        return

    # 3. Processing (Intelligence & Pipeline)
    print("\n[Phase 2] Intelligence & Drafting...")
    
    # Fetch leads that need processing
    # We fetch up to the limit, assuming we just found them or they were pending.
    # Note: If there were old 'discovered' leads, this might pick them up. This is acceptable behavior.
    leads = get_discovered_leads(args.limit)
    
    if not leads:
        print(" [!] No 'discovered' leads found in database to process.")
        return

    success_count = 0
    failure_count = 0
    
    with tqdm(total=len(leads), desc="Processing Leads") as pbar:
        for lead in leads:
            try:
                # Analyze
                analysis = await analyze_site(lead['website_url'], args.niche)
                
                if analysis:
                    # Generate Email
                    # Pass combined data to email generator
                    lead_context = {
                        **lead,
                        **analysis
                    }
                    email_draft = generate_email(lead_context)
                    
                    if email_draft:
                        # Save
                        update_lead_record(lead['id'], analysis, email_draft)
                        success_count += 1
                    else:
                        print(f" [!] Failed to draft email for {lead['company_name']}")
                        failure_count += 1
                else:
                    print(f" [!] Analysis failed for {lead['company_name']}")
                    failure_count += 1
                    
            except Exception as e:
                print(f" [!] Error processing lead {lead.get('id')}: {e}")
                failure_count += 1
                
            pbar.update(1)

    # Final Report
    print("\n=== Execution Complete ===")
    print(f"Processed: {len(leads)}")
    print(f"Successes: {success_count}")
    print(f"Failures:  {failure_count}")
    print("Check Supabase for details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user.")

