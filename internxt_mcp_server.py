"""
Internxt MCP Server
===================
MCP server wrapping the Internxt CLI (@internxt/cli).

Prerequisites:
  npm install -g @internxt/cli
  internxt login   (one-time authentication)

Usage:
  pip install mcp
  python internxt_mcp_server.py
"""

import json
import subprocess
import sys
from typing import Any

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Helpers & Path Resolution
# ---------------------------------------------------------------------------

_root_folder_id_cache = None

def get_root_folder_id() -> str:
    global _root_folder_id_cache
    if _root_folder_id_cache:
        return _root_folder_id_cache
    
    result = run_internxt(["whoami"])
    if result["success"] and isinstance(result["output"], dict):
        login_data = result["output"].get("login", {})
        user_data = login_data.get("user", {})
        _root_folder_id_cache = user_data.get("rootFolderId")
        return _root_folder_id_cache
    return None

def resolve_path_to_uuid(path: str) -> tuple[str, str]:
    """
    Resolves a path like 'folder/subfolder/file.txt' to its (UUID, type).
    Returns (UUID, type) if found, otherwise raises ValueError.
    Type is either 'folder' or 'file'.
    """
    if not path or path in ["/", "root"]:
        return get_root_folder_id(), "folder"

    parts = [p for p in path.strip("/").split("/") if p]
    current_id = get_root_folder_id()
    current_type = "folder"

    for i, part in enumerate(parts):
        res = run_internxt(["list", "--id", current_id])
        if not res["success"]:
            raise ValueError(f"Failed to list folder at '{'/'.join(parts[:i])}': {res['output']}")
        
        output = res.get("output", {})
        if not isinstance(output, dict):
            raise ValueError(f"Unexpected output format from 'list': {output}")
            
        list_data = output.get("list", {})
        folders = list_data.get("folders", [])
        files = list_data.get("files", [])

        found = False
        # Look for folder
        for folder in folders:
            if folder.get("plainName") == part:
                current_id = folder.get("uuid")
                current_type = "folder"
                found = True
                break
        
        if not found and i == len(parts) - 1:
            # Check files if it's the last part
            for file in files:
                if file.get("plainName") == part:
                    current_id = file.get("uuid")
                    current_type = "file"
                    found = True
                    break
        
        if not found:
            raise ValueError(f"Item '{part}' not found in path '{path}'")
    
    return current_id, current_type

def run_internxt(args: list[str], timeout: int | None = 60) -> dict[str, Any]:
    """
    Executes `internxt <args>` with --json and -x (non-interactive) flags.
    Returns {"success": bool, "output": str | dict}.
    """
    cmd = ["internxt"] + args + ["--json", "-x"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            return {
                "success": False,
                "output": stderr or stdout or f"Exit code {result.returncode}",
            }

        if stdout:
            try:
                parsed = json.loads(stdout)
                return {"success": True, "output": parsed}
            except json.JSONDecodeError:
                return {"success": True, "output": stdout}

        return {"success": True, "output": "OK"}

    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"Timeout after {timeout}s"}
    except FileNotFoundError:
        return {
            "success": False,
            "output": "Command 'internxt' not found. Install it with: npm install -g @internxt/cli",
        }

def fmt(result: dict[str, Any]) -> str:
    out = result["output"]
    if isinstance(out, (dict, list)):
        return json.dumps(out, indent=2, ensure_ascii=False)
    return str(out)

# ---------------------------------------------------------------------------
# Server Initialization
# ---------------------------------------------------------------------------

mcp = FastMCP("internxt")

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def internxt_whoami() -> str:
    """Shows the user currently logged in to the Internxt CLI."""
    result = run_internxt(["whoami"])
    return f"{'✅' if result['success'] else '❌'} {fmt(result)}"

@mcp.tool()
def internxt_config() -> str:
    """Shows configuration and information for the logged-in user."""
    result = run_internxt(["config"])
    return f"{'✅' if result['success'] else '❌'} {fmt(result)}"

@mcp.tool()
def internxt_logout() -> str:
    """Logs out from the Internxt account in the CLI."""
    result = run_internxt(["logout"])
    return f"{'✅' if result['success'] else '❌'} {fmt(result)}"

@mcp.tool()
def internxt_list(path: str | None = None, folder_id: str | None = None) -> str:
    """
    Lists the contents of an Internxt Drive folder.
    Accepts either a human-readable path (e.g., 'Photos/Summer') or a folder UUID.
    If neither is specified, it lists the root folder.

    Args:
        path: Human-readable path to list (e.g., 'Documents/Work').
        folder_id: UUID of the folder to list (fallback).
    """
    try:
        if not folder_id and path:
            folder_id, _ = resolve_path_to_uuid(path)
        cmd = ["list"]
        if folder_id:
            cmd += ["-i", folder_id]
        res = run_internxt(cmd)
        if res["success"] and isinstance(res["output"], dict):
            list_data = res["output"].get("list", {})
            folders = list_data.get("folders", [])
            files = list_data.get("files", [])
            clean = []
            for f in folders:
                clean.append({"name": f.get("plainName"), "type": "folder", "uuid": f.get("uuid")})
            for f in files:
                clean.append({"name": f.get("plainName"), "type": "file", "uuid": f.get("uuid"), "size": f.get("size")})
            result = {"success": True, "output": clean}
            return f"✅ {fmt(result)}"
        return f"{'✅' if res['success'] else '❌'} {fmt(res)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_create_folder(name: str, parent_path: str | None = None, parent_id: str | None = None) -> str:
    """
    Creates a new folder in Internxt Drive.

    Args:
        name: Name of the new folder.
        parent_path: Human-readable path of the parent folder.
        parent_id: UUID of the parent folder (fallback).
    """
    try:
        if not parent_id and parent_path:
            parent_id, _ = resolve_path_to_uuid(parent_path)
        cmd = ["create-folder", "-n", name]
        if parent_id:
            cmd += ["-i", parent_id]
        result = run_internxt(cmd)
        return f"{'✅' if result['success'] else '❌'} {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_upload(file_path: str, destination_path: str | None = None, folder_id: str | None = None) -> str:
    """
    Uploads a local file to Internxt Drive. For multiple files, upload them one by one.

    Args:
        file_path: Local path of the file to upload.
        destination_path: Remote path where the file will be uploaded.
        folder_id: UUID of the destination folder (fallback).
    """
    try:
        if not folder_id and destination_path:
            folder_id, _ = resolve_path_to_uuid(destination_path)
        cmd = ["upload-file", "-f", file_path]
        if folder_id:
            cmd += ["-i", folder_id]
        # No timeout for uploads
        result = run_internxt(cmd, timeout=None)
        return f"{'✅' if result['success'] else '❌'} {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_download(directory: str, path: str | None = None, file_id: str | None = None, overwrite: bool = False) -> str:
    """
    Downloads a file from Internxt Drive. For multiple files, download them one by one.

    Args:
        directory: Local directory path where the file will be saved.
        path: Human-readable path of the file to download.
        file_id: UUID of the file to download (fallback).
        overwrite: Overwrite the file if it already exists.
    """
    try:
        if not file_id and path:
            file_id, _ = resolve_path_to_uuid(path)
        if not file_id:
            return "❌ Error: File ID or path required."
        cmd = ["download-file", "-i", file_id, "-d", directory]
        if overwrite:
            cmd.append("--overwrite")
        # No timeout for downloads
        result = run_internxt(cmd, timeout=None)
        return f"{'✅' if result['success'] else '❌'} {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_delete_permanently(path: str | None = None, item_id: str | None = None) -> str:
    """
    PERMANENTLY deletes a file or folder (irreversible).

    Args:
        path: Human-readable path of the item to delete.
        item_id: UUID of the item to delete (fallback).
    """
    try:
        item_type = None
        if not item_id and path:
            item_id, item_type = resolve_path_to_uuid(path)
        if not item_id:
            return "❌ Error: Item ID or path required."
        cmd_name = "delete-permanently-folder" if item_type == "folder" else "delete-permanently-file"
        result = run_internxt([cmd_name, "-i", item_id])
        return f"{'✅' if result['success'] else '❌'} {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_move(path: str | None = None, item_id: str | None = None, destination_path: str | None = None, destination_id: str | None = None) -> str:
    """
    Moves a file or folder into another folder.

    Args:
        path: Human-readable path of the item to move.
        item_id: UUID of the item to move (fallback).
        destination_path: Human-readable path of the destination folder.
        destination_id: UUID of the destination folder (fallback).
    """
    try:
        item_type = None
        if not item_id and path:
            item_id, item_type = resolve_path_to_uuid(path)
        if not destination_id and destination_path:
            destination_id, _ = resolve_path_to_uuid(destination_path)
        if not item_id or not destination_id:
            return "❌ Error: Item and destination required."
        cmd_name = "move-folder" if item_type == "folder" else "move-file"
        result = run_internxt([cmd_name, "-i", item_id, "-d", destination_id])
        return f"{'✅' if result['success'] else '❌'} {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_trash(path: str | None = None, item_id: str | None = None) -> str:
    """
    Moves a file or folder to the trash.

    Args:
        path: Human-readable path of the item to trash.
        item_id: UUID of the item to trash (fallback).
    """
    try:
        item_type = None
        if not item_id and path:
            item_id, item_type = resolve_path_to_uuid(path)
        if not item_id:
            return "❌ Error: Item ID or path required."
        cmd_name = "trash-folder" if item_type == "folder" else "trash-file"
        result = run_internxt([cmd_name, "-i", item_id])
        return f"{'✅' if result['success'] else '❌'} {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_check_auth() -> str:
    """Verifies if the user is logged into the Internxt CLI."""
    result = run_internxt(["whoami"])
    if result["success"]:
        out = result["output"]
        email = out.get("email", out) if isinstance(out, dict) else out
        return f"✅ Logged in as: {email}"
    return "❌ Not logged in. Run 'internxt login'."

@mcp.tool()
def internxt_webdav(action: str) -> str:
    """
    Manages the Internxt local WebDAV server (enable, disable, restart, status).

    Args:
        action: Action to perform ('enable', 'disable', 'restart', 'status').
    """
    result = run_internxt(["webdav", action])
    return f"{'✅' if result['success'] else '❌'} {fmt(result)}"

@mcp.tool()
def internxt_workspaces_list() -> str:
    """Lists available workspaces for the user."""
    result = run_internxt(["workspaces", "list"])
    return f"{'✅' if result['success'] else '❌'} {fmt(result)}"

@mcp.tool()
def internxt_generate_upload_script(file_paths: list[str], destination_path: str | None = None, destination_id: str | None = None) -> str:
    """
    Generates a shell script containing 'internxt upload-file' commands for one or more files.

    Args:
        file_paths: List of local file paths to upload.
        destination_path: Remote path where the files will be uploaded.
        destination_id: UUID of the destination folder (fallback).
    """
    try:
        if not destination_id and destination_path:
            destination_id, _ = resolve_path_to_uuid(destination_path)
        
        # Default to root if no ID or path is provided
        if not destination_id:
            destination_id = get_root_folder_id()
            
        script_lines = ["#!/bin/bash"]
        for f in file_paths:
            # Basic escaping for paths with spaces
            escaped_f = f"\"{f}\"" if " " in f else f
            script_lines.append(f"internxt upload-file -i {destination_id} -f {escaped_f}")
        
        result = {"success": True, "output": "\n".join(script_lines)}
        return f"✅ {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
def internxt_generate_download_script(directory: str, remote_paths: list[str] | None = None, file_ids: list[str] | None = None, overwrite: bool = False) -> str:
    """
    Generates a shell script containing 'internxt download-file' commands for one or more files.

    Args:
        directory: Local directory path where the files will be saved.
        remote_paths: List of remote file paths to download.
        file_ids: List of file UUIDs to download (fallback).
        overwrite: Include the overwrite flag in the commands.
    """
    try:
        overwrite_flag = " -o" if overwrite else ""
        script_lines = ["#!/bin/bash"]
        
        # Handle remote paths
        if remote_paths:
            for p in remote_paths:
                file_id, _ = resolve_path_to_uuid(p)
                script_lines.append(f"internxt download-file -i {file_id} -d {directory}{overwrite_flag}")
        
        # Handle file IDs
        if file_ids:
            for fid in file_ids:
                script_lines.append(f"internxt download-file -i {fid} -d {directory}{overwrite_flag}")
        
        result = {"success": True, "output": "\n".join(script_lines)}
        return f"✅ {fmt(result)}"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main_sync():
    mcp.run()

if __name__ == "__main__":
    main_sync()
