from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Extra
from typing import List, Dict, Any, Optional
import os
import time
import httpx
from kubernetes import client, config

# Load in-cluster config or fallback to kubeconfig
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

batch_v1 = client.BatchV1Api()

REGISTRY = os.getenv("REGISTRY", "l4sttr4in/scan-tools")
TAG = os.getenv("TAG", "latest")
NAMESPACE = os.getenv("NAMESPACE", "scan-system")

class ScanRequest(BaseModel):
    tool: str
    targets: List[str]
    options: Dict[str, Any] = {}
    job_id: Optional[str] = None
    controller_callback_url: Optional[str] = None

    class Config:
        extra = Extra.ignore  # ignore additional fields like scanner_node_url

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/scan", status_code=201)
def scan(req: ScanRequest):
    return _create_job(req)

@app.post("/api/scan/execute", status_code=201)
def execute_scan(req: ScanRequest):
    return _create_job(req)


def _create_job(req: ScanRequest):
    job_name = f"{req.tool}-scan-{int(time.time())}"
    
    # Tạo environment variables cho container
    env_vars = [
        client.V1EnvVar(name="TARGETS", value=",".join(req.targets))
    ]
    
    # Thêm controller callback URL nếu có
    if req.controller_callback_url:
        env_vars.append(client.V1EnvVar(name="CONTROLLER_CALLBACK_URL", value=req.controller_callback_url))
    
    # Thêm job ID nếu có
    if req.job_id:
        env_vars.append(client.V1EnvVar(name="JOB_ID", value=req.job_id))
    
    container = client.V1Container(
        name=req.tool,
        image=f"{REGISTRY}/{req.tool}:latest",
        args=req.targets,
        env=env_vars,
        image_pull_policy="Never"
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"job-name": job_name}),
        spec=client.V1PodSpec(
            containers=[container],
            restart_policy="Never"
        )
    )
    job_spec = client.V1JobSpec(
        template=template,
        backoff_limit=0
    )
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name, namespace=NAMESPACE),
        spec=job_spec
    )
    try:
        batch_v1.create_namespaced_job(namespace=NAMESPACE, body=job)
        return {"job_name": job_name, "status": "created"}
    except client.rest.ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {e}")
