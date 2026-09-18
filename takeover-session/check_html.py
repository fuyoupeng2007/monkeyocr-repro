import re
import io
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "MinerU_vs_MonkeyOCR_报告.html"
h = io.open(path, encoding="utf-8").read()
tu = "charset" + '="utf-8"'
print("bytes        :", len(h.encode("utf-8")))
print("h1           :", len(re.findall(r"<h1>", h)))
print("h2           :", len(re.findall(r"<h2>", h)))
print("h3           :", len(re.findall(r"<h3>", h)))
print("tables       :", len(re.findall(r"<table>", h)))
print("rows         :", len(re.findall(r"<tr>", h)))
print("blockquotes  :", len(re.findall(r"<blockquote>", h)))
print("lists        :", len(re.findall(r"<ul>", h)))
print("charset ok   :", tu in h)
print("unclosed tbl :", len(re.findall(r"<table>", h)) - len(re.findall(r"</table>", h)))
print("leftover md table rows:", len(re.findall(r"(?m)^\|", h)))
print("leftover bullets     :", len(re.findall(r"(?m)^- ", h)))
print("literal placeholders :", len(re.findall(r"\(source_table|\(headline_table|\(worst_pages", h)))
