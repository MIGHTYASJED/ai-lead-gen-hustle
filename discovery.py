import asyncio
import os
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from supabase_client import create_client, SupabaseClient as Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def check_lead_exists(website_url: str) -> bool:
    """Checks if a lead with the given URL already exists in Supabase."""
    try:
        response = supabase.table("leads").select("website_url").eq("website_url", website_url).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"[!] database check error: {e}")
        return False

def save_discovered_lead(lead_data: dict):
    """Upserts a discovered lead into Supabase with status 'discovered'."""
    try:
        supabase.table("leads").upsert(lead_data, on_conflict="website_url").execute()
        print(f" [+] Valid Lead Found & Saved: {lead_data['company_name']}")
    except Exception as e:
        print(f" [!] Database Upsert Error: {e}")

async def process_listing(listing, processed_urls, niche, location):
    """Extracts data from a single listing and saves it if valid."""
    try:
        # Extract Name
        aria_label = await listing.get_attribute("aria-label")
        if not aria_label or aria_label in processed_urls:
             return False

        # Click to load details
        await listing.click()
        # Small wait for panel to load, can be improved with specific wait
        await asyncio.sleep(1) 

        # We need to find the website button in the newly opened panel or the list item
        # Just searching the whole page for the authority link is risky but often effective if we assume the clicked item is active.
        # A better approach for the "active" item in Google Maps is hard without specific stable classes.
        # We will try to find the website link specifically.
        
        # 'a[data-item-id="authority"]' is often the website button in the detail panel.
        website_element = listing.page.locator('a[data-item-id="authority"]')
        
        website = None
        if await website_element.count() > 0:
            website = await website_element.first.get_attribute("href")
        
        if not website:
            return False

        # Deduplicate Global
        if check_lead_exists(website):
            print(f" [!] Duplicate skipping: {website}")
            processed_urls.add(website)
            return False
            
        # Deduplicate Local
        if website in processed_urls:
             return False
        
        # Extract Rating and Review Count
        # This is tricky with obfuscated classes. We will skip for now or use generic aria-label search on the listing/panel if requested.
        # The prompt asked for them optionally. We'll leave them as default for robustness.
        rating = None 
        review_count = None

        processed_urls.add(website)
        
        lead_data = {
            "niche": niche,
            "location": location,
            "company_name": aria_label,
            "website_url": website,
            "rating": rating,
            "review_count": review_count,
            "status": "discovered",
            "engine_used": "google_maps_playwright"
        }
        save_discovered_lead(lead_data)
        return True

    except Exception:
        return False

async def scroll_feed(page):
    """Scrolls the Google Maps feed to load more results."""
    feed = page.locator('div[role="feed"]')
    if await feed.count() > 0:
        await feed.focus()
        await page.keyboard.press("PageDown")
        await asyncio.sleep(random.uniform(2, 5))
        return True
    else:
        print("No feed found, stopping.")
        return False

async def process_batch(page, processed_urls, niche, location, limit, current_count):
    """Processes a batch of listings from the current view."""
    listings = await page.locator('div[role="article"]').all()
    new_leads = 0
    
    for listing in listings:
        if current_count + new_leads >= limit:
            break
        
        if await process_listing(listing, processed_urls, niche, location):
            new_leads += 1
            
    return new_leads

async def search_leads(niche: str, location: str, limit: int):
    """
    Searches for leads on Google Maps using Playwright.
    Scrolls results, extracts data, deduplicates, and saves to Supabase.
    """
    search_query = f"{niche} in {location}"
    print(f"\n[*] Starting Discovery for: {search_query} (Limit: {limit} new leads)")

    unique_leads_count = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # Apply stealth to context
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        
        page = await context.new_page()
        
        try:
            await page.goto("https://www.google.com/maps", timeout=60000)
            
            # Consent handling (common in EU/others)
            try:
                # Look for "Accept all" or matches
                consent_button = page.locator('button[aria-label="Accept all"], button:has-text("Accept all")')
                if await consent_button.count() > 0:
                    await consent_button.first.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

            # Try to find search box with multiple strategies
            search_box = page.locator('input#searchboxinput')
            if await search_box.count() == 0:
                 search_box = page.get_by_role("searchbox")
            if await search_box.count() == 0:
                 # Fallback for different locales/versions
                 search_box = page.locator('input[name="q"]')
            
            # Wait for it to be ready
            await search_box.first.wait_for(state="visible", timeout=30000)
            
            await search_box.first.fill(search_query)
            await page.keyboard.press("Enter")
            
            # Wait for results to load
            await page.wait_for_selector('div[role="feed"]', timeout=30000)
            
            processed_urls = set()
            
            while unique_leads_count < limit:
                unique_leads_count += await process_batch(page, processed_urls, niche, location, limit, unique_leads_count)
                
                if unique_leads_count >= limit:
                    break
                
                # Scroll Logic
                if not await scroll_feed(page):
                    break
                    
                if await page.get_by_text("You've reached the end of the list").is_visible():
                     print("End of results reached.")
                     break

        except Exception as e:
            print(f"Discovery Error: {e}")
            try:
                await page.screenshot(path="error_screenshot.png")
                print(" [!] Screenshot saved to error_screenshot.png")
            except:
                pass
        finally:
            await browser.close()
    
    print(f"\n[*] Discovery Complete. Found {unique_leads_count} new leads.")

if __name__ == "__main__":
    # Test run
    # asyncio.run(search_leads("plumbers", "New York", 1))
    pass

