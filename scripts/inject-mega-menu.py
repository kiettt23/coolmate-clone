"""
Inject CSS-only mega dropdown menus into navbar on all 5 pages.
Data sourced from sr-only nav structure matching coolmate.me.
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Menu data ──────────────────────────────────────────────
MENUS = {
    "Nam": {
        "ga": "menu__male",
        "columns": [
            {
                "title": "Nổi bật",
                "links": [
                    ("Tất cả sản phẩm", "/collection/do-nam"),
                    ("Sản phẩm mới", "/collection/san-pham-moi?gender_type=male"),
                    ("Bán chạy nhất", "/collection/ban-chay-nhat?gender_type=male"),
                    ("Cool Set", "/collection/set-do-nam"),
                    ("Đồ Thu Đông", "/collection/do-thu-dong?itm_source=navbar&gender_type=male"),
                ]
            },
            {
                "title": "Áo",
                "links": [
                    ("Tất cả Áo nam", "/collection/ao-nam"),
                    ("Áo Thun", "/collection/ao-thun-nam"),
                    ("Áo Polo", "/collection/ao-polo-nam"),
                    ("Áo Sơ Mi", "/collection/ao-so-mi-nam"),
                    ("Áo Thể Thao", "/collection/ao-nam-choi-the-thao"),
                    ("Áo Dài Tay", "/collection/ao-nam-dai-tay"),
                    ("Áo Hoodie", "/collection/ao-hoodies"),
                    ("Áo Khoác", "/collection/ao-khoac-nam"),
                ]
            },
            {
                "title": "Quần",
                "links": [
                    ("Tất cả Quần nam", "/collection/quan-nam"),
                    ("Quần Short", "/collection/quan-short-nam"),
                    ("Quần Jogger", "/collection/quan-jogger-nam"),
                    ("Quần Dài", "/collection/quan-dai-nam"),
                    ("Quần Jean", "/collection/quan-jeans-nam"),
                    ("Quần Thể Thao", "/collection/quan-nam-choi-the-thao"),
                    ("Quần Bơi", "/collection/do-boi-nam"),
                ]
            },
            {
                "title": "Đồ lót",
                "links": [
                    ("Đồ lót", "/collection/quan-lot-nam"),
                    ("Brief (Tam giác)", "/collection/quan-tam-giac-brief"),
                    ("Trunk (Boxer)", "/collection/quan-boxer-trunk"),
                    ("Boxer Brief", "/collection/quan-boxer-brief-dang-dai"),
                ]
            },
            {
                "title": "Phụ kiện",
                "links": [
                    ("Tất cả phụ kiện", "/collection/phu-kien-nam"),
                ]
            },
        ]
    },
    "Nữ": {
        "ga": "menu__female",
        "columns": [
            {
                "title": "Nổi bật",
                "links": [
                    ("Sản phẩm mới", "/collection/san-pham-moi?gender_type=female"),
                    ("Bán chạy nhất", "/collection/ban-chay-nhat?gender_type=female"),
                    ("Cool Set", "/collection/combo-do-nu"),
                    ("Đồ Thu Đông", "/collection/do-thu-dong?itm_source=navbar&gender_type=female"),
                ]
            },
            {
                "title": "Áo",
                "links": [
                    ("Tất cả Áo nữ", "/collection/ao-nu"),
                    ("Sport Bra", "/collection/ao-bra-nu"),
                    ("Croptop", "/collection/ao-cropped-top"),
                    ("Áo Polo", "/collection/ao-polo-nu"),
                    ("Áo Thun", "/collection/ao-thun-nu"),
                    ("Hoodie & Sweater", "/collection/ao-hoodie-sweater-nu"),
                    ("Áo Khoác", "/collection/ao-khoac-nu"),
                ]
            },
            {
                "title": "Quần",
                "links": [
                    ("Tất cả Quần nữ", "/collection/quan-nu"),
                    ("Legging", "/collection/quan-legging"),
                    ("Shorts", "/collection/quan-short-nu"),
                    ("Biker Shorts", "/collection/quan-biker-short"),
                    ("Váy Thể Thao", "/collection/vay-dam-nu"),
                    ("Quần Dài", "/collection/quan-dai-nu"),
                ]
            },
            {
                "title": "Phụ kiện",
                "links": [
                    ("Tất cả phụ kiện", "/collection/phu-kien-nu"),
                ]
            },
        ]
    },
    "THỂ THAO": {
        "ga": "menu__sport__sport",
        "columns": [
            {
                "title": "Nam",
                "links": [
                    ("Thể thao chung", "/collection/the-thao-chung?gender_type=male"),
                    ("Chạy bộ", "/collection/quan-ao-chay-bo"),
                    ("Gym", "/collection/quan-ao-phu-kien-tap-gym"),
                    ("Bóng đá", "/collection/quan-ao-da-bong-coolmate"),
                    ("Cầu lông & Bóng bàn", "/collection/racquet-sports-collection"),
                    ("Outdoor", "/collection/outdoor-collection"),
                ]
            },
            {
                "title": "Nữ",
                "links": [
                    ("Thể thao chung", "/collection/the-thao-chung-nu"),
                    ("Áo thể thao", "/collection/ao-nu-choi-the-thao"),
                    ("Quần thể thao", "/collection/quan-nu-choi-the-thao"),
                    ("Gym", "/collection/quan-ao-phu-kien-tap-gym-nu"),
                    ("Phụ kiện", "/collection/phu-kien-nu-choi-the-thao"),
                ]
            },
            {
                "title": "Bộ môn",
                "links": [
                    ("Pickleball", "/collection/pickleball-tennis?gender_type=male"),
                    ("Yoga & Pilates", "/collection/yoga-pilates"),
                ]
            },
        ]
    },
    "PHỤ KIỆN": {
        "ga": "menu__accessories",
        "columns": [
            {
                "title": "Nam",
                "links": [
                    ("Tất cả phụ kiện nam", "/collection/phu-kien-nam"),
                ]
            },
            {
                "title": "Nữ",
                "links": [
                    ("Tất cả phụ kiện nữ", "/collection/phu-kien-nu"),
                ]
            },
        ]
    },
    "BỘ SƯU TẬP": {
        "ga": "menu__collection",
        "columns": [
            {
                "title": "Bộ sưu tập",
                "links": [
                    ("Care & Share", "/collection/care-and-share"),
                    ("Áo ấm cho em", "/collection/ao-am-cho-em"),
                    ("Vụn Art", "/collection/vun-art-du-an-chung-tay-xay-nha-moi"),
                    ("Cung Hoàng Đạo", "/collection/cung-hoang-dao-collection"),
                    ("Áo thun Graphic", "/graphic-tee"),
                ]
            },
        ]
    },
    "SALE": {
        "ga": "menu__outlet",
        "columns": [
            {
                "title": "Nam",
                "links": [
                    ("SALE -50%", "/collection/giam-gia?gender_type=male"),
                ]
            },
            {
                "title": "Nữ",
                "links": [
                    ("SALE -30%", "/collection/giam-gia?gender_type=female"),
                ]
            },
            {
                "title": "Nổi bật",
                "links": [
                    ("Bra & Legging", "/collection/bra-legging-collection"),
                    ("Vital Seamless", "/collection/vital-seamless"),
                ]
            },
        ]
    },
}

# ── Build dropdown HTML for a menu ─────────────────────────
def build_dropdown(menu_data):
    cols_html = []
    for col in menu_data["columns"]:
        links_html = ""
        for text, href in col["links"]:
            links_html += f'<li><a href="{href}">{text}</a></li>'
        cols_html.append(
            f'<div class="mega-col">'
            f'<h4 class="mega-col-title">{col["title"]}</h4>'
            f'<ul>{links_html}</ul>'
            f'</div>'
        )
    return f'<div class="mega-dropdown">{"".join(cols_html)}</div>'


# ── CSS for mega menu ──────────────────────────────────────
MEGA_CSS = '''<style id="mega-menu">
  /* Mega dropdown container */
  .mega-dropdown {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    width: 100vw;
    background: #fff;
    border-top: 1px solid #f0f0f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    padding: 28px 48px;
    z-index: 100;
    gap: 32px;
    flex-wrap: wrap;
  }
  /* Show on hover */
  nav[aria-label="Thanh điều hướng chính"] ul > li:hover > .mega-dropdown {
    display: flex;
  }
  /* Position the li relatively for dropdown */
  nav[aria-label="Thanh điều hướng chính"] ul > li {
    position: static;
  }
  nav[aria-label="Thanh điều hướng chính"] ul[role="menu"] {
    position: relative;
  }
  /* Column */
  .mega-col { min-width: 160px; }
  .mega-col-title {
    font-size: 13px;
    font-weight: 600;
    color: #1a1a1a;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f0f0f0;
  }
  .mega-col ul { list-style: none; margin: 0; padding: 0; }
  .mega-col ul li { margin-bottom: 6px; }
  .mega-col ul li a {
    font-size: 13px;
    font-weight: 400;
    color: #525252;
    text-decoration: none;
    transition: color 0.15s;
    line-height: 1.6;
  }
  .mega-col ul li a:hover { color: #1a1a1a; }
  /* Hide on small screens */
  @media (max-width: 1023px) {
    .mega-dropdown { display: none !important; }
  }
</style>'''


# ── Inject into pages ──────────────────────────────────────
pages = [
    'site/index.html',
    'site/category.html',
    'site/product.html',
    'site/cart.html',
    'site/collection.html',
]

for page in pages:
    with open(page, 'r', encoding='utf-8') as f:
        html = f.read()

    # Skip if already injected
    if 'id="mega-menu"' in html:
        print(f'{page}: already has mega-menu, skipping')
        continue

    # 1. Add CSS before </head>
    head_idx = html.find('</head>')
    if head_idx < 0:
        print(f'{page}: no </head>')
        continue
    html = html[:head_idx] + '\n' + MEGA_CSS + '\n' + html[head_idx:]

    # 2. For each menu item, inject dropdown HTML after the <a> tag
    for menu_name, menu_data in MENUS.items():
        ga_label = menu_data["ga"]
        # Find the <a> trigger by ga-tracking-value
        pattern = f'ga-tracking-value="{ga_label}"'
        idx = html.find(pattern)
        if idx < 0:
            print(f'{page}: {menu_name} ({ga_label}) not found')
            continue

        # Find the closing </a> after this
        a_close = html.find('</a>', idx)
        if a_close < 0:
            continue

        # Find closing </li> after </a>
        li_close = html.find('</li>', a_close)
        if li_close < 0:
            continue

        # Insert dropdown HTML before </li>
        dropdown_html = build_dropdown(menu_data)
        html = html[:li_close] + dropdown_html + html[li_close:]

    with open(page, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'{page}: mega menu injected')
