# Internxt MCP Server

An MCP server for [Internxt Drive CLI](https://github.com/internxt/cli).. This server allows AI agents (like Claude) to interact with your encrypted Internxt Drive using natural language and human-readable paths. Please note Internxt Drive CLI is available for Internxt users on the Ultimate plan. Refer to [Internxt Web page](https://internxt.com) for more information.


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

### With uvx (Recommended)

The easiest way to use this server is with `uvx`. No manual installation of the script is required:

```json
{
  "mcpServers": {
    "internxt": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mamorett/internxt-mcp", "internxt-mcp"]
    }
  }
}
```

### Manual Installation (Claude Desktop)

If you prefer to run the script directly:

1. Clone the repository: `git clone https://github.com/mamorett/internxt-mcp`
2. Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "internxt": {
      "command": "python",
      "args": ["/absolute/path/to/internxt_mcp_server.py"]
    }
  }
}
```

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

#### `internxt_generate_upload_script`
**Description:** Generates a shell script containing `internxt upload-file` commands for one or more local files. This is useful for batch uploads that you want to run yourself.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_paths` | array[string] | Yes | List of local file paths to upload |
| `destination_path` | string | No | Remote path where the files will be uploaded |
| `destination_id` | string | No | Destination folder UUID (fallback) |

---

#### `internxt_generate_download_script`
**Description:** Generates a shell script containing `internxt download-file` commands for one or more files.
**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `remote_paths` | array[string] | No | List of remote file paths to download |
| `file_ids` | array[string] | No | List of file UUIDs to download (fallback) |
| `directory` | string | Yes | Local directory path where the files will be saved |
| `overwrite` | boolean | No | Include the overwrite flag in the commands (default: `false`) |

---

#### `internxt_workspaces_list`
**Description:** Lists available workspaces for the user (for business/team accounts).
**Parameters:** None

---

## Usage Guidelines

- **Sequential Operations**: When uploading or downloading multiple files, perform the operations **one by one**. Wait for each operation to complete before starting the next one.
- **No Timeouts**: Upload and download operations have no timeout set at the MCP level to accommodate large files or slow connections. However, ensure your MCP client (like Claude) doesn't have its own session timeout.
- **Path Support**: Use human-readable paths (e.g., `Documents/Reports/2023.pdf`). The server will automatically resolve these to the internal UUIDs required by Internxt.

## Development

```bash
git clone https://github.com/mamorett/internxt-mcp
cd internxt-mcp
# Run the server via stdio
python internxt_mcp_server.py
```

---
*Created with ❤️ for the Internxt community.*
