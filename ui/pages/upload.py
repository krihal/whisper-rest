import requests

from nicegui import ui
from pages.common import page_init, API_URL
from starlette.formparsers import MultiPartParser

MultiPartParser.spool_max_size = 1024 * 1024 * 500


def create() -> None:
    @ui.page("/upload")
    def upload() -> None:
        """
        Page to upload files for transcription.
        """

        page_init()

        with ui.card().style(
            "background-color: white; width: 100%; align-self: center; border: 0; height: calc(100vh - 130px);"
        ).classes("w-full no-shadow no-border"):

            async def handle_upload(file):
                files = {"file": (file.name, file.content.read())}
                response = requests.post(f"{API_URL}/transcriber", files=files)

                if response.status_code != 200:
                    ui.notify(f"Error: Failed to upload file {file.name}")
                    return

                # Also save the file to the server
                try:
                    with open(f"static/{file.name}", "wb") as f:
                        file.content.seek(0)
                        f.write(file.content.read())
                except Exception as e:
                    print(e)
                    ui.notify(f"Error: Failed to save file {file.name}: {e}")
                    return

                ui.notify(f"Uploaded: {file.name}")

            def after_upload(file):
                ui.navigate.to("/home")

            ui.upload(
                on_upload=handle_upload,
                on_multi_upload=after_upload,
                multiple=True,
                max_files=5,
                label="Upload file",
            ).classes("q-mt-md q-mb-md").style(
                "width: 75%; align-self: center; border-radius: 10px; height: 75%;"
            )

            ui.label(
                "You can upload multiple audio files at once. Supported formats: MP3, WAV, OGG, MP4 etc."
            ).classes("text-caption text-grey-6").style(
                "width: 50%; align-self: center; border-radius: 10px;"
            )

        with ui.left_drawer(fixed=True):
            ui.button(
                "Home",
                icon="home",
            ).on(
                "click", lambda: ui.navigate.to("/home")
            ).classes("w-full")
