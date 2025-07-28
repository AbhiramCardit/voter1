#!/usr/bin/env python3
"""
Playwright script to open the ECI Voters Download page
https://voters.eci.gov.in/download-eroll
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def open_eci_voters_page():
    """Open the ECI voters download page using Playwright"""
    
    async with async_playwright() as p:
        try:
            # Launch browser (you can change to 'firefox' or 'webkit' if needed)
            browser = await p.chromium.launch(
                headless=False,  # Set to True if you don't want to see the browser
                slow_mo=1000     # Add delay between actions for better visibility
            )
            
            # Create a new page
            page = await browser.new_page()
            
            # Set viewport size
            await page.set_viewport_size({"width": 1280, "height": 720})
            
            print("Opening ECI Voters Download page...")
            
            # Navigate to the ECI voters download page
            await page.goto("https://voters.eci.gov.in/download-eroll", 
                           wait_until="networkidle")
            
            print(f"Successfully opened: {page.url}")
            print("Page title:", await page.title())
            
            # Wait for user to interact with the page
            print("\nPage is now open. You can interact with it.")
            print("Press Ctrl+C in the terminal to close the browser.")
            
            # Keep the browser open for user interaction
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing browser...")
            
        except Exception as e:
            print(f"Error occurred: {e}")
            sys.exit(1)
        finally:
            # Close browser
            if 'browser' in locals():
                await browser.close()
                print("Browser closed.")

async def main():
    """Main function to run the script"""
    print("ECI Voters Download Page Opener")
    print("=" * 40)
    
    await open_eci_voters_page()

if __name__ == "__main__":
    # Run the async function
    asyncio.run(main()) 