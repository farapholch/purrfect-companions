#!/usr/bin/env python3
"""Markdown → HTML för CurseForge-beskrivningen.

CurseForges editor är rich text: klistrar man in markdown escapar den alla
specialtecken (\\###, \\*\\*). Antingen byter man editorn till Markdown-läge,
eller klistrar in HTML — den här filen genererar HTML-varianten.

    python3 md2html.py in.md ut.html
"""
import html, re, sys


def inline(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))


def is_ul(l):
    # kräver mellanslag efter tecknet, annars matchar "**fet text**" som lista
    return re.match(r"^[-*] ", l) is not None


def is_ol(l):
    return re.match(r"^\d+\. ", l) is not None


def convert(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("### "):
            out.append(f"<h3>{inline(l[4:])}</h3>"); i += 1
        elif l.startswith("## "):
            out.append(f"<h2>{inline(l[3:])}</h2>"); i += 1
        elif l.strip() == "---":
            out.append("<hr>"); i += 1
        elif l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<table><thead><tr>"] + [f"<th>{inline(c)}</th>" for c in rows[0]] + ["</tr></thead><tbody>"]
            for r in rows[2:]:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("".join(t) + "</tbody></table>")
        elif is_ul(l):
            items = []
            while i < len(lines) and (is_ul(lines[i]) or (lines[i].startswith("  ") and items)):
                if is_ul(lines[i]):
                    items.append(lines[i][2:])
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
        elif is_ol(l):
            items = []
            while i < len(lines) and is_ol(lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i])); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
        elif not l.strip():
            i += 1
        else:
            par = []
            while (i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|"))
                   and not is_ul(lines[i]) and not is_ol(lines[i]) and lines[i].strip() != "---"):
                par.append(lines[i].strip()); i += 1
            out.append(f"<p>{inline(' '.join(par))}</p>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    h = convert(open(src, encoding="utf-8").read())
    open(dst, "w", encoding="utf-8").write(h)
    print(f"{dst}: {len(h)} tecken, {h.count('<table')} tabeller, {h.count('<li>')} listpunkter")
