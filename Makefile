all: index.html

schulgesetz.html: schulgesetz.md
	pandoc -i $< -o $@

index.html: schulgesetz.html wrapper.html
	sed -e '/<!--CONTENT-->/r./schulgesetz.html' wrapper.html > $@

clean:
	rm -rf schulgesetz.html index.html
