import argparse
import csv
import json
import random
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlparse

DATA_FILE = "urls.json"
DATE_FORMAT = "%Y-%m-%d %H:%M"
CODE_LENGTH = 6
MAX_ALIAS_LENGTH = 20
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_valid_url(url):
    parts = urlparse(url)
    return parts.scheme in ("http", "https") and parts.netloc != ""


def is_valid_alias(alias):
    if alias == "":
        return False
    for ch in alias:
        if ch not in CHARS:
            return False
    return True


def make_code(data):
    while True:
        code = ""
        for _ in range(CODE_LENGTH):
            code += random.choice(CHARS)
        if code not in data:
            return code


def is_expired(entry):
    expires = entry.get("expires")
    if expires is None:
        return False
    return datetime.now() > datetime.strptime(expires, DATE_FORMAT)


def print_table(data, codes):
    print("CODE".ljust(22) + "CLICKS".ljust(8) + "EXPIRES".ljust(18) + "URL")
    print("-" * 70)
    for code in codes:
        entry = data[code]
        expires = entry.get("expires")
        if expires is None:
            expires = "never"
        elif is_expired(entry):
            expires = "EXPIRED"
        print(code.ljust(22) + str(entry["clicks"]).ljust(8) + expires.ljust(18) + entry["url"])


def shorten(url, alias=None, expire_minutes=None):
    data = load_data()
    url = url.strip()

    if not is_valid_url(url):
        print("Error: that is not a valid URL. It should start with http:// or https://")
        return

    if expire_minutes is not None and expire_minutes <= 0:
        print("Error: --expire must be a number of minutes greater than 0.")
        return

    if alias:
        if not is_valid_alias(alias):
            print("Error: alias can only contain letters and numbers.")
            return
        if len(alias) > MAX_ALIAS_LENGTH:
            print("Error: alias can be at most " + str(MAX_ALIAS_LENGTH) + " characters.")
            return
        if alias in data:
            print("Error: the alias '" + alias + "' is already taken.")
            return
        code = alias
    else:
        for old_code in data:
            if data[old_code]["url"] == url:
                print("This URL was already shortened. Code:", old_code)
                return
        code = make_code(data)

    expires = None
    if expire_minutes is not None:
        expires = (datetime.now() + timedelta(minutes=expire_minutes)).strftime(DATE_FORMAT)

    data[code] = {
        "url": url,
        "clicks": 0,
        "created": datetime.now().strftime(DATE_FORMAT),
        "expires": expires,
    }
    save_data(data)
    print("Short code:", code)
    if expires:
        print("Expires at:", expires)


def resolve(code, open_in_browser=False):
    data = load_data()

    if code not in data:
        print("Error: no URL found for code '" + code + "'.")
        return

    if is_expired(data[code]):
        print("Error: the code '" + code + "' has expired.")
        return

    data[code]["clicks"] += 1
    save_data(data)

    url = data[code]["url"]
    print("Original URL:", url)

    if open_in_browser:
        webbrowser.open(url)


def list_all():
    data = load_data()

    if len(data) == 0:
        print("No URLs saved yet.")
        return

    print_table(data, list(data))
    print("\nTotal links:", len(data))


def delete(code):
    data = load_data()

    if code not in data:
        print("Error: no URL found for code '" + code + "'.")
        return

    del data[code]
    save_data(data)
    print("Deleted code:", code)


def search(word):
    data = load_data()
    word = word.lower()

    matches = []
    for code in data:
        if word in code.lower() or word in data[code]["url"].lower():
            matches.append(code)

    if len(matches) == 0:
        print("No links found for '" + word + "'.")
        return

    print_table(data, matches)
    print("\nFound:", len(matches))


def stats():
    data = load_data()

    if len(data) == 0:
        print("No URLs saved yet.")
        return

    total_clicks = 0
    expired_count = 0
    top_code = None

    for code in data:
        total_clicks += data[code]["clicks"]
        if is_expired(data[code]):
            expired_count += 1
        if top_code is None or data[code]["clicks"] > data[top_code]["clicks"]:
            top_code = code

    print("Total links  :", len(data))
    print("Total clicks :", total_clicks)
    print("Expired links:", expired_count)
    if data[top_code]["clicks"] == 0:
        print("Most clicked : nothing clicked yet")
    else:
        print("Most clicked :", top_code, "(" + str(data[top_code]["clicks"]) + " clicks)")


def top(count):
    data = load_data()

    if len(data) == 0:
        print("No URLs saved yet.")
        return

    if count < 1:
        print("Error: the number must be at least 1.")
        return

    ranked = sorted(data, key=lambda code: data[code]["clicks"], reverse=True)
    print_table(data, ranked[:count])


def cleanup():
    data = load_data()

    expired_codes = []
    for code in data:
        if is_expired(data[code]):
            expired_codes.append(code)

    if len(expired_codes) == 0:
        print("No expired links to remove.")
        return

    for code in expired_codes:
        del data[code]
    save_data(data)
    print("Removed " + str(len(expired_codes)) + " expired link(s).")


def export(filename):
    data = load_data()

    if len(data) == 0:
        print("Nothing to export.")
        return

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "url", "clicks", "created", "expires"])
        for code in data:
            entry = data[code]
            writer.writerow([
                code,
                entry["url"],
                entry["clicks"],
                entry.get("created", ""),
                entry.get("expires") or "",
            ])

    print("Exported " + str(len(data)) + " links to " + filename)


def main():
    parser = argparse.ArgumentParser(description="Mini URL Shortener")
    subparsers = parser.add_subparsers(dest="command")

    shorten_parser = subparsers.add_parser("shorten", help="make a short code for a URL")
    shorten_parser.add_argument("url")
    shorten_parser.add_argument("--alias", help="your own custom code")
    shorten_parser.add_argument("--expire", type=float, help="link expires after this many minutes")

    resolve_parser = subparsers.add_parser("resolve", help="get the original URL")
    resolve_parser.add_argument("code")
    resolve_parser.add_argument("--open", action="store_true", help="open it in the browser")

    subparsers.add_parser("list", help="show all saved URLs")

    delete_parser = subparsers.add_parser("delete", help="remove a saved URL")
    delete_parser.add_argument("code")

    search_parser = subparsers.add_parser("search", help="find links by word")
    search_parser.add_argument("word")

    subparsers.add_parser("stats", help="show totals and the most clicked link")

    top_parser = subparsers.add_parser("top", help="show the most clicked links")
    top_parser.add_argument("count", nargs="?", type=int, default=5)

    subparsers.add_parser("cleanup", help="remove all expired links")

    export_parser = subparsers.add_parser("export", help="save all links to a CSV file")
    export_parser.add_argument("filename", nargs="?", default="links.csv")

    args = parser.parse_args()

    if args.command == "shorten":
        shorten(args.url, args.alias, args.expire)
    elif args.command == "resolve":
        resolve(args.code, args.open)
    elif args.command == "list":
        list_all()
    elif args.command == "delete":
        delete(args.code)
    elif args.command == "search":
        search(args.word)
    elif args.command == "stats":
        stats()
    elif args.command == "top":
        top(args.count)
    elif args.command == "cleanup":
        cleanup()
    elif args.command == "export":
        export(args.filename)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
