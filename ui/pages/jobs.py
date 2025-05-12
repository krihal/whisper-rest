import requests

from nicegui import ui
from pages.common import page_init, API_URL


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
            job["status"] = "started"
        job_data = {
            "id": idx,
            "uuid": job["uuid"],
            "filename": job["filename"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "status": job["status"].capitalize(),
        }

        jobs.append(job_data)

    # Sort jobs by created_at in descending order
    jobs.sort(key=lambda x: x["created_at"], reverse=True)

    return jobs


def table_click(event) -> None:
    """
    Handle the click event on the table rows.
    """
    status = event.args[1]["status"]
    uuid = event.args[1]["uuid"]
    filename = event.args[1]["filename"]

    match status.lower():
        case "completed":
            ui.navigate.to(f"/result?uuid={uuid}&filename={filename}")
        case _:
            ui.navigate.to(f"/transcribe?uuid={uuid}")


@ui.refreshable
def table_jobs() -> None:
    """
    Create a table to display the transcription jobs.
    """
    global rows

    columns = [
        {
            "name": "filename",
            "label": "Filename",
            "field": "filename",
            "align": "left",
            "classes": "text-weight-medium",
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
        },
    ]

    table = (
        ui.table(
            columns=columns,
            rows=rows,
            selection="none",
            pagination=10,
        )
        .style("width: 100%; height: calc(100vh - 130px); overflow: auto; ")
        .on("rowClick", table_click)
        # Larger font size
        .classes("text-h2")
    )

    table.add_slot(
        "body-cell-status",
        """
        <q-td key="status" :props="props">
            <q-badge v-if="{Completed: 'green', Uploaded: 'orange', Failed: 'red', Started: 'orange', Pending: 'blue'}[props.value]" :color="{Completed: 'green', Uploaded: 'orange', Failed: 'red', Started: 'orange', Pending: 'blue'}[props.value]">
                {{props.value}}
            </q-badge>
            <p v-else>
                {{props.value}}
            </p>
        </q-td>
        """,
    )

    # Remove shadows around table
    table.style("box-shadow: none;")

    with table.add_slot("top-left"):
        ui.label("My files").classes("text-h5 q-my-md")
    with table.add_slot("top-right"):
        with ui.row().classes("items-center gap-8"):
            with ui.input(placeholder="Search").props("type=search").bind_value(
                table, "filter"
            ).add_slot("append"):
                ui.icon("search")
            with ui.button("Upload").props("color=primary").on(
                "click", lambda: ui.navigate.to("/upload")
            ):
                ui.icon("upload")


rows = []


def create() -> None:
    @ui.page("/home")
    def home() -> None:
        """
        Main page of the application.
        """
        global rows

        rows = get_jobs()
        page_init()
        table_jobs()

        def update_table():
            global rows

            new_rows = get_jobs()

            if new_rows != rows:
                rows = new_rows
                table_jobs.refresh()

        ui.timer(5.0, update_table)
