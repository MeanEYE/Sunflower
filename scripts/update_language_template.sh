#!/bin/bash

echo -n "Updating language template..."
cd `hg root`
find . -iname "*.py" | xargs xgettext --language=Python --package-name=Sunflower --package-version=0.1 --output translations/sunflower.pot
echo "done!"
