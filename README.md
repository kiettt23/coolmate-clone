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

## Thay đổi so với web gốc

### Cart (`cart.html`)
- Thêm step indicator (Giỏ hàng → Thanh toán → Hoàn tất)
- Ẩn form checkout, thêm nút "Tiến hành thanh toán"
- Thêm cross-sell "Mua kèm giảm thêm 15%"
- Thêm trust badges (Đổi trả 60 ngày / Freeship / Thanh toán bảo mật)
- Ẩn tab COD + Voucher thừa, giới hạn cart max-width

### Category (`category.html`)
- Thêm wishlist heart icon cạnh tên sản phẩm

### Navbar (tất cả 5 trang)
- Thêm mega dropdown hover cho Nam, Nữ, Thể Thao, Phụ Kiện, Sale
- Thêm icon wishlist + search (kính lúp khi responsive)
- Di chuyển icon đăng nhập sang phải cart
- Fix responsive: nav links hiển thị mọi kích thước, logo thu nhỏ, badge -50% không chồng chữ

### Floating button (4 trang, trừ cart)
- Redesign: circle xanh Coolmate (#2F5ACF), icon chat minimalist
