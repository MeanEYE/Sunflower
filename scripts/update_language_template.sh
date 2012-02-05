#!/bin/bash
working_directory=`hg root`

cd $working_directory
find . -iname "*.py" | xargs xgettext --language=Python --package-name=Sunflower --package-version=0.1 --output translations/sunflower.pot
