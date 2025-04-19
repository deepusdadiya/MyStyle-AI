import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random
import time

BASE_URL = "https://www.myntra.com/men-shoes"
NUM_PAGES = 1                    # Scrape 100+ pages
MAX_CONCURRENT_PAGES = 10          # Parallel detail pages
MAX_RETRIES = 2                    # Retry a failed page
DELAY_BETWEEN_REQUESTS = (0.5, 2)  # Range of sleep between tasks

all_products = []
semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)

async def scrape_product_detail(context, product_link):
    for attempt in range(1, MAX_RETRIES + 1):
        async with semaphore:
            page = await context.new_page()
            try:
                await page.goto(product_link, timeout=30000)
                await page.wait_for_selector("h1.pdp-title", timeout=10000)

                product_id = product_link.split("/")[-2]
                name = await page.locator("h1.pdp-title").text_content()
                brand = await page.locator("h1.pdp-title + h1").text_content()
                try:
                    price_text = await page.locator("span.pdp-price").text_content()
                    price = ''.join(filter(str.isdigit, price_text))
                except:
                    price = "N/A"

                try:
                    image_url = await page.locator("img[src*='assets.myntassets.com']").first.get_attribute("src")
                except:
                    image_url = "N/A"

                try:
                    description = await page.locator(".pdp-productDescriptorsContainer").text_content()
                except:
                    description = "N/A"

                try:
                    rating_raw = await page.locator(".index-overallRating").text_content()
                    rating = rating_raw.replace("\n", " | ")
                except:
                    rating = "N/A"

                try:
                    in_stock = await page.locator("div:has-text('ADD TO BAG')").is_visible()
                    stock_status = "In Stock" if in_stock else "Out of Stock"
                except:
                    stock_status = "Unknown"

                print(f"[✓] {name[:40]} | ₹{price} | {rating} | {stock_status}")

                await page.close()
                return {
                    "product_id": product_id,
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "image_url": image_url,
                    "description": description,
                    "rating": rating,
                    "stock_status": stock_status,
                    "category": "Men Shoes",
                    "product_link": product_link
                }

            except Exception as e:
                await page.close()
                print(f"[!] Retry {attempt}/{MAX_RETRIES} failed for {product_link}: {e}")
                await asyncio.sleep(random.uniform(2, 4))
                continue

    print(f"[x] Skipped: {product_link}")
    return None


async def scrape_listing_page(context, listing_page, page_num):
    url = f"{BASE_URL}?p={page_num}"
    print(f"\n--- Scraping listing page {page_num} ---")
    try:
        await listing_page.goto(url, timeout=30000)
        await listing_page.wait_for_selector(".product-base", timeout=10000)

        product_links = await listing_page.locator(".product-base a").evaluate_all(
            "(elements) => elements.map(el => el.href)"
        )
        product_links = list(set(product_links))

        tasks = [scrape_product_detail(context, link) for link in product_links]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r:
                all_products.append(r)

        await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
    except Exception as e:
        print(f"[!] Failed listing page {page_num}: {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        listing_page = await context.new_page()

        for page_num in range(1, NUM_PAGES + 1):
            await scrape_listing_page(context, listing_page, page_num)

        await browser.close()

    # Save results
    df = pd.DataFrame(all_products)
    df.to_csv("myntra_100_pages_async.csv", index=False)
    print("\n✅ All data saved to 'myntra_100_pages_async.csv'")


if __name__ == "__main__":
    asyncio.run(main())