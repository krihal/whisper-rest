import requests
from nicegui import ui, app
from pages.common import page_init, API_URL

# Set up global state
expanded_row = None  # Track which row is currently expanded
edit_inputs = {}  # Store input elements for the currently edited row
data = []


def format_time(time_str):
    """Format the time for display"""
    parts = time_str.split(",")
    if len(parts) == 2:
        return f"{parts[0]}<span class='text-gray-500'>,{parts[1]}</span>"
    return time_str


def is_valid_time(time_str):
    """Validate the SRT timestamp format"""
    try:
        parts = time_str.split(",")
        if len(parts) != 2:
            return False

        time_parts = parts[0].split(":")
        if len(time_parts) != 3:
            return False

        hours, minutes, seconds = map(int, time_parts)
        milliseconds = int(parts[1])

        return (
            0 <= hours <= 99
            and 0 <= minutes <= 59
            and 0 <= seconds <= 59
            and 0 <= milliseconds <= 999
        )
    except:
        return False


def calculate_duration(start_time, end_time):
    """Calculate duration between two timestamps"""
    try:
        # Parse start time
        start_parts = start_time.split(",")
        start_time_parts = start_parts[0].split(":")
        start_h, start_m, start_s = map(int, start_time_parts)
        start_ms = int(start_parts[1])
        start_total_ms = ((start_h * 3600) + (start_m * 60) + start_s) * 1000 + start_ms

        # Parse end time
        end_parts = end_time.split(",")
        end_time_parts = end_parts[0].split(":")
        end_h, end_m, end_s = map(int, end_time_parts)
        end_ms = int(end_parts[1])
        end_total_ms = ((end_h * 3600) + (end_m * 60) + end_s) * 1000 + end_ms

        # Calculate difference
        diff_ms = end_total_ms - start_total_ms

        # Format result
        if diff_ms < 0:
            return "Invalid (end before start)"

        diff_s, ms = divmod(diff_ms, 1000)
        diff_m, diff_s = divmod(diff_s, 60)

        if diff_m > 0:
            return f"{diff_m}m {diff_s}s {ms}ms"
        else:
            return f"{diff_s}s {ms}ms"
    except:
        return "Invalid format"


@ui.refreshable
def render_data_table():
    """Render the data table with expandable rows"""
    global expanded_row, edit_inputs, data

    with ui.card().classes("w-full no-shadow no-border"):
        # No data message
        if len(data) == 0:
            with ui.row().classes("w-full p-8 text-center text-gray-500"):
                ui.label('No subtitle entries. Click "Add New" to create one.').classes(
                    "text-lg"
                )

        # Data rows
        for index, item in enumerate(data):
            is_expanded = expanded_row == item["index"]

            # Main row - clickable to expand/collapse
            with ui.row().classes(
                "border-b p-2 hover:bg-gray-50 cursor-pointer"
            ) as row:
                row.on("click", lambda e, idx=item["index"]: toggle_expand(idx))

                ui.label(f"{item['index']}").classes("w-16 font-mono")

                with ui.element("div").classes("w-48"):
                    ui.html(
                        f"{format_time(item['start_time'])} → {format_time(item['end_time'])}"
                    )

                ui.label(item["text"]).classes("flex-grow truncate")

            # Expanded content - shows when row is clicked
            if is_expanded:
                with ui.card().classes("bg-blue-50 p-4 mb-2"):
                    # Display mode
                    if not edit_inputs.get(item["index"]):
                        with ui.row().classes("gap-4 w-full"):
                            with ui.column().classes("w-full"):
                                index_label = ui.label(f"{index + 1}")
                                ui.label("Time Details").classes("font-bold")
                                start_time = ui.input(
                                    "Start time",
                                    value=item["start_time"],
                                )
                                end_time = ui.input("End time", value=item["end_time"])
                                ui.label(
                                    f"Duration: {calculate_duration(item['start_time'], item['end_time'])}"
                                )

                            with ui.column().classes("w-full"):
                                ui.label("Content").classes("font-bold")
                                text = ui.textarea(value=item["text"]).classes(
                                    "bg-white p-2 rounded w-full"
                                )
                                ui.label(
                                    f"Characters: {len(item['text'])} | Words: {len(item['text'].split())}"
                                )

                        with ui.row().classes("justify-end mt-4"):
                            ui.button(
                                "Add new before",
                                icon="add",
                                on_click=lambda e: add_new_entry(
                                    int(index_label.text) - 1
                                ),
                            )
                            ui.button(
                                "Add new after",
                                icon="add",
                                on_click=lambda e: add_new_entry(int(index_label.text)),
                            )
                            ui.button(
                                "Save",
                                icon="save",
                                on_click=lambda e: save_edit(
                                    int(index_label.text),
                                    text.value,
                                    start_time.value,
                                    end_time.value,
                                ),
                            ).classes("bg-blue-500")
                            delete_btn = ui.button(
                                "Delete",
                                icon="delete",
                                color="negative",
                                on_click=lambda e, idx=item["index"]: delete_entry(
                                    int(index_label.text) - 1
                                ),
                            )
                            delete_btn.on("click.stop")  # Stop propagation


def toggle_expand(index):
    """Toggle the expanded state of a row"""
    global expanded_row

    if expanded_row == index:
        expanded_row = None
    else:
        expanded_row = index

    render_data_table.refresh()


def save_edit(index, text, start_time, end_time):
    """Save the edited data"""
    global edit_inputs, expanded_row, data

    # Validate time formats
    if not is_valid_time(start_time) or not is_valid_time(end_time):
        ui.notify("Invalid time format! Use HH:MM:SS,mmm", type="negative")
        return

    # Find and update item
    for item in data:
        if item["index"] == index:
            item["start_time"] = start_time
            item["end_time"] = end_time
            item["text"] = text
            break

    expanded_row = False

    ui.notify("Changes saved successfully", type="positive")
    render_data_table.refresh()


def delete_entry(index):
    """Delete an entry from the data"""
    global expanded_row, edit_inputs, data

    # Find the item to remove
    for i, item in enumerate(data):
        if item["index"] == index:
            data.pop(i)
            break

    # Reset expanded row if it was deleted
    if expanded_row == index:
        expanded_row = None

    # Remove from edit inputs if present
    if index in edit_inputs:
        del edit_inputs[index]

    # Re-index remaining items
    for i, item in enumerate(data):
        item["index"] = i + 1

    ui.notify("Entry deleted", type="info")
    render_data_table.refresh()


def add_new_entry(index: int):
    """Add a new entry to the data"""
    global data, expanded_row, edit_inputs

    if index == -1:
        index = 0

    # Get default start time from the last entry end time if available
    default_start = data[-1]["end_time"] if data else "00:00:00,000"

    # Create new entry
    new_entry = {
        "index": None,
        "start_time": default_start,
        "end_time": default_start,
        "text": "New subtitle text",
    }

    # Add to data to index position in list
    data.insert(index, new_entry)

    # Auto-expand and edit the new entry
    expanded_row = index
    edit_inputs[index] = {}

    # Set new index for all items
    for i, item in enumerate(data):
        item["index"] = i

    for i, _ in enumerate(data):
        print(f"Index: {i}, text: {data[i]['text']}")

    # Sort data by index
    data = sorted(data, key=lambda d: d["index"])

    expanded_row = None

    render_data_table.refresh()


def parse_srt(data):
    """Parse SRT data into a structured format"""
    parsed_data = []
    lines = data.splitlines()

    for i in range(0, len(lines), 4):
        if i + 3 < len(lines):
            index = int(lines[i])
            time_range = lines[i + 1].split(" --> ")
            start_time = time_range[0].strip()
            end_time = time_range[1].strip()
            text = lines[i + 2].strip()

            parsed_data.append(
                {
                    "index": index,
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text,
                }
            )

    return parsed_data


def export_srt():
    """Export data in SRT format"""
    srt_content = ""
    for item in sorted(data, key=lambda x: x["index"]):
        srt_content += f"{item['index']}\n"
        srt_content += f"{item['start_time']} --> {item['end_time']}\n"
        srt_content += f"{item['text']}\n\n"

    ui.download("subtitles.srt", srt_content)
    ui.notify("SRT file ready for download", type="positive")


def create() -> None:
    @ui.page("/srt")
    def result(uuid: str, filename: str) -> None:
        """
        Display the result of the transcription job.
        """
        global data
        page_init()

        app.add_static_files(url_path="/static", local_directory="static/")
        response = requests.get(f"{API_URL}/transcriber/{uuid}/result")

        if response.status_code != 200:
            ui.notify("Error: Failed to get result")
            return

        data = response.content.decode()
        data = parse_srt(data)

        # Create a toolbar with buttons on the top
        with ui.row().classes("justify-between items-center"):
            ui.button(
                "Export SRT",
                icon="save",
                on_click=export_srt,
            ).props("color=primary")
            ui.button("Revert", icon="undo").props("color=negative")
            ui.button("Files", icon="folder").props("color=primary").on_click(
                lambda: ui.navigate.to("/home")
            )

        # Split screen in 2/3 and 1/3
        with ui.row().classes("w-full"):
            with ui.column().classes("w-2/3"):
                with ui.card().classes("w-full no-shadow no-border"):
                    with ui.scroll_area().style("height: calc(100vh - 200px);"):
                        render_data_table()

            with ui.column().classes("w-1/3"):
                with ui.card().classes("w-full no-shadow no-border"):
                    ui.label("Preview").classes("text-lg font-semibold")
                    ui.label(
                        "This is a preview of the selected subtitle entry. You can edit the text and time range."
                    ).classes("text-sm text-gray-500")
                    ui.label(
                        "Click on a row to expand and edit the subtitle entry."
                    ).classes("text-sm text-gray-500")
