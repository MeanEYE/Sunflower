#!/bin/bash
cd ..
find . -iname "*.py" | xargs xgettext --language=Python --package-name=Sunflower --package-version=0.1 --output translations/sunflower.pot
