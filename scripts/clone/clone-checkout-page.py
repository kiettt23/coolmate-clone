"""
Coolmate.me checkout page cloner.
Adds a product to cart, then navigates to checkout/order flow.
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

# Fix Windows console encoding for Vietnamese text
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


def scroll_page(page, max_scrolls=15, pause=0.3):
    print("  Scrolling...")
    prev = 0
    for i in range(max_scrolls):
        page.evaluate("window.scrollBy(0, 700)")
        time.sleep(pause)
        curr = page.evaluate("document.body.scrollHeight")
        if curr == prev and i > 5:
            break
        prev = curr
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)


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
    external_hrefs = set()
    for sd in style_data:
        if sd.get("cssText"):
            base = sd["href"] if sd["href"] else page_url
            rewritten = rewrite_css_urls(sd["cssText"], base)
            all_css_texts.append(rewritten)
            if sd["href"]:
                external_hrefs.add(sd["href"])
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
                    external_hrefs.add(sd["href"])
            except Exception:
                pass
    print(f"    Captured {len(all_css_texts)} stylesheets")
    return all_css_texts, external_hrefs


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
    for tag in soup.find_all("script", id="__NEXT_DATA__"):
        tag.decompose()
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
    print("COOLMATE.ME CHECKOUT PAGE CLONER")
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

        # Step 1: Add product to cart
        print("\n[STEP 1] Adding product to cart...")
        product_url = "https://www.coolmate.me/product/ao-thun-chay-bo-viet-nam-tien-buoc"
        pg.goto(product_url, wait_until="domcontentloaded", timeout=120000)
        time.sleep(10)
        close_popups(pg)

        # Select size M
        print("  Selecting size...")
        pg.evaluate("""
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
        time.sleep(2)

        # Click add to cart
        print("  Adding to cart...")
        pg.evaluate("""
            () => {
                const allBtns = document.querySelectorAll('button, a[role="button"]');
                for (const btn of allBtns) {
                    const text = (btn.innerText || btn.textContent || '').toLowerCase().trim();
                    if (text.includes('thêm vào giỏ') || text.includes('them vao gio') ||
                        text.includes('chọn mua') || text.includes('mua ngay')) {
                        btn.click();
                        return text;
                    }
                }
                return null;
            }
        """)
        time.sleep(5)
        close_popups(pg)

        # Step 2: Go to cart and click "Dat hang" (Place Order)
        print("\n[STEP 2] Going to cart page...")
        pg.goto("https://www.coolmate.me/cart", wait_until="domcontentloaded", timeout=120000)
        time.sleep(8)
        close_popups(pg)

        # Take screenshot to debug
        pg.screenshot(path=str(BASE_DIR / "_cart_debug.png"))
        print("  Saved debug screenshot: _cart_debug.png")

        # Click "Dat hang" button
        print("  Clicking 'Dat hang' (Place Order)...")
        clicked_text = pg.evaluate("""
            () => {
                const allBtns = document.querySelectorAll('button, a');
                for (const btn of allBtns) {
                    const text = (btn.innerText || btn.textContent || '').trim();
                    const lower = text.toLowerCase();
                    if (lower.includes('đặt hàng') || lower.includes('dat hang') ||
                        lower.includes('thanh toán') || lower.includes('checkout')) {
                        console.log('Clicking:', text, btn.tagName, btn.className);
                        btn.click();
                        return text;
                    }
                }
                return null;
            }
        """)
        print(f"  Clicked: {clicked_text}")

        # Wait for navigation
        time.sleep(10)

        current_url = pg.url
        print(f"  Current URL: {current_url}")

        # Take another screenshot
        pg.screenshot(path=str(BASE_DIR / "_checkout_debug.png"))
        print("  Saved debug screenshot: _checkout_debug.png")

        # If we didn't navigate away from cart, try alternative approaches
        if "cart" in current_url.lower():
            print("  Still on cart page, trying direct checkout navigation...")

            # Try clicking with force/dispatch
            pg.evaluate("""
                () => {
                    const allBtns = document.querySelectorAll('button');
                    for (const btn of allBtns) {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        if (text.includes('đặt hàng')) {
                            // Try dispatching click event
                            btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                            return true;
                        }
                    }
                    return false;
                }
            """)
            time.sleep(8)
            current_url = pg.url
            print(f"  URL after forced click: {current_url}")

        if "cart" in current_url.lower():
            print("  Still on cart, trying to use Playwright click...")
            try:
                # Use Playwright's click method which is more reliable
                btn = pg.locator('button:has-text("Đặt hàng")')
                if btn.count() > 0:
                    btn.first.click(force=True)
                    time.sleep(8)
                    current_url = pg.url
                    print(f"  URL after playwright click: {current_url}")
            except Exception as e:
                print(f"  Playwright click failed: {e}")

        if "cart" in current_url.lower():
            print("  Still on cart, trying /checkout URL directly...")
            pg.goto("https://www.coolmate.me/checkout", wait_until="domcontentloaded", timeout=120000)
            time.sleep(8)
            current_url = pg.url
            print(f"  URL after direct /checkout: {current_url}")

        # Now capture whatever page we're on
        pg.screenshot(path=str(BASE_DIR / "_checkout_final.png"))
        print(f"\n  Final URL: {current_url}")
        print("  Capturing page...")

        close_popups(pg)
        scroll_page(pg, max_scrolls=10, pause=0.3)
        force_lazy_images(pg)
        time.sleep(3)

        all_css, _ = capture_all_styles(pg, current_url)

        html = pg.content()
        print(f"    Raw HTML: {len(html):,} bytes")

        result_html = process_html(html, current_url, all_css)

        out_path = BASE_DIR / "checkout.html"
        out_path.write_text(result_html, encoding="utf-8")
        print(f"  SAVED: {out_path} ({len(result_html):,} bytes)")

        browser.close()

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
