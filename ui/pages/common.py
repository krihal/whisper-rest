from nicegui import ui
from typing import Optional

API_URL = "http://localhost:8000/api/v1"


def page_init(header_text: Optional[str] = "") -> None:
    """
    Initialize the page with a header and background color.
    """
    ui.add_head_html("<style>body {background-color: #ffffff;}</style>")

    if header_text:
        header_text = f" - {header_text}"

    with ui.header():
        ui.label(f"Sunet Transcriber{header_text}").classes(
            "text-h5 text-weight-medium q-mb-none"
        ).on("click", lambda: ui.navigate.to("/home"))
