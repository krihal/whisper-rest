import requests
import httpx
from nicegui import ui
from typing import Optional
from settings import get_settings

settings = get_settings()

API_URL = settings.API_URL
STATIC_FILES = settings.STATIC_FILES


def page_init(header_text: Optional[str] = "") -> None:
    """
    Initialize the page with a header and background color.
    """
    ui.add_head_html("<style>body {background-color: #ffffff;}</style>")

    if header_text:
        header_text = f" - {header_text}"

    with ui.header().style(
        "background-color: #77aadb; display: flex; justify-content: space-between; align-items: center;"
    ):
        ui.label("Sunet Transcriber" + header_text).classes("text-h5 text-white")

        with ui.element("div").style("display: flex; gap: 0px;"):
            ui.button(
                icon="home",
                on_click=lambda: ui.navigate.to("/home"),
            ).props("flat color=white")
            ui.button(
                icon="person",
                on_click=lambda: ui.navigate.to("/home"),
            ).props("flat color=white")
            ui.button(
                icon="help",
                on_click=lambda: ui.navigate.to("/home"),
            ).props("flat color=white")


def get_jobs():
    """
    Get the list of transcription jobs from the API.
    """
    jobs = []
    response = requests.get(f"{API_URL}/api/v1/transcriber")
    if response.status_code != 200:
        return []

    for idx, job in enumerate(response.json()["result"]["jobs"]):
        if job["status"] == "in_progress":
            job["status"] = "transcribing"

        if job["status"] != "completed":
            output_format = ""
        else:
            output_format = job["output_format"].upper()

        job_data = {
            "id": idx,
            "uuid": job["uuid"],
            "filename": job["filename"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "status": job["status"].capitalize(),
            "format": output_format,
        }

        jobs.append(job_data)

    # Sort jobs by created_at in descending order
    jobs.sort(key=lambda x: x["created_at"], reverse=True)

    return jobs


def table_click(event) -> None:
    """
    Handle the click event on the table rows.
    """

    status = event.args[1]["status"].lower()
    uuid = event.args[1]["uuid"]
    filename = event.args[1]["filename"]
    output_format = event.args[1]["format"]

    if status != "completed":
        return

    match output_format.lower():
        case "srt":
            ui.navigate.to(f"/srt?uuid={uuid}&filename={filename}")
        case "txt":
            ui.navigate.to(f"/txt?uuid={uuid}&filename={filename}")
        case _:
            ui.notify(
                "Error: Unsupported output format",
                type="negative",
                position="top",
            )


async def upload_file(files):
    try:
        for file, name in zip(files.contents, files.names):
            files_json = {"file": (name, file.read())}

            response = requests.post(f"{API_URL}/api/v1/transcriber", files=files_json)

            if response.status_code != 200:
                ui.notify(f"Error: Failed to upload file {name}")
                return

            ui.notify(f"Uploaded: {name}")
    except Exception as e:
        ui.notify(f"Error: Failed to save file {name}: {e}")
        return


def table_upload(table) -> None:
    """
    Handle the click event on the Upload button.
    """
    with ui.dialog() as dialog:
        ui.upload(
            on_multi_upload=lambda file: upload_file(file),
            multiple=True,
            max_files=5,
            label="Upload file",
        ).style("width: 100%; align-self: center; border-radius: 10px; height: 50%;")

        dialog.open()


def table_transcribe(table) -> None:
    """
    Handle the click event on the Transcribe button.
    """

    selected_rows = table.selected

    if not selected_rows:
        ui.notify("Error: No files selected", type="negative", position="top")
        return

    if not any(row["status"] == "Uploaded" for row in selected_rows):
        ui.notify(
            "Error: Selected files already transcribed",
            type="negative",
            position="top",
        )
        return

    with ui.dialog() as dialog:
        with ui.card().style(
            "background-color: white; align-self: center; border: 0;"
        ).classes("w-full no-shadow no-border"):
            with ui.row().classes("w-full"):
                ui.label("Transcription Settings").style("width: 100%;").classes(
                    "text-h6 q-mb-md text-primary"
                )

                with ui.column().classes("col-12 col-sm-24"):
                    ui.label("Language").classes("text-subtitle2 q-mb-sm")
                    language = ui.select(
                        ["Swedish", "English"],
                        label="Select language",
                    ).classes("w-full")

                with ui.column().classes("col-12 col-sm-24"):
                    ui.label("Model").classes("text-subtitle2 q-mb-sm")
                    model = ui.select(
                        ["Tiny", "Base", "Large"],
                        label="Select model",
                    ).classes("w-full")

                with ui.column().classes("col-12 col-sm-24"):
                    ui.label("Output format").classes("text-subtitle2 q-mb-sm")
                    output_format = ui.select(
                        ["SRT", "TXT"],
                        label="Select output format",
                    ).classes("w-full")
            ui.separator()
            with ui.row():
                ui.button(
                    "Start",
                    icon="play_circle_filled",
                    on_click=lambda: start_transcription(
                        selected_rows,
                        language.value,
                        model.value,
                        output_format.value,
                    ),
                ).props("color=primary")
                ui.button(
                    "Cancel",
                    icon="cancel",
                ).on("click", lambda: dialog.close())

        dialog.open()


def start_transcription(
    rows: list, language: str, model: str, output_format: str
) -> None:
    # Get selected values
    selected_language = language
    selected_model = model

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

    output_format = output_format.lower()

    # Start the transcription job
    try:
        for row in rows:
            uuid = row["uuid"]
            response = requests.put(
                f"{API_URL}/api/v1/transcriber/{uuid}",
                headers={"Content-Type": "application/json"},
                json={
                    "language": f"{selected_language}",
                    "model": f"{selected_model}",
                    "output_format": f"{output_format}",
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

    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative", position="top")
