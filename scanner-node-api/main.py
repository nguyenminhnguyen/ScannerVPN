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
    
    # Thêm controller callback URL - ưu tiên external URL
    if req.controller_callback_url:
        # Convert internal service URL to external IP if needed
        callback_url = req.controller_callback_url
        if "controller.scan-system.svc.cluster.local" in callback_url:
            # Get external controller IP from environment or use default
            external_controller_ip = os.getenv("EXTERNAL_CONTROLLER_IP", "10.102.199.42")  # Ubuntu VM IP
            callback_url = callback_url.replace(
                "controller.scan-system.svc.cluster.local", 
                external_controller_ip
            )
        env_vars.append(client.V1EnvVar(name="CONTROLLER_CALLBACK_URL", value=callback_url))
    
    # Thêm job ID nếu có
    if req.job_id:
        env_vars.append(client.V1EnvVar(name="JOB_ID", value=req.job_id))
    
    container = client.V1Container(
        name=req.tool,
        image=f"{REGISTRY}/{req.tool}:latest",
        args=req.targets,
        env=env_vars,
        image_pull_policy="Never",
        security_context=client.V1SecurityContext(
            privileged=True,
            capabilities=client.V1Capabilities(
                add=["NET_ADMIN"]
            )
        ),
        volume_mounts=[
            client.V1VolumeMount(
                name="dev-tun",
                mount_path="/dev/net/tun"
            )
        ]
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"job-name": job_name}),
        spec=client.V1PodSpec(
            containers=[container],
            restart_policy="Never",
            volumes=[
                client.V1Volume(
                    name="dev-tun",
                    host_path=client.V1HostPathVolumeSource(
                        path="/dev/net/tun",
                        type="CharDevice"
                    )
                )
            ]
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
