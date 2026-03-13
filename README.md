# internxt-mcp

MCP server for [Internxt Drive CLI](https://github.com/internxt/cli).  
Lets Claude (or any MCP client) interact with your Internxt Drive via natural language.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (for uvx usage)
- Internxt CLI: `npm install -g @internxt/cli`
- One-time login: `internxt login`

## Installation & usage

### With uvx (recommended)

No installation needed — uvx runs it directly from GitHub:

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

### From source

```bash
git clone https://github.com/mamorett/internxt-mcp
cd internxt-mcp
uv run internxt_mcp_server.py
```

## Available Tools

The MCP server exports **15 tools** organized into categories: authentication, navigation, folder operations, file operations, movement/trash, WebDAV, and workspaces.

### Quick Reference

| Tool | Category | Description |
|------|----------|-------------|
| `internxt_check_auth` | Auth | Verifies login status |
| `internxt_whoami` | Auth | Shows the logged-in user |
| `internxt_config` | Auth | Shows account configuration |
| `internxt_logout` | Auth | Logs out from Internxt |
| `internxt_list` | Navigation | Lists folder contents |
| `internxt_create_folder` | Folders | Creates a new folder |
| `internxt_delete_permanently_folder` | Folders | Permanently deletes a folder |
| `internxt_upload` | Files | Uploads a local file |
| `internxt_download` | Files | Downloads a file from Drive |
| `internxt_delete_permanently_file` | Files | Permanently deletes a file |
| `internxt_move` | Movement | Moves items between folders |
| `internxt_trash` | Movement | Sends items to trash |
| `internxt_webdav` | WebDAV | Manages the local WebDAV server |
| `internxt_workspaces_list` | Workspaces | Lists available workspaces |

---

### Authentication & Account

#### `internxt_check_auth`
**Description:** Verifies if you are logged into the Internxt CLI. Use this first before any operation.

**Parameters:** None

**Returns:** Login status and user email if authenticated, or instructions to authenticate.

---

#### `internxt_whoami`
**Description:** Shows detailed information about the currently logged-in user.

**Parameters:** None

**Returns:** User profile information including email, name, and account details.

---

#### `internxt_config`
**Description:** Displays configuration settings and account information.

**Parameters:** None

**Returns:** Configuration details including API endpoints, storage limits, and preferences.

---

#### `internxt_logout`
**Description:** Logs out from the Internxt account in the CLI.

**Parameters:** None

**Returns:** Confirmation of logout.

---

### Navigation

#### `internxt_list`
**Description:** Lists the contents (files and folders) of a Drive folder. If no folder ID is provided, lists the root directory.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `folder_id` | string | No | ID of the folder to list (default: root) |

**Returns:** Array of items with type, name, ID, size, and modification date.

---

### Folder Operations

#### `internxt_create_folder`
**Description:** Creates a new folder in Internxt Drive.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Name of the new folder |
| `parent_id` | string | No | ID of the parent folder (default: root) |

**Returns:** Created folder details including its ID.

---

#### `internxt_delete_permanently_folder`
**Description:** Permanently deletes a folder. This action is **irreversible** and immediately removes the folder and all its contents.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `folder_id` | string | Yes | ID of the folder to delete |

**Warning:** This bypasses trash and cannot be undone.

---

### File Operations

#### `internxt_upload`
**Description:** Uploads a local file to Internxt Drive. Automatically handles encryption before upload.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Local path of the file to upload |
| `folder_id` | string | No | Destination folder ID (default: root) |

**Returns:** Uploaded file details including its ID.

**Timeout:** 5 minutes (files can take longer to upload)

---

#### `internxt_download`
**Description:** Downloads and decrypts a file from Internxt Drive to a local directory.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_id` | string | Yes | - | ID of the file to download (use `internxt_list` to find it) |
| `directory` | string | Yes | - | Local directory path where the file will be saved |
| `overwrite` | boolean | No | `false` | Overwrite the file if it already exists |

**Returns:** Download confirmation with saved file path.

**Timeout:** 5 minutes

---

#### `internxt_delete_permanently_file`
**Description:** Permanently deletes a file. This action is **irreversible**.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | Yes | ID of the file to delete |

**Warning:** This bypasses trash and cannot be undone.

---

### Movement & Trash

#### `internxt_move`
**Description:** Moves a file or folder to another location in Drive.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | string | Yes | ID of the file or folder to move |
| `destination_id` | string | Yes | ID of the destination folder |

**Returns:** Move confirmation with new location details.

---

#### `internxt_trash`
**Description:** Moves a file or folder to the trash. Items in trash can be recovered later.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | string | Yes | ID of the file or folder to put in the trash |

**Note:** Trashed items remain recoverable until permanently deleted.

---

### WebDAV Server

#### `internxt_webdav`
**Description:** Manages the local WebDAV server for accessing Drive as a network drive.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | Action to perform: `enable`, `disable`, `restart`, or `status` |

**Supported Actions:**
- `enable` - Start the WebDAV server
- `disable` - Stop the WebDAV server
- `restart` - Restart the WebDAV server
- `status` - Check if the WebDAV server is running

**Returns:** Current WebDAV status and connection information.

---

### Workspaces

#### `internxt_workspaces_list`
**Description:** Lists available workspaces for the user (for business/team accounts).

**Parameters:** None

**Returns:** List of workspaces with names, IDs, and access permissions.

---

## Common Workflows

### Check Authentication and Browse
```
1. internxt_check_auth
2. internxt_list (to see root contents)
3. internxt_list with folder_id (to navigate deeper)
```

### Upload Workflow
```
1. internxt_check_auth
2. internxt_list (optional: find destination folder)
3. internxt_upload with file_path and optional folder_id
```

### Download Workflow
```
1. internxt_check_auth
2. internxt_list (to find file_id)
3. internxt_download with file_id and directory
```

### Organize with Move
```
1. internxt_list (to find item_id and destination_id)
2. internxt_move with item_id and destination_id
```

### Safe Deletion
```
1. internxt_trash with item_id (recoverable)
2. internxt_delete_permanently_file/folder (only if certain)
```

---

## First run

Before using the MCP server, authenticate once from your terminal:

```bash
internxt login
```

This opens a browser window. After login, the CLI saves a token locally — no further login needed.
