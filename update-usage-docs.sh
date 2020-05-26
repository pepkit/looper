#!/bin/bash
cp docs/usage.template usage.template
#looper --help > USAGE.temp 2>&1

for cmd in "--help" "run --help" "runp --help" "rerun --help" "report --help" "table --help" "inspect --help" "init --help" "destroy --help" "check --help" "clean --help"; do
	echo $cmd
	echo -e "## \`looper $cmd\`" > USAGE_header.temp
	looper $cmd --help > USAGE.temp 2>&1
	# sed -i 's/^/\t/' USAGE.temp
	sed -i.bak '1s;^;\`\`\`console\
;' USAGE.temp
#	sed -i '1s/^/\n\`\`\`console\n/' USAGE.temp
	echo -e "\`\`\`\n" >> USAGE.temp
	#sed -i -e "/\`looper $cmd\`/r USAGE.temp" -e '$G' usage.template  # for -in place inserts
	cat USAGE_header.temp USAGE.temp >> usage.template # to append to the end
done
rm USAGE.temp
rm USAGE_header.temp
rm USAGE.temp.bak
mv usage.template  docs/usage.md
cat docs/usage.md
#rm USAGE.temp
