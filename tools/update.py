import requests
from bs4 import BeautifulSoup
import pypandoc
from textnorm import normalize_space
import re

"""
TODO:
A way better approach would be to not scrape this website, but get the data from the source
Which is here: https://gesetze.berlin.de/bsbe/document/jlr-SchulGBErahmen
We can fetch an XML version (in a zip file) there:
https://gesetze.berlin.de/jportal/bsbeAizDownload/SchulG_BE.zip?doc.id=jlr-SchulGBErahmen&doc.part=X&_=%2FSchulG_BE.zip
Then either parse directly or use XSLT to convert to Markdown or HTML

Syntax for XSLT ref in XML:

<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="class.xsl"?>

or use e.g. xsltproc

The latter makes more sense, this is the kind of static content
that should be rendered once on the server and then never again
"""

r = requests.get("https://schulgesetz-berlin.de/schulgesetz-berlin/gesamtansicht.php")
if r.ok:
	r.encoding = r.apparent_encoding
	fullhtml = r.text
else:
	print("Error getting html")
	exit()

soup = BeautifulSoup(fullhtml, "lxml")

content = soup.find(id="inhalt")

for match in content.find_all("h1", class_="zeile1"):
    match.replace_with('')

for match in content.find_all(["sup", "span", "br"]):
    match.replace_with('')

for match in content.find_all("p", ["druckfooter", "druckleerzeile"]):
    match.replace_with('')

for match in content.find_all("a"):
    match.unwrap()

# New format doesn't use h1 tags, so we insert them so pandoc handles the headings correctly
for match in content.find_all("p", class_="output_paragraph"):
    h1tag = soup.new_tag("h1")
    h1tag.string = match.get_text()
    match.replace_with(h1tag)

htmlcontent = str(content)

rawmd = pypandoc.convert_text(htmlcontent, 'markdown_strict', format='html')
#print(rawmd)

cleanmd = normalize_space(rawmd, preserve = ['\n'])

of = open('schulgesetz-raw.md', 'w+')
of.write(cleanmd)
of.close()

md = ""
currentpar = 0
padict = {}

for line in cleanmd.splitlines():
	par = re.match(r'# § (\d+[abcdef]?)', line)
	if par:
		print('\n§', par.group(1))
		line = re.sub(r'§ (\d+[abcdef]?)', r'<par id="P\1">§ \1</par>', line)
		currentpar = par.group(1)
		padict[currentpar] = set()
	abs = re.match(r'^\\\((\d+)\\\)', line)
	if abs:
		print(' (' + abs.group(1) + ')', end='')
		line = re.sub(r'^\\\((\d+)\\\)', r'<abs id="P{0}A\1">(\1)</abs>'.format(currentpar), line)
		padict[currentpar].add(abs.group(1))

	#print(line)
	md += line + '\n'

print('\n\n')
#print(padict)

linked = set()

for ref in re.finditer(r'§\s{1,3}(\d+[abcdef]?)\s{1,3}Absatz\s{1,3}(\d+)', md):
	p = ref.group(1)
	a = ref.group(2)
	exists = p in padict and a in padict[p]
	print(ref.group(0), '->', ref.group(1), ref.group(2), "exists" if exists else "fake")
	if exists and not (p, a) in linked:
		md = re.sub(r'§\s{{1,3}}{0}\s{{1,3}}Absatz\s{{1,3}}{1}'.format(p, a),
			r'<a href="#P{0}A{1}">§ {0} Absatz {1}</a>'.format(p, a),
			md)
		linked.add((p,a))

of = open('schulgesetz.md', 'w+')
of.write(md)
of.close()
