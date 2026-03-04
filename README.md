# coolmate-clone

Clone tĩnh coolmate.me — Phục vụ phân tích và cải thiện UI/UX.

## Cấu trúc

```
├── site/                    # 5 trang clone, mở offline trong browser
│   ├── index.html           # Trang chủ
│   ├── category.html        # Danh mục tổng quan /nam
│   ├── collection.html      # Bộ sưu tập thể thao (có filter/sort)
│   ├── product.html         # Chi tiết sản phẩm (có giá sale)
│   ├── cart.html            # Giỏ hàng + checkout
│   └── assets/
│       ├── css/
│       ├── fonts/
│       └── images/
│
├── report/                  # Báo cáo Word
│   ├── bao-cao-clean.docx
│   └── bao-cao-dembrandt.docx
│
├── screenshots/             # Ảnh chụp trang web
│   ├── originals/
│   └── annotated/
│
├── data/                    # Dữ liệu Dembrandt
│   └── dembrandt-coolmate.json
│
└── scripts/                 # Scripts tạo report, clone, annotate
```

## Cách xem

Mở `site/index.html` trong browser — 5 trang navigate qua lại, offline 100%.

## Routes

| Trang | File | URL gốc |
|-------|------|---------|
| Trang chủ | `site/index.html` | coolmate.me |
| Danh mục Nam | `site/category.html` | coolmate.me/nam |
| Bộ sưu tập Thể thao | `site/collection.html` | coolmate.me/collection/do-the-thao |
| Chi tiết sản phẩm | `site/product.html` | coolmate.me/ao-thun-chay-bo-viet-nam-tien-buoc |
| Giỏ hàng | `site/cart.html` | coolmate.me/cart |

## Đề xuất cải thiện

Xem `git diff` giữa commit "original" và "improved" để thấy thay đổi màu sắc.
