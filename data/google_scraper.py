# data/google_scraper.py
import os
import sys
import time
import pandas as pd
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAX_REVIEWS_PER_RUN


def scrape_google_reviews(business_name: str, limit: int = MAX_REVIEWS_PER_RUN) -> pd.DataFrame:
    """
    Scrape reviews từ Google Maps theo tên quán.
    Trả về DataFrame với các cột: business_name, stars, text, date
    """
    print(f"🌐 Scraping Google Maps: '{business_name}'...")
    reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Tìm kiếm quán trên Google Maps
        search_url = f"https://www.google.com/maps/search/{business_name.replace(' ', '+')}"
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        # Click vào kết quả đầu tiên trong danh sách
        try:
            # Selector đúng cho item trong danh sách kết quả
            first_result = page.locator("div.Nv2PK").first
            first_result.click()
            time.sleep(4)  # chờ trang quán load đầy đủ
            print(f"   ✅ Đã vào trang quán")
            page.screenshot(path="debug_after_click.png")  # chụp để kiểm tra
        except Exception as e:
            print(f"   ❌ Không click được vào quán: {e}")
            page.screenshot(path="debug_screenshot.png")
            browser.close()
            return pd.DataFrame()

        # Click vào tab Reviews - thử nhiều selector
        clicked = False
        tab_selectors = [
            "//button[@role='tab'][contains(., 'Reviews')]",
            "//button[@role='tab'][contains(., 'Đánh giá')]",
            "//button[@role='tab'][contains(., 'review')]",
        ]

        for selector in tab_selectors:
            try:
                tab = page.locator(f"xpath={selector}").first
                if tab.count() > 0:
                    tab.click()
                    time.sleep(3)
                    clicked = True
                    print(f"   ✅ Đã click tab Reviews")
                    break
            except Exception:
                continue

        if not clicked:
            print("   ❌ Không tìm thấy tab Reviews — chụp ảnh màn hình để debug")
            page.screenshot(path="debug_screenshot.png")
            browser.close()
            return pd.DataFrame()

        # Chờ reviews load
        time.sleep(3)

        # Scroll để load thêm reviews
        print(f"   📜 Đang scroll để load reviews...")
        no_new_count = 0

        while len(reviews) < limit:
            review_elements = page.locator("div.jftiEf").all()
            current_count = len(review_elements)
            print(f"   → Tìm thấy {current_count} reviews trên trang")

            for el in review_elements[len(reviews):]:
                if len(reviews) >= limit:
                    break
                try:
                    more_btn = el.locator("button.w8nwRe")
                    if more_btn.count() > 0:
                        more_btn.click()
                        time.sleep(0.3)

                    text = el.locator("span.wiI7pd").inner_text(timeout=2000)
                    stars_el = el.locator("span.kvMYJc")
                    stars_aria = stars_el.get_attribute("aria-label") if stars_el.count() > 0 else ""
                    stars = int(stars_aria.split()[0]) if stars_aria else None
                    date = el.locator("span.rsqaWe").inner_text(timeout=2000)

                    if text:
                        reviews.append({
                            "business_name": business_name,
                            "stars": stars,
                            "text": text,
                            "date": date,
                        })
                except Exception:
                    continue

            # Scroll xuống
            try:
                review_container = page.locator("div.m6QErb.DxyBCb").first
                review_container.evaluate("el => el.scrollTop += 1500")
            except Exception:
                pass
            time.sleep(2)

            new_count = len(page.locator("div.jftiEf").all())
            if new_count == current_count:
                no_new_count += 1
                if no_new_count >= 3:
                    print("   ℹ️  Đã hết reviews để load")
                    break
            else:
                no_new_count = 0

        browser.close()

    if not reviews:
        print("   ❌ Không scrape được reviews nào")
        print("   💡 Kiểm tra file 'debug_after_click.png'")
        return pd.DataFrame()

    df = pd.DataFrame(reviews)
    print(f"✅ Scrape xong: {len(df)} reviews cho '{business_name}'")
    return df


if __name__ == "__main__":
    df = scrape_google_reviews("Highland Coffee", limit=20)
    if not df.empty:
        print(df[["business_name", "stars", "text"]].head())