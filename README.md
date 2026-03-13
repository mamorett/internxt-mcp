# Internxt MCP Server

An MCP server for [Internxt Drive CLI](https://github.com/internxt/cli). This server allows AI agents (like Claude) to interact with your encrypted Internxt Drive using natural language and human-readable paths.

## Key Features

- **Path-based Navigation**: Use human-readable paths like `Documents/Work/report.pdf` instead of cryptic UUIDs.
- **Smart Tooling**: Automatically resolves names to IDs and selects the correct CLI commands (e.g., differentiating between moving a file vs. a folder).
- **Full Drive Management**: List, upload, download, move, trash, and permanently delete files and folders.
- **WebDAV & Workspace Support**: Manage your local WebDAV server and list workspaces directly.

## Prerequisites

- **Python**: 3.11+
- **Internxt CLI**: `npm install -g @internxt/cli`
- **Authentication**: Run `internxt login` once in your terminal to authenticate.

## Installation

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "internxt": {
      "command": "python",
      "args": ["/path/to/internxt_mcp_server.py"]
    }
  }
}
```

*Note: Replace `/path/to/` with the actual path to the script.*

---

## Detailed Tool Reference

### 📂 Navigation & Discovery

#### `internxt_list`
**Description:** Lists the contents (files and folders) of a Drive folder.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | No | Human-readable path to list (e.g., `Documents/Work`) |
| `folder_id` | string | No | UUID of the folder to list (fallback) |

---

#### `internxt_check_auth`
**Description:** Verifies if you are logged into the Internxt CLI. Use this first before any operation.
**Parameters:** None

---

#### `internxt_whoami`
**Description:** Shows detailed information about the currently logged-in user.
**Parameters:** None

---

#### `internxt_config`
**Description:** Displays configuration settings and account information.
**Parameters:** None

---

### 📄 File Operations

#### `internxt_upload`
**Description:** Uploads a local file to Internxt Drive. Automatically handles encryption before upload.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Local path of the file to upload |
| `destination_path` | string | No | Remote path where the file will be uploaded (e.g., `Backups/DB`) |
| `folder_id` | string | No | Destination folder UUID (fallback) |

---

#### `internxt_download`
**Description:** Downloads and decrypts a file from Internxt Drive to a local directory.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | No | Remote path of the file to download |
| `file_id` | string | No | UUID of the file to download (fallback) |
| `directory` | string | Yes | Local directory path where the file will be saved |
| `overwrite` | boolean | No | Overwrite the file if it already exists (default: `false`) |

---

#### `internxt_delete_permanently`
**Description:** Permanently deletes a file or folder. This action is **irreversible**.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | No | Remote path of the item to delete |
| `item_id` | string | No | UUID of the item to delete (fallback) |

---

### 📁 Folder Operations

#### `internxt_create_folder`
**Description:** Creates a new folder in Internxt Drive.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Name of the new folder |
| `parent_path` | string | No | Remote path of the parent folder |
| `parent_id` | string | No | UUID of the parent folder (fallback) |

---

#### `internxt_move`
**Description:** Moves a file or folder to another location in Drive.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | No | Remote path of the item to move |
| `item_id` | string | No | UUID of the item to move (fallback) |
| `destination_path` | string | No | Remote path of the destination folder |
| `destination_id` | string | No | UUID of the destination folder (fallback) |

---

#### `internxt_trash`
**Description:** Moves a file or folder to the trash. Items in trash can be recovered later.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | No | Remote path of the item to trash |
| `item_id` | string | No | UUID of the item to trash (fallback) |

---

### 🔧 System & Workspaces

#### `internxt_webdav`
**Description:** Manages the local WebDAV server for accessing Drive as a network drive.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | Action to perform: `enable`, `disable`, `restart`, or `status` |

---

#### `internxt_workspaces_list`
**Description:** Lists available workspaces for the user (for business/team accounts).
**Parameters:** None

---

## Path Support Tips

- **Root**: Use `/` or leave the path empty to refer to your root folder.
- **Paths**: Use forward slashes (e.g., `Documents/Invoices/2023`).
- **Ambiguity**: If a path is ambiguous or resolution fails, you can always fallback to using the `uuid` directly.

## Development

```bash
git clone https://github.com/mamorett/internxt-mcp
cd internxt-mcp
# Run the server via stdio
python internxt_mcp_server.py
```

---
*Created with ❤️ for the Internxt community.*
