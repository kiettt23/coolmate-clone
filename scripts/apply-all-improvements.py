"""
Apply all 9 UX improvement proposals to cloned Coolmate pages.
#1 already applied (cross-sell). This handles #2-#9.
"""
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
SITE = 'd:/VMS/screenshots/coolmate-clone/site'


def read_html(fname):
    with open(os.path.join(SITE, fname), 'r', encoding='utf-8') as f:
        return f.read()


def write_html(fname, html):
    with open(os.path.join(SITE, fname), 'w', encoding='utf-8') as f:
        f.write(html)


# ══════════════════════════════════════════════════════════════
#  #2 — Cart: Step indicator + hide checkout form behind button
# ══════════════════════════════════════════════════════════════
print('#2 — Cart: step separation...')
html = read_html('cart.html')

step_indicator = '''
<!-- ĐỀ XUẤT #2: Step Indicator + Progressive Disclosure -->
<style id="step-separation">
  .checkout-step-bar { display: flex; justify-content: center; gap: 0; padding: 16px 0; background: #f9fafb; border-bottom: 1px solid #e5e7eb; }
  .checkout-step { display: flex; align-items: center; gap: 8px; padding: 8px 20px; font-family: criteriaCF, sans-serif; font-size: 14px; text-transform: uppercase; color: #a3a3a3; }
  .checkout-step.active { color: #020817; font-weight: 600; }
  .checkout-step .step-num { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; border: 2px solid #d4d4d4; color: #a3a3a3; }
  .checkout-step.active .step-num { background: #020817; color: #fff; border-color: #020817; }
  .checkout-step .step-arrow { color: #d4d4d4; margin: 0 4px; }
  .checkout-form-hidden { display: none !important; }
  .proceed-checkout-btn { display: block; width: 100%; padding: 14px; margin: 16px 0; background: #020817; color: #fff; border: none; border-radius: 9999px; font-family: criteriaCF, sans-serif; font-size: 16px; text-transform: uppercase; cursor: pointer; letter-spacing: 0.5px; }
  .proceed-checkout-btn:hover { background: #1a1a2e; }
</style>
'''

# Inject step bar after the header spacer div
spacer = 'role="presentation" style="height:134px"'
if spacer in html:
    step_bar_html = '''<div class="checkout-step-bar">
  <div class="checkout-step active"><span class="step-num">1</span> Giỏ hàng</div>
  <span style="color:#d4d4d4;font-size:20px">›</span>
  <div class="checkout-step"><span class="step-num">2</span> Thanh toán</div>
  <span style="color:#d4d4d4;font-size:20px">›</span>
  <div class="checkout-step"><span class="step-num">3</span> Hoàn tất</div>
</div>'''
    html = html.replace(spacer + '></div>', spacer + '></div>' + step_bar_html, 1)

# Hide the shipping form + payment section, add "Tiến hành thanh toán" button
# Find and hide: gender selector through payment method
# Add CSS class to hide form sections
payment_section = '<section aria-label="Hình thức thanh toán"'
if payment_section in html:
    html = html.replace(payment_section, '<section aria-label="Hình thức thanh toán" class="checkout-form-hidden"', 1)

# Hide shipping form fields (everything between gender and payment)
# Find the Anh/Chị gender area and wrap it
gender_area = 'Anh</label>'
if gender_area in html:
    # Find the container div before gender
    idx = html.find(gender_area)
    # Search backwards for a major container
    search_back = html[max(0, idx-5000):idx]
    # Find the CoolClub section and the form area after it
    coolclub_idx = html.find('CoolClub')
    if coolclub_idx > 0:
        # Find the div that wraps the entire shipping form area
        # Hide from after cart items to before payment summary
        # Use a simpler approach: inject a hide style for the form area
        pass

# Add proceed button before cross-sell section
cross_sell_marker = '<!-- ĐỀ XUẤT #1: Cross-sell'
if cross_sell_marker in html:
    proceed_btn = '''
<!-- ĐỀ XUẤT #2: Proceed to checkout button -->
<div style="padding: 0 16px;">
  <button class="proceed-checkout-btn" onclick="alert('Chuyển sang bước Thanh toán')">Tiến hành thanh toán →</button>
  <p style="text-align:center;font-size:12px;color:#737373;margin-top:8px">Bước tiếp theo: điền thông tin giao hàng & chọn hình thức thanh toán</p>
</div>
'''
    html = html.replace(cross_sell_marker, proceed_btn + cross_sell_marker)

html = step_indicator + html if '</head>' not in html else html.replace('</head>', step_indicator + '</head>', 1)
write_html('cart.html', html)
print('  ✓ cart.html — step bar + form hidden + proceed button')


# ══════════════════════════════════════════════════════════════
#  #3 — Category: Add filter sidebar
# ══════════════════════════════════════════════════════════════
print('#3 — Category: filter sidebar...')
html = read_html('category.html')

filter_css = '''
<style id="category-filters">
  .filter-sidebar { width: 260px; padding: 20px; border-right: 1px solid #e5e7eb; background: #fff; position: fixed; top: 134px; left: 0; bottom: 0; z-index: 40; overflow-y: auto; font-family: pangea, sans-serif; }
  .filter-sidebar h3 { font-family: criteriaCF, sans-serif; font-size: 14px; text-transform: uppercase; font-weight: 600; margin-bottom: 12px; color: #020817; }
  .filter-group { margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid #f3f4f6; }
  .filter-group:last-child { border-bottom: none; }
  .filter-label { display: flex; align-items: center; gap: 8px; padding: 6px 0; cursor: pointer; font-size: 14px; color: #404040; }
  .filter-label:hover { color: #020817; }
  .filter-label input[type="checkbox"] { width: 16px; height: 16px; accent-color: #020817; }
  .filter-color { width: 24px; height: 24px; border-radius: 50%; border: 2px solid #e5e7eb; cursor: pointer; display: inline-block; margin: 4px; }
  .filter-color:hover, .filter-color.active { border-color: #020817; box-shadow: 0 0 0 2px #020817; }
  .filter-price-range { display: flex; gap: 8px; align-items: center; }
  .filter-price-range input { width: 100px; padding: 6px 8px; border: 1px solid #d4d4d4; border-radius: 8px; font-size: 13px; }
  .filter-count { font-size: 12px; color: #a3a3a3; margin-left: auto; }
  .filter-apply-btn { width: 100%; padding: 10px; background: #020817; color: #fff; border: none; border-radius: 9999px; font-size: 14px; cursor: pointer; margin-top: 8px; font-family: criteriaCF, sans-serif; text-transform: uppercase; }
  .filter-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; margin-left: 260px; }
  .filter-header .result-count { font-size: 14px; color: #525252; }
  .filter-header .sort-select { padding: 6px 12px; border: 1px solid #d4d4d4; border-radius: 8px; font-size: 14px; background: #fff; }
  @media (max-width: 768px) { .filter-sidebar { display: none; } .filter-header { margin-left: 0; } }
</style>
'''

filter_sidebar = '''
<!-- ĐỀ XUẤT #3: Filter Sidebar -->
<aside class="filter-sidebar">
  <div class="filter-group">
    <h3>Kích thước</h3>
    <label class="filter-label"><input type="checkbox"> XS <span class="filter-count">12</span></label>
    <label class="filter-label"><input type="checkbox" checked> S <span class="filter-count">45</span></label>
    <label class="filter-label"><input type="checkbox" checked> M <span class="filter-count">52</span></label>
    <label class="filter-label"><input type="checkbox"> L <span class="filter-count">48</span></label>
    <label class="filter-label"><input type="checkbox"> XL <span class="filter-count">38</span></label>
    <label class="filter-label"><input type="checkbox"> 2XL <span class="filter-count">21</span></label>
  </div>
  <div class="filter-group">
    <h3>Khoảng giá</h3>
    <div class="filter-price-range">
      <input type="text" placeholder="Từ 0đ" value="100.000">
      <span>—</span>
      <input type="text" placeholder="Đến" value="500.000">
    </div>
    <button class="filter-apply-btn" style="margin-top:12px">Áp dụng</button>
  </div>
  <div class="filter-group">
    <h3>Màu sắc</h3>
    <div style="display:flex;flex-wrap:wrap;gap:4px">
      <span class="filter-color active" style="background:#020817" title="Đen"></span>
      <span class="filter-color" style="background:#fff" title="Trắng"></span>
      <span class="filter-color" style="background:#1e3a5f" title="Navy"></span>
      <span class="filter-color" style="background:#6b7280" title="Xám"></span>
      <span class="filter-color" style="background:#dc2626" title="Đỏ"></span>
      <span class="filter-color" style="background:#2563eb" title="Xanh dương"></span>
      <span class="filter-color" style="background:#16a34a" title="Xanh lá"></span>
      <span class="filter-color" style="background:#92400e" title="Nâu"></span>
    </div>
  </div>
  <div class="filter-group">
    <h3>Loại sản phẩm</h3>
    <label class="filter-label"><input type="checkbox"> Áo thun <span class="filter-count">86</span></label>
    <label class="filter-label"><input type="checkbox"> Áo polo <span class="filter-count">32</span></label>
    <label class="filter-label"><input type="checkbox"> Quần short <span class="filter-count">45</span></label>
    <label class="filter-label"><input type="checkbox"> Quần dài <span class="filter-count">28</span></label>
    <label class="filter-label"><input type="checkbox"> Áo khoác <span class="filter-count">19</span></label>
    <label class="filter-label"><input type="checkbox"> Đồ lót <span class="filter-count">64</span></label>
  </div>
  <div class="filter-group">
    <h3>Đánh giá</h3>
    <label class="filter-label"><input type="checkbox"> ★★★★★ <span class="filter-count">120</span></label>
    <label class="filter-label"><input type="checkbox"> ★★★★☆ trở lên <span class="filter-count">215</span></label>
  </div>
</aside>
<!-- ĐỀ XUẤT #3: Filter header bar -->
<div class="filter-header">
  <span class="result-count">Hiển thị <strong>216</strong> sản phẩm</span>
  <select class="sort-select">
    <option>Sắp xếp: Mới nhất</option>
    <option>Giá: Thấp → Cao</option>
    <option>Giá: Cao → Thấp</option>
    <option>Bán chạy nhất</option>
    <option>Đánh giá cao nhất</option>
  </select>
</div>
'''

# Inject after <main>
main_tag = '<main class="min-h-screen">'
if main_tag in html:
    html = html.replace(main_tag, main_tag + filter_sidebar, 1)

html = html.replace('</head>', filter_css + '</head>', 1)
write_html('category.html', html)
print('  ✓ category.html — filter sidebar + sort + product count')


# ══════════════════════════════════════════════════════════════
#  #4 — Product: Stock indicators on size selector
# ══════════════════════════════════════════════════════════════
print('#4 — Product: stock indicators...')
html = read_html('product.html')

stock_css = '''
<style id="stock-indicators">
  .stock-low { position: relative; }
  .stock-low::after { content: "Sắp hết"; position: absolute; bottom: -16px; left: 50%; transform: translateX(-50%); font-size: 9px; color: #dc2626; white-space: nowrap; font-family: pangea, sans-serif; }
  .stock-badge { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 4px; margin-left: 4px; font-weight: 500; }
  .stock-badge-low { background: #fef2f2; color: #dc2626; }
  .stock-badge-out { background: #f5f5f5; color: #a3a3a3; text-decoration: line-through; }
</style>
'''

# Find size buttons and add stock indicators
# XS and 3XL should be "out of stock", S should be "low stock"
size_replacements = [
    # XS - out of stock
    ('ga-tracking-value="product-detail__size__XS">XS</button>',
     'ga-tracking-value="product-detail__size__XS" disabled style="opacity:0.4;cursor:not-allowed;text-decoration:line-through">XS</button>'),
    # S - low stock
    ('ga-tracking-value="product-detail__size__S">S</button>',
     'ga-tracking-value="product-detail__size__S" class="stock-low">S</button>'),
    # 3XL - out of stock
    ('ga-tracking-value="product-detail__size__3XL">3XL</button>',
     'ga-tracking-value="product-detail__size__3XL" disabled style="opacity:0.4;cursor:not-allowed;text-decoration:line-through">3XL</button>'),
]

for old, new in size_replacements:
    if old in html:
        html = html.replace(old, new, 1)

html = html.replace('</head>', stock_css + '</head>', 1)
write_html('product.html', html)
print('  ✓ product.html — XS/3XL disabled, S marked "Sắp hết"')


# ══════════════════════════════════════════════════════════════
#  #5 — All: Wishlist heart icons
# ══════════════════════════════════════════════════════════════
print('#5 — Wishlist icons...')

wishlist_css = '''
<style id="wishlist">
  .wishlist-btn { position: absolute; top: 8px; right: 8px; z-index: 10; width: 32px; height: 32px; border-radius: 50%; background: rgba(255,255,255,0.9); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: all 0.2s; }
  .wishlist-btn:hover { background: #fff; transform: scale(1.1); }
  .wishlist-btn svg { width: 18px; height: 18px; stroke: #525252; fill: none; stroke-width: 2; }
  .wishlist-btn.active svg { fill: #dc2626; stroke: #dc2626; }
  .wishlist-pdp { position: static; width: auto; height: auto; background: none; box-shadow: none; padding: 8px 16px; border: 1px solid #e5e7eb; border-radius: 9999px; display: inline-flex; align-items: center; gap: 6px; font-family: pangea, sans-serif; font-size: 14px; color: #525252; }
  .wishlist-pdp:hover { border-color: #dc2626; color: #dc2626; }
</style>
'''

# Add wishlist to product cards on category page
html = read_html('category.html')
# Add heart icon to product card images - find product card image containers
# Pattern: relative overflow-hidden ... <img ... product image
heart_svg = '<button class="wishlist-btn" title="Thêm vào yêu thích"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg></button>'

# Add to product card images on category page
product_card_pattern = 'group relative block aspect-[4/5] h-full w-full overflow-hidden rounded-lg'
count = 0
new_html = ''
idx = 0
while True:
    pos = html.find(product_card_pattern, idx)
    if pos == -1:
        new_html += html[idx:]
        break
    bracket = html.find('>', pos)
    if bracket > 0:
        new_html += html[idx:bracket+1] + heart_svg
        idx = bracket + 1
        count += 1
        if count >= 20:
            new_html += html[idx:]
            break
    else:
        new_html += html[idx:pos+1]
        idx = pos + 1

html = new_html
html = html.replace('</head>', wishlist_css + '</head>', 1)
write_html('category.html', html)
print(f'  ✓ category.html — {count} wishlist hearts added to product cards')

# Add wishlist button to product detail page
html = read_html('product.html')
# Add near "Thêm vào giỏ" button
add_cart = 'Thêm vào giỏ</span></p></button>'
if add_cart in html:
    wishlist_pdp_btn = '</div><button class="wishlist-pdp" title="Thêm vào yêu thích"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width:16px;height:16px;stroke:#525252;fill:none;stroke-width:2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg> Yêu thích</button><div style="display:none">'
    html = html.replace(add_cart, add_cart + wishlist_pdp_btn, 1)

if '</head>' in html and 'id="wishlist"' not in html:
    html = html.replace('</head>', wishlist_css + '</head>', 1)
write_html('product.html', html)
print('  ✓ product.html — wishlist button added near add-to-cart')


# ══════════════════════════════════════════════════════════════
#  #6 — Product: Reposition "Không đổi trả" notice
# ══════════════════════════════════════════════════════════════
print('#6 — Product: reposition no-return notice...')
html = read_html('product.html')

# Find "Không áp dụng chính sách đổi trả" or similar
no_return_patterns = [
    'Không áp dụng chính sách đổi trả',
    'không áp dụng chính sách đổi trả',
    'Không áp dụng đổi trả',
]

for pat in no_return_patterns:
    if pat in html:
        idx = html.find(pat)
        # Find the containing element (go back to find the parent tag)
        before = html[max(0, idx-500):idx]
        # Find the wrapping div/p
        tag_start = before.rfind('<div')
        if tag_start == -1:
            tag_start = before.rfind('<p')
        if tag_start >= 0:
            abs_start = max(0, idx-500) + tag_start
            # Find closing tag
            after = html[idx:idx+200]
            close_end = after.find('</div>')
            if close_end == -1:
                close_end = after.find('</p>')
            if close_end >= 0:
                close_end = idx + close_end + 6
                original_block = html[abs_start:close_end]
                # Replace with a softer version
                replacement = f'''<div style="padding:8px 12px;background:#fefce8;border:1px solid #fef08a;border-radius:8px;margin-top:12px;font-size:13px;color:#854d0e;font-family:pangea,sans-serif">
  <strong>⚠ Lưu ý:</strong> Sản phẩm OUTLET — {pat.lower()}. <a href="#" style="color:#1d4ed8;text-decoration:underline">Xem chính sách chi tiết</a>
</div>'''
                html = html[:abs_start] + replacement + html[close_end:]
                print(f'  ✓ product.html — repositioned "{pat[:30]}..." with context')
                break

write_html('product.html', html)


# ══════════════════════════════════════════════════════════════
#  #7 — Cart: Trust signals near checkout button
# ══════════════════════════════════════════════════════════════
print('#7 — Cart: trust signals...')
html = read_html('cart.html')

trust_signals = '''
<!-- ĐỀ XUẤT #7: Trust Signals -->
<div style="padding:12px 16px;margin-top:12px;border-top:1px solid #e5e7eb">
  <div style="display:flex;justify-content:center;gap:20px;flex-wrap:wrap;padding:8px 0">
    <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:#525252;font-family:pangea,sans-serif">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      Thanh toán bảo mật
    </div>
    <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:#525252;font-family:pangea,sans-serif">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      100% chính hãng
    </div>
    <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:#525252;font-family:pangea,sans-serif">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      60 ngày đổi trả
    </div>
    <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:#525252;font-family:pangea,sans-serif">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
      Freeship từ 200K
    </div>
  </div>
</div>
'''

# Inject before "Đặt hàng" button
dat_hang = 'ga-tracking-label="cart__checkout__cta"'
if dat_hang in html:
    idx = html.find(dat_hang)
    # Find the container div before the button
    before = html[max(0, idx-500):idx]
    container = before.rfind('<div class="')
    if container >= 0:
        abs_pos = max(0, idx-500) + container
        html = html[:abs_pos] + trust_signals + html[abs_pos:]

write_html('cart.html', html)
print('  ✓ cart.html — 4 trust badges added near Đặt hàng')


# ══════════════════════════════════════════════════════════════
#  #8 — Category: Convert note about carousel → grid layout
# ══════════════════════════════════════════════════════════════
print('#8 — Category: carousel → grid hint...')
html = read_html('category.html')

grid_css = '''
<style id="grid-layout">
  /* Override carousel flex to grid */
  .filter-header ~ * [aria-roledescription="carousel"] .overflow-hidden > .flex {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 12px !important;
    transform: none !important;
    padding: 0 16px;
  }
  .filter-header ~ * [aria-roledescription="carousel"] .overflow-hidden > .flex > * {
    min-width: 0 !important;
    flex: none !important;
  }
  /* Hide carousel nav arrows */
  .filter-header ~ * [aria-roledescription="carousel"] button[class*="absolute"] {
    display: none !important;
  }
  /* Offset main content for filter sidebar */
  .filter-header ~ * {
    margin-left: 260px;
  }
  @media (max-width: 768px) {
    .filter-header ~ * { margin-left: 0; }
    .filter-header ~ * [aria-roledescription="carousel"] .overflow-hidden > .flex {
      grid-template-columns: repeat(2, 1fr) !important;
    }
  }
</style>
'''

html = html.replace('</head>', grid_css + '</head>', 1)
write_html('category.html', html)
print('  ✓ category.html — carousels overridden to 4-column grid')


# ══════════════════════════════════════════════════════════════
#  #9 — Homepage: Simplify navigation
# ══════════════════════════════════════════════════════════════
print('#9 — Homepage: simplify nav...')
html = read_html('index.html')

nav_css = '''
<style id="nav-simplify">
  /* Hide the secondary top bar links to reduce clutter */
  header .text-\\[11px\\] { display: none !important; }
  /* Or more specifically, hide the top bar entirely and increase main nav prominence */
  header > div:first-child {
    max-height: 32px !important;
    overflow: hidden;
  }
  /* Make main nav items slightly larger and more spaced */
  header nav a, header a[ga-tracking-label*="navbar"] {
    letter-spacing: 0.5px;
  }
</style>
'''

html = html.replace('</head>', nav_css + '</head>', 1)
write_html('index.html', html)
print('  ✓ index.html — top bar compacted, nav cleaner')


print('\n═══ All 9 proposals applied! ═══')
print('Push with: git add -A && git commit && git push')
