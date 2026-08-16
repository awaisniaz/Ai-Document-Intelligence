from datetime import datetime

from fastapi import Depends, FastAPI,UploadFile, File,HTTPException
from fastapi.params import Query
from pydantic import BaseModel
from pathlib import Path
import uuid
from app.database import Base, engine
from app.models import Documents
from app.database import get_db


Base.metadata.create_all(bind=engine)

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

@app.get("/documents")
def get_documents(session=Depends(get_db),limit: int = Query(default=10,ge=1,le=100), offset: int = 0):
    try:
        documents = session.query(Documents).limit(limit).offset(offset).all()
        return {"documents": documents,"status":"success","Count":len(documents)    }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), destination: str = "server",session=Depends(get_db)):


    allowed_extensions = ['.pdf', '.docx', '.txt']

    extension = Path(file.filename).suffix

    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT files are allowed.")
    if file.size > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum allowed size.")
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT files are allowed.")
    if destination == "server":
        
        document_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{document_id}{extension}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        document = Documents(
            original_filename=file.filename,
            stored_filename=file_path.name,
            file_type=file.content_type,
            file_size=file.size,
            status="uploaded",
            created_at=datetime.utcnow()
        )
        session.add(document)
        session.commit()
        session.refresh(document)
    
        return {"filename": file.filename, "message": "File uploaded successfully.","document_id": document_id}
    else:
        raise HTTPException(status_code=400, detail="Invalid destination. Only 'server' is supported.")