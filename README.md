
# file2text_api

Small FastAPI app that extracts text from uploaded PDF, DOCX and TXT files and stores the extracted text under the `data/` folder as a `.txt` file named by a generated UUID.

This README documents how to create and activate a virtual environment (PowerShell and common alternatives), install dependencies, run the server, and exercise the API endpoints.

## What this service does

- Accepts file uploads (PDF, DOCX, TXT) at `POST /upload` and extracts text.
- Stores extracted text files in `data/` as `<uuid>.txt` and returns the generated `id` in the response.
- Retrieve stored text with `GET /text/{doc_id}`.
- Small safety guard: uploads are limited to 10 MB by default.

Supported file extensions: `.pdf`, `.docx`, `.txt`.

## Project layout

- `main.py` - FastAPI application and text-extraction logic.
- `data/` - directory where extracted `.txt` documents are stored (created automatically).
- `tests/` - pytest tests (example: `tests/test_upload_txt.py`).
- `requirements.txt` - Python dependencies.

## Create & activate a virtual environment (recommended)

The following commands show how to create and activate a virtual environment for this project.

PowerShell (Windows) - recommended for this workspace:

```powershell
python -m venv .venv
# If you see an execution policy error when activating, run PowerShell as Administrator and allow RemoteSigned or run: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Command Prompt (cmd.exe):

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

macOS / Linux (bash/zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation you should see the virtualenv name (for example `.venv`) in your prompt.

## Install dependencies

With the virtual environment activated, install the required packages:

```powershell
python -m pip install -r requirements.txt
```

If you need to add or upgrade a package, prefer `pip install <pkg>` and then update `requirements.txt` with `pip freeze > requirements.txt`.

## Run the server

Start the FastAPI app locally using Uvicorn (development mode / auto-reload):

```powershell
uvicorn main:app --reload
```

The OpenAPI docs will be available at `http://127.0.0.1:8000/docs`.

## API endpoints

- POST /upload
	- Accepts multipart file upload with form field name `file`.
	- Supported file types: `.pdf`, `.docx`, `.txt`.
	- Returns JSON: `{ "id": "<uuid>", "filename": "original-filename", "num_chars": <n>, "message": "..." }`.

- GET /text/{doc_id}
	- Returns `{ "id": "<doc_id>", "text": "...extracted text..." }` or 404 if not found.

- GET /
	- Health endpoint returning `{ "message": "Server is alive! Go to /docs" }`.

### Example: upload a text file (PowerShell)

This example uses PowerShell's form-post support (`Invoke-RestMethod` with `-Form`) to upload a file and then fetch the text back.

```powershell
$resp = Invoke-RestMethod -Uri http://127.0.0.1:8000/upload -Method Post -Form @{ file = Get-Item './example.txt' }
$resp | ConvertTo-Json -Depth 4

#$resp.id now contains the UUID. Retrieve the stored text:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/text/$($resp.id)" -Method Get
```

If you prefer curl (PowerShell alias to Invoke-WebRequest):

```powershell
curl -X POST "http://127.0.0.1:8000/upload" -F "file=@example.txt"
```

Note: shell behavior differs across platforms. The above examples assume Windows PowerShell; on Linux/macOS replace the upload command with the native `curl` or an appropriate `curl -F` form.

## Implementation notes (from `main.py`)

- PDF text extraction uses `PyPDF2.PdfReader` and concatenates extracted text for all pages.
- DOCX extraction uses `docx2txt` and a temporary file to pass bytes to the library.
- TXT files are decoded as UTF-8 with replacement for invalid bytes.
- Temporary files used for DOCX are removed after processing.
- If no text is extractable, the server returns HTTP 400.
- Uploaded text is written to `data/<uuid>.txt` in UTF-8.

## Limits and error handling

- Upload size is limited by `MAX_UPLOAD_SIZE` (default: 10 * 1024 * 1024 = 10 MB). Larger files return HTTP 413.
- Unsupported file types return HTTP 400.
- Extraction errors return HTTP 400 (server logs include details).

## Tests

Run the project's tests with pytest:

```powershell
pytest -q
```

There's at least one test in `tests/test_upload_txt.py` that posts a small `.txt` file and verifies the extraction and retrieval flow.

## Troubleshooting

- If `docx2txt` or `PyPDF2` raise errors, inspect the server logs (stdout) for stack traces. Ensure dependencies are installed in the active venv.
- If PowerShell refuses to activate the venv, check the execution policy (`Get-ExecutionPolicy`) and consider running: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.