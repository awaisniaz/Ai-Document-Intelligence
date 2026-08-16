from fastapi import FastAPI,UploadFile, File,HTTPException
from pydantic import BaseModel
from pathlib import Path
import uuid


class Document(BaseModel):
    title: str = "Sample Document"
    content: str = "This is a sample document content."

MAX_FILE_SIZE_MB = 10  * 1024 * 1024  # 10 MB

app = FastAPI()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service":"AI Document Intelligence API",
        "version":"1.0.0"
    }

@app.get("/about")
def get_about():
    return {
        "service": "AI Document Intelligence API",
        "version": "1.0.0",
        "description": "This service provides AI documentation and related functionalities.",
        "stage":"development"
    }
@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), destination: str = "server"):

    if file.size > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum allowed size.")
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT files are allowed.")
    if destination == "server":
        extension = Path(file.filename).suffix
        document_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{document_id}{extension}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
    
        return {"filename": file.filename, "message": "File uploaded successfully.","document_id": document_id}
    else:
        raise HTTPException(status_code=400, detail="Invalid destination. Only 'server' is supported.")