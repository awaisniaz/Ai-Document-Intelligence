from datetime import datetime

from fastapi import Depends, FastAPI,UploadFile, File,HTTPException
from fastapi.params import Query
from pydantic import BaseModel
from pathlib import Path
import uuid
from app.database import Base, engine
from app.models import Documents
from app.database import get_db
import fitz


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
@app.get("/documents/{document_id}")
def get_document(document_id: str, session=Depends(get_db)):
    try:
        document = session.query(Documents).filter(Documents.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"document": document,"status":"success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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
    if destination == "server":  
        document_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{document_id}{extension}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        document = Documents(
            original_filename=file.filename,
            stored_filename=file_path.name,
            file_type=extension,
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
@app.delete("/documents/{document_id}")
def delete_document(document_id: str, session=Depends(get_db)):
    try:
        document = session.query(Documents).filter(Documents.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        file_path = UPLOAD_DIR / document.stored_filename
        if file_path.exists():
            file_path.unlink()  # Delete the file from the server
        session.delete(document)
        session.commit()
        return {"message": "Document deleted successfully","status":"success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/{document_id}/extract-text")
def extract_text(document_id: int, session=Depends(get_db)):
    try:
        document = session.query(Documents).filter(Documents.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        file_path = UPLOAD_DIR / document.stored_filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if document.file_type != ".pdf":
            raise HTTPException(status_code=400, detail="Text extraction is only supported for PDF files")
        pages = []
        character_count = 0
        with fitz.open(file_path) as pdf_document:
            page_count = len(pdf_document)

            for page_number,page in enumerate(pdf_document):
                 text = page.get_text()
                 character_count += len(text)
                 if text.strip():  # Only add pages with non-empty text
                  pages.append({"page_number": page_number+1, "text": text})

        if character_count == 0:
            return {"pages": [], "status": "success", "message": "No text found in the document",document_id: document_id,"page_count": page_count,"character_count": character_count,"file_path": str(file_path)}
        return {"pages": pages, "status": "success", "document_id": document_id, "page_count": page_count, "character_count": character_count, "file_path": str(file_path)}
    except Exception as e:
            raise HTTPException(status_code=404, detail="No text found in the document")
