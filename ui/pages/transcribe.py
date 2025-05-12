import requests

from nicegui import ui
from pages.common import page_init, API_URL


def create() -> None:
    @ui.page("/transcribe")
    def transcribe(uuid: str) -> None:
        """
        Page to transcribe a file.
        """

        page_init()

        filename = uuid

        with ui.row().style("width: 100%;") as row:
            row.style("margin-left: 5%;")
            with ui.column().style("width: 50%;").classes("w-full no-shadow no-border"):
                ui.label("Transcription Settings").style("width: 100%;").classes(
                    "text-h6 q-mb-md text-primary"
                )

                with ui.row().classes(
                    "q-col-gutter-md items-end w-full no-shadow no-border"
                ).style("width: 100%;"):
                    # Language selection
                    with ui.column().classes("col-12 col-sm-6"):
                        ui.label("Language").classes("text-subtitle2 q-mb-sm")
                        language = ui.select(
                            ["Swedish", "English"],
                            label="Select language",
                        ).classes("w-full")

                    # Model selection
                    with ui.column().classes("col-12 col-sm-6"):
                        ui.label("Model").classes("text-subtitle2 q-mb-sm")
                        model = ui.select(
                            ["Tiny", "Base", "Large"],
                            label="Select model",
                        ).classes("w-full")

                    # Output format selection, SRT or text
                    with ui.column().classes("col-12 col-sm-6"):
                        ui.label("Output format").classes("text-subtitle2 q-mb-sm")
                        ui.select(
                            ["SRT", "Text"],
                            label="Select output format",
                        ).classes("w-full")

        with ui.column().style("width: 50%;") as row:
            row.style("margin-left: 5%;")
            ui.label("Advanced Settings").classes("text-h6 q-mb-md text-primary").style(
                "width: 100%;"
            )

            with ui.column().classes("col-12 col-sm-6"):
                ui.checkbox("Detect speaker changes").classes("q-mb-sm")
                ui.checkbox("Include timestamps").classes("q-mb-sm")

            with ui.column().classes("col-12 col-sm-6"):
                ui.checkbox("Filter background noise").classes("q-mb-sm")
                ui.checkbox("Auto-punctuate").classes("q-mb-sm")

        # Action buttons
        with ui.row().classes("q-mt-lg justify-between"):

            def start_transcription():
                # Get selected values
                selected_language = language.value
                selected_model = model.value

                match selected_language:
                    case "Swedish":
                        selected_language = "sv"
                    case "English":
                        selected_language = "en"
                    case _:
                        ui.notify(
                            "Error: Unsupported language",
                            type="negative",
                            position="top",
                        )
                        return

                match selected_model:
                    case "Tiny":
                        selected_model = "tiny"
                    case "Base":
                        selected_model = "base"
                    case "Large":
                        selected_model = "large"
                    case _:
                        ui.notify(
                            "Error: Unsupported model",
                            type="negative",
                            position="top",
                        )
                        return

                # Start the transcription job
                try:
                    response = requests.put(
                        f"{API_URL}/transcriber/{uuid}",
                        headers={"Content-Type": "application/json"},
                        json={
                            "language": f"{selected_language}",
                            "model": f"{selected_model}",
                            "status": "pending",
                        },
                    )

                    if response.status_code != 200:
                        error = response.json()["result"]["error"]
                        ui.notify(
                            f"Error: Failed to start transcription: {error}",
                            type="negative",
                            position="top",
                        )
                        return

                    ui.notify(
                        f"Transcription started for {filename}",
                        type="positive",
                        position="top",
                        icon="check_circle",
                    )
                    ui.navigate.to("/home")

                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative", position="top")

        # Status information
        with ui.row().classes("q-mt-md items-center justify-center"):
            ui.icon("info").classes("text-grey-6 q-mr-xs")
            ui.label(
                "Transcription will run in the background. You'll be notified when it's complete."
            ).classes("text-caption text-grey-7")

        with ui.left_drawer(fixed=True):
            ui.icon("record_voice_over").classes("text-primary text-h4 q-mr-md").style(
                "width: 48px; height: 48px;"
            )
            with ui.column():
                ui.label("Audio Transcription").classes(
                    "text-h5 text-weight-medium q-mb-none"
                )
                ui.label(f"Job UUID: {filename}").classes("text-caption text-grey")

            ui.separator()

            ui.button("Start Transcription", icon="play_circle_filled").classes(
                "w-full"
            ).on("click", start_transcription)
            ui.button(
                "Cancel transcription",
                icon="cancel",
            ).on(
                "click", lambda: ui.navigate.to("/home")
            ).classes("w-full")
