import re

f = open('schulgesetz.md')
lines = f.readlines()
f.close()

outtext = ''
currentpar = 0

for line in lines:
	m1 = re.match(r'<par id="p(\d+)">', line)
	if m1:
		print('§', m1.group(0))
		currentpar = m1.group(1)
	m2 = re.match(r'<abs id="a(\d+)">', line)
	if m2:
		print('  (', m2.group(0), ')', end='\t->\t')
		line = re.sub(r'<abs id="a(\d+)">', r'<abs id="p{0}a\1">'.format(currentpar), line)
		print(re.match(r'<abs [^>]*>', line).group(0))

	outtext += line

of = open('schulgesetz-re.md', 'w+')
of.write(outtext)
of.close()
