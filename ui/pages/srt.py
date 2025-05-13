import re
import requests
from nicegui import ui, app
from pages.common import page_init, API_URL
from datetime import timedelta
from typing import Dict, Any, Optional


class SRTEditor:
    def __init__(self, srt_content: str = "", filename: Optional[str] = "") -> None:
        """Initialize the SRT Editor with optional content."""
        self.entries = []
        self.result = {"srt_content": srt_content}
        self.video = None
        self.filename = filename

        if srt_content:
            self.parse_srt(srt_content)
        else:
            # Add a default empty entry if no content is provided
            self.entries.append(
                {
                    "index": 1,
                    "start_time": "00:00:00,000",
                    "end_time": "00:00:05,000",
                    "text": "",
                }
            )

        # Set up the UI
        self.create_ui()

    def set_video(self, video: str) -> None:
        """Set the video element for seeking."""
        self.video = video

    def parse_srt(self, srt_content: str) -> None:
        """Parse SRT content into structured entries."""
        self.entries = []

        # Split by double newline (entry separator)
        blocks = re.split(r"\n\s*\n", srt_content.strip())

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                index = int(lines[0])
                time_line = lines[1]
                text = "\n".join(lines[2:])

                # Extract start and end times
                time_match = re.match(
                    r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
                    time_line,
                )
                if time_match:
                    start_time, end_time = time_match.groups()
                    self.entries.append(
                        {
                            "index": index,
                            "start_time": start_time,
                            "end_time": end_time,
                            "text": text,
                        }
                    )
            except Exception as e:
                print(f"Error parsing entry: {e}")

    def validate_time_format(self, time_str: str) -> bool:
        """Validate if the time string matches SRT format."""
        pattern = r"^\d{2}:\d{2}:\d{2},\d{3}$"
        return bool(re.match(pattern, time_str))

    def parse_time(self, time_str: str) -> timedelta:
        """Parse SRT time format to timedelta."""
        hours, minutes, rest = time_str.split(":")
        seconds, milliseconds = rest.split(",")

        return timedelta(
            hours=int(hours),
            minutes=int(minutes),
            seconds=int(seconds),
            milliseconds=int(milliseconds),
        )

    def format_time(self, time_obj: timedelta) -> str:
        """Format timedelta to SRT time format HH:MM:SS,mmm."""
        total_seconds = int(time_obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int(time_obj.microseconds / 1000)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def generate_srt(self) -> str:
        """Generate SRT content from entries."""
        result = []

        # Renumber entries
        for i, entry in enumerate(self.entries, 1):
            entry["index"] = i
            result.append(
                f"{entry['index']}\n{entry['start_time']} --> {entry['end_time']}\n{entry['text']}"
            )

        return "\n\n".join(result)

    def add_entry(self, index: int) -> None:
        """Add a new entry after the specified index."""
        # Calculate position to insert the new entry
        position = index + 1

        # Default times based on previous entry
        if 0 <= index < len(self.entries):
            prev_entry = self.entries[index]
            prev_end = self.parse_time(prev_entry["end_time"])
            new_start = prev_end + timedelta(seconds=1)
            new_end = new_start + timedelta(seconds=5)

            start_time = self.format_time(new_start)
            end_time = self.format_time(new_end)
        else:
            # Default values if no reference entry
            start_time = "00:00:00,000"
            end_time = "00:00:05,000"

        # Create and insert the new entry
        new_entry = {
            "index": position,
            "start_time": start_time,
            "end_time": end_time,
            "text": "",
        }

        self.entries.insert(position, new_entry)

        # Refresh the UI
        self.refresh_ui()

    def remove_entry(self, index: int) -> None:
        """Remove the entry at the specified index."""
        if 0 <= index < len(self.entries) and len(self.entries) > 1:
            self.entries.pop(index)
            self.refresh_ui()
        else:
            ui.notify("Cannot remove the last caption", type="warning")

    def save_srt(self) -> str:
        """Save and return the generated SRT content."""
        return self.generate_srt()

    async def seek_caption(self, e) -> None:
        """
        Select the caption based on the time.
        This function is called when the video is seeked.
        """

        current_time = await ui.run_javascript(f'getHtmlElement("{self.video.id}").currentTime')

        # Select the caption based on the current time
        for i, entry in enumerate(self.entries):
            start_time = self.parse_time(entry["start_time"])
            end_time = self.parse_time(entry["end_time"])

            if start_time.total_seconds() <= current_time <= end_time.total_seconds():
                # Focus entry["textarea"]
                #ui.run_javascript(f'getElement({entry["textarea"].id}).$refs.qRef.focus()')
                # scrollIntoView
                await ui.run_javascript(f'getHtmlElement("{entry["textarea"].id}").scrollIntoView()')

    def create_ui(self) -> None:
        """Create the UI elements."""

        # Sticky row with two buttons to the right: Revert and Export
        with ui.header():
            ui.label("Sunet Transcriber - SRT Editor").classes(
                "text-h5 text-weight-medium q-mb-none"
            )

        with ui.row():
            self.captions_container = ui.column()
            self.refresh_ui()

            with ui.page_sticky():
                self.video = ui.video(
                    f"/static/{self.filename}",
                    autoplay=False,
                    controls=True).classes("h-64").style("margin-top: 20px;")

                # On video seek select the caption 
                self.video.on("click", lambda e: self.seek_caption(e))


    def refresh_ui(self) -> None:
        """Refresh the UI with current entries."""

        # Clear existing captions
        self.captions_container.clear()

        # Add captions
        with self.captions_container:
            for i, entry in enumerate(self.entries):
                self.create_caption_row(i, entry)

    def revert_srt(self) -> None:
        """Revert to the original SRT content."""
        self.entries.clear()
        self.parse_srt(self.result["srt_content"])
        self.refresh_ui()

    def create_caption_row(self, index: int, entry: Dict[str, Any]) -> None:
        """Create a UI row for a caption entry."""

        def on_start_time_change(e):
            new_value = e.sender.value
            if self.validate_time_format(new_value):
                self.entries[index]["start_time"] = new_value
            else:
                ui.notify(
                    "Invalid time format (HH:MM:SS,mmm)",
                    type="negative",
                )
                e.sender.value = entry["start_time"]

        def on_end_time_change(e):
            new_value = e.sender.value
            if self.validate_time_format(new_value):
                self.entries[index]["end_time"] = new_value
            else:
                ui.notify(
                    "Invalid time format (HH:MM:SS,mmm)",
                    type="negative",
                )
                e.sender.value = entry["end_time"]

        def seek_video(time: str) -> None:
            if self.video:
                print("Video")
                self.video.seek(self.parse_time(time).total_seconds())

        with ui.card().classes("w-full no-shadow no-border "):
            with ui.row().classes("w-full no-shadow no-border "):
                with ui.row().classes("w-full items-center gap-2"):
                    start_time = ui.input(
                        label="Start time", value=entry["start_time"]
                    ).classes("w-24")
                    start_time.on("change", on_start_time_change)
                    start_time.on("click", lambda: seek_video(entry["start_time"]))

                    end_time = ui.input(
                        label="End time", value=entry["end_time"]
                    ).classes("w-24")
                    end_time.on("change", on_end_time_change)
                    end_time.on("click", lambda: seek_video(entry["end_time"]))

                    def save_srt_entry():
                        for i in range(len(self.entries) - 1):
                            if self.parse_time(
                                self.entries[i]["end_time"]
                            ) > self.parse_time(self.entries[i + 1]["start_time"]):
                                ui.notify(f"Timestamps overlap for:\n{self.entries[i]["text"]}", type="negative")
                                return

                        new_value = srt_caption.value
                        self.entries[index]["text"] = new_value
                        # self.save_srt()

                    srt_caption = ui.textarea(label="Caption", value=entry["text"]).classes("flex-grow").props("input-class=h-8").on("click", lambda: seek_video(entry["start_time"]))
                    entry["textarea"] = srt_caption
                    
                with ui.column().style("margin-left: auto;"):
                    with ui.row():
                        ui.button(
                            icon="arrow_upward",
                            on_click=lambda: self.move_entry(index, -1),
                        ).props("flat dense").tooltip("Move Up").classes("right").style(
                            "margin-left: auto;"
                        )

                        ui.button(
                            icon="arrow_downward",
                            on_click=lambda: self.move_entry(index, 1),
                        ).props("flat dense").tooltip("Move Down").classes("right")
                        ui.button(
                            icon="add",
                            color="positive",
                            on_click=lambda: self.add_entry(index),
                        ).props("flat dense").tooltip("Add After").classes("right")
                        ui.button(
                            icon="delete",
                            color="negative",
                            on_click=lambda: self.remove_entry(index),
                        ).props("flat dense").tooltip("Remove").classes("right")
                        ui.button(
                            icon="save",
                            color="primary",
                            on_click=lambda: save_srt_entry(),
                        ).props("flat dense").tooltip("Save")



    def move_entry(self, index: int, direction: int) -> None:
        """Move an entry up or down."""
        new_index = index + direction

        if 0 <= new_index < len(self.entries):
            # Swap entries
            self.entries[index], self.entries[new_index] = (
                self.entries[new_index],
                self.entries[index],
            )
            self.refresh_ui()


def create() -> None:
    @ui.page("/srt")
    def result(uuid: str, filename: str) -> None:
        """
        Display the result of the transcription job.
        """
        app.add_static_files(url_path="/static", local_directory="static/")
        response = requests.get(f"{API_URL}/transcriber/{uuid}/result")

        if response.status_code != 200:
            ui.notify("Error: Failed to get result")
            return

        srt = SRTEditor(response.content.decode(), filename)

        with ui.left_drawer(fixed=True):
            with ui.row().classes("justify-end"):
                ui.button(
                    "My files",
                    icon="arrow_back",
                    color="primary",
                    on_click=lambda: ui.navigate.to("/home"),
                ).classes("w-full")
                ui.button(
                    "Export",
                    icon="save",
                    color="primary",
                    on_click=lambda: ui.download(
                        srt.save_srt(),
                        filename=f"{srt.filename}.srt",
                    ),
                ).classes("w-full")
                ui.button(
                    "Revert",
                    icon="undo",
                    color="negative",
                    on_click=lambda: srt.revert_srt(),
                ).classes("w-full")



