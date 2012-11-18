#!/bin/bash

working_directory=`hg root`
version_major=`cat $working_directory/application/gui/main_window.py | grep \'major\': | cut -f 2 -d : | tr -d [:space:][,]`
version_minor=`cat $working_directory/application/gui/main_window.py | grep \'minor\': | cut -f 2 -d : | tr -d [:space:][,]`
version_build=`cat $working_directory/application/gui/main_window.py | grep \'build\': | cut -f 2 -d : | tr -d [:space:][,]`
version_stage=`cat $working_directory/application/gui/main_window.py | grep \'stage\': | cut -f 2 -d : | tr -d [:space:][\'][,]`

# form file names
file_google_code="Sunflower-$version_major.$version_minor$version_stage-$version_build.tgz"
file_home_page="Sunflower.tgz"
tar_file_home_page="Sunflower.tar"

# archive files
echo Preparing release: Sunflower $version_major.$version_minor$version_stage \($version_build\)
echo -e "\t- Archiving source code"
cd $working_directory
hg archive --exclude scripts/ --type tgz --prefix Sunflower ~/Desktop/$file_home_page

# remove unneeded files
echo -e "\t- Unpacking gzip archive"
gunzip ~/Desktop/$file_home_page

echo -e "\t- Removing unneeded files"
tar --delete --wildcards --file=$HOME/Desktop/$tar_file_home_page Sunflower/.hg*
tar --delete --wildcards --file=$HOME/Desktop/$tar_file_home_page Sunflower/images/*.xcf
tar --delete --wildcards --file=$HOME/Desktop/$tar_file_home_page Sunflower/images/selection_arrow.svg

echo -e "\t- Repacking gzip archive"
gzip --best ~/Desktop/$tar_file_home_page

# move file
echo -e "\t- Moving file"
mv ~/Desktop/$tar_file_home_page.gz ~/Desktop/$file_google_code

echo "Done!"
