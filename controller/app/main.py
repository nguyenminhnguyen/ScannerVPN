from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import httpx
import logging
import yaml
import os
from uuid import uuid4
from pydantic import BaseModel

from app import models, schemas, database

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo bảng nếu chưa có
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Scanner Controller",
    version="1.0"
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load metadata của các tool từ tools.yaml ở thư mục làm việc
TOOLS_FILE = os.path.join(os.getcwd(), "tools.yaml")
if not os.path.exists(TOOLS_FILE):
    raise RuntimeError(f"tools.yaml not found at {TOOLS_FILE}")
with open(TOOLS_FILE, 'r') as f:
    TOOLS = yaml.safe_load(f).get("tools", [])

@app.get("/api/tools")
def list_tools():
    """
    Trả về danh sách các tool, bao gồm name, image, description, args.
    """
    return {"tools": TOOLS}

@app.post("/api/scan_results", status_code=status.HTTP_204_NO_CONTENT)
def create_scan_result(
    payload: schemas.ScanResultCreate,
    db: Session = Depends(get_db)
):
    """
    Nhận POST từ Scanner Node, lưu kết quả vào DB.
    """
    db_obj = models.ScanResult(
        target=payload.target,
        resolved_ips=payload.resolved_ips,
        open_ports=payload.open_ports,
        scan_metadata=payload.scan_metadata,
    )
    db.add(db_obj)
    db.commit()
    return

@app.get("/api/scan_results", response_model=List[schemas.ScanResult])
def read_scan_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db)
):
    """
    Trả về các scan results, hỗ trợ phân trang bằng skip & limit.
    """
    return db.query(models.ScanResult).offset(skip).limit(limit).all()

@app.get("/api/scan_jobs", response_model=List[schemas.ScanJob])
def read_scan_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db)
):
    """
    Trả về các scan jobs, hỗ trợ phân trang bằng skip & limit.
    """
    return db.query(models.ScanJob).offset(skip).limit(limit).all()

@app.get("/api/scan_jobs/{job_id}", response_model=schemas.ScanJob)
def read_scan_job(job_id: str, db: Session = Depends(get_db)):
    """
    Trả về thông tin của một scan job cụ thể.
    """
    job = db.query(models.ScanJob).filter(models.ScanJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    return job

@app.post("/api/scan", status_code=201)
def create_scan(
    req: schemas.ScanJobRequest,
    db: Session = Depends(get_db)
):
    """
    Gửi scan request tới Scanner Node API.
    """
    # 1. Kiểm tra tool tồn tại
    meta = next((t for t in TOOLS if t.get("name") == req.tool), None)
    if not meta:
        raise HTTPException(status_code=404, detail="Tool not found")

    # 2. Tạo job record trong database
    job_id = f"scan-{req.tool}-{uuid4().hex[:6]}"
    db_job = models.ScanJob(
        job_id=job_id,
        tool=req.tool,
        targets=req.targets,
        options=req.options,
        status="submitted"
    )
    db.add(db_job)
    db.commit()

    # 3. Gửi request tới Scanner Node API
    try:
        scanner_node_url = os.getenv("SCANNER_NODE_URL", "http://scanner-node-api:8000")
        scanner_response = call_scanner_node(req.tool, req.targets, req.options, job_id, scanner_node_url)
        
        # 4. Cập nhật job status
        db_job.scanner_job_name = scanner_response.get("job_name")
        db_job.status = "running"
        db.commit()
        
        logger.info(f"Scan job {job_id} submitted to scanner node: {scanner_response}")
        return {"job_id": job_id, "status": "submitted", "scanner_job": scanner_response}
        
    except Exception as e:
        logger.error(f"Error calling scanner node: {e}")
        db_job.status = "failed"
        db_job.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to submit scan to scanner node: {e}")

def call_scanner_node(tool: str, targets: List[str], options: Dict[str, Any], job_id: str, scanner_url: str):
    """
    Gọi Scanner Node API để thực hiện scan.
    """
    payload = {
        "tool": tool,
        "targets": targets,
        "options": options,
        "job_id": job_id,
        "controller_callback_url": os.getenv("CONTROLLER_CALLBACK_URL", "http://controller:8000")
    }
    
    response = httpx.post(
        f"{scanner_url}/api/scan/execute",
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    return response.json()

# Schema riêng cho payload mỗi tool
class ToolRequest(BaseModel):
    targets: List[str]
    options: Dict[str, Any] = {}

# Endpoint cho từng tool
@app.post("/api/scan/dns-lookup", status_code=201)
def dns_lookup_endpoint(req: ToolRequest, db: Session = Depends(get_db)):
    scan_req = schemas.ScanJobRequest(tool="dns-lookup", targets=req.targets, options=req.options)
    return create_scan(scan_req, db)

@app.post("/api/scan/port-scan", status_code=201)
def port_scan_endpoint(req: ToolRequest, db: Session = Depends(get_db)):
    scan_req = schemas.ScanJobRequest(tool="port-scan", targets=req.targets, options=req.options)
    return create_scan(scan_req, db)

@app.post("/api/scan/httpx-scan", status_code=201)
def httpx_scan_endpoint(req: ToolRequest, db: Session = Depends(get_db)):
    scan_req = schemas.ScanJobRequest(tool="httpx-scan", targets=req.targets, options=req.options)
    return create_scan(scan_req, db)
