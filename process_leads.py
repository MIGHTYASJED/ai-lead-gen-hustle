import asyncio
from tqdm import tqdm
from pipeline import get_discovered_leads, generate_email, update_lead_record
from intelligence import analyze_site

async def process_existing_leads():
    print("Fetching discovered leads from database...")
    leads = get_discovered_leads(50) # Process up to 50
    
    if not leads:
        print("No discovered leads found.")
        return

    print(f"Found {len(leads)} leads to process.")
    
    success_count = 0
    failure_count = 0
    
    with tqdm(total=len(leads), desc="Processing Leads") as pbar:
        for lead in leads:
            try:
                print(f"\nProcessing: {lead['company_name']}")
                # Analyze
                analysis = await analyze_site(lead['website_url'], lead['niche'] or "business")
                
                if analysis:
                    # Generate Email
                    lead_context = {
                        **lead,
                        **analysis
                    }
                    email_draft = generate_email(lead_context)
                    
                    if email_draft:
                        # Save
                        update_lead_record(lead['id'], analysis, email_draft)
                        success_count += 1
                        print(" [V] Success.")
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

    print("\n=== Processing Complete ===")
    print(f"Successes: {success_count}")
    print(f"Failures:  {failure_count}")

if __name__ == "__main__":
    asyncio.run(process_existing_leads())
