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
import subprocess
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

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

def run_internxt(args: list[str], timeout: int = 60) -> dict[str, Any]:
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
# Server
# ---------------------------------------------------------------------------

server = Server("internxt")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="internxt_whoami",
            description="Shows the user currently logged in to the Internxt CLI.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="internxt_config",
            description="Shows configuration and information for the logged-in user.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="internxt_logout",
            description="Logs out from the Internxt account in the CLI.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="internxt_list",
            description=(
                "Lists the contents of an Internxt Drive folder. "
                "Accepts either a human-readable path (e.g., 'Photos/Summer') or a folder UUID. "
                "If neither is specified, it lists the root folder."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Human-readable path to list (e.g., 'Documents/Work').",
                    },
                    "folder_id": {
                        "type": "string",
                        "description": "UUID of the folder to list.",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="internxt_create_folder",
            description="Creates a new folder in Internxt Drive.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the new folder.",
                    },
                    "parent_path": {
                        "type": "string",
                        "description": "Human-readable path of the parent folder.",
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "UUID of the parent folder.",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="internxt_upload",
            description="Uploads a local file to Internxt Drive.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Local path of the file to upload.",
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "Remote path where the file will be uploaded.",
                    },
                    "folder_id": {
                        "type": "string",
                        "description": "UUID of the destination folder.",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="internxt_download",
            description="Downloads a file from Internxt Drive.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Human-readable path of the file to download.",
                    },
                    "file_id": {
                        "type": "string",
                        "description": "UUID of the file to download.",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Local directory path where the file will be saved.",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite the file if it already exists.",
                        "default": False,
                    },
                },
                "required": ["directory"],
            },
        ),
        Tool(
            name="internxt_delete_permanently",
            description="PERMANENTLY deletes a file or folder (irreversible).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Human-readable path of the item to delete.",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "UUID of the item to delete.",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="internxt_move",
            description="Moves a file or folder into another folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Human-readable path of the item to move.",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "UUID of the item to move.",
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "Human-readable path of the destination folder.",
                    },
                    "destination_id": {
                        "type": "string",
                        "description": "UUID of the destination folder.",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="internxt_trash",
            description="Moves a file or folder to the trash.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Human-readable path of the item to trash.",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "UUID of the item to trash.",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="internxt_check_auth",
            description="Verifies if the user is logged into the Internxt CLI.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="internxt_webdav",
            description="Manages the Internxt local WebDAV server (enable, disable, restart, status).",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["enable", "disable", "restart", "status"],
                    }
                },
                "required": ["action"],
            },
        ),
        Tool(
            name="internxt_workspaces_list",
            description="Lists available workspaces for the user.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        result = _dispatch(name, arguments)
        status = "✅" if result["success"] else "❌"
        return [TextContent(type="text", text=f"{status} {fmt(result)}")]
    except ValueError as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Unexpected error: {str(e)}")]

def _dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    match name:
        case "internxt_check_auth":
            result = run_internxt(["whoami"])
            if result["success"]:
                out = result["output"]
                email = out.get("email", out) if isinstance(out, dict) else out
                return {"success": True, "output": f"✅ Logged in as: {email}"}
            return {"success": False, "output": "❌ Not logged in. Run 'internxt login'."}

        case "internxt_whoami":
            return run_internxt(["whoami"])

        case "internxt_config":
            return run_internxt(["config"])

        case "internxt_logout":
            return run_internxt(["logout"])

        case "internxt_list":
            folder_id = args.get("folder_id")
            if not folder_id and (path := args.get("path")):
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
                return {"success": True, "output": clean}
            return res

        case "internxt_create_folder":
            parent_id = args.get("parent_id")
            if not parent_id and (path := args.get("parent_path")):
                parent_id, _ = resolve_path_to_uuid(path)
            cmd = ["create-folder", "-n", args["name"]]
            if parent_id:
                cmd += ["-i", parent_id]
            return run_internxt(cmd)

        case "internxt_upload":
            folder_id = args.get("folder_id")
            if not folder_id and (path := args.get("destination_path")):
                folder_id, _ = resolve_path_to_uuid(path)
            cmd = ["upload-file", "-f", args["file_path"]]
            if folder_id:
                cmd += ["-i", folder_id]
            return run_internxt(cmd, timeout=300)

        case "internxt_download":
            file_id = args.get("file_id")
            if not file_id and (path := args.get("path")):
                file_id, _ = resolve_path_to_uuid(path)
            if not file_id:
                return {"success": False, "output": "File ID or path required."}
            cmd = ["download-file", "-i", file_id, "-d", args["directory"]]
            if args.get("overwrite"):
                cmd.append("--overwrite")
            return run_internxt(cmd, timeout=300)

        case "internxt_delete_permanently":
            item_id = args.get("item_id")
            item_type = None
            if not item_id and (path := args.get("path")):
                item_id, item_type = resolve_path_to_uuid(path)
            if not item_id:
                return {"success": False, "output": "Item ID or path required."}
            cmd_name = "delete-permanently-folder" if item_type == "folder" else "delete-permanently-file"
            return run_internxt([cmd_name, "-i", item_id])

        case "internxt_move":
            item_id = args.get("item_id")
            item_type = None
            if not item_id and (path := args.get("path")):
                item_id, item_type = resolve_path_to_uuid(path)
            dest_id = args.get("destination_id")
            if not dest_id and (dpath := args.get("destination_path")):
                dest_id, _ = resolve_path_to_uuid(dpath)
            if not item_id or not dest_id:
                return {"success": False, "output": "Item and destination required."}
            cmd_name = "move-folder" if item_type == "folder" else "move-file"
            return run_internxt([cmd_name, "-i", item_id, "-d", dest_id])

        case "internxt_trash":
            item_id = args.get("item_id")
            item_type = None
            if not item_id and (path := args.get("path")):
                item_id, item_type = resolve_path_to_uuid(path)
            if not item_id:
                return {"success": False, "output": "Item ID or path required."}
            cmd_name = "trash-folder" if item_type == "folder" else "trash-file"
            return run_internxt([cmd_name, "-i", item_id])

        case "internxt_webdav":
            return run_internxt(["webdav", args["action"]])

        case "internxt_workspaces_list":
            return run_internxt(["workspaces", "list"])

        case _:
            return {"success": False, "output": f"Unknown tool: {name}"}

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

def main_sync():
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()
