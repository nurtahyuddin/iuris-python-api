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
    # Koneksi Lokal
    # SQLALCHEMY_DATABASE_URL = "mysql+pymysql://ironnur:Project@25@127.0.0.1:3306/iuris_legal_db"
    # Karakter '@' di password 'Project@25' diganti menjadi '%40'
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://ironnur:Project%4025@127.0.0.1:3306/iuris_legal_db"
else:
    # Koneksi Cloud (Aiven)
    SQLALCHEMY_DATABASE_URL = DB_URL_RAW.replace("mysql://", "mysql+pymysql://")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODEL DATABASE (SQLAlchemy) ---
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
# Schema untuk menerima input data
class CaseBase(BaseModel):
    client_id: int
    lawyer_id: Optional[int] = None
    case_title: str
    case_description: Optional[str] = None
    status: Optional[str] = "open"

# Schema untuk merespon data (termasuk ID)
class CaseResponse(CaseBase):
    id: int
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

# 1. READ ALL (Melihat semua kasus)
@app.get("/cases", response_model=List[CaseResponse])
def read_all_cases(db: Session = Depends(get_db)):
    return db.query(LegalCase).all()

# 2. READ ONE (Melihat detail kasus berdasarkan ID)
@app.get("/cases/{case_id}", response_model=CaseResponse)
def read_one_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(LegalCase).filter(LegalCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Kasus tidak ditemukan")
    return db_case

# 3. CREATE (Menambah kasus baru)
@app.post("/cases", response_model=CaseResponse)
def create_case(case: CaseBase, db: Session = Depends(get_db)):
    db_case = LegalCase(**case.dict())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

# 4. UPDATE (Mengubah data kasus)
@app.put("/cases/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, case_update: CaseBase, db: Session = Depends(get_db)):
    db_case = db.query(LegalCase).filter(LegalCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Kasus tidak ditemukan")
    
    # Update field yang dikirim
    for key, value in case_update.dict().items():
        setattr(db_case, key, value)
    
    db.commit()
    db.refresh(db_case)
    return db_case

# 5. DELETE (Menghapus kasus)
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
    uvicorn.run(app, host="0.0.0.0", port=8000)