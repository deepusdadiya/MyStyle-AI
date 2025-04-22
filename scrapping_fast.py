import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random
import time

CATEGORIES = [
    # {"name": "Men Shoes", "url": "https://www.myntra.com/men-shoes"},
    # {"name": "Men Shirts", "url": "https://www.myntra.com/men-shirts"},
    # {"name": "Men T-Shirts", "url": "https://www.myntra.com/men-tshirts"},
    # {"name": "Men Jeans", "url": "https://www.myntra.com/men-jeans"},
    # {"name": "Men Trousers", "url": "https://www.myntra.com/men-trousers"},
    # {"name": "Women Shoes", "url": "https://www.myntra.com/women-shoes"},
    # {"name": "Women Shirts", "url": "https://www.myntra.com/women-shirts"},
    # {"name": "Women T-Shirts", "url": "https://www.myntra.com/women-tshirts"},
    # {"name": "Women Jeans", "url": "https://www.myntra.com/women-jeans"},
    {"name": "Women Trousers", "url": "https://www.myntra.com/women-trousers"},
]
NUM_PAGES = 25
MAX_CONCURRENT_PAGES = 25         # Parallel detail pages
MAX_RETRIES = 2                    # Retry a failed page
DELAY_BETWEEN_REQUESTS = (0.5, 2)  # Range of sleep between tasks

all_products = []
semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)

async def scrape_product_detail(context, product_link, category_name):
    for attempt in range(1, MAX_RETRIES + 1):
        async with semaphore:
            page = await context.new_page()
            try:
                await page.goto(product_link, timeout=30000)
                await page.wait_for_selector("h1.pdp-title", timeout=10000)

                product_id = product_link.split("/")[-2]
                name = await page.locator("h1.pdp-title + h1").text_content()
                brand = await page.locator("h1.pdp-title").text_content()

                try:
                    price_text = await page.locator("span.pdp-price").text_content()
                    price = ''.join(filter(str.isdigit, price_text))
                except:
                    price = "N/A"

                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    await asyncio.sleep(1.5)
                    await page.wait_for_selector("img[src*='assets.myntassets.com']", timeout=10000)
                    image_elements = page.locator("img[src*='assets.myntassets.com']")
                    image_count = await image_elements.count()
                    for i in range(image_count):
                        src = await image_elements.nth(i).get_attribute("src")
                        if src and "http" in src:
                            image_url = src
                            break
                    else:
                        image_url = "N/A"
                except Exception as e:
                    print(f"[!] Image not found after scroll and wait: {e}")
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
                    if await page.locator("//div[contains(@class, 'pdp-add-to-bag') and contains(text(), 'ADD TO BAG')]").is_visible():
                        stock_status = "In Stock"
                    elif await page.locator("//div[contains(text(), 'SOLD OUT')]").is_visible():
                        stock_status = "Out of Stock"
                    else:
                        stock_status = "Out of Stock"
                except:
                    stock_status = "Out of Stock"

                print(f"[✓] {name[:40]} | ₹{price} | {rating} | {stock_status} | {category_name}")

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
                    "category": category_name,
                    "product_link": product_link
                }

            except Exception as e:
                await page.close()
                print(f"[!] Retry {attempt}/{MAX_RETRIES} failed for {product_link}: {e}")
                await asyncio.sleep(random.uniform(2, 4))
                continue

    print(f"[x] Skipped: {product_link}")
    return None


async def scrape_listing_page(context, listing_page, page_num, category):
    url = f"{category['url']}?p={page_num}"
    # url = f"{BASE_URL}?p={page_num}"
    print(f"\n--- Scraping {category['name']} page {page_num} ---")
    try:
        await listing_page.goto(url, timeout=30000)
        await listing_page.wait_for_selector(".product-base", timeout=10000)

        product_links = await listing_page.locator(".product-base a").evaluate_all(
            "(elements) => elements.map(el => el.href)"
        )
        product_links = list(set(product_links))
        tasks = [scrape_product_detail(context, link, category['name']) for link in product_links]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r:
                all_products.append(r)

        await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
    except Exception as e:
        print(f"[!] Failed listing page {page_num}: {e}")

async def scrape_all_pages_for_category(context, category):
    page = await context.new_page()
    print(f"Starting category: {category['name']}")
    category_products = []

    try:
        for page_num in range(1, NUM_PAGES + 1):
            await page.goto(f"{category['url']}?p={page_num}", timeout=30000)
            await page.wait_for_selector(".product-base", timeout=10000)

            product_links = await page.locator(".product-base a").evaluate_all(
                "(elements) => elements.map(el => el.href)"
            )
            product_links = list(set(product_links))

            tasks = [
                scrape_product_detail(context, link, category['name'])
                for link in product_links
            ]
            results = await asyncio.gather(*tasks)
            for r in results:
                if r:
                    category_products.append(r)

            await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))

    except Exception as e:
        print(f"Failed category {category['name']}: {e}")

    await page.close()

    df = pd.DataFrame(category_products)
    filename = f"{category['name'].replace(' ', '_').lower()}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(category_products)} products to {filename}")

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        category_tasks = [
            scrape_all_pages_for_category(context, category)
            for category in CATEGORIES
        ]
        await asyncio.gather(*category_tasks)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())