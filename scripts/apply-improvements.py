"""
Apply 4 color improvement proposals to cloned Coolmate pages.
Injects CSS overrides into each page's <head>.
"""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

SITE_DIR = 'd:/VMS/screenshots/coolmate-clone/site'

# ── CSS overrides for all pages ──
SHARED_CSS = """
/* ============================================
   ĐỀ XUẤT CẢI THIỆN HỆ THỐNG MÀU COOLMATE
   ============================================ */

/* --- ĐỀ XUẤT 1: Brand color #273BCE hiện diện hơn --- */

/* CTA primary buttons: đen → xanh brand */
[ga-tracking-label="product-detail__add_to_cart"],
[ga-tracking-label="cart__checkout__cta"],
[data-label*="đặt hàng" i],
[data-label*="dat hang" i] {
  background-color: #273BCE !important;
  border-color: #273BCE !important;
}
[ga-tracking-label="product-detail__add_to_cart"]:hover,
[ga-tracking-label="cart__checkout__cta"]:hover {
  background-color: #1E30A0 !important;
}

/* "Mua ngay" / "SHOP NOW" hero buttons */
a[aria-label*="Mua ngay"],
a[aria-label*="SHOP NOW"],
a[aria-label*="Shop now"] {
  background-color: #273BCE !important;
  color: #FFFFFF !important;
  border-color: #273BCE !important;
}
a[aria-label*="Mua ngay"]:hover,
a[aria-label*="SHOP NOW"]:hover {
  background-color: #1E30A0 !important;
}

/* Active nav item highlight */
nav a[aria-current="page"],
header a[aria-current="page"] {
  color: #273BCE !important;
  border-bottom: 2px solid #273BCE !important;
}

/* --- ĐỀ XUẤT 2: Tăng contrast màu đỏ sale --- */

/* Giá khuyến mãi: #DC2626 → #B91C1C (đạt WCAG AAA) */
.text-red-600,
.text-\\[\\#DC2626\\],
[class*="text-red"] {
  color: #B91C1C !important;
}

/* Badge giảm giá */
.bg-red-600,
.bg-\\[\\#DC2626\\],
[class*="bg-red"] {
  background-color: #B91C1C !important;
}

/* Sale link trong nav */
a[href*="sale"] {
  color: #B91C1C !important;
}

/* --- ĐỀ XUẤT 3: Phân biệt link vs text --- */

/* Footer links: thêm underline khi hover + đổi sang brand color */
footer a:not([class*="bg-"]):not([aria-label]) {
  transition: color 0.2s, text-decoration 0.2s !important;
}
footer a:not([class*="bg-"]):not([aria-label]):hover {
  color: #7B8FE0 !important;
  text-decoration: underline !important;
}

/* In-content links: thêm dấu hiệu nhận biết */
main a[href]:not([class*="bg-"]):not([class*="button"]):not([aria-label*="banner"]):not([aria-label*="Banner"]):not([ga-tracking-label*="banner"]):not([ga-tracking-label*="product-card"]) {
  text-decoration-color: #273BCE !important;
}

/* Product name links: underline on hover */
a[ga-tracking-label*="product-card"]:hover p,
a[ga-tracking-label*="product-card"]:hover span {
  text-decoration: underline !important;
}

/* --- ĐỀ XUẤT 4: Hover/focus states rõ hơn --- */

/* Focus ring: dày hơn, brand color rõ ràng */
*:focus-visible {
  outline: 3px solid #273BCE !important;
  outline-offset: 2px !important;
  box-shadow: 0 0 0 5px rgba(39, 59, 206, 0.25) !important;
}

/* Button hover: transition mượt */
button, a[class*="inline-flex"] {
  transition: all 0.2s ease !important;
}

/* Nav links hover */
header a:hover {
  color: #273BCE !important;
  transition: color 0.2s !important;
}

/* Input focus: viền brand */
input:focus, select:focus, textarea:focus {
  border-color: #273BCE !important;
  box-shadow: 0 0 0 3px rgba(39, 59, 206, 0.2) !important;
  outline: none !important;
}
"""

# ── Page-specific CSS ──
PAGE_CSS = {
    'index.html': """
/* Homepage: hero section brand accent */
section[aria-label*="Hero"] button {
  border-color: rgba(39, 59, 206, 0.5) !important;
}
""",
    'category.html': """
/* Category: active filter dùng brand color */
button[aria-pressed="true"],
button[data-state="active"] {
  background-color: #273BCE !important;
  color: #FFFFFF !important;
}
""",
    'product.html': """
/* Product: size selector active */
button[aria-pressed="true"] {
  border-color: #273BCE !important;
  color: #273BCE !important;
}

/* Star rating giữ nguyên vàng - không đổi */
""",
    'cart.html': """
/* Cart: coupon input focus */
input[placeholder*="voucher" i]:focus,
input[placeholder*="coupon" i]:focus,
input[placeholder*="mã" i]:focus {
  border-color: #273BCE !important;
  box-shadow: 0 0 0 3px rgba(39, 59, 206, 0.2) !important;
}
""",
}


def inject_css(filepath, css_block):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    style_tag = f'\n<style id="color-improvements">{css_block}\n</style>\n'

    # Inject before </head>
    if '</head>' in html:
        html = html.replace('</head>', style_tag + '</head>', 1)
    else:
        html = style_tag + html

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def fix_sale_red_inline(filepath):
    """Also fix inline style colors for sale red."""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    count = 0
    # rgb(220, 38, 38) → rgb(185, 28, 28)
    new_html = html.replace('rgb(220, 38, 38)', 'rgb(185, 28, 28)')
    count += html.count('rgb(220, 38, 38)')

    # color:#DC2626 → color:#B91C1C (inline styles)
    new_html = new_html.replace('#DC2626', '#B91C1C')
    count += html.count('#DC2626')
    new_html = new_html.replace('#dc2626', '#B91C1C')
    count += html.count('#dc2626')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_html)

    return count


# ── Apply to all pages ──
import os

for fname in ['index.html', 'category.html', 'product.html', 'cart.html']:
    fpath = os.path.join(SITE_DIR, fname)
    if not os.path.exists(fpath):
        print(f'  SKIP {fname} (not found)')
        continue

    # 1. Inject CSS overrides
    page_specific = PAGE_CSS.get(fname, '')
    full_css = SHARED_CSS + page_specific
    inject_css(fpath, full_css)

    # 2. Fix inline sale red colors
    red_fixes = fix_sale_red_inline(fpath)

    print(f'  ✓ {fname} — CSS injected + {red_fixes} inline red fixes')

print('\nDone! All 4 proposals applied.')
print('Run: git diff site/ to see changes.')
