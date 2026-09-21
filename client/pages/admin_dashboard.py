import reflex as rx
from components.product_card import format_currency_vnd
from layouts.base_layout import base_layout
from state.product_state import ProductState


def stat_card(title: str, value: rx.Var, icon_name: str, color_scheme: str) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(title, size="1", color="gray"),
                rx.heading(value, size="5", weight="bold"),
                spacing="1",
            ),
            rx.spacer(),
            rx.icon(icon_name, size=24, color=f"var(--{color_scheme}-9)"),
            align="center",
            width="100%",
        ),
        width="100%",
        size="2",
    )


def admin_dashboard_page() -> rx.Component:
    """Administrator control panel for inventory metrics, stock adjustments, and product monitoring."""
    dashboard_content = rx.vstack(
        # Page Title
        rx.hstack(
            rx.vstack(
                rx.heading("Quản Trị Kho & Bán Hàng", size="6", weight="bold"),
                rx.text("Giám sát sản phẩm, trạng thái tồn kho và tích hợp thị giác máy tính", size="2", color="gray"),
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon("refresh-cw", size=16),
                    rx.text("Làm mới dữ liệu"),
                    align="center",
                    spacing="2",
                ),
                variant="outline",
                on_click=ProductState.reload_catalog,
                size="2",
            ),
            width="100%",
            align="center",
            padding_bottom="1.5rem",
        ),

        # Metrics Overview Row
        rx.grid(
            stat_card("Tổng sản phẩm", ProductState.stats["total_products"].to(str), "boxes", "indigo"),
            stat_card("Đang mở bán", ProductState.stats["available_products"].to(str), "circle-check", "green"),
            stat_card("Hết hàng", ProductState.stats["out_of_stock_products"].to(str), "triangle-alert", "red"),
            stat_card("Tổng số lượng tồn", ProductState.stats["total_stock_units"].to(str), "layers", "blue"),
            columns="4",
            spacing="4",
            width="100%",
        ),

        rx.separator(width="100%"),

        # Inventory Table
        rx.vstack(
            rx.heading("Danh Sách Sản Phẩm & Điều Chỉnh Tồn Kho", size="4", weight="bold"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Hình ảnh"),
                        rx.table.column_header_cell("Tên sản phẩm"),
                        rx.table.column_header_cell("Nhãn YOLO"),
                        rx.table.column_header_cell("Giá niêm yết"),
                        rx.table.column_header_cell("Số lượng kho"),
                        rx.table.column_header_cell("Thao tác kho nhanh"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProductState.products,
                        lambda item: rx.table.row(
                            rx.table.cell(
                                rx.image(
                                    src=rx.cond(
                                        item["image_url"] != "",
                                        item["image_url"],
                                        "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=100",
                                    ),
                                    fallback="https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=100",
                                    width="40px",
                                    height="40px",
                                    object_fit="cover",
                                    border_radius="4px",
                                )
                            ),
                            rx.table.cell(rx.text(item["name"], weight="medium")),
                            rx.table.cell(
                                rx.cond(
                                    item["class_name"] != "",
                                    rx.badge(item["class_name"], color_scheme="violet"),
                                    rx.text("-", color="gray"),
                                )
                            ),
                            rx.table.cell(
                                rx.text(
                                    rx.cond(
                                        item["formatted_price"] != "",
                                        item["formatted_price"],
                                        item["price"].to(str) + " đ",
                                    )
                                )
                            ),
                            rx.table.cell(
                                rx.badge(
                                    item["stock_quantity"],
                                    color_scheme=rx.cond(item["stock_quantity"].to(int) > 0, "green", "red"),
                                    variant="surface",
                                )
                            ),
                            rx.table.cell(
                                rx.hstack(
                                    rx.button(
                                        "-5",
                                        size="1",
                                        variant="soft",
                                        color_scheme="gray",
                                        on_click=ProductState.update_stock(item["id"], -5, "increment"),
                                    ),
                                    rx.button(
                                        "+5",
                                        size="1",
                                        variant="soft",
                                        color_scheme="indigo",
                                        on_click=ProductState.update_stock(item["id"], 5, "increment"),
                                    ),
                                    spacing="1",
                                )
                            ),
                        ),
                    )
                ),
                width="100%",
                variant="surface",
            ),
            width="100%",
            spacing="3",
        ),
        max_width="1200px",
        margin_x="auto",
        padding_x="1.5rem",
        padding_y="2.5rem",
        width="100%",
        spacing="5",
        on_mount=ProductState.reload_catalog,
    )

    return base_layout(dashboard_content, role_required="admin")

