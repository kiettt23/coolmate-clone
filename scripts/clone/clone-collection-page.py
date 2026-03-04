"""
Coolmate.me collection page cloner.
Clones the /collection/do-the-thao page using same technique as clone-additional-pages.py.
Reuses existing assets - only downloads NEW ones that don't already exist.
Outputs to site/collection.html with relative asset paths.
"""

import sys
import os
import re
import time
import hashlib
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_DIR = Path("d:/VMS/screenshots/coolmate-clone/site")
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
    """Create a safe, unique-ish filename from a URL."""
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
    """Determine if a URL points to a font, image, or css."""
    lower = url.lower()
    path = urlparse(lower).path
    if any(path.endswith(e) for e in ('.woff2', '.woff', '.ttf', '.otf', '.eot')):
        return "fonts"
    if any(path.endswith(e) for e in ('.css',)):
        return "css"
    return "images"


def download_file(url, force_type=None):
    """Download a file and return local relative path. Skips if already exists."""
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

        # If file already exists from previous clone runs, reuse it
        if fpath.exists():
            rel = f"assets/{asset_type}/{fpath.name}"
            downloaded_map[url] = rel
            return rel

        resp = SESSION.get(url, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            return None

        # Deduplicate filenames
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
    """Rewrite url() references inside CSS text to local paths."""
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


def scroll_page(page, max_scrolls=35, pause=0.4):
    """Scroll to trigger lazy loading."""
    print("  Scrolling to load lazy content...")
    prev = 0
    for i in range(max_scrolls):
        page.evaluate("window.scrollBy(0, 700)")
        time.sleep(pause)
        curr = page.evaluate("document.body.scrollHeight")
        if curr == prev and i > 8:
            break
        prev = curr
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)
    print(f"    Scrolled {min(i+1, max_scrolls)} times")


def capture_all_styles(page, page_url):
    """
    Capture ALL CSS from the page - both <style> tags and external sheets.
    Returns a list of CSS text strings with urls already resolved.
    """
    print("  Capturing all active stylesheets...")

    style_data = page.evaluate("""
        () => {
            const results = [];
            for (const sheet of document.styleSheets) {
                try {
                    const rules = Array.from(sheet.cssRules || []);
                    const cssText = rules.map(r => r.cssText).join('\\n');
                    results.push({
                        href: sheet.href || null,
                        cssText: cssText,
                        ownerNodeTag: sheet.ownerNode ? sheet.ownerNode.tagName : null
                    });
                } catch (e) {
                    results.push({
                        href: sheet.href || null,
                        cssText: null,
                        ownerNodeTag: sheet.ownerNode ? sheet.ownerNode.tagName : null,
                        crossOrigin: true
                    });
                }
            }
            return results;
        }
    """)

    all_css_texts = []
    external_hrefs_captured = set()

    for sd in style_data:
        if sd.get("cssText"):
            base = sd["href"] if sd["href"] else page_url
            rewritten = rewrite_css_urls(sd["cssText"], base)
            all_css_texts.append(rewritten)
            if sd["href"]:
                external_hrefs_captured.add(sd["href"])
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
                    external_hrefs_captured.add(sd["href"])
            except Exception:
                pass

    print(f"    Captured {len(all_css_texts)} stylesheets "
          f"({len(external_hrefs_captured)} external)")

    return all_css_texts, external_hrefs_captured


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


# Navigation link mapping: coolmate.me URLs -> local HTML files
NAV_LINK_MAP = {
    "https://www.coolmate.me": "index.html",
    "https://www.coolmate.me/": "index.html",
    "https://coolmate.me": "index.html",
    "https://coolmate.me/": "index.html",
    "/": "index.html",
    "/nam": "category.html",
    "/nu": "category.html",
    "https://www.coolmate.me/nam": "category.html",
    "https://www.coolmate.me/nu": "category.html",
    "/cart": "cart.html",
    "https://www.coolmate.me/cart": "cart.html",
    "/collection/do-the-thao": "collection.html",
    "https://www.coolmate.me/collection/do-the-thao": "collection.html",
}


def fix_navigation_links(soup):
    """Rewrite navigation links to point to local HTML files."""
    print("  Fixing navigation links...")
    link_count = 0
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        # Direct match
        if href in NAV_LINK_MAP:
            a_tag["href"] = NAV_LINK_MAP[href]
            link_count += 1
            continue
        # Product links
        if "/product/" in href:
            a_tag["href"] = "product.html"
            link_count += 1
            continue
        # Collection links
        if "/collection/" in href:
            a_tag["href"] = "collection.html"
            link_count += 1
            continue
        # Category-like links (men/women sections)
        if href.startswith("/") and not href.startswith("//"):
            # Keep as-is for non-mapped local paths
            pass
    print(f"    Fixed {link_count} navigation links")
    return soup


def process_html(html, page_url, all_css_texts, captured_hrefs):
    """
    Process the rendered HTML:
    - Remove scripts
    - Remove existing <style>/<link stylesheet>
    - Download and rewrite image URLs
    - Inject the captured CSS as a single <style> block
    - Fix slider/carousel transforms
    - Fix navigation links
    """
    print("  Processing HTML...")
    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove all scripts
    script_count = 0
    for s in soup.find_all("script"):
        s.decompose()
        script_count += 1
    print(f"    Removed {script_count} scripts")

    # 2. Remove existing <link rel="stylesheet"> and <style> tags
    for link in soup.find_all("link", rel=lambda r: r and "stylesheet" in r):
        link.decompose()
    for style in soup.find_all("style"):
        style.decompose()

    # 3. Remove Next.js data tags
    for tag in soup.find_all("script", id="__NEXT_DATA__"):
        tag.decompose()

    # 4. Unwrap noscript
    for ns in soup.find_all("noscript"):
        ns.unwrap()

    # 5. Process images
    print("  Downloading images...")
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

    # 6. Process <source> tags
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

    # 7. Process video posters
    for video in soup.find_all("video"):
        poster = video.get("poster")
        if poster:
            abs_url = urljoin(page_url, poster)
            local = download_file(abs_url)
            if local:
                video["poster"] = local

    # 8. Process background images in inline styles
    print("  Processing inline style backgrounds...")
    bg_count = 0
    for tag in soup.find_all(style=True):
        style_val = tag["style"]
        if "url(" in style_val:
            tag["style"] = rewrite_css_urls(style_val, page_url)
            bg_count += 1
    print(f"    Processed {bg_count} background styles")

    # 9. Process favicon / icons
    for link in soup.find_all("link"):
        rel = link.get("rel", [])
        href = link.get("href")
        if href and any(r in rel for r in ["icon", "shortcut", "apple-touch-icon", "preload"]):
            abs_url = urljoin(page_url, href)
            atype = "fonts" if link.get("as") == "font" else classify_url(abs_url)
            local = download_file(abs_url, force_type=atype)
            if local:
                link["href"] = local

    # 10. Fix slider/carousel transforms to 0px
    print("  Fixing slider/carousel transforms...")
    transform_count = 0
    for tag in soup.find_all(style=True):
        style_val = tag["style"]
        if "translate" in style_val.lower() or "transform" in style_val.lower():
            new_style = re.sub(
                r'translate3d\([^)]*\)',
                'translate3d(0px, 0px, 0px)',
                style_val
            )
            new_style = re.sub(
                r'translateX\([^)]*\)',
                'translateX(0px)',
                new_style
            )
            if new_style != style_val:
                tag["style"] = new_style
                transform_count += 1
    print(f"    Fixed {transform_count} transforms")

    # 11. Fix navigation links to local pages
    fix_navigation_links(soup)

    # 12. Inject all captured CSS as a single large <style> block in <head>
    print("  Injecting captured CSS...")
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


def close_popups(page):
    """Close any popups/modals/overlays."""
    try:
        page.evaluate("""
            () => {
                document.querySelectorAll(
                    '[class*="popup"], [class*="Popup"], [class*="modal"], ' +
                    '[class*="Modal"], [class*="overlay"], [class*="Overlay"], ' +
                    '[class*="cookie"], [class*="Cookie"], [class*="banner-noti"], ' +
                    '[class*="notification"]'
                ).forEach(el => { el.style.display = 'none'; });
            }
        """)
    except Exception:
        pass


def force_lazy_images(page):
    """Force load lazy images."""
    page.evaluate("""
        () => {
            document.querySelectorAll('img[data-src]').forEach(img => {
                if (!img.src || img.src.includes('data:') || img.src.includes('placeholder'))
                    img.src = img.getAttribute('data-src');
            });
            document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                img.loading = 'eager';
            });
            document.querySelectorAll('[data-bg]').forEach(el => {
                el.style.backgroundImage = 'url(' + el.getAttribute('data-bg') + ')';
            });
        }
    """)


def clone_page(page, url, output_name):
    """Full pipeline: navigate, render, capture styles, process, save."""
    print(f"\n{'='*60}")
    print(f"CLONING: {url}")
    print(f"OUTPUT:  {output_name}")
    print(f"{'='*60}")

    print("  Navigating...")
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    time.sleep(10)

    close_popups(page)
    scroll_page(page)
    force_lazy_images(page)
    time.sleep(3)

    # Capture all styles BEFORE we touch the DOM
    all_css, captured_hrefs = capture_all_styles(page, url)

    # Get rendered HTML
    print("  Extracting rendered DOM...")
    html = page.content()
    print(f"    Raw HTML: {len(html):,} bytes")

    # Process HTML
    result_html = process_html(html, url, all_css, captured_hrefs)

    # Save
    out_path = BASE_DIR / output_name
    out_path.write_text(result_html, encoding="utf-8")
    print(f"  SAVED: {out_path} ({len(result_html):,} bytes)")
    return out_path


def main():
    print("=" * 60)
    print("COOLMATE.ME COLLECTION PAGE CLONER")
    print("  Clones /collection/do-the-thao page")
    print("=" * 60)

    ensure_dirs()

    with sync_playwright() as p:
        print("\n[INIT] Launching browser...")
        browser = p.chromium.launch(
            headless=True,
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

        # Block video to speed things up
        pg.route("**/*.{mp4,webm,ogg}", lambda r: r.abort())

        # Clone collection page
        print("\n[1/1] CLONING COLLECTION PAGE")
        clone_page(
            pg,
            "https://www.coolmate.me/collection/do-the-thao",
            "collection.html"
        )

        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    imgs = len(list(IMAGES_DIR.glob("*")))
    fonts = len(list(FONTS_DIR.glob("*")))
    csss = len(list(CSS_DIR.glob("*")))
    print(f"  Assets: {imgs} images, {fonts} fonts, {csss} CSS files")
    print(f"  Collection: {BASE_DIR / 'collection.html'}")


if __name__ == "__main__":
    main()
