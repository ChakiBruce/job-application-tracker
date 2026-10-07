# Job Application Tracker

A Python and SQLite tracker with terminal and Django browser interfaces.

## Features

- Browser: view and add applications with validated forms.
- Terminal: add, view, update status, search/filter, and view statistics.
- Both interfaces share `data/applications.db`.

## Setup (Windows PowerShell)

Run these commands from the project folder:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If your virtual environment already exists, skip creating it.

## Database setup

```powershell
.venv\Scripts\python.exe manage.py migrate --fake-initial
```

The Django model maps to the existing `applications` table. On an existing tracker
installation, `--fake-initial` records its initial migration without recreating that
table. On a fresh installation, the migration creates it. Subsequent database
changes should use normal Django migrations.

## Run the browser interface

```powershell
.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/ to view your applications or add one through a form.
Stop the local development server with Ctrl+C. Search, status updates, and
statistics currently remain available in the terminal interface.

These settings are for local development. Before deployment, configure a persistent
`DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=0`, configure allowed hosts, and protect
access to application data. The default development key changes on server restart.

## Run the terminal interface

```powershell
.venv\Scripts\python.exe app.py
```

## Tests

```powershell
.venv\Scripts\python.exe manage.py test applications
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Web tests use a separate test database; terminal tests use temporary databases.

## Project structure

- `manage.py`: Django commands, including starting the server and running migrations.
- `config/`: website settings and root URLs.
- `applications/models.py`: the application model mapped to the existing table.
- `applications/forms.py`: form fields and validation.
- `applications/views.py`: request handling and database operations.
- `applications/templates/applications/`: HTML templates.
- `applications/static/applications/`: CSS styling.
- `src/tracker.py`: database functions used by the terminal app.

A browser GET request displays a page. A POST request submits the add form.
Django validates the form, saves a model, and redirects to the application list.
