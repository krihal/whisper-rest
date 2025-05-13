from nicegui import ui
from pages.common import page_init, start_transcription


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
                    with ui.column().classes("col-12 col-sm-6"):
                        ui.label("Language").classes("text-subtitle2 q-mb-sm")
                        language = ui.select(
                            ["Swedish", "English"],
                            label="Select language",
                        ).classes("w-full")

                    with ui.column().classes("col-12 col-sm-6"):
                        ui.label("Model").classes("text-subtitle2 q-mb-sm")
                        model = ui.select(
                            ["Tiny", "Base", "Large"],
                            label="Select model",
                        ).classes("w-full")

                    with ui.column().classes("col-12 col-sm-6"):
                        ui.label("Output format").classes("text-subtitle2 q-mb-sm")
                        output_format = ui.select(
                            ["SRT", "TXT"],
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
            ).on(
                "click",
                lambda e: start_transcription(
                    uuid,
                    language.value,
                    model.value,
                    output_format.value,
                ),
            )
            ui.button(
                "Cancel transcription",
                icon="cancel",
            ).on(
                "click", lambda: ui.navigate.to("/home")
            ).classes("w-full")
