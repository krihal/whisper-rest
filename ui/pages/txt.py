import requests
from nicegui import ui, app
from pages.common import API_URL, page_init


def save_file(data: str) -> None:
    """
    Save the edited content to a file.
    """
    filename = ui.input("Enter filename").value
    if not filename:
        ui.notify("Filename cannot be empty")
        return

    with open(filename, "w") as f:
        f.write(data)
    ui.notify(f"File saved as {filename}")


# A simple text editor using ui.editor
def txt_editor(data):
    """
    Create a text editor with the given data.
    """
    editor = (
        ui.editor(
            value=data,
        )
        .style("width: 100%; height: calc(100vh - 100px); white-space: pre-wrap;")
        .classes("no-border no-shadow")
    )

    return editor


def create() -> None:
    @ui.page("/txt")
    def result(uuid: str, filename: str) -> None:
        """
        Display the result of the transcription job.
        """
        app.add_static_files(url_path="/static", local_directory="static/")
        response = requests.get(f"{API_URL}/transcriber/{uuid}/result")

        if response.status_code != 200:
            ui.notify("Error: Failed to get result")
            return

        data = response.content.decode("utf-8")

        page_init()
        txt_editor(data)

        with ui.left_drawer(fixed=True).style("background-color: white;"):
            with ui.row().classes("justify-end"):
                ui.button(
                    "Export",
                    icon="save",
                    color="primary",
                ).classes("w-full")
                ui.button(
                    "Revert",
                    icon="undo",
                    color="negative",
                ).classes("w-full")
