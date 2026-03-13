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

import asyncio
import json
import sys
from typing import Any, Literal

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

# ---------------------------------------------------------------------------
# Helpers & Path Resolution
# ---------------------------------------------------------------------------

_root_folder_id_cache = None

async def get_root_folder_id() -> str:
    global _root_folder_id_cache
    if _root_folder_id_cache:
        return _root_folder_id_cache
    
    result = await run_internxt(["whoami"])
    if result["success"] and isinstance(result["output"], dict):
        login_data = result["output"].get("login", {})
        user_data = login_data.get("user", {})
        _root_folder_id_cache = user_data.get("rootFolderId")
        return _root_folder_id_cache
    return None

async def resolve_path_to_uuid(path: str) -> tuple[str, str]:
    """
    Resolves a path like 'folder/subfolder/file.txt' to its (UUID, type).
    Returns (UUID, type) if found, otherwise raises ValueError.
    Type is either 'folder' or 'file'.
    """
    if not path or path in ["/", "root"]:
        root_id = await get_root_folder_id()
        return root_id, "folder"

    parts = [p for p in path.strip("/").split("/") if p]
    current_id = await get_root_folder_id()
    current_type = "folder"

    for i, part in enumerate(parts):
        res = await run_internxt(["list", "-i", current_id])
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

async def run_internxt(args: list[str], timeout: int | None = 60) -> dict[str, Any]:
    """
    Executes `internxt <args>` with --json and -x (non-interactive) flags.
    Returns {"success": bool, "output": str | dict}.
    """
    cmd = ["internxt"] + args + ["--json", "-x"]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        try:
            if timeout:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            else:
                stdout, stderr = await process.communicate()
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            return {"success": False, "output": f"Timeout after {timeout}s"}

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if process.returncode != 0:
            return {
                "success": False,
                "output": stderr_str or stdout_str or f"Exit code {process.returncode}",
            }

        if stdout_str:
            try:
                parsed = json.loads(stdout_str)
                return {"success": True, "output": parsed}
            except json.JSONDecodeError:
                return {"success": True, "output": stdout_str}

        return {"success": True, "output": "OK"}

    except Exception as e:
        return {"success": False, "output": str(e)}

def fmt(result: dict[str, Any]) -> str:
    out = result["output"]
    status = "✅" if result["success"] else "❌"
    if isinstance(out, (dict, list)):
        return f"{status} {json.dumps(out, indent=2, ensure_ascii=False)}"
    return f"{status} {str(out)}"

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

server = Server("internxt")

@server.tool()
async def internxt_whoami() -> str:
    """Shows the user currently logged in to the Internxt CLI."""
    return fmt(await run_internxt(["whoami"]))

@server.tool()
async def internxt_config() -> str:
    """Shows configuration and information for the logged-in user."""
    return fmt(await run_internxt(["config"]))

@server.tool()
async def internxt_logout() -> str:
    """Logs out from the Internxt account in the CLI."""
    return fmt(await run_internxt(["logout"]))

@server.tool()
async def internxt_list(path: str | None = None, folder_id: str | None = None) -> str:
    """
    Lists the contents of an Internxt Drive folder.
    Accepts either a human-readable path (e.g., 'Photos/Summer') or a folder UUID.
    If neither is specified, it lists the root folder.
    """
    try:
        if not folder_id and path:
            folder_id, _ = await resolve_path_to_uuid(path)
        
        cmd = ["list"]
        if folder_id:
            cmd += ["-i", folder_id]
            
        res = await run_internxt(cmd)
        if res["success"] and isinstance(res["output"], dict):
            list_data = res["output"].get("list", {})
            folders = list_data.get("folders", [])
            files = list_data.get("files", [])
            clean = []
            for f in folders:
                clean.append({"name": f.get("plainName"), "type": "folder", "uuid": f.get("uuid")})
            for f in files:
                clean.append({"name": f.get("plainName"), "type": "file", "uuid": f.get("uuid"), "size": f.get("size")})
            return fmt({"success": True, "output": clean})
        return fmt(res)
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_create_folder(name: str, parent_path: str | None = None, parent_id: str | None = None) -> str:
    """Creates a new folder in Internxt Drive."""
    try:
        if not parent_id and parent_path:
            parent_id, _ = await resolve_path_to_uuid(parent_path)
        
        cmd = ["create-folder", "-n", name]
        if parent_id:
            cmd += ["-i", parent_id]
        return fmt(await run_internxt(cmd))
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_upload(file_path: str, destination_path: str | None = None, folder_id: str | None = None) -> str:
    """Uploads a local file to Internxt Drive. For multiple files, upload them one by one."""
    try:
        if not folder_id and destination_path:
            folder_id, _ = await resolve_path_to_uuid(destination_path)
        
        cmd = ["upload-file", "-f", file_path]
        if folder_id:
            cmd += ["-i", folder_id]
        # No timeout for uploads
        return fmt(await run_internxt(cmd, timeout=None))
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_download(directory: str, path: str | None = None, file_id: str | None = None, overwrite: bool = False) -> str:
    """Downloads a file from Internxt Drive. For multiple files, download them one by one."""
    try:
        if not file_id and path:
            file_id, _ = await resolve_path_to_uuid(path)
        
        if not file_id:
            return "❌ Error: File ID or path required."
            
        cmd = ["download-file", "-i", file_id, "-d", directory]
        if overwrite:
            cmd.append("--overwrite")
        # No timeout for downloads
        return fmt(await run_internxt(cmd, timeout=None))
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_delete_permanently(path: str | None = None, item_id: str | None = None) -> str:
    """PERMANENTLY deletes a file or folder (irreversible)."""
    try:
        item_type = None
        if not item_id and path:
            item_id, item_type = await resolve_path_to_uuid(path)
        
        if not item_id:
            return "❌ Error: Item ID or path required."
        
        cmd_name = "delete-permanently-folder" if item_type == "folder" else "delete-permanently-file"
        return fmt(await run_internxt([cmd_name, "-i", item_id]))
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_move(path: str | None = None, item_id: str | None = None, destination_path: str | None = None, destination_id: str | None = None) -> str:
    """Moves a file or folder into another folder."""
    try:
        item_type = None
        if not item_id and path:
            item_id, item_type = await resolve_path_to_uuid(path)
        
        if not destination_id and destination_path:
            destination_id, _ = await resolve_path_to_uuid(destination_path)
            
        if not item_id or not destination_id:
            return "❌ Error: Item and destination required."
            
        cmd_name = "move-folder" if item_type == "folder" else "move-file"
        return fmt(await run_internxt([cmd_name, "-i", item_id, "-d", destination_id]))
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_trash(path: str | None = None, item_id: str | None = None) -> str:
    """Moves a file or folder to the trash."""
    try:
        item_type = None
        if not item_id and path:
            item_id, item_type = await resolve_path_to_uuid(path)
            
        if not item_id:
            return "❌ Error: Item ID or path required."
            
        cmd_name = "trash-folder" if item_type == "folder" else "trash-file"
        return fmt(await run_internxt([cmd_name, "-i", item_id]))
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_check_auth() -> str:
    """Verifies if the user is logged into the Internxt CLI."""
    result = await run_internxt(["whoami"])
    if result["success"]:
        out = result["output"]
        email = out.get("email", out) if isinstance(out, dict) else out
        return f"✅ Logged in as: {email}"
    return "❌ Not logged in. Run 'internxt login'."

@server.tool()
async def internxt_webdav(action: Literal["enable", "disable", "restart", "status"]) -> str:
    """Manages the Internxt local WebDAV server."""
    return fmt(await run_internxt(["webdav", action]))

@server.tool()
async def internxt_workspaces_list() -> str:
    """Lists available workspaces for the user."""
    return fmt(await run_internxt(["workspaces", "list"]))

@server.tool()
async def internxt_generate_upload_script(file_paths: list[str], destination_path: str | None = None, destination_id: str | None = None) -> str:
    """Generates a shell script containing 'internxt upload-file' commands for one or more files."""
    try:
        if not destination_id and destination_path:
            destination_id, _ = await resolve_path_to_uuid(destination_path)
        
        if not destination_id:
            destination_id = await get_root_folder_id()
            
        script_lines = ["#!/bin/bash"]
        for f in file_paths:
            escaped_f = f'"{f}"' if " " in f else f
            script_lines.append(f"internxt upload-file -i {destination_id} -f {escaped_f}")
        
        return "\n".join(script_lines)
    except ValueError as e:
        return f"❌ Error: {str(e)}"

@server.tool()
async def internxt_generate_download_script(directory: str, remote_paths: list[str] | None = None, file_ids: list[str] | None = None, overwrite: bool = False) -> str:
    """Generates a shell script containing 'internxt download-file' commands for one or more files."""
    try:
        overwrite_flag = " -o" if overwrite else ""
        script_lines = ["#!/bin/bash"]
        
        if remote_paths:
            for p in remote_paths:
                file_id, _ = await resolve_path_to_uuid(p)
                script_lines.append(f"internxt download-file -i {file_id} -d {directory}{overwrite_flag}")
        
        if file_ids:
            for fid in file_ids:
                script_lines.append(f"internxt download-file -i {fid} -d {directory}{overwrite_flag}")
        
        return "\n".join(script_lines)
    except ValueError as e:
        return f"❌ Error: {str(e)}"

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

def main_sync():
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()
