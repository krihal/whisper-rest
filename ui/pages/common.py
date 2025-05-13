import requests
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


def get_jobs():
    """
    Get the list of transcription jobs from the API.
    """
    jobs = []
    response = requests.get(f"{API_URL}/transcriber")
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
        ui.navigate.to(f"/transcribe?uuid={uuid}")
    else:
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


def start_transcription(
    uuid: str, language: str, model: str, output_format: str
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
        response = requests.put(
            f"{API_URL}/transcriber/{uuid}",
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

        ui.navigate.to("/home")

    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative", position="top")
