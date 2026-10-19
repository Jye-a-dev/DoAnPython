from nicegui import ui

def render_navbar():
    with ui.header().classes('bg-slate-900 text-white flex justify-between items-center px-8 py-4 shadow-md'):
        ui.label('EduFlash AI').classes('text-2xl font-black text-indigo-400')
        with ui.row().classes('gap-4'):
            ui.link('Trang chủ', '/').classes('text-gray-300 hover:text-white')
