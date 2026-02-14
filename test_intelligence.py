import asyncio
from intelligence import analyze_site

async def test():
    # Test with a known URL from our list
    url = "https://www.pearldentalclinics.com/"
    print(f"Testing analysis for: {url}")
    
    result = await analyze_site(url, "dentist")
    print("\nResult:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test())
