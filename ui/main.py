from nicegui import ui
import requests

API_URL = "http://localhost:8000/api/v1"


def get_jobs():
    """
    Get the list of transcription jobs from the API.
    """
    jobs = []
    response = requests.get(f"{API_URL}/transcriber")
    if response.status_code != 200:
        return []

    idx = 0
    for job in response.json()["result"]["jobs"]:
        match job["status"]:
            case "pending":
                color = "text-yellow-6"
            case "completed":
                color = "text-green-6"
            case "failed":
                color = "text-red-6"
            case _:
                color = "text-grey-6"

        job_data = {
            "id": idx,
            "uuid": job["uuid"],
            "filename": job["filename"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "status": job["status"].capitalize().replace("_", " "),
            "classes": color,
        }

        jobs.append(job_data)
        idx += 1

    # Sort jobs by created_at in descending order
    jobs.sort(key=lambda x: x["created_at"], reverse=True)

    return jobs


def page_init():
    ui.add_head_html("<style>body {background-color: #f6f5f6; }</style>")

    # Header with slight shadow and nice background color
    with ui.header().classes("q-pa-md bg-white").style("width: 100%; height: 100px"):
        ui.label("SUNET Transcriber").classes("text-h4 q-my-md").style(
            "font-weight: bold; color: #333; font-family: 'Arial', sans-serif;"
        )


def table_click(event):
    """
    Handle the click event on the table rows.
    """
    status = event.args[1]["status"]
    uuid = event.args[1]["uuid"]

    match status.lower():
        case "completed":
            ui.navigate.to(f"/result?uuid={uuid}")
        case _:
            ui.navigate.to(f"/transcribe?uuid={uuid}")


@ui.page("/result")
def result(uuid):
    page_init()

    # Get the filename for display
    response = requests.get(f"{API_URL}/transcriber/{uuid}/result")

    if response.status_code != 200:
        ui.notify("Error: Failed to get result")
        return

    with ui.card().style(
        "background-color: white; width: 100%; align-self: center; border-radius: 10px; height: 100%;"
    ):

        def download():
            ui.notify("Downloaded result.txt")

        ui.button("Download Result", icon="download").on_click(download)

        with ui.editor().classes("col").style(
            "width: 100%; height: 400px; border-radius: 10px;"
        ) as editor:
            editor.value = response.content.decode()


@ui.refreshable
def table_jobs():
    columns = [
        {
            "name": "filename",
            "label": "Filename",
            "field": "filename",
            "align": "left",
        },
        {
            "name": "created_at",
            "label": "Created At",
            "field": "created_at",
            "align": "left",
        },
        {
            "name": "created_at",
            "label": "Updated At",
            "field": "updated_at",
            "align": "left",
        },
        {
            "name": "status",
            "label": "Status",
            "field": "status",
            "align": "left",
            ":classes": "(row) => row.classes",
        },
    ]

    table = ui.table(
        columns=columns,
        rows=get_jobs(),
        selection="none",
        pagination=20,
    )
    table.style("width: 100%; border-radius: 10px; height: 100%;")
    table.on("rowClick", table_click)
    table.style("height: calc(100vh - 120px);")

    with table.add_slot("top-left"):
        ui.label("My files").classes("text-h5 q-my-md")
    with table.add_slot("top-right"):
        with ui.row().classes("items-center gap-8"):
            with ui.button("Upload").props("color=primary").on(
                "click", lambda: ui.navigate.to("/upload")
            ):
                ui.icon("upload")
            with ui.input(placeholder="Search").props("type=search").bind_value(
                table, "filter"
            ).add_slot("append"):
                ui.icon("search")


@ui.page("/transcribe")
def transcribe(uuid):
    page_init()

    # Get the filename for display
    filename = uuid

    with ui.card().style(
        "background-color: white; width: 100%; align-self: center; border-radius: 10px; height: 100%;"
    ) as card:
        # Make the card fill the height of the page
        card.style("height: calc(100vh - 120px);")

        # Header with icon
        with ui.row().classes("items-center q-mb-lg"):
            ui.icon("record_voice_over").classes("text-primary text-h4 q-mr-md").style(
                "width: 48px; height: 48px;"
            )
            with ui.column().classes("col"):
                ui.label("Audio Transcription").classes(
                    "text-h5 text-weight-medium q-mb-none"
                )
                ui.label(f"Job UUID: {filename}").classes("text-caption text-grey")

        # Divider
        ui.separator().classes("q-my-md")

        # Settings area
        with ui.card().classes("q-pa-md bg-grey-1").style("width: 100%;"):
            ui.label("Transcription Settings").classes(
                "text-h6 q-mb-md text-primary"
            ).style("width: 100%;")

            with ui.row().classes("q-col-gutter-md items-end").style("width: 100%;"):
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

        # Options area
        with ui.expansion("Advanced Options", icon="settings").classes("q-mt-md"):
            with ui.row().classes("q-col-gutter-md q-mt-sm"):
                with ui.column().classes("col-12 col-sm-6"):
                    ui.checkbox("Detect speaker changes").classes("q-mb-sm")
                    ui.checkbox("Include timestamps").classes("q-mb-sm")

                with ui.column().classes("col-12 col-sm-6"):
                    ui.checkbox("Filter background noise").classes("q-mb-sm")
                    ui.checkbox("Auto-punctuate").classes("q-mb-sm")

        # Action buttons
        with ui.row().classes("q-mt-lg justify-between"):

            def cancel_transcription():
                ui.navigate.to("/")

            ui.button("Cancel", icon="close", on_click=cancel_transcription).props(
                "flat"
            ).classes("text-grey-8")

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
                    ui.navigate.to("/")

                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative", position="top")

            ui.button("Start Transcription", icon="play_circle_filled").props(
                "color=primary"
            ).on("click", start_transcription)

        # Status information
        with ui.row().classes("q-mt-md items-center justify-center"):
            ui.icon("info").classes("text-grey-6 q-mr-xs")
            ui.label(
                "Transcription will run in the background. You'll be notified when it's complete."
            ).classes("text-caption text-grey-7")


@ui.page("/upload")
def upload():
    page_init()

    # A box with white background
    with ui.card().style(
        "background-color: white; width: 100%; align-self: center; border-radius: 10px; height: 100%;"
    ) as card:
        # Make the card fill the height of the page
        card.style("height: calc(100vh - 120px);")
        ui.label("Upload files").classes("text-h5 q-my-md")

        def handle_upload(file):
            # Upload the file to the API
            files = {"file": (file.name, file.content.read())}
            response = requests.post(f"{API_URL}/transcriber", files=files)

            if response.status_code != 200:
                ui.notify(f"Error: Failed to upload file {file.name}")
                return

            ui.notify(f"Uploaded: {file.name}")

        def after_upload(file):
            ui.navigate.to("/")

        ui.upload(
            on_upload=handle_upload,
            on_multi_upload=after_upload,
            multiple=True,
            max_files=5,
            label="Upload file",
        ).classes("q-mt-md q-mb-md").style(
            "width: 50%; align-self: center; border-radius: 10px;"
        )

        # Create help text for the upload box
        ui.label(
            "You can upload multiple audio files at once. Supported formats: MP3, WAV, OGG, MP4 etc."
        ).classes("text-caption text-grey-6").style(
            "width: 50%; align-self: center; border-radius: 10px;"
        )


@ui.page("/")
def index():
    page_init()
    table_jobs()

    ui.timer(5.0, table_jobs.refresh)


ui.run(storage_secret="secret", title="SUNET Transcriber", port=8080)
