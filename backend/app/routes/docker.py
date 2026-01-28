"""
Docker management routes
"""
import subprocess
import json
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/docker", tags=["docker"])


class Container(BaseModel):
    """Container information"""
    id: str
    name: str
    image: str
    status: str
    state: str
    ports: str


@router.get("/containers", response_model=List[Container])
async def list_containers():
    """List all Docker containers"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                data = json.loads(line)
                containers.append(Container(
                    id=data.get("ID", "")[:12],
                    name=data.get("Names", ""),
                    image=data.get("Image", ""),
                    status=data.get("Status", ""),
                    state=data.get("State", ""),
                    ports=data.get("Ports", "")
                ))
        
        return containers
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Docker not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/container/{container_id}/{action}")
async def control_container(container_id: str, action: str):
    """Control a Docker container (start/stop/restart)"""
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    try:
        result = subprocess.run(
            ["docker", action, container_id],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        
        return {"status": "success", "action": action, "container": container_id}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/container/{container_id}/logs")
async def get_container_logs(container_id: str, lines: int = 50):
    """Get container logs"""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "container": container_id,
            "logs": result.stdout + result.stderr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images")
async def list_images():
    """List Docker images"""
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        images = []
        for line in result.stdout.strip().split('\n'):
            if line:
                data = json.loads(line)
                images.append({
                    "id": data.get("ID", "")[:12],
                    "repository": data.get("Repository", ""),
                    "tag": data.get("Tag", ""),
                    "size": data.get("Size", ""),
                    "created": data.get("CreatedSince", "")
                })
        
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
