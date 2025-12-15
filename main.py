import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
import datetime

# --- 1. KONFIGURASI DATABASE ---
DB_URL_RAW = os.getenv("DB_URL")

if not DB_URL_RAW:
    # Koneksi Lokal (Pastikan encoding %40 untuk @)
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://ironnur:Project%4025@127.0.0.1:3306/iuris_legal_db"
    # Create engine standar untuk lokal
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
    # Koneksi Cloud (Aiven)
    if DB_URL_RAW.startswith("mysql://"):
        SQLALCHEMY_DATABASE_URL = DB_URL_RAW.replace("mysql://", "mysql+pymysql://", 1)
    else:
        SQLALCHEMY_DATABASE_URL = DB_URL_RAW
    
    # PERBAIKAN: Gunakan parameter 'ssl' yang benar untuk PyMySQL agar tidak TypeError
    # Ini akan memaksa koneksi menggunakan SSL tanpa membutuhkan file sertifikat fisik
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"ssl": {}} 
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODEL DATABASE (Menggunakan Base yang sudah didefinisikan di atas) ---
# --- 2. MODEL DATABASE ---
class LegalCase(Base):
    __tablename__ = "legal_cases"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False)
    lawyer_id = Column(Integer, nullable=True)
    case_title = Column(String(255), nullable=False)
    case_description = Column(Text, nullable=True)
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# --- 3. SCHEMA VALIDASI (Pydantic) ---
class CaseBase(BaseModel):
    client_id: int
    lawyer_id: Optional[int] = None
    case_title: str
    case_description: Optional[str] = None
    status: Optional[str] = "open"

class CaseResponse(CaseBase):
    id: int
    created_at: datetime.datetime
    class Config:
        from_attributes = True

# --- 4. INIT FASTAPI & DEPENDENCY ---
app = FastAPI(title="IURIS Legal Python API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. ENDPOINTS CRUD ---

# Endpoint Utama (Agar tidak "Not Found" saat akses URL utama)
@app.get("/")
def read_root():
    return {
        "status": "Online",
        "message": "IURIS Python API is running successfully!",
        "docs": "/docs"
    }

# 1. READ ALL
@app.get("/cases", response_model=List[CaseResponse])
def read_all_cases(db: Session = Depends(get_db)):
    return db.query(LegalCase).all()

# 2. READ ONE
@app.get("/cases/{case_id}", response_model=CaseResponse)
def read_one_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(LegalCase).filter(LegalCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Kasus tidak ditemukan")
    return db_case

# 3. CREATE
@app.post("/cases", response_model=CaseResponse)
def create_case(case: CaseBase, db: Session = Depends(get_db)):
    db_case = LegalCase(**case.dict())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

# 4. UPDATE
@app.put("/cases/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, case_update: CaseBase, db: Session = Depends(get_db)):
    db_case = db.query(LegalCase).filter(LegalCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Kasus tidak ditemukan")
    
    for key, value in case_update.dict().items():
        setattr(db_case, key, value)
    
    db.commit()
    db.refresh(db_case)
    return db_case

# 5. DELETE
@app.delete("/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(LegalCase).filter(LegalCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Kasus tidak ditemukan")
    
    db.delete(db_case)
    db.commit()
    return {"message": f"Kasus dengan ID {case_id} berhasil dihapus"}

if __name__ == "__main__":
    import uvicorn
    # Mengambil port dari environment (Render) atau default 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)