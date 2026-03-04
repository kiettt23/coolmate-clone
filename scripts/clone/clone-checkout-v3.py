"""
Coolmate.me checkout page cloner v3.
Adds product to cart via the cart page directly (not navigating away),
fills checkout form fields, and captures.
"""

import sys
import os
import io
import re
import time
import hashlib
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path("d:/VMS/screenshots/coolmate-clone")
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
FONTS_DIR = ASSETS_DIR / "fonts"
CSS_DIR = ASSETS_DIR / "css"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})

downloaded_map = {}


def ensure_dirs():
    for d in [IMAGES_DIR, FONTS_DIR, CSS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def safe_filename(url, fallback_ext=""):
    parsed = urlparse(url)
    basename = os.path.basename(unquote(parsed.path))
    if not basename or basename == "/":
        basename = "asset_" + hashlib.md5(url.encode()).hexdigest()[:12]
    basename = re.sub(r'[<>:"|?*\\]', '_', basename)
    basename = re.sub(r'\s+', '_', basename)
    if fallback_ext and '.' not in basename:
        basename += f".{fallback_ext}"
    if len(basename) > 150:
        name, ext = os.path.splitext(basename)
        basename = name[:130] + "_" + hashlib.md5(url.encode()).hexdigest()[:8] + ext
    return basename


def classify_url(url):
    lower = url.lower()
    path = urlparse(lower).path
    if any(path.endswith(e) for e in ('.woff2', '.woff', '.ttf', '.otf', '.eot')):
        return "fonts"
    if any(path.endswith(e) for e in ('.css',)):
        return "css"
    return "images"


def download_file(url, force_type=None):
    if not url or url.startswith("data:") or url.startswith("blob:") or url.startswith("javascript:"):
        return None
    url = url.split("#")[0]
    if url.startswith("//"):
        url = "https:" + url
    if url in downloaded_map:
        return downloaded_map[url]
    try:
        asset_type = force_type or classify_url(url)
        target_dir = {"fonts": FONTS_DIR, "css": CSS_DIR, "images": IMAGES_DIR}[asset_type]
        fname = safe_filename(url)
        fpath = target_dir / fname
        if fpath.exists():
            rel = f"assets/{asset_type}/{fpath.name}"
            downloaded_map[url] = rel
            return rel
        resp = SESSION.get(url, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            return None
        counter = 1
        while fpath.exists() and url not in downloaded_map:
            name, ext = os.path.splitext(fname)
            fpath = target_dir / f"{name}_{counter}{ext}"
            counter += 1
        fpath.write_bytes(resp.content)
        rel = f"assets/{asset_type}/{fpath.name}"
        downloaded_map[url] = rel
        return rel
    except Exception as e:
        print(f"    [DL-ERR] {url[:70]}: {e}")
        return None


def rewrite_css_urls(css_text, css_base_url):
    pattern = re.compile(r'url\(\s*["\']?([^"\')\s]+)["\']?\s*\)', re.IGNORECASE)
    def replacer(m):
        ref = m.group(1)
        if ref.startswith("data:"):
            return m.group(0)
        abs_url = urljoin(css_base_url, ref)
        atype = classify_url(abs_url)
        local = download_file(abs_url, force_type=atype)
        if local:
            return f'url("{local}")'
        return m.group(0)
    return pattern.sub(replacer, css_text)


def rewrite_srcset(srcset_val, base_url):
    parts = []
    for entry in srcset_val.split(","):
        entry = entry.strip()
        if not entry:
            continue
        tokens = entry.split()
        url = tokens[0]
        desc = " ".join(tokens[1:]) if len(tokens) > 1 else ""
        abs_url = urljoin(base_url, url)
        local = download_file(abs_url)
        if local:
            parts.append(f"{local} {desc}".strip())
        else:
            parts.append(entry)
    return ", ".join(parts)


def capture_all_styles(page, page_url):
    print("  Capturing stylesheets...")
    style_data = page.evaluate("""
        () => {
            const results = [];
            for (const sheet of document.styleSheets) {
                try {
                    const rules = Array.from(sheet.cssRules || []);
                    const cssText = rules.map(r => r.cssText).join('\\n');
                    results.push({ href: sheet.href || null, cssText: cssText });
                } catch (e) {
                    results.push({ href: sheet.href || null, cssText: null, crossOrigin: true });
                }
            }
            return results;
        }
    """)
    all_css_texts = []
    for sd in style_data:
        if sd.get("cssText"):
            base = sd["href"] if sd["href"] else page_url
            rewritten = rewrite_css_urls(sd["cssText"], base)
            all_css_texts.append(rewritten)
        elif sd.get("crossOrigin") and sd.get("href"):
            css_url = sd["href"]
            if css_url.startswith("//"):
                css_url = "https:" + css_url
            try:
                resp = SESSION.get(css_url, timeout=30)
                if resp.status_code == 200:
                    base = css_url.rsplit("/", 1)[0] + "/"
                    rewritten = rewrite_css_urls(resp.text, base)
                    all_css_texts.append(rewritten)
            except Exception:
                pass
    print(f"    Captured {len(all_css_texts)} stylesheets")
    return all_css_texts


def close_popups(page):
    try:
        page.evaluate("""
            () => {
                document.querySelectorAll(
                    '[class*="popup"], [class*="Popup"], [class*="modal"], ' +
                    '[class*="Modal"], [class*="overlay"], [class*="Overlay"], ' +
                    '[class*="cookie"], [class*="notification"]'
                ).forEach(el => { el.style.display = 'none'; });
            }
        """)
    except Exception:
        pass


def force_lazy_images(page):
    page.evaluate("""
        () => {
            document.querySelectorAll('img[data-src]').forEach(img => {
                if (!img.src || img.src.includes('data:') || img.src.includes('placeholder'))
                    img.src = img.getAttribute('data-src');
            });
            document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                img.loading = 'eager';
            });
        }
    """)


def process_html(html, page_url, all_css_texts):
    print("  Processing HTML...")
    soup = BeautifulSoup(html, "html.parser")

    for s in soup.find_all("script"):
        s.decompose()
    for link in soup.find_all("link", rel=lambda r: r and "stylesheet" in r):
        link.decompose()
    for style in soup.find_all("style"):
        style.decompose()
    for ns in soup.find_all("noscript"):
        ns.unwrap()

    img_count = 0
    for img in soup.find_all("img"):
        for attr in ["src", "data-src", "data-lazy-src"]:
            src = img.get(attr)
            if src and not src.startswith("data:"):
                abs_url = urljoin(page_url, src)
                local = download_file(abs_url)
                if local:
                    img[attr] = local
                    if attr == "src":
                        img_count += 1
        srcset = img.get("srcset")
        if srcset:
            img["srcset"] = rewrite_srcset(srcset, page_url)
    print(f"    Downloaded {img_count} images")

    for source in soup.find_all("source"):
        for attr in ["src", "srcset"]:
            val = source.get(attr)
            if val:
                if attr == "srcset":
                    source["srcset"] = rewrite_srcset(val, page_url)
                else:
                    abs_url = urljoin(page_url, val)
                    local = download_file(abs_url)
                    if local:
                        source[attr] = local

    for video in soup.find_all("video"):
        poster = video.get("poster")
        if poster:
            abs_url = urljoin(page_url, poster)
            local = download_file(abs_url)
            if local:
                video["poster"] = local

    for tag in soup.find_all(style=True):
        style_val = tag["style"]
        if "url(" in style_val:
            tag["style"] = rewrite_css_urls(style_val, page_url)

    for link in soup.find_all("link"):
        rel = link.get("rel", [])
        href = link.get("href")
        if href and any(r in rel for r in ["icon", "shortcut", "apple-touch-icon", "preload"]):
            abs_url = urljoin(page_url, href)
            atype = "fonts" if link.get("as") == "font" else classify_url(abs_url)
            local = download_file(abs_url, force_type=atype)
            if local:
                link["href"] = local

    # Fix slider transforms
    for tag in soup.find_all(style=True):
        style_val = tag["style"]
        if "translate" in style_val.lower() or "transform" in style_val.lower():
            new_style = re.sub(r'translate3d\([^)]*\)', 'translate3d(0px, 0px, 0px)', style_val)
            new_style = re.sub(r'translateX\([^)]*\)', 'translateX(0px)', new_style)
            if new_style != style_val:
                tag["style"] = new_style

    if not soup.head:
        head_tag = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head_tag)

    meta_exists = soup.find("meta", charset=True)
    if not meta_exists:
        meta = soup.new_tag("meta", charset="utf-8")
        soup.head.insert(0, meta)

    viewport_exists = soup.find("meta", attrs={"name": "viewport"})
    if not viewport_exists:
        vp = soup.new_tag("meta", attrs={
            "name": "viewport",
            "content": "width=device-width, initial-scale=1"
        })
        soup.head.append(vp)

    combined_css = "\n\n".join(all_css_texts)
    style_tag = soup.new_tag("style")
    style_tag.string = combined_css
    soup.head.append(style_tag)
    print(f"    Injected {len(combined_css):,} chars of CSS")

    return str(soup)


def main():
    print("=" * 60)
    print("COOLMATE.ME CHECKOUT PAGE CLONER v3")
    print("=" * 60)

    ensure_dirs()

    with sync_playwright() as p:
        print("\n[INIT] Launching browser...")
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="vi-VN",
        )
        pg = ctx.new_page()
        pg.route("**/*.{mp4,webm,ogg}", lambda r: r.abort())

        # Step 1: Navigate to product and add to cart
        print("\n[STEP 1] Navigate to product page...")
        product_url = "https://www.coolmate.me/product/ao-thun-chay-bo-viet-nam-tien-buoc"
        pg.goto(product_url, wait_until="domcontentloaded", timeout=120000)
        time.sleep(12)
        close_popups(pg)

        # Select size
        print("  Selecting size...")
        size_result = pg.evaluate("""
            () => {
                const allEls = document.querySelectorAll('button, div, span, label');
                for (const el of allEls) {
                    const text = (el.innerText || el.textContent || '').trim();
                    if (text === 'M' || text === 'L') {
                        el.click();
                        return text;
                    }
                }
                return null;
            }
        """)
        print(f"    Size selected: {size_result}")
        time.sleep(2)

        # Click add to cart
        print("  Clicking add to cart...")
        atc_result = pg.evaluate("""
            () => {
                const allBtns = document.querySelectorAll('button, a[role="button"]');
                for (const btn of allBtns) {
                    const text = (btn.innerText || btn.textContent || '').toLowerCase().trim();
                    if (text.includes('th\u00eam v\u00e0o gi\u1ecf') || text.includes('ch\u1ecdn mua')) {
                        btn.click();
                        return text;
                    }
                }
                return null;
            }
        """)
        print(f"    Add to cart result: {atc_result}")
        time.sleep(5)

        # Step 2: Navigate to cart
        print("\n[STEP 2] Navigating to /cart ...")
        pg.goto("https://www.coolmate.me/cart", wait_until="domcontentloaded", timeout=120000)
        time.sleep(12)
        close_popups(pg)

        # Check if cart has items
        cart_check = pg.evaluate("""
            () => {
                const body = document.body.innerText || '';
                const hasProduct = body.includes('191.000') || body.includes('thun') || body.includes('Xóa');
                const hasEmptyCart = body.includes('trống') || body.includes('chưa có');
                return { hasProduct, hasEmptyCart, url: window.location.href };
            }
        """)
        print(f"  Cart check: {cart_check}")

        # Take screenshot to see current state
        pg.screenshot(path=str(BASE_DIR / "_checkout_v3_cart_state.png"))

        if cart_check.get('hasEmptyCart') or not cart_check.get('hasProduct'):
            print("  Cart appears empty! Trying to add via API...")
            # Use Coolmate's API to add product directly
            pg.evaluate("""
                () => {
                    // Try adding via localStorage or API
                    const cartData = localStorage.getItem('cart') || localStorage.getItem('coolmate_cart');
                    console.log('Current cart data:', cartData);
                }
            """)

            # Try going back to product and adding again with a different approach
            print("  Re-navigating to product...")
            pg.goto(product_url, wait_until="networkidle", timeout=120000)
            time.sleep(10)
            close_popups(pg)

            # Select size with Playwright click
            print("  Re-selecting size with Playwright click...")
            try:
                size_btns = pg.locator('button, div, span, label')
                count = size_btns.count()
                for i in range(count):
                    try:
                        text = size_btns.nth(i).inner_text().strip()
                        if text == 'M':
                            size_btns.nth(i).click()
                            print(f"    Clicked size M via Playwright")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"    Size click error: {e}")

            time.sleep(2)

            # Click add to cart with Playwright
            print("  Re-clicking add to cart with Playwright...")
            try:
                # Try various button text patterns
                for text_pattern in ['Thêm vào giỏ', 'THÊM VÀO GIỎ', 'Chọn mua', 'MUA NGAY']:
                    try:
                        btn = pg.get_by_text(text_pattern, exact=False)
                        if btn.count() > 0 and btn.first.is_visible():
                            btn.first.click()
                            print(f"    Clicked: {text_pattern}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"    ATC click error: {e}")

            time.sleep(5)

            # Navigate to cart again
            print("  Re-navigating to cart...")
            pg.goto("https://www.coolmate.me/cart", wait_until="domcontentloaded", timeout=120000)
            time.sleep(10)
            close_popups(pg)

            pg.screenshot(path=str(BASE_DIR / "_checkout_v3_cart_retry.png"))

        # Step 3: Fill checkout form
        print("\n[STEP 3] Filling checkout form fields...")
        try:
            # Use Playwright fill with various selectors
            inputs = pg.locator('input[type="text"], input[type="tel"], input[type="email"], input:not([type])')
            count = inputs.count()
            print(f"    Found {count} input fields")

            for i in range(count):
                try:
                    inp = inputs.nth(i)
                    placeholder = inp.get_attribute('placeholder') or ''
                    name_attr = inp.get_attribute('name') or ''
                    input_type = inp.get_attribute('type') or 'text'
                    print(f"    Input {i}: placeholder='{placeholder[:40]}', name='{name_attr}', type='{input_type}'")

                    lower_ph = placeholder.lower()
                    lower_name = name_attr.lower()

                    if any(kw in lower_ph for kw in ['họ tên', 'ho ten', 'name', 'tên']) or 'name' in lower_name:
                        inp.fill("Nguyen Van A")
                        print(f"      -> Filled name")
                    elif any(kw in lower_ph for kw in ['điện thoại', 'phone', 'số điện']) or 'phone' in lower_name:
                        inp.fill("0901234567")
                        print(f"      -> Filled phone")
                    elif any(kw in lower_ph for kw in ['email']) or input_type == 'email' or 'email' in lower_name:
                        inp.fill("nguyenvana@email.com")
                        print(f"      -> Filled email")
                    elif any(kw in lower_ph for kw in ['địa chỉ', 'dia chi', 'address']) or 'address' in lower_name:
                        inp.fill("123 Nguyen Hue, Quan 1")
                        print(f"      -> Filled address")
                except Exception as e:
                    pass

            time.sleep(2)
        except Exception as e:
            print(f"    Form fill error: {e}")

        # Step 4: Capture the page
        print("\n[STEP 4] Capturing checkout page...")
        current_url = pg.url
        print(f"  URL: {current_url}")

        force_lazy_images(pg)
        time.sleep(2)

        all_css = capture_all_styles(pg, current_url)

        html = pg.content()
        print(f"    Raw HTML: {len(html):,} bytes")

        result_html = process_html(html, current_url, all_css)

        out_path = BASE_DIR / "checkout.html"
        out_path.write_text(result_html, encoding="utf-8")
        print(f"\n  SAVED: {out_path} ({len(result_html):,} bytes)")

        pg.screenshot(path=str(BASE_DIR / "_checkout_v3_final.png"))
        print("  Screenshot: _checkout_v3_final.png")

        browser.close()

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
