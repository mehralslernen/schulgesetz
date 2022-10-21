import requests
from bs4 import BeautifulSoup
import pypandoc
from textnorm import normalize_space
import re

r = requests.get("https://www.schulgesetz-berlin.de/berlin/schulgesetz/gesamtes-schulgesetz-anzeigen.php")
if r.ok:
	r.encoding = r.apparent_encoding
	fullhtml = r.text
else:
	print("Error getting html")
	exit()

soup = BeautifulSoup(fullhtml, "lxml")

content = soup.find(id="inhalt")

for match in content.find_all(["sup", "span", "br"]):
    match.replace_with('')

for match in content.find_all("p", ["druckfooter", "druckleerzeile"]):
    match.replace_with('')

for match in content.find_all("a"):
    match.unwrap()

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
	print(ref, ref.group(1), ref.group(2), "exists" if exists else "fake")
	if exists and not (p, a) in linked:
		md = re.sub(r'§\s{{1,3}}{0}\s{{1,3}}Absatz\s{{1,3}}{1}'.format(p, a),
			r'<a href="#P{0}A{1}">§ {0} Absatz {1}</a>'.format(p, a),
			md)
		linked.add((p,a))

md = md[3:]

of = open('schulgesetz.md', 'w+')
of.write(md)
of.close()
