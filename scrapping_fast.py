import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random
import time

CATEGORIES = [
    # {"name": "Men Shoes", "url": "https://www.myntra.com/men-shoes"},
    # {"name": "Men Shirts", "url": "https://www.myntra.com/men-shirts"},
    # {"name": "Men T-Shirts 2", "url": "https://www.myntra.com/men-tshirts"},
    # {"name": "Men Jeans 1", "url": "https://www.myntra.com/men-jeans"},
    # {"name": "Men Trousers 1", "url": "https://www.myntra.com/men-trousers"},
    {"name": "Women Shoes 1", "url": "https://www.myntra.com/women-shoes"},
    # {"name": "Women Shirts", "url": "https://www.myntra.com/women-shirts"},
    # {"name": "Women T-Shirts", "url": "https://www.myntra.com/women-tshirts"},
    # {"name": "Women Jeans", "url": "https://www.myntra.com/women-jeans"},
    # {"name": "Women Trousers 26-50", "url": "https://www.myntra.com/women-trousers"},
]
NUM_PAGES = 35
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

                # Multiple image URLs
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1.5)
                    image_elements = page.locator("img[src*='assets.myntassets.com']")
                    image_count = await image_elements.count()
                    image_urls = []
                    for i in range(min(image_count, 8)):
                        src = await image_elements.nth(i).get_attribute("src")
                        if src and "http" in src and src not in image_urls:
                            image_urls.append(src)
                    image_url_combined = "|".join(image_urls)
                except Exception as e:
                    print(f"[!] Error fetching images: {e}")
                    image_url_combined = "N/A"

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

                try:
                    size_elements = await page.locator(".size-buttons-size-button").all_text_contents()
                    cleaned_sizes = []
                    for size in size_elements:
                        size_clean = size.split("Rs")[0].strip()
                        size_clean = size_clean.split("₹")[0].strip()  # extra fallback
                        if size_clean:
                            cleaned_sizes.append(size_clean)
                    available_sizes = " | ".join(cleaned_sizes) if cleaned_sizes else "N/A"
                except:
                    available_sizes = "N/A"

                fit_keywords = [
                    "slim fit", "regular fit", "skinny fit", "super skinny fit", "tapered fit", "relaxed fit", "loose fit", 
                    "straight fit", "comfort fit", "tailored fit", "athletic fit", "narrow fit", "muscle fit", "baggy fit", "bootcut fit"
                ]
                try:
                    fit_type = "N/A"
                    product_info = await page.locator(".pdp-productDescriptorsContainer").text_content()
                    product_info_lower = product_info.lower()
                    for keyword in fit_keywords:
                        if keyword in product_info_lower:
                            fit_type = keyword.title()
                            break
                except:
                    fit_type = "N/A"

                material_keywords = ["cotton", "polyester", "rayon", "viscose", "linen", "nylon", "modal", "jersey",
                "spandex", "lycra", "elastane", "silk", "wool", "acrylic", "bamboo", "satin", "chiffon", "georgette", "net", 
                "blend", "terrycot", "khadi", "denim", "cotton", "polyester", "viscose", "lycra", "elastane", "nylon",
                "spandex", "twill", "wool", "rayon", "terrycot", "linen", "stretch denim", "chino", "gabardine", "canvas", 
                "corduroy", "satin", "blend", "leather", "synthetic", "canvas", "mesh", "rubber", "eva", "foam", "nylon",
                "textile", "suede", "fabric", "knit", "flyknit", "phylon", "tpr", "pu", "polyurethane", "polyester", "plastic", 
                "air mesh", "netted", "neoprene"]
                try:
                    material_type = "N/A"
                    product_info = await page.locator(".pdp-productDescriptorsContainer").text_content()
                    product_info_lower = product_info.lower()
                    for keyword in material_keywords:
                        if keyword in product_info_lower:
                            material_type = keyword.title()
                            break
                except:
                    material_type = "N/A"

                print(f"{product_id} | {name[:40]} | ₹{price} | {rating} | {stock_status} | {category_name} | {available_sizes} | {fit_type} | {material_type}")

                await page.close()
                return {
                    "product_id": product_id,
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "image_urls": image_url_combined,
                    "description": description,
                    "rating": rating,
                    "stock_status": stock_status,
                    "available_sizes": available_sizes,
                    "fit_type": fit_type,
                    "material": material_type,
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
    print(f"--- Scraping {category['name']} page {page_num} ---")
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
                print(f"Scraped so far: {len(all_products)}")

        await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
    except Exception as e:
        print(f"[!] Failed listing page {page_num}: {e}")

async def scrape_all_pages_for_category(context, category):
    page = await context.new_page()
    print(f"Starting category: {category['name']}")
    category_products = []

    try:
        for page_num in range(26, NUM_PAGES + 1):
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