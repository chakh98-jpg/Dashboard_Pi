"""
Process management routes
"""
import psutil
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/processes", tags=["processes"])


class ProcessInfo(BaseModel):
    """Process information"""
    pid: int
    name: str
    username: str
    cpu_percent: float
    memory_percent: float
    status: str


@router.get("/list", response_model=List[ProcessInfo])
async def list_processes(
    sort_by: str = "cpu",
    limit: int = 20
):
    """List running processes sorted by CPU or memory usage"""
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'] or "Unknown",
                    username=info['username'] or "Unknown",
                    cpu_percent=info['cpu_percent'] or 0.0,
                    memory_percent=info['memory_percent'] or 0.0,
                    status=info['status'] or "Unknown"
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort
        if sort_by == "memory":
            processes.sort(key=lambda x: x.memory_percent, reverse=True)
        else:
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        
        return processes[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kill/{pid}")
async def kill_process(pid: int):
    """Kill a process by PID"""
    try:
        proc = psutil.Process(pid)
        
        # Don't allow killing critical processes
        critical_names = ['systemd', 'init', 'dockerd', 'containerd', 'sshd']
        if proc.name().lower() in critical_names:
            raise HTTPException(status_code=403, detail="Cannot kill critical system process")
        
        proc.terminate()
        
        # Wait up to 3 seconds for graceful termination
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()  # Force kill
        
        return {"status": "killed", "pid": pid}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="Process not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{pid}")
async def process_info(pid: int):
    """Get detailed info about a process"""
    try:
        proc = psutil.Process(pid)
        
        with proc.oneshot():
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "exe": proc.exe() if hasattr(proc, 'exe') else None,
                "cmdline": proc.cmdline(),
                "status": proc.status(),
                "username": proc.username(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "memory_info": {
                    "rss": proc.memory_info().rss,
                    "vms": proc.memory_info().vms
                },
                "num_threads": proc.num_threads(),
                "create_time": proc.create_time()
            }
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="Process not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
