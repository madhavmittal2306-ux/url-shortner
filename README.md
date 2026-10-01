# Mini URL Shortener (CLI)

A command-line tool that turns long URLs into short codes and gets them back later. Built with Python 3 and only the standard library. No external APIs or packages.

## Setup

Python 3 is the only requirement.

```
python main.py <command>
```

## Commands

| Command | What it does |
|---|---|
| `shorten <url>` | Make a short code for a URL |
| `shorten <url> --alias myco` | Use your own custom code |
| `shorten <url> --expire 60` | Link stops working after 60 minutes |
| `resolve <code>` | Show the original URL and count a click |
| `resolve <code> --open` | Same, and open the URL in the browser |
| `list` | Show all saved URLs with clicks and expiry |
| `delete <code>` | Remove a saved URL |
| `search <word>` | Find links where the code or URL contains the word |
| `stats` | Total links, total clicks, expired links, most clicked link |
| `top [n]` | Show the n most clicked links (default 5) |
| `cleanup` | Remove all expired links |
| `export [file.csv]` | Save everything to a CSV file (default `links.csv`) |

## Sample output

```
$ python main.py shorten https://www.example.com/page
Short code: idn2v8

$ python main.py shorten https://github.com/madhav --alias gh
Short code: gh

$ python main.py shorten https://www.google.com --alias goog --expire 60
Short code: goog
Expires at: 2026-10-01 19:06

$ python main.py resolve gh
Original URL: https://github.com/madhav

$ python main.py list
CODE                  CLICKS  EXPIRES           URL
----------------------------------------------------------------------
idn2v8                0       never             https://www.example.com/page
gh                    1       never             https://github.com/madhav
goog                  0       2026-10-01 19:06  https://www.google.com

Total links: 3

$ python main.py stats
Total links  : 3
Total clicks : 1
Expired links: 0
Most clicked : gh (1 clicks)

$ python main.py top 2
CODE                  CLICKS  EXPIRES           URL
----------------------------------------------------------------------
gh                    1       never             https://github.com/madhav
idn2v8                0       never             https://www.example.com/page
```

## Error handling

```
$ python main.py shorten hello
Error: that is not a valid URL. It should start with http:// or https://

$ python main.py shorten https://google.com --alias gh
Error: the alias 'gh' is already taken.

$ python main.py shorten https://a.com --alias "bad alias!"
Error: alias can only contain letters and numbers.

$ python main.py resolve nope
Error: no URL found for code 'nope'.

$ python main.py resolve goog
Error: the code 'goog' has expired.
```

## Design notes

- Links are stored in `urls.json`, so they persist between runs.
- Codes are 6 random letters and digits. The program checks that a code is unused before picking it.
- Shortening the same URL twice returns the existing code.
- Aliases allow only letters and numbers, up to 20 characters. The check is written by hand.
- Only `http://` and `https://` links are accepted, so unsafe schemes such as `javascript:` are rejected.
- Expired links cannot be resolved and do not get clicks. `cleanup` deletes them.
- A missing, empty or broken `urls.json` is treated as having no links.
- Libraries: `argparse`, `json`, `csv`, `random`, `datetime`, `webbrowser`, `urllib.parse`.
