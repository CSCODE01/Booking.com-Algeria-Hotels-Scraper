import os
import time
import random
import re
import json
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


class BookingDeepScraper:
    def __init__(self, location, checkin, checkout, max_hotels=100):
        self.location = location
        self.checkin = checkin
        self.checkout = checkout
        self.max_hotels = max_hotels
        self.base_url = "https://www.booking.com"
        self.raw_data = []
        self.clean_data = []

    def run(self):
        print(f"\n{'=' * 60}")
        print(f" TARGET CITY: {self.location.upper()}")
        print(f"{'=' * 60}")

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            print(f"[*] Step 1: Navigating to search results...")
            hotel_links = self._get_hotel_links(page)

            total_links = len(hotel_links)
            target_count = min(total_links, self.max_hotels)

            print(f"[*] Step 2: Found {total_links} hotel links. Processing top {target_count}...")

            for i, link in enumerate(hotel_links[:self.max_hotels]):
                progress = ((i + 1) / target_count) * 100
                print(f"    [{progress:.1f}%] Scrapping Hotel {i + 1}/{target_count}...", end='\r')

                hotel_details = self._scrape_hotel_page(page, link)
                if hotel_details:
                    self.raw_data.append(hotel_details)

                time.sleep(random.uniform(3.5, 6.0))

            print(f"\n[*] Step 3: Closing browser for {self.location}...")
            browser.close()

            self._clean_and_filter_data()
            print(f"[+] Successfully extracted {len(self.clean_data)} valid hotels from {self.location}.")
            return self.clean_data

    def _get_hotel_links(self, page):
        search_url = (f"{self.base_url}/searchresults.html?ss={self.location}"
                      f"&checkin={self.checkin}&checkout={self.checkout}"
                      f"&group_adults=2&no_rooms=1&nflt=ht_id%3A204%3B")

        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        self._close_popup(page)

        for i in range(5):
            page.mouse.wheel(0, 1000)
            time.sleep(0.5)

        links = page.query_selector_all('a[data-testid="title-link"]')
        return list(set([link.get_attribute("href") for link in links if link.get_attribute("href")]))

    def _scrape_hotel_page(self, page, url):
        full_url = url if url.startswith("http") else self.base_url + url
        try:
            page.goto(full_url, wait_until="domcontentloaded", timeout=45000)
            self._close_popup(page)

            data = {"url": full_url.split('?')[0]}
            html_content = page.content()

            data['name'] = "N/A"
            data['rating_value'] = "N/A"
            data['review_count'] = 0

            json_ld_elements = page.query_selector_all('script[type="application/ld+json"]')
            for el in json_ld_elements:
                try:
                    json_content = json.loads(el.inner_text())
                    if '@type' in json_content and json_content['@type'] in ['Hotel', 'LodgingBusiness']:
                        data['name'] = json_content.get('name', "N/A")
                        data['rating_value'] = json_content.get('aggregateRating', {}).get('ratingValue', "N/A")
                        data['review_count'] = json_content.get('aggregateRating', {}).get('reviewCount', 0)
                        break
                except:
                    pass

            lat_match = re.search(r'latitude[":\s=]+([0-9.-]+)', html_content, re.IGNORECASE)
            lon_match = re.search(r'longitude[":\s=]+([0-9.-]+)', html_content, re.IGNORECASE)

            data['latitude'] = lat_match.group(1) if lat_match else "N/A"
            data['longitude'] = lon_match.group(1) if lon_match else "N/A"

            price_el = page.query_selector(
                '.prco-valign-middle-helper, .bui-price-display__value, [data-testid="price-and-discounted-price"]')
            data['raw_price'] = price_el.inner_text().strip() if price_el else None

            try:
                
                fac_locator = page.locator('.f6b6d2a959')
                fac_texts = fac_locator.all_inner_texts()
                clean_facs = [f.strip() for f in fac_texts if f.strip()]
                data['facilities'] = " | ".join(list(set(clean_facs))) if clean_facs else "N/A"
            except:
                data['facilities'] = "N/A"

            return data
        except:
            return None

    def _clean_and_filter_data(self):
        for item in self.raw_data:
            if not item.get('name') or item.get('name') == "N/A":
                continue

            clean_price = "N/A"
            if item.get('raw_price'):
                price_numbers = re.findall(r'\d+', item['raw_price'].replace(',', '').replace(' ', ''))
                if price_numbers:
                    clean_price = float(price_numbers[0])

            clean_item = {
                "City": self.location,
                "Hotel_Name": item.get('name') or "N/A",
                "Price_DZD": clean_price,
                "Rating_Out_of_10": item.get('rating_value') or "N/A",
                "Reviews_Count": item.get('review_count') or 0,
                "Latitude": item.get('latitude') or "N/A",
                "Longitude": item.get('longitude') or "N/A",
                "Facilities": item.get('facilities') or "N/A",
                "URL": item.get('url') or "N/A"
            }
            self.clean_data.append(clean_item)

    def _close_popup(self, page):
        try:
            page.locator('button[aria-label="Dismiss sign-in info."]').click(timeout=2000)
        except:
            pass


if __name__ == "__main__":
    cities = ["Algiers", "Oran", "Annaba", "Constantine"]
    master_collection = []
    start_time = time.time()

    print("--- STARTING MASTER SCRAPER ---")

    for city in cities:
        scraper = BookingDeepScraper(
            location=city,
            checkin="2026-05-10",
            checkout="2026-05-15",
            max_hotels=100
        )
        result = scraper.run()
        if result:
            master_collection.extend(result)

        print(f"--- Cooldown: Waiting 10 seconds before next city ---")
        time.sleep(10)

    if master_collection:
        df = pd.DataFrame(master_collection)
        output_file = f"booking_algeria_hotels_dataset_{int(time.time())}.csv"
        final_path = os.path.abspath(output_file)
        df.to_csv(final_path, index=False, encoding='utf-8-sig')

        duration = (time.time() - start_time) / 60
        print(f"\n{'#' * 60}")
        print(f" MISSION COMPLETE")
        print(f" Total Time: {duration:.2f} minutes")
        print(f" Total Hotels Collected: {len(master_collection)}")
        print(f" Master File Saved At: {final_path}")
        print(f"{'#' * 60}")
    else:
        print("\n[!] Error: No data was collected.")
