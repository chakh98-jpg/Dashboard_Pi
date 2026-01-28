"""
File manager routes for browsing and editing files
"""
import os
import stat
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["files"])

# Root path for file browsing (mounted from host)
FILE_ROOT = "/host"


class FileInfo(BaseModel):
    """File/directory information"""
    name: str
    path: str
    is_dir: bool
    size: int
    modified: str
    permissions: str


class FileContent(BaseModel):
    """File content for reading/writing"""
    content: str


def get_file_info(filepath: str) -> FileInfo:
    """Get file/directory information"""
    try:
        stat_info = os.stat(filepath)
        return FileInfo(
            name=os.path.basename(filepath),
            path=filepath.replace(FILE_ROOT, ""),
            is_dir=os.path.isdir(filepath),
            size=stat_info.st_size,
            modified=datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            permissions=stat.filemode(stat_info.st_mode)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[FileInfo])
async def list_directory(
    path: str = Query(default="/", description="Directory path to list")
):
    """List files and directories in a path"""
    full_path = os.path.join(FILE_ROOT, path.lstrip("/"))
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Path not found")
    
    if not os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    try:
        items = []
        for item in sorted(os.listdir(full_path)):
            item_path = os.path.join(full_path, item)
            try:
                items.append(get_file_info(item_path))
            except:
                continue  # Skip inaccessible files
        return items
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/read")
async def read_file(
    path: str = Query(..., description="File path to read")
):
    """Read file content"""
    full_path = os.path.join(FILE_ROOT, path.lstrip("/"))
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="Path is a directory")
    
    # Check file size (limit to 1MB for safety)
    if os.path.getsize(full_path) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 1MB)")
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return {"path": path, "content": content}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/write")
async def write_file(
    path: str = Query(..., description="File path to write"),
    body: FileContent = Body(...)
):
    """Write content to a file"""
    full_path = os.path.join(FILE_ROOT, path.lstrip("/"))
    
    if os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="Path is a directory")
    
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(body.content)
        return {"status": "success", "path": path}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_file(
    path: str = Query(..., description="File path to delete")
):
    """Delete a file"""
    full_path = os.path.join(FILE_ROOT, path.lstrip("/"))
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Prevent deleting critical paths
    dangerous_paths = ["/", "/etc", "/usr", "/bin", "/sbin", "/var", "/boot"]
    if path.rstrip("/") in dangerous_paths:
        raise HTTPException(status_code=403, detail="Cannot delete system directories")
    
    try:
        if os.path.isdir(full_path):
            os.rmdir(full_path)  # Only empty directories
        else:
            os.remove(full_path)
        return {"status": "deleted", "path": path}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
