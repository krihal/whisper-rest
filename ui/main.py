from nicegui import ui
from pages.srt import create as create_srt
from pages.home import create as create_files_table
from pages.txt import create as create_txt

# Create the pages
create_files_table()
create_srt()
create_txt()


@ui.page("/")
def index() -> None:
    """
    Index page with login.
    """

    with ui.card().style(
        "width: 50%; align-self: center; height: calc(100vh - 50%); margin-top: 10%;"
    ):
        ui.label("Welcome to SUNET Transcriber").classes(
            "text-h5 text-weight-medium q-mb-none"
        )

        ui.separator().classes("q-my-md")

        with ui.row().classes("q-col-gutter-md q-mt-sm").style(
            "align -items: center; justify-content: center;"
        ):
            with ui.column():
                username = ui.input(label="Username", placeholder="Enter your username")
            with ui.column().classes("col-12 col-sm-6"):
                password = ui.input(
                    label="Password", placeholder="Enter your password"
                ).props("type=password")

        def login():
            if username.value == "admin" and password.value == "admin":
                ui.navigate.to("/home")
            else:
                ui.notify("Login failed", type="negative")

        ui.separator().classes("q-my-md")
        with ui.row().style("align -items: center; justify-content: center;"):
            ui.button("Login", icon="login").props("color=primary").on("click", login)
            ui.button("Login with SSO", icon="login").props("color=primary")


ui.run(storage_secret="secret", title="SUNET Transcriber", port=8080)
