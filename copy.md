# Simple Password Manager (CLI)

A simple command-line password manager built for learning purposes.  
It stores credentials (site, username, password) in a local JSON file and allows adding, retrieving, updating, deleting, listing, searching, exporting, and showing statistics.

⚠️ **Disclaimer:** This project is for **educational use only**. Do not store real passwords.

---

## Usage

```bash
python passman.py <command> [arguments] [--file store.json]
```

If `--file` is not provided, the default file `store.json` will be used.

---

## Commands

### init
Create a new password store file.

```bash
python passman.py init [--file store.json]
```

### add
Add a new entry for a site.

```bash
python passman.py add <site> <username> <password> [--file store.json]
```

### get
Retrieve credentials for a given site.

```bash
python passman.py get <site> [--file store.json]
```

### update
Update the username and/or password for an existing site.

```bash
python passman.py update <site> [--username new_user] [--password new_pass] [--file store.json]
```

### delete
Delete an entry by site name.

```bash
python passman.py delete <site> [--file store.json]
```

### list
List all entries in the store.

```bash
python passman.py list [--sort site|last_updated] [--file store.json]
```

### search
Search for a keyword in site names or usernames.

```bash
python passman.py search <keyword> [--file store.json]
```

### export
Export all entries to CSV format.

```bash
python passman.py export csv --out export.csv [--file store.json]
```

### stats
Show statistics about the store (number of entries, oldest/newest entry, average password length, etc.).

```bash
python passman.py stats [--file store.json]
```

---

## JSON Schema

The password store is saved as a single JSON file with the following structure:

```json
{
  "metadata": {
    "version": 1,
    "created_at": "2025-09-04T14:00:00Z",
    "updated_at": "2025-09-04T14:05:00Z",
    "count": 2
  },
  "entries": {
    "github": {
      "username": "alice",
      "password": "mypass123",
      "last_updated": "2025-09-04T14:00:00Z"
    },
    "gmail": {
      "username": "alice.mail",
      "password": "secretpass",
      "last_updated": "2025-09-04T14:05:00Z"
    }
  }
}
```

- **metadata** → contains version, timestamps, and entry count.  
- **entries** → dictionary where each key is a site name, mapping to its credentials.  
- Each entry has: `username`, `password`, and `last_updated`.

---

## Example Workflow

```bash
$ python passman.py init store.json
Created new password store at store.json.

$ python passman.py add github alice mypass123 --file store.json
Added: github (alice)

$ python passman.py add gmail alice.mail secretpass --file store.json
Added: gmail (alice.mail)

$ python passman.py list --file store.json
SITE      USERNAME     LAST_UPDATED
github    alice        2025-09-04T14:00:00Z
gmail     alice.mail   2025-09-04T14:05:00Z

$ python passman.py get github --file store.json
site: github
username: alice
password: mypass123
last_updated: 2025-09-04T14:00:00Z

$ python passman.py update github --password newpass999 --file store.json
Updated: github (password changed)

$ python passman.py delete gmail --file store.json
Deleted: gmail

$ python passman.py stats --file store.json
entries: 1
oldest:  2025-09-04T14:00:00Z
newest:  2025-09-04T14:10:00Z
avg password length: 10
```

---

## Notes
- All operations are done via the command line.  
- The program uses a single JSON file as its database.  
- This project is a **practice exercise** in command-line arguments, file I/O, and data manipulation.  
- For security reasons, **never store real passwords** in this manager.
