import json  # Built-in module to encode/decode JSON data
import sys   # Provides sys.exit for clean error exits and argv access
import csv   # Built-in module to write CSV files (used in export_csv)
import argparse  # Built-in module to parse command-line arguments
from datetime import datetime  # For timestamps in UTC ISO8601 format


def current_time_in_ISO8601():
    """Return current UTC time as an ISO8601 string like 'YYYY-MM-DDTHH:MM:SSZ'."""  # Function purpose (docstring)
    # e.g., "2025-09-04T14:00:00Z"
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")  # Get UTC "now" and format it as ISO8601 with 'Z'


def init_store(path):
    """Create a new empty password store on disk at 'path' and return it as a dict."""  # Explains effect + return
    store = {  # Construct the in-memory structure that matches our JSON schema
        "metadata": {  # Top-level metadata section
            "version": 1,  # Schema version for future upgrades
            "created_at": current_time_in_ISO8601(),  # When the store was created
            "updated_at": current_time_in_ISO8601(),  # Last time the store changed (same as created_at initially)
            "count": 0  # Number of entries currently stored
        },
        "entries": {}  # Actual credentials live here as site -> {username, password, last_updated}
    }

    with open(path, mode="w", encoding="utf-8") as file:  # Open target file for writing (overwrite) using UTF-8
        json.dump(store, file, indent=2, ensure_ascii=False)  # Serialize 'store' dict to pretty JSON

    print("Created new password store at", path)  # Inform the user where the store was created
    return store  # Return the in-memory store so caller can use it


def load_store(path):
    """Load JSON store from disk or exit with a clear message on error. Returns dict on success."""  # What/return
    try:
        with open(path, mode="r", encoding="utf-8") as f:  # Open the JSON file for reading
            store = json.load(f)  # Parse JSON into a Python dict
            return store  # Return the loaded store to the caller
    except FileNotFoundError:  # Triggered if the file does not exist
        sys.exit("Store file not found. Run 'init' first.")  # Exit with a helpful message
    except json.JSONDecodeError:  # Triggered if the file contents are not valid JSON
        sys.exit("Store file is corrupted. Restore or re-init.")  # Exit with a helpful message


def validate_store_schema(store):
    """
    Validate minimal schema and exit with a clear message if invalid.
    Ensures:
      - top-level keys: metadata (dict), entries (dict)
      - metadata has version:int, created_at:str, updated_at:str, count:int
      - entries is dict of site -> {username:str, password:str, last_updated:str}
      - metadata.count == len(entries)
    """  # Detailed docstring for constraints and behavior
    if not isinstance(store, dict):  # Ensure root is an object/dict
        sys.exit("Invalid store schema: top-level is not an object.")  # Exit if wrong type

    if "metadata" not in store or "entries" not in store:  # Must have both sections
        sys.exit("Invalid store schema: missing 'metadata' or 'entries'.")  # Exit if missing

    meta = store["metadata"]  # Shortcut to metadata dict
    entries = store["entries"]  # Shortcut to entries dict

    if not isinstance(meta, dict) or not isinstance(entries, dict):  # Both must be dicts
        sys.exit("Invalid store schema: 'metadata' or 'entries' is not an object.")  # Exit if wrong types

    # Required metadata fields with expected types:
    for key, typ in (("version", int), ("created_at", str),
                     ("updated_at", str), ("count", int)):  # Iterate required keys and their types
        if key not in meta:  # Check presence
            sys.exit(f"Invalid store schema: metadata missing '{key}'.")  # Exit if missing key
        if not isinstance(meta[key], typ):  # Check type correctness
            sys.exit(f"Invalid store schema: metadata '{key}' must be {typ.__name__}.")  # Exit if wrong type

    # Validate each entry in entries:
    for site, rec in entries.items():  # site: key; rec: value (dict with username/password/last_updated)
        if not isinstance(site, str):  # Site keys must be strings
            sys.exit("Invalid store schema: site keys must be strings.")  # Exit if not string
        if not isinstance(rec, dict):  # Each entry must be an object/dict
            sys.exit(f"Invalid store schema: entry for '{site}' is not an object.")  # Exit if wrong type
        for key, typ in (("username", str), ("password", str), ("last_updated", str)):  # Required fields
            if key not in rec:  # Ensure field exists
                sys.exit(f"Invalid store schema: entry '{site}' missing '{key}'.")  # Exit if missing
            if not isinstance(rec[key], typ):  # Ensure correct type
                sys.exit(f"Invalid store schema: '{site}.{key}' must be {typ.__name__}.")  # Exit if wrong type

    if meta["count"] != len(entries):  # The metadata count must match number of entries
        sys.exit("Invalid store schema: metadata.count does not match number of entries.")  # Exit if mismatch


def now_iso():
    """Return current UTC timestamp in ISO8601 (delegates to current_time_in_ISO8601)."""  # Docstring for clarity
    return current_time_in_ISO8601()  # Simple wrapper for naming convenience


def normalize_site(s):
    """Normalize a site key by trimming whitespace and lowercasing (ensures consistent keys)."""  # Docstring
    return s.strip().lower()  # Remove leading/trailing spaces and lowercase the name


# ---------- CRUD ----------

def add_entry(store, site, username, password):
    """
    Add a new site entry to the store.
    Rules:
      - 'site' is normalized (trim+lower)
      - 'site' must be unique (no overwrite)
      - 'username'/'password' cannot be empty
      - updates metadata.count and metadata.updated_at
    """  # Docstring describing contract
    if site is None:  # Must provide site name
        sys.exit("add: site is required.")  # Exit with clear message
    site_key = normalize_site(site)  # Normalize the site to a consistent key
    if not username or not password:  # Ensure non-empty credentials
        sys.exit("add: username and password cannot be empty.")  # Exit if empty

    entries = store["entries"]  # Shortcut to entries dict
    if site_key in entries:  # Disallow duplicates to prevent silent overwrite
        sys.exit(f"add: entry for '{site_key}' already exists. Use 'update' instead.")  # Exit if duplicate

    entries[site_key] = {  # Create new entry for this site
        "username": str(username),  # Store username as string
        "password": str(password),  # Store password as string
        "last_updated": now_iso()  # Set per-entry timestamp to now
    }
    store["metadata"]["count"] = len(entries)  # Sync count with number of entries
    store["metadata"]["updated_at"] = now_iso()  # Update global "updated_at" timestamp


def get_entry(store, site):
    """Return entry dict for 'site' or None if not found (exits if site missing)."""  # Docstring
    if site is None:  # Must provide site name
        sys.exit("get: site is required.")  # Exit with clear message
    site_key = normalize_site(site)  # Normalize key for consistent lookup
    return store["entries"].get(site_key, None)  # Return entry or None if absent


def update_entry(store, site, username=None, password=None):
    """
    Update username/password for an existing site.
    Requirements:
      - 'site' is required
      - at least one of username/password must be provided
      - updates entry.last_updated and metadata.updated_at
    """  # Docstring
    if site is None:  # Must provide site name
        sys.exit("update: site is required.")  # Exit with message
    if username is None and password is None:  # Need at least one field to change
        sys.exit("update: nothing to update (provide --username and/or --password).")  # Exit if nothing to change

    site_key = normalize_site(site)  # Normalize lookup key
    entries = store["entries"]  # Shortcut to entries
    if site_key not in entries:  # Ensure site exists
        sys.exit(f"update: no entry found for '{site_key}'.")  # Exit if missing

    if username is not None:  # If username update requested
        if not username:  # Disallow empty username
            sys.exit("update: username cannot be empty.")  # Exit if empty
        entries[site_key]["username"] = str(username)  # Apply username change

    if password is not None:  # If password update requested
        if not password:  # Disallow empty password
            sys.exit("update: password cannot be empty.")  # Exit if empty
        entries[site_key]["password"] = str(password)  # Apply password change

    entries[site_key]["last_updated"] = now_iso()  # Refresh per-entry timestamp
    store["metadata"]["updated_at"] = now_iso()  # Refresh global updated_at


def delete_entry(store, site):
    """Delete an entry by site name and update metadata count/updated_at."""  # Docstring
    if site is None:  # Require site name
        sys.exit("delete: site is required.")  # Exit with message
    site_key = normalize_site(site)  # Normalize key for consistency
    entries = store["entries"]  # Shortcut to entries

    if site_key not in entries:  # Must exist to delete
        sys.exit(f"delete: no entry found for '{site_key}'.")  # Exit if missing

    del entries[site_key]  # Remove the entry from the dictionary
    store["metadata"]["count"] = len(entries)  # Recompute count after deletion
    store["metadata"]["updated_at"] = now_iso()  # Update global updated_at


# ---------- Listing / Search / Export / Stats ----------

def list_entries(store, sort_key="site"):
    """
    Return a list of tuples: (site, username, last_updated).
    Sorting:
      - sort_key='site' (default) sorts alphabetically by site
      - sort_key='last_updated' sorts by timestamp (ISO string compares chronologically)
    """  # Docstring explaining return/sort
    rows = [(site, rec["username"], rec["last_updated"])  # Build (site, username, last_updated) tuples
            for site, rec in store["entries"].items()]  # Iterate over all entries in the store

    if sort_key == "last_updated":  # If caller wants chronological ordering
        rows.sort(key=lambda t: t[2])  # Sort by the ISO timestamp (string compares chronologically)
    else:  # Default sorting path
        rows.sort(key=lambda t: t[0])  # Sort by site name alphabetically

    return rows  # Return the sorted list of tuples


def search_entries(store, keyword):
    """
    Case-insensitive search over 'site' and 'username'.
    Returns a sorted list of matching site names (may be empty).
    """  # Docstring
    if not keyword:  # If keyword is empty/None
        return []  # No results by definition
    k = keyword.lower()  # Normalize search keyword to lowercase
    hits = []  # Accumulate matching site names here
    for site, rec in store["entries"].items():  # Scan all entries
        if k in site.lower() or k in rec["username"].lower():  # Match on site or username (case-insensitive)
            hits.append(site)  # Keep the site key if it matches
    hits.sort()  # Sort results alphabetically for stable output
    return hits  # Return the list of matches


def export_csv(store, out_path):
    """
    Export entries to CSV with headers:
      site,username,password,last_updated
    Returns the number of rows written (excluding the header).
    """  # Docstring explains format and return
    count = 0  # Will count data rows written (not counting header)
    with open(out_path, mode="w", newline="", encoding="utf-8") as f:  # Open CSV for writing
        writer = csv.writer(f)  # Create a simple CSV writer
        writer.writerow(["site", "username", "password", "last_updated"])  # Write header row
        for site, rec in store["entries"].items():  # Iterate all entries
            writer.writerow([site, rec["username"], rec["password"], rec["last_updated"]])  # Write one row
            count += 1  # Increment number of written entries
    return count  # Return the number of data rows written


def stats(store):
    """
    Compute basic statistics:
      - count: number of entries
      - oldest: minimum of last_updated or None
      - newest: maximum of last_updated or None
      - avg_password_length: average length of passwords (float)
    Returns a dict with those fields.
    """  # Docstring with outputs
    entries = store["entries"]  # Shortcut to entries
    total = len(entries)  # Number of entries
    if total == 0:  # Edge-case: no data
        return {  # Return zero/None defaults
            "count": 0,
            "oldest": None,
            "newest": None,
            "avg_password_length": 0.0
        }

    times = [rec["last_updated"] for rec in entries.values()]  # Collect timestamps
    pw_lengths = [len(rec["password"]) for rec in entries.values()]  # Collect password lengths
    oldest = min(times)  # ISO strings: min is chronologically oldest
    newest = max(times)  # ISO strings: max is chronologically newest
    avg_len = sum(pw_lengths) / len(pw_lengths)  # Average password length as float

    return {  # Package the computed stats
        "count": total,
        "oldest": oldest,
        "newest": newest,
        "avg_password_length": avg_len
    }


# ---------- Save (Step 7) ----------

def save_store(path, store):
    """
    Persist the store to disk (simple overwrite write).
    For extra safety you could write to a temp file then rename atomically.
    """  # Docstring with optional improvement hint
    store["metadata"]["updated_at"] = now_iso()  # Update global updated_at before writing
    with open(path, mode="w", encoding="utf-8") as f:  # Open target JSON file for writing
        json.dump(store, f, indent=2, ensure_ascii=False)  # Serialize store back to disk (pretty JSON)


# ---------- CLI parsing ----------

def parse_args(argv=None):
    """
    Define and parse command-line interface using argparse with subcommands.
    Returns an argparse.Namespace containing all parsed arguments/options.
    """  # Docstring
    parser = argparse.ArgumentParser(  # Create the top-level parser
        prog="passman.py",  # Program name shown in help
        description="Simple Password Manager (CLI) — educational use only."  # Help description
    )
    parser.add_argument(  # Global option available to all subcommands
        "--file", "-f",  # Long and short flag
        default="store.json",  # Default path when not provided
        help="Path to the JSON store file (default: store.json)"  # Help text for the option
    )

    subparsers = parser.add_subparsers(dest="command", required=True)  # Set up subcommands; require one command

    # init subcommand (no extra args)
    p_init = subparsers.add_parser("init", help="Create a new password store file.")  # 'init' parser

    # add subcommand
    p_add = subparsers.add_parser("add", help="Add a new entry.")  # 'add' parser
    p_add.add_argument("site", help="Site key (will be normalized)")  # Positional: site
    p_add.add_argument("username", help="Username for the site")  # Positional: username
    p_add.add_argument("password", help="Password for the site")  # Positional: password

    # get subcommand
    p_get = subparsers.add_parser("get", help="Retrieve an entry by site.")  # 'get' parser
    p_get.add_argument("site", help="Site key to fetch")  # Positional: site

    # update subcommand
    p_update = subparsers.add_parser("update", help="Update username and/or password for a site.")  # 'update' parser
    p_update.add_argument("site", help="Site key to update")  # Positional: site
    p_update.add_argument("--username", help="New username")  # Optional: new username
    p_update.add_argument("--password", help="New password")  # Optional: new password

    # delete subcommand
    p_delete = subparsers.add_parser("delete", help="Delete an entry by site.")  # 'delete' parser
    p_delete.add_argument("site", help="Site key to delete")  # Positional: site

    # list subcommand
    p_list = subparsers.add_parser("list", help="List all entries.")  # 'list' parser
    p_list.add_argument(  # Optional sort choice
        "--sort",
        choices=["site", "last_updated"],  # Allowed choices
        default="site",  # Default sorting by site
        help="Sort by 'site' (default) or 'last_updated'"  # Help text
    )

    # search subcommand
    p_search = subparsers.add_parser("search", help="Search in site and username.")  # 'search' parser
    p_search.add_argument("keyword", help="Keyword to search (case-insensitive)")  # Positional: keyword

    # export subcommand
    p_export = subparsers.add_parser("export", help="Export entries (CSV).")  # 'export' parser
    # keep it simple: only CSV mode in this project
    p_export.add_argument("--out", required=True, help="Output CSV file path")  # Require target CSV path

    # stats subcommand (no extra args)
    subparsers.add_parser("stats", help="Show basic statistics.")  # 'stats' parser

    return parser.parse_args(argv)  # Parse argv (or sys.argv if None) and return Namespace


# ---------- main ----------

def main():
    """Parse CLI, load/validate store (except on init), dispatch command, and print results."""  # High-level docstring
    args = parse_args()  # Parse all command-line arguments/options into 'args'

    # 'init' does not need an existing store on disk:
    if args.command == "init":  # If the user wants to create a new store
        init_store(args.file)  # Build and write a fresh store to args.file
        return  # Nothing else to do for init

    # For all other commands we need a valid existing store:
    store = load_store(args.file)  # Read and parse JSON store from disk
    validate_store_schema(store)  # Ensure the file structure is correct before operating

    if args.command == "add":  # 'add' subcommand logic
        add_entry(store, args.site, args.username, args.password)  # Insert a new entry
        save_store(args.file, store)  # Persist changes to disk
        print(f"Added: {normalize_site(args.site)} ({args.username})")  # Confirmation output

    elif args.command == "get":  # 'get' subcommand logic
        entry = get_entry(store, args.site)  # Lookup entry by site
        if entry is None:  # If not found
            print(f"No entry found for {normalize_site(args.site)}")  # Inform user
        else:  # Found: print fields plainly (note: not secure for real passwords)
            print("site:", normalize_site(args.site))  # Show normalized site
            print("username:", entry["username"])  # Show username
            print("password:", entry["password"])  # Show password (educational only)
            print("last_updated:", entry["last_updated"])  # Show last updated timestamp

    elif args.command == "update":  # 'update' subcommand logic
        update_entry(store, args.site, username=args.username, password=args.password)  # Apply changes
        save_store(args.file, store)  # Persist changes to disk
        print(f"Updated: {normalize_site(args.site)}")  # Confirmation output

    elif args.command == "delete":  # 'delete' subcommand logic
        delete_entry(store, args.site)  # Remove the entry
        save_store(args.file, store)  # Persist changes to disk
        print(f"Deleted: {normalize_site(args.site)}")  # Confirmation output

    elif args.command == "list":  # 'list' subcommand logic
        rows = list_entries(store, sort_key=args.sort)  # Build (site, username, last_updated) rows with sorting
        if not rows:  # No entries at all
            print("(empty)")  # Friendly empty message
        else:  # Print a simple aligned table
            print("SITE".ljust(12), "USERNAME".ljust(16), "LAST_UPDATED")  # Header with spacing
            for site, username, last_updated in rows:  # Iterate over rows
                print(site.ljust(12), username.ljust(16), last_updated)  # Print each row aligned

    elif args.command == "search":  # 'search' subcommand logic
        hits = search_entries(store, args.keyword)  # Search by keyword in site and username
        if not hits:  # Nothing matched
            print("(no results)")  # Friendly message
        else:  # Print each matching site on its own line
            for site in hits:  # Iterate sorted matches
                print(site)  # Output site name

    elif args.command == "export":  # 'export' subcommand logic
        written = export_csv(store, args.out)  # Write CSV file and get number of rows
        print(f"Exported {written} entries to {args.out}")  # Confirmation output

    elif args.command == "stats":  # 'stats' subcommand logic
        info = stats(store)  # Compute statistics
        print("entries:", info["count"])  # Show total count
        print("oldest: ", info["oldest"])  # Show oldest last_updated
        print("newest: ", info["newest"])  # Show newest last_updated
        print("avg password length:", info["avg_password_length"])  # Show average password length

    else:  # Safety net (argparse should prevent unknown commands)
        print("Unknown command. Use --help for usage.")  # Fallback message


if __name__ == "__main__":  # Standard entry-point check when running as a script
    main()  # Invoke main() to run the CLI program
