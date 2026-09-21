from typing import Any, Dict
import reflex as rx
from state.cart_state import CartState


def format_currency_vnd(amount: Any) -> Any:
    """Định dạng tiền tệ chuẩn Việt Nam Đồng (VND). Hỗ trợ cả số thực và Reflex Var."""
    if isinstance(amount, (int, float)):
        return f"{amount:,.0f} đ".replace(",", ".")
    if isinstance(amount, rx.Var):
        return amount.to(str) + " đ"
    try:
        val = float(amount)
        return f"{val:,.0f} đ".replace(",", ".")
    except Exception:
        return rx.cond(
            amount != "",
            amount.to(str) + " đ",
            "0 đ",
        )


def product_card(product: Any, record_id: str = "") -> rx.Component:
    """Card hiển thị sản phẩm E-Commerce hiện đại theo phong cách Apple / Shopee Mall."""
    product_id = product["id"]
    image_src = rx.cond(
        (product["image_url"] != "") & (product["image_url"] != None),
        product["image_url"],
        "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&auto=format&fit=crop&q=80",
    )
    is_in_stock = rx.cond(
        product["is_in_stock"] != None,
        product["is_in_stock"],
        product["is_available"] & (product["stock_quantity"].to(int) > 0),
    )
    tag_name = rx.cond(
        product["class_name"] != "",
        product["class_name"],
        product["category_name"],
    )

    return rx.card(
        rx.vstack(
            # Khung chứa hình ảnh & Badge nhãn AI
            rx.box(
                rx.image(
                    src=image_src,
                    alt=product["name"],
                    width="100%",
                    height="210px",
                    object_fit="cover",
                    border_radius="10px",
                    transition="transform 0.3s ease",
                    _hover={"transform": "scale(1.04)"},
                ),
                rx.cond(
                    tag_name != "",
                    rx.badge(
                        "#",
                        tag_name,
                        color_scheme="violet",
                        variant="solid",
                        radius="full",
                        position="absolute",
                        top="10px",
                        left="10px",
                        box_shadow="0 2px 8px rgba(109, 40, 217, 0.3)",
                    ),
                ),
                rx.badge(
                    rx.cond(is_in_stock, "Còn hàng", "Hết hàng"),
                    color_scheme=rx.cond(is_in_stock, "grass", "ruby"),
                    variant="surface",
                    radius="full",
                    position="absolute",
                    top="10px",
                    right="10px",
                    size="1",
                ),
                position="relative",
                width="100%",
                overflow="hidden",
                border_radius="10px",
            ),

            # Nội dung chi tiết sản phẩm
            rx.vstack(
                rx.heading(
                    product["name"],
                    size="3",
                    weight="bold",
                    truncate=True,
                    width="100%",
                ),
                rx.text(
                    rx.cond(
                        product["description"] != "",
                        product["description"],
                        "Sản phẩm chính hãng tích hợp nhận diện qua mô hình thị giác máy tính.",
                    ),
                    size="1",
                    color="gray",
                    line_clamp=2,
                    min_height="32px",
                ),
                rx.separator(width="100%"),

                # Giá bán và nút Thêm vào giỏ hàng
                rx.hstack(
                    rx.vstack(
                        rx.text("Giá niêm yết", size="1", color="gray"),
                        rx.text(
                            rx.cond(
                                product["formatted_price"] != "",
                                product["formatted_price"],
                                product["price"].to(str) + " đ",
                            ),
                            size="4",
                            weight="bold",
                            color="var(--accent-9)",
                        ),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon("shopping-bag", size=16),
                            rx.text("Thêm giỏ", size="2", weight="medium"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=CartState.add_to_cart(product_id, record_id),
                        disabled=~is_in_stock,
                        size="2",
                        color_scheme="indigo",
                        variant="solid",
                        radius="large",
                        cursor="pointer",
                        _hover={"transform": "translateY(-1px)", "box_shadow": "0 4px 12px rgba(99, 102, 241, 0.35)"},
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="2",
                width="100%",
                padding_top="0.25rem",
            ),
            width="100%",
            spacing="3",
        ),
        width="100%",
        max_width="290px",
        padding="0.85rem",
        border_radius="14px",
        border="1px solid var(--gray-4)",
        background_color="var(--color-surface)",
        box_shadow="0 4px 16px rgba(0, 0, 0, 0.04)",
        transition="all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
        _hover={
            "transform": "translateY(-4px)",
            "box_shadow": "0 12px 28px rgba(0, 0, 0, 0.09)",
            "border_color": "var(--accent-7)",
        },
    )
