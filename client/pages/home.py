from nicegui import ui
from services.api import generate_flashcards


def render_home_page():
    with ui.column().classes(
        "w-full max-w-2xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-md"
    ):
        ui.label("Tạo Thẻ Học").classes("text-2xl font-bold text-gray-800")
        text_input = ui.textarea(placeholder="Dán bài học vào đây...").classes(
            "w-full border p-2 rounded-lg mt-2"
        )

        async def on_submit():
            content = text_input.value.strip()
            if not content:
                ui.notify("Vui lòng nhập nội dung bài học", color="warning")
                return
            result = await generate_flashcards(content)
            if isinstance(result, dict) and result.get("error"):
                ui.notify(
                    result.get("message", "Có lỗi xảy ra khi tạo thẻ"), color="negative"
                )
            elif isinstance(result, list):
                ui.notify(f"Tạo thành công {len(result)} thẻ!", color="positive")
            else:
                ui.notify("Tạo thành công thẻ học!", color="positive")

        ui.button("Gửi đến Server", on_click=on_submit).classes(
            "mt-4 bg-indigo-600 text-white px-4 py-2 rounded-lg"
        )
