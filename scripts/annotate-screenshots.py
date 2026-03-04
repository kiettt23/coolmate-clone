from PIL import Image, ImageDraw, ImageFont
import os, math

SCREENSHOT_DIR = r'd:\VMS\screenshots\coolmate-screenshots'
OUTPUT_DIR = r'd:\VMS\screenshots\coolmate-annotated'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_font(size):
    for fp in [r'C:\Windows\Fonts\arialbd.ttf', r'C:\Windows\Fonts\arial.ttf']:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


FONT_TAG = get_font(36)
FONT_TAG_SMALL = get_font(28)
FONT_LEGEND = get_font(34)
FONT_LEGEND_SMALL = get_font(28)


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_tag(draw, num, cx, cy, color=(255, 80, 80)):
    """Draw a numbered circle tag at position."""
    r = 30
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=(255, 255, 255), width=3)
    text = str(num)
    bbox = draw.textbbox((0, 0), text, font=FONT_TAG)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 4), text, fill=(255, 255, 255), font=FONT_TAG)


def draw_rect(draw, x1, y1, x2, y2, color=(255, 80, 80), width=5):
    """Highlight rectangle."""
    draw.rectangle([x1, y1, x2, y2], outline=color, width=width)


def add_legend(img, entries, bg_color=(20, 20, 20)):
    """Add a legend bar at the bottom with numbered entries.
    entries: list of (hex_color, label)
    """
    draw_temp = ImageDraw.Draw(img)
    line_h = 52
    pad = 30
    swatch_size = 36
    legend_h = len(entries) * line_h + pad * 2 + 10

    # Create new image with legend space
    new_img = Image.new('RGB', (img.width, img.height + legend_h), bg_color)
    new_img.paste(img, (0, 0))
    draw = ImageDraw.Draw(new_img)

    # Draw legend entries
    y_start = img.height + pad
    col_w = img.width // 2  # 2 columns

    for i, (hex_color, label) in enumerate(entries):
        col = i % 2
        row = i // 2
        x = pad + col * col_w
        y = y_start + row * line_h

        # Number circle
        num = i + 1
        cx = x + 20
        cy = y + 18
        r = 18
        tag_color = (255, 80, 80)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tag_color, outline=(255, 255, 255), width=2)
        num_text = str(num)
        bbox = draw.textbbox((0, 0), num_text, font=FONT_TAG_SMALL)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw // 2, cy - th // 2 - 3), num_text, fill=(255, 255, 255), font=FONT_TAG_SMALL)

        # Color swatch
        sx = x + 50
        sy = y + 2
        rgb = hex_to_rgb(hex_color)
        draw.rectangle([sx, sy, sx + swatch_size, sy + swatch_size],
                       fill=rgb, outline=(255, 255, 255), width=2)

        # Label text
        tx = sx + swatch_size + 12
        draw.text((tx, y + 4), f'{hex_color}  {label}',
                  fill=(230, 230, 230), font=FONT_LEGEND_SMALL)

    return new_img


# ════════════════════════════════════════════════════════════════
#  1. HOMEPAGE
# ════════════════════════════════════════════════════════════════
print('1/4 - Homepage...')
img = Image.open(os.path.join(SCREENSHOT_DIR, '02-trang-chu-above-fold.png'))
draw = ImageDraw.Draw(img)

# 1 - Top bar dark
draw_rect(draw, 0, 0, img.width, 56, color=(255, 200, 0))
draw_tag(draw, 1, 2700, 28, color=(255, 200, 0))

# 2 - Nav bar white
draw_rect(draw, 0, 56, img.width, 165, color=(0, 180, 255))
draw_tag(draw, 2, 2700, 110, color=(0, 180, 255))

# 3 - "SALE" red text
draw_rect(draw, 930, 80, 1070, 145, color=(255, 60, 60))
draw_tag(draw, 3, 1090, 80, color=(255, 60, 60))

# 4 - Hero banner
draw_rect(draw, 0, 200, img.width, 1200, color=(255, 165, 0))
draw_tag(draw, 4, 2700, 700, color=(255, 165, 0))

# 5 - CTA button "MUA NGAY"
draw_rect(draw, 78, 870, 385, 950, color=(0, 255, 100))
draw_tag(draw, 5, 410, 870, color=(0, 255, 100))

# 6 - White heading on hero
draw_rect(draw, 78, 570, 870, 810, color=(200, 130, 255))
draw_tag(draw, 6, 900, 680, color=(200, 130, 255))

img = add_legend(img, [
    ('#1A1A1A', 'Top bar – nền xám đậm'),
    ('#FFFFFF', 'Navigation – nền trắng'),
    ('#DC2626', '"SALE" – chữ đỏ nhấn mạnh'),
    ('#000000', 'Hero banner – nền tối/ảnh'),
    ('#000000', 'Button "MUA NGAY" – nền đen, chữ trắng'),
    ('#FFFFFF', 'Heading trắng trên nền ảnh tối'),
])
img.save(os.path.join(OUTPUT_DIR, 'annotated-01-homepage.png'), quality=90)
print('  Done')


# ════════════════════════════════════════════════════════════════
#  2. PRODUCT DETAIL - PRICES
# ════════════════════════════════════════════════════════════════
print('2/4 - Product detail...')
img = Image.open(os.path.join(SCREENSHOT_DIR, '07-chi-tiet-san-pham.png'))
draw = ImageDraw.Draw(img)

# 1 - Product title
draw_rect(draw, 1205, 190, 2450, 270, color=(0, 180, 255))
draw_tag(draw, 1, 2480, 230, color=(0, 180, 255))

# 2 - Star rating
draw_rect(draw, 1205, 280, 1440, 330, color=(255, 200, 0))
draw_tag(draw, 2, 1465, 305, color=(255, 200, 0))

# 3 - Old price (strikethrough)
draw_rect(draw, 1205, 360, 1440, 400, color=(150, 150, 150))
draw_tag(draw, 3, 1465, 380, color=(150, 150, 150))

# 4 - New price
draw_rect(draw, 1205, 405, 1520, 470, color=(0, 200, 100))
draw_tag(draw, 4, 1545, 435, color=(0, 200, 100))

# 5 - Badge -20%
draw_rect(draw, 1530, 405, 1650, 465, color=(255, 60, 60))
draw_tag(draw, 5, 1675, 435, color=(255, 60, 60))

# 6 - "Thêm vào giỏ" button
draw_rect(draw, 1485, 870, 1875, 940, color=(255, 255, 0))
draw_tag(draw, 6, 1910, 905, color=(255, 255, 0))

img = add_legend(img, [
    ('#020817', 'Tên sản phẩm – gần đen, font đậm'),
    ('#F59E0B', 'Đánh giá sao – vàng'),
    ('#525252', 'Giá cũ 239.000đ – XÁM, gạch ngang'),
    ('#020817', 'Giá mới 191.000đ – gần đen, font đậm'),
    ('#DC2626', 'Badge -20% – ĐỎ nổi bật'),
    ('#000000', 'Button "Thêm vào giỏ" – nền ĐEN, chữ trắng'),
])
img.save(os.path.join(OUTPUT_DIR, 'annotated-02-product-detail.png'), quality=90)
print('  Done')


# ════════════════════════════════════════════════════════════════
#  3. FOOTER
# ════════════════════════════════════════════════════════════════
print('3/4 - Footer...')
img = Image.open(os.path.join(SCREENSHOT_DIR, '04-footer.png'))
draw = ImageDraw.Draw(img)

# 1 - Dark bg
draw_tag(draw, 1, 60, 60, color=(100, 100, 255))

# 2 - White heading "COOLMATE lắng nghe bạn!"
draw_rect(draw, 30, 120, 750, 200, color=(0, 255, 200))
draw_tag(draw, 2, 780, 160, color=(0, 255, 200))

# 3 - White menu titles
draw_rect(draw, 30, 370, 230, 420, color=(255, 255, 100))
draw_tag(draw, 3, 260, 395, color=(255, 255, 100))

# 4 - Gray link text
draw_rect(draw, 30, 430, 340, 470, color=(180, 180, 180))
draw_tag(draw, 4, 370, 450, color=(180, 180, 180))

# 5 - Hotline white
draw_rect(draw, 1500, 130, 2460, 300, color=(0, 200, 100))
draw_tag(draw, 5, 2490, 210, color=(0, 200, 100))

img = add_legend(img, [
    ('#020817', 'Nền footer – gần đen'),
    ('#FFFFFF', 'Heading "COOLMATE lắng nghe bạn!" – trắng'),
    ('#FFFFFF', 'Tiêu đề danh mục – trắng, font đậm'),
    ('#D1D1D1', 'Link chi tiết – xám sáng'),
    ('#FFFFFF', 'Hotline + Email – trắng nổi bật'),
])
img.save(os.path.join(OUTPUT_DIR, 'annotated-03-footer.png'), quality=90)
print('  Done')


# ════════════════════════════════════════════════════════════════
#  4. PRODUCT SECTION
# ════════════════════════════════════════════════════════════════
print('4/4 - Product section...')
img = Image.open(os.path.join(SCREENSHOT_DIR, '03-section-san-pham.png'))
draw = ImageDraw.Draw(img)

# 1 - White nav bg
draw_rect(draw, 0, 0, img.width, 90, color=(0, 180, 255))
draw_tag(draw, 1, 2700, 45, color=(0, 180, 255))

# 2 - Red category section
draw_rect(draw, 0, 95, img.width, 560, color=(255, 60, 60))
draw_tag(draw, 2, 2700, 330, color=(255, 60, 60))

# 3 - Category label text
draw_rect(draw, 45, 455, 280, 515, color=(0, 200, 255))
draw_tag(draw, 3, 310, 485, color=(0, 200, 255))

# 4 - White bg section
draw_rect(draw, 0, 560, img.width, 850, color=(0, 255, 100))
draw_tag(draw, 4, 2700, 710, color=(0, 255, 100))

# 5 - "SHOP NOW" button
draw_rect(draw, 75, 1248, 350, 1315, color=(255, 255, 0))
draw_tag(draw, 5, 375, 1280, color=(255, 255, 0))

# 6 - "MEN WEAR" white heading
draw_rect(draw, 75, 1140, 520, 1230, color=(200, 130, 255))
draw_tag(draw, 6, 550, 1185, color=(200, 130, 255))

img = add_legend(img, [
    ('#FFFFFF', 'Navigation – nền trắng'),
    ('#B91C1C', 'Section danh mục – nền đỏ đậm'),
    ('#020817', 'Tên danh mục "ÁO KHOÁC" – gần đen'),
    ('#FFFFFF', 'Nền trắng – khoảng trắng giữa sections'),
    ('#000000', 'Button "SHOP NOW" – nền đen, chữ trắng'),
    ('#FFFFFF', '"MEN WEAR" – heading trắng trên ảnh tối'),
])
img.save(os.path.join(OUTPUT_DIR, 'annotated-04-section.png'), quality=90)
print('  Done')

print(f'\nAll done! Files in {OUTPUT_DIR}:')
for f in sorted(os.listdir(OUTPUT_DIR)):
    size_kb = os.path.getsize(os.path.join(OUTPUT_DIR, f)) // 1024
    print(f'  {f} ({size_kb} KB)')
