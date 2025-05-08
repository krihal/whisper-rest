import gradio as gr
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

    for job in response.json()["result"]["jobs"]:
        download = ""
        if job["status"] == "completed":
            download = f'<a href="{API_URL}/transcriber/{job["uuid"]}/result" target="_blank">Download</a>'

        match job["status"]:
            case "completed":
                job_status = f'<span style="color: green; font-weight: bold;">{job["status"]}</span>'
            case "pending":
                job_status = f'<span style="color: orange; font-weight: bold;">{job["status"]}</span>'
            case "failed":
                job_status = f'<span style="color: red; font-weight: bold;">{job["status"]}</span>'
            case "uploading":
                job_status = f'<span style="color: blue; font-weight: bold;">{job["status"]}</span>'
            case "in_progress":
                job_status = f'<span style="color: orange; font-weight: bold;">{job["status"]}</span>'
            case _:
                job_status = job["status"]

        job_data = [
            job["uuid"],
            job["filename"],
            job["created_at"],
            job_status,
            download,
        ]
        jobs.append(job_data)

    return jobs


def upload_file(file, model, language):
    """
    Upload a file to the API for transcription.
    """
    if not file:
        return "No file uploaded"

    # File name without path
    file_name = file.name.split("/")[-1]

    with open(file.name, "rb") as f:
        files = {"file": (file_name, f)}
        response = requests.post(
            f"{API_URL}/transcriber?model={model}&language={language}", files=files
        )

    if response.status_code != 200:
        return f"Error: {response.json()['message']}"

    return f"File {file_name} uploaded successfully."


def job_download(job_id):
    """
    Download the transcription result for a job.
    """

    response = requests.get(f"{API_URL}/transcriber/{job_id}/result")
    if response.status_code != 200:
        return f"Error: {response.json()['message']}"

    with open(job_id, "wb") as f:
        f.write(response.content)

    return f"Job {job_id} downloaded successfully."


def job_delete(job_id):
    """
    Delete a transcription job.
    """
    response = requests.delete(f"{API_URL}/transcriber/{job_id}")
    if response.status_code != 200:
        return f"Error: {response.json()['message']}"

    return f"Job {job_id} deleted successfully."


def main():
    """
    Gradio app for uploading files to be transcribed, also a list of
    transcription jobs and their status.
    """
    file_input = None

    with gr.Blocks(theme=gr.themes.Origin(), fill_height=True) as app:
        with gr.Row():
            gr.Markdown(
                """
                <h1 style="text-align: center;">SUNET Transcription Service</h1>
                """
            )
        with gr.Sidebar():
            with gr.Row():
                file_input = gr.File(
                    file_types=[".wav", ".mp3", ".flac", ".mp4"],
                )
                model = gr.Dropdown(
                    label="Model",
                    choices=["small", "base", "large"],
                    value="base",
                    filterable=False,
                )
                language = gr.Dropdown(
                    label="Language",
                    choices=["en", "sv"],
                    value="sv",
                    filterable=False,
                )
                status = gr.Textbox(label="Status", interactive=False, container=False)
                submit_button = gr.Button("Submit")
                submit_button.click(
                    upload_file,
                    inputs=[file_input, model, language],
                    outputs=status,
                )

        gr.Dataframe(
            get_jobs,
            every=5,
            headers=["Job ID", "File Name", "Created", "Status", "Download"],
            datatype="html",
            interactive=False,
            static_columns=False,
            column_widths=[2, 2, 2, 1, 1],
            max_height=2000,
        )

    app.launch(share=False)


if __name__ == "__main__":
    main()
