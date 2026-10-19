from nicegui import ui
from components.navbar import render_navbar
from pages.home import render_home_page

ui.query('body').classes('bg-slate-50 min-h-screen text-slate-800')

@ui.page('/')
def index():
    render_navbar()
    render_home_page()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='EduFlash AI Client', port=8080, reload=True)
