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
        job_data = [
            job["uuid"],
            job["filename"],
            job["created_at"],
            job["status"].upper(),
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


def show_job_details(evt: gr.SelectData):
    """
    Show the details of a selected job in the accordion.
    """
    download_url = f"{API_URL}/transcriber/{evt.row_value[0]}/result"
    delete_url = f"{API_URL}/transcriber/{evt.row_value[0]}"

    job_details = f"""
 <div style="margin-top: 20px;">
        <a href="{download_url}" target="_blank" style="
            text-decoration: none;
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            border-radius: 5px;
            margin-right: 10px;
            display: inline-block;
        ">📥 Download</a>
        <a href="{delete_url}" target="_blank" style="
            text-decoration: none;
            background-color: #e74c3c;
            color: white;
            padding: 8px 16px;
            border-radius: 5px;
            display: inline-block;
        ">🗑️ Delete</a>
    </div>
   """
    return (
        job_details,
        gr.Accordion(open=True),
    )


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

    with gr.Blocks(theme=gr.themes.Origin(), fill_height=True) as app:
        with gr.Sidebar():
            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(
                        file_types=[".wav", ".mp3", ".flac", ".mp4"],
                    )
                    model = gr.Dropdown(
                        label="Model",
                        choices=["small", "base", "large"],
                        value="base",
                    )
                    language = gr.Dropdown(
                        label="Language",
                        choices=["en", "sv"],
                        value="sv",
                    )
                    status = gr.Textbox(
                        label="Status", interactive=False, container=False
                    )
                    submit_button = gr.Button("Submit")
                    submit_button.click(
                        upload_file,
                        inputs=[file_input, model, language],
                        outputs=status,
                    )
        with gr.Accordion():
            with gr.Row(scale=1, height="50%"):
                job_list = gr.Dataframe(
                    get_jobs,
                    every=1,
                    headers=["Job ID", "File Name", "Created", "Status"],
                    datatype=["str", "str", "str", "str"],
                    interactive=False,
                )

        with gr.Accordion("Job Details", open=False) as accordion:
            # Create empty textboxes to be filled with job details
            job_details = gr.HTML("Job details here.")

        job_list.select(
            show_job_details,
            outputs=[
                job_details,
                accordion,
            ],
        )

    app.launch(share=False)


if __name__ == "__main__":
    main()
