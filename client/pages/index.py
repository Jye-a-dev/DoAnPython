import reflex as rx
from components.product_card import product_card
from layouts.base_layout import base_layout
from state.detect_state import DetectState
from state.product_state import ProductState


def hero_section() -> rx.Component:
    """Hero Section chuẩn Apple / Vercel: Headline lớn, Subheadline, 2 CTAs và Mockup Visual Pipeline."""
    return rx.box(
        rx.vstack(
            # Badge giới thiệu tính năng AI
            rx.box(
                rx.hstack(
                    rx.icon("sparkles", size=16, color="var(--accent-9)"),
                    rx.text("AI-First Visual Search & Neural Voice Assistant", size="2", weight="bold", color="var(--accent-11)"),
                    align="center",
                    spacing="2",
                ),
                padding_x="1rem",
                padding_y="0.35rem",
                border_radius="full",
                border="1px solid var(--accent-6)",
                background_color="var(--accent-2)",
            ),

            # Tiêu đề lớn & Phụ đề
            rx.heading(
                "Mua sắm thông minh với Trợ lý Thị giác AI",
                size="9",
                weight="bold",
                letter_spacing="-0.03em",
                text_align="center",
                max_width="820px",
                line_height="1.15",
            ),
            rx.text(
                "Chỉ cần chụp hoặc tải ảnh món đồ bạn muốn mua. AI sẽ tự động phân loại, tìm kiếm sản phẩm tương ứng và đọc thông tin bằng giọng nói tự nhiên.",
                size="4",
                color="gray",
                text_align="center",
                max_width="660px",
                line_height="1.6",
            ),

            # 2 nút Call To Action (CTA)
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("camera", size=20),
                        rx.text("Chụp ảnh / Quét vật thể ngay", size="3", weight="bold"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=DetectState.open_modal,
                    size="4",
                    radius="large",
                    color_scheme="indigo",
                    box_shadow="0 8px 24px rgba(99, 102, 241, 0.4)",
                    cursor="pointer",
                    _hover={"transform": "translateY(-2px)", "box_shadow": "0 12px 28px rgba(99, 102, 241, 0.55)"},
                ),
                rx.link(
                    rx.button(
                        rx.hstack(
                            rx.icon("compass", size=20),
                            rx.text("Khám phá danh mục", size="3", weight="medium"),
                            align="center",
                            spacing="2",
                        ),
                        size="4",
                        radius="large",
                        variant="surface",
                        color_scheme="gray",
                    ),
                    href="#catalog-section",
                    underline="none",
                ),
                spacing="3",
                padding_top="1rem",
                wrap="wrap",
                justify="center",
            ),

            # Mockup minh họa luồng: Ảnh chụp -> Khung nhận diện Bounding Box -> Card sản phẩm
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.badge("Luồng xử lý thời gian thực", color_scheme="indigo", variant="surface", size="1"),
                        rx.spacer(),
                        rx.hstack(
                            rx.box(width="8px", height="8px", border_radius="full", background_color="#ef4444"),
                            rx.box(width="8px", height="8px", border_radius="full", background_color="#eab308"),
                            rx.box(width="8px", height="8px", border_radius="full", background_color="#22c55e"),
                            spacing="1",
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.grid(
                        # Bước 1: Ảnh chụp thực tế
                        rx.vstack(
                            rx.box(
                                rx.image(
                                    src="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop&q=80",
                                    height="150px",
                                    width="100%",
                                    object_fit="cover",
                                    border_radius="8px",
                                ),
                                rx.badge("1. Ảnh chụp thực tế", color_scheme="gray", variant="solid", position="absolute", bottom="8px", left="8px"),
                                position="relative",
                                width="100%",
                            ),
                            rx.text("Camera thiết bị gửi stream ảnh gốc lên API", size="1", color="gray", text_align="center"),
                            spacing="1",
                            align="center",
                        ),

                        # Bước 2: Bounding Box & AI Audio
                        rx.vstack(
                            rx.box(
                                rx.image(
                                    src="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop&q=80",
                                    height="150px",
                                    width="100%",
                                    object_fit="cover",
                                    border_radius="8px",
                                    filter="brightness(0.9)",
                                ),
                                rx.box(
                                    border="2px solid #a855f7",
                                    background_color="rgba(168, 85, 247, 0.15)",
                                    position="absolute",
                                    top="15%",
                                    left="15%",
                                    width="70%",
                                    height="70%",
                                    border_radius="6px",
                                ),
                                rx.badge("2. YOLOv8: #laptop (0.95)", color_scheme="violet", variant="solid", position="absolute", top="20%", left="18%", size="1"),
                                position="relative",
                                width="100%",
                            ),
                            rx.text("Trích xuất nhãn & tổng hợp giọng nói Edge-TTS", size="1", color="gray", text_align="center"),
                            spacing="1",
                            align="center",
                        ),

                        # Bước 3: Card sản phẩm trong shop
                        rx.vstack(
                            rx.box(
                                rx.image(
                                    src="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop&q=80",
                                    height="150px",
                                    width="100%",
                                    object_fit="cover",
                                    border_radius="8px",
                                ),
                                rx.badge("3. Khớp 100% trong Kho", color_scheme="grass", variant="solid", position="absolute", bottom="8px", left="8px"),
                                position="relative",
                                width="100%",
                            ),
                            rx.text("Tự động gợi ý sản phẩm khớp nhãn và thêm giỏ hàng", size="1", color="gray", text_align="center"),
                            spacing="1",
                            align="center",
                        ),
                        columns=rx.breakpoints(initial="1", sm="3", md="3"),
                        spacing="4",
                        width="100%",
                        padding_y="0.5rem",
                    ),
                    width="100%",
                    spacing="3",
                ),
                max_width="880px",
                width="100%",
                padding="1.25rem",
                border_radius="18px",
                border="1px solid var(--gray-5)",
                background_color="var(--color-surface)",
                box_shadow="0 20px 40px rgba(0,0,0,0.06)",
                margin_top="2rem",
            ),
            align="center",
            spacing="4",
            padding_y=["2.5rem", "4rem", "5rem"],
            padding_x="1rem",
        ),
        background="radial-gradient(ellipse 80% 50% at 50% -10%, var(--accent-3), transparent)",
        width="100%",
    )


def featured_categories_section() -> rx.Component:
    """Featured Categories Section: Hiển thị các danh mục dạng Grid Card trực quan."""
    categories_data = [
        {"name": "Thiết bị điện tử", "icon": "laptop", "tag": "laptop", "desc": "Máy tính, tablet, điện thoại thông minh"},
        {"name": "Đồ uống & Thực phẩm", "icon": "coffee", "tag": "bottle", "desc": "Nước ngọt, cà phê, thực phẩm đóng hộp"},
        {"name": "Thời trang & Phụ kiện", "icon": "shirt", "tag": "backpack", "desc": "Balo, túi xách, trang phục cá tính"},
        {"name": "Văn phòng phẩm", "icon": "book-open", "tag": "book", "desc": "Sổ tay, bút viết, sách tham khảo"},
    ]

    return rx.vstack(
        rx.vstack(
            rx.badge("Danh mục nổi bật", color_scheme="indigo", variant="surface", size="2"),
            rx.heading("Khám Phá Danh Mục Đa Dạng", size="6", weight="bold"),
            rx.text("Lựa chọn các nhóm sản phẩm được hỗ trợ nhận diện thị giác tốt nhất", size="2", color="gray"),
            align="center",
            spacing="1",
            text_align="center",
            width="100%",
        ),
        rx.grid(
            *[
                rx.card(
                    rx.hstack(
                        rx.box(
                            rx.icon(cat["icon"], size=28, color="var(--accent-9)"),
                            background_color="var(--accent-3)",
                            padding="12px",
                            border_radius="12px",
                        ),
                        rx.vstack(
                            rx.heading(cat["name"], size="3", weight="bold"),
                            rx.text(cat["desc"], size="1", color="gray"),
                            rx.badge(f"Nhãn AI: #{cat['tag']}", color_scheme="violet", variant="soft", size="1"),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    on_click=ProductState.select_category(cat["tag"]),
                    cursor="pointer",
                    padding="1.25rem",
                    border_radius="14px",
                    border="1px solid var(--gray-4)",
                    transition="all 0.2s ease",
                    _hover={"transform": "translateY(-3px)", "border_color": "var(--accent-8)", "box_shadow": "0 8px 20px rgba(0,0,0,0.06)"},
                )
                for cat in categories_data
            ],
            columns=rx.breakpoints(initial="1", sm="2", md="4"),
            spacing="4",
            width="100%",
        ),
        id="category-section",
        max_width="1200px",
        margin_x="auto",
        padding_x=["1rem", "1.5rem", "2rem"],
        padding_y="3.5rem",
        spacing="5",
        width="100%",
    )


def why_choose_us_section() -> rx.Component:
    """Why Choose Us Section: 3 Card giới thiệu giá trị cốt lõi của giải pháp AI E-Commerce."""
    features = [
        {
            "icon": "zap",
            "title": "Thị giác máy tính tức thì",
            "desc": "Pipeline YOLOv8 phân tích và phân loại vật thể trong chưa đầy 1 giây với độ chính xác cao.",
            "badge": "< 1s Latency",
            "color": "amber",
        },
        {
            "icon": "volume-2",
            "title": "Xác nhận bằng giọng nói",
            "desc": "Tự động phát âm thanh tóm tắt giỏ hàng và chốt đơn tự nhiên qua công nghệ Edge-TTS mượt mà.",
            "badge": "Neural Speech",
            "color": "indigo",
        },
        {
            "icon": "shopping-bag",
            "title": "Mua sắm một chạm",
            "desc": "Tự động đối chiếu ảnh chụp đời thực với toàn bộ cơ sở dữ liệu hàng hóa có sẵn trong kho.",
            "badge": "Visual Search",
            "color": "grass",
        },
    ]

    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.badge("Công nghệ tiên phong", color_scheme="indigo", variant="surface", size="2"),
                rx.heading("Tại Sao Chọn VisionStore AI?", size="6", weight="bold"),
                rx.text("Kết hợp sức mạnh Computer Vision và Voice Assistant trong một trải nghiệm duy nhất", size="2", color="gray"),
                align="center",
                spacing="1",
                text_align="center",
                width="100%",
            ),
            rx.grid(
                *[
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.box(
                                    rx.icon(f["icon"], size=24, color=f"var(--{f['color']}-9)"),
                                    background_color=f"var(--{f['color']}-3)",
                                    padding="10px",
                                    border_radius="10px",
                                ),
                                rx.spacer(),
                                rx.badge(f["badge"], color_scheme=f["color"], variant="surface", size="1", radius="full"),
                                width="100%",
                                align="center",
                            ),
                            rx.heading(f["title"], size="3", weight="bold"),
                            rx.text(f["desc"], size="2", color="gray", line_height="1.5"),
                            spacing="3",
                            align="start",
                        ),
                        padding="1.5rem",
                        border_radius="16px",
                        border="1px solid var(--gray-4)",
                        background_color="var(--color-surface)",
                    )
                    for f in features
                ],
                columns=rx.breakpoints(initial="1", sm="3", md="3"),
                spacing="4",
                width="100%",
            ),
            max_width="1200px",
            margin_x="auto",
            padding_x=["1rem", "1.5rem", "2rem"],
            padding_y="4rem",
            spacing="5",
            width="100%",
        ),
        background_color="var(--gray-2)",
        width="100%",
        id="features-section",
    )


def trending_products_section() -> rx.Component:
    """Trending Products Grid: Danh sách sản phẩm dạng Grid (3-4 cột) với bộ lọc danh mục."""
    return rx.vstack(
        # Tiêu đề & thanh phân loại
        rx.hstack(
            rx.vstack(
                rx.badge("Bộ sưu tập thịnh hành", color_scheme="indigo", variant="surface", size="1"),
                rx.heading("Sản Phẩm Được Mua Nhiều Nhất", size="6", weight="bold"),
                rx.text("Tất cả sản phẩm đã được gắn nhãn AI và sẵn sàng tìm kiếm bằng hình ảnh", size="2", color="gray"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            # Nút filter danh mục
            rx.hstack(
                rx.button(
                    "Tất cả",
                    variant=rx.cond(ProductState.selected_category == "", "solid", "surface"),
                    color_scheme="indigo",
                    size="2",
                    radius="large",
                    on_click=ProductState.select_category(""),
                ),
                rx.foreach(
                    ProductState.categories,
                    lambda cat: rx.button(
                        cat.get("name", ""),
                        variant=rx.cond(ProductState.selected_category == cat.get("id"), "solid", "surface"),
                        color_scheme="indigo",
                        size="2",
                        radius="large",
                        on_click=ProductState.select_category(cat.get("id")),
                    ),
                ),
                wrap="wrap",
                spacing="2",
            ),
            width="100%",
            align="end",
            wrap="wrap",
            spacing="3",
            padding_bottom="1.5rem",
        ),

        # Grid sản phẩm thịnh hành
        rx.cond(
            ProductState.is_loading_products,
            rx.center(
                rx.spinner(size="3", color="var(--accent-9)"),
                width="100%",
                padding="4rem",
            ),
            rx.cond(
                ProductState.products.length() > 0,
                rx.grid(
                    rx.foreach(
                        ProductState.products,
                        lambda p: product_card(p),
                    ),
                    columns=rx.breakpoints(initial="1", sm="2", md="3", lg="4"),
                    spacing="4",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("package-open", size=48, color="gray"),
                        rx.text("Không có sản phẩm nào phù hợp với bộ lọc.", color="gray"),
                        align="center",
                        spacing="2",
                        padding="4rem",
                    ),
                    width="100%",
                ),
            ),
        ),
        id="catalog-section",
        max_width="1200px",
        margin_x="auto",
        padding_x=["1rem", "1.5rem", "2rem"],
        padding_y="3.5rem",
        spacing="4",
        width="100%",
        on_mount=ProductState.on_mount,
    )


def index() -> rx.Component:
    """Trang chủ E-Commerce hoàn chỉnh tích hợp Apple-style Hero, Visual Search và Voice Assistant."""
    page_content = rx.box(
        hero_section(),
        featured_categories_section(),
        trending_products_section(),
        why_choose_us_section(),
        width="100%",
    )
    return base_layout(page_content)
