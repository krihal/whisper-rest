from nicegui import ui
from pages.common import page_init, get_jobs, table_click


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
        .style(
            "width: 100%; height: calc(100vh - 130px); overflow: auto; box-shadow: none;"
        )
        .on("rowClick", table_click)
        .classes("text-h2")
    ).props("dense hover")

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

    with table.add_slot("top-left"):
        ui.label("My files").classes("text-h5 q-my-md")

    with table.add_slot("top-right"):
        with ui.row().classes("items-center gap-8"):
            with ui.input(placeholder="Search").props("type=search").bind_value(
                table, "filter"
            ).add_slot("append"):
                ui.icon("search")
            with ui.button("Upload") as upload:
                upload.props("color=primary")
                upload.on("click", lambda: ui.navigate.to("/upload"))
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
