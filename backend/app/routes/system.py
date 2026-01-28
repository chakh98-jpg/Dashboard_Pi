"""
System control routes for reboot, shutdown, etc.
"""
import subprocess
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/system", tags=["system"])


class CommandResult(BaseModel):
    """Command execution result"""
    status: str
    output: str


@router.post("/reboot")
async def reboot_system():
    """Reboot the Raspberry Pi"""
    try:
        subprocess.Popen(["reboot"], shell=False)
        return {"status": "rebooting", "message": "System will reboot shortly"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shutdown")
async def shutdown_system():
    """Shutdown the Raspberry Pi"""
    try:
        subprocess.Popen(["shutdown", "-h", "now"], shell=False)
        return {"status": "shutting_down", "message": "System will shutdown shortly"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def list_services():
    """List systemd services"""
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--plain"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        services = []
        for line in result.stdout.strip().split('\n')[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4:
                services.append({
                    "name": parts[0],
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3]
                })
        
        return {"services": services[:20]}  # Limit to 20
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/service/{name}/{action}")
async def control_service(name: str, action: str):
    """Control a systemd service (start/stop/restart)"""
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    try:
        result = subprocess.run(
            ["systemctl", action, name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        
        return {"status": "success", "action": action, "service": name}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hostname")
async def get_hostname():
    """Get system hostname and user info"""
    import platform
    import pwd
    
    try:
        # Get the user running the process on the host
        uid = os.getuid()
        try:
            user = pwd.getpwuid(uid).pw_name
        except:
            user = "root"
        
        return {
            "hostname": platform.node(),
            "user": user,
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
