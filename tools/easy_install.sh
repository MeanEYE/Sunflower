#!/bin/bash
#
#   Sunflower Installation Script
#   Written by Marek Suchánek, adapted by Mladen Mijatov
#
# This script downloads and installs the Sunflower file manager in /opt
# creating shortcuts for easy CLI or GUI starting.

installer_version=1.5
download_link="http://rcf-group.com/generator/download/23/0.tgz"
location="/opt"
shared_path="/usr"
operation="none"
create_path=0
superuser=0

# show a nice information message assuring the user he's doing the right thing
echo -e "\033[1mSunflower Installer $installer_version\033[0m\n"
echo "Hello and thank you for choosing Sunflower! This script will help you"
echo -e "to install or remove Sunflower with ease.\n"

function check_privileges() {
	# check whether we're running under super-user
	if [ "$( id -u )" = "0" ]; then
		echo " * Okay, we have superuser privileges."
		superuser=1

	else
		shared_path="$HOME/.local"

		if [ $operation = "install" ]; then
			echo " * No superuser privileges! We'll skip installing launcher."
		else
			echo " * No superuser privileges! We'll skip removing launcher."
		fi
	fi
}

function remove_program() {
	# first check if we have superuser privileges
	check_privileges

	echo " * Removing program:"

	# remove program
	if [ -d $location/Sunflower ]; then
		echo "   - Removing code"
		rm -rf $location/Sunflower

	else
		echo -e "\nSunflower installation was not found in specified directory."
		exit 2
	fi

	# remove desktop file
	echo "   - Removing desktop file"
	rm -f $shared_path/share/applications/sunflower.desktop

	# remove icons
	echo "   - Removing icons"
	rm -f \
		$shared_path/share/icons/hicolor/64x64/apps/sunflower.png\
		$shared_path/share/icons/hicolor/scalable/apps/sunflower.svg\
		$shared_path/share/icons/gnome/64x64/apps/sunflower.png\
		$shared_path/share/icons/gnome/scalable/apps/sunflower.svg\
		$shared_path/share/pixmaps/sunflower.png

	# remove icons and launcher
	if [ $superuser = "1" ]; then
		echo "   - Removing launcher"
		rm -f /usr/local/bin/sunflower
	else
		echo "   - Skipped removing launcher"
	fi

	echo -e "\nSunflower was removed from your system. If you removed it"
	echo "because you had a problem, please let us know! :)"
	echo -e "\nBug tracker: http://code.google.com/p/sunflower-fm/issues/list"
}

function install_program() {
	# first check if we have superuser privileges
	check_privileges

	# make sure destination directory exists
	if [ ! -d $location ]; then
		if [ ! $create_path = 1 ]; then
			echo -e "\nSpecified path doesn't exist. We can create it but"
			echo "you need to confirm if this really what you want want"
			echo "by including --create-path flag."
			exit 3

		else
			echo " * Specified path doesn't exist but it will be created"
			mkdir -p $location > /dev/null 2>&1

			if [ "$?" -ne "0" ]; then
				echo -e "\nWe need superuser privileges to install in specified directory!"
				exit 6
			fi
		fi
	fi

	# change into destination directory
	cd $location

	echo " * Installing program:"

	# check for existing installation
	if [ -d Sunflower ]; then
		echo -e "\nSunflower seems to be already installed in specified directory. "
		echo "Would you like to overwrite existing installation? [yes / overwrite / no / quit ]"
		read update

		case $update in
			no|No|n|N|quit)
				echo "Alright then. See you."
				exit 4
				;;
			yes|Yes|y|Y|overwrite|o)
				echo "   - Removing existing installation (keeping config files)"
					rm -rf Sunflower
				;;
			*)
				echo "Installation aborted."
				exit 4
				;;
		esac
	fi

	# install program
	echo "   - Downloading archive"

	touch sunflower.tgz > /dev/null 2>&1
	if [ "$?" -ne "0" ]; then
		echo -e "\nWe need superuser privileges to install in specified directory!"
		exit 6
	fi

	# get archive from internet
	if [ -x /usr/bin/wget -o -x /usr/local/bin/wget ]; then
		wget --ignore-length -t 1 -q "$download_link" -O sunflower.tgz

	else
		echo -e "\nWe need `wget` to download archive for us."
		echo -e "Please make sure you have it installed.\n"
		exit 5
	fi

	# unpack archive
	echo "   - Unpacking the archive"
	tar xzpf sunflower.tgz
	rm sunflower.tgz

	# make desktop file
	echo "   - Creating desktop file"
	cp -f $location/Sunflower.desktop $shared_path/share/applications/

	# copy icons to system directories
	echo "   - Copying icons"
	mkdir -p $shared_path/share/icons/hicolor/64x64/apps
	cp -f $location/Sunflower/images/sunflower_64.png $shared_path/share/icons/hicolor/64x64/apps/sunflower.png

	mkdir -p $shared_path/share/icons/hicolor/scalable/apps/
	cp -f $location/Sunflower/images/sunflower.svg $shared_path/share/icons/hicolor/scalable/apps/sunflower.svg

	mkdir -p $shared_path/share/icons/gnome/64x64/apps
	cp -f $location/Sunflower/images/sunflower_64.png $shared_path/share/icons/gnome/64x64/apps/sunflower.png

	mkdir -p $shared_path/share/icons/gnome/scalable/apps
	cp -f $location/Sunflower/images/sunflower.svg $shared_path/share/icons/gnome/scalable/apps/sunflower.svg

	mkdir -p $shared_path/share/pixmaps
	cp -f $location/Sunflower/images/sunflower.png $shared_path/share/pixmaps/sunflower.png

	# make launcher script
	if [ $superuser = "1" ]; then
		echo "   - Creating launcher script"
		mkdir -p /usr/local/bin
		echo "#!/bin/sh" > /usr/local/bin/sunflower
		echo "cd $location/Sunflower" >> /usr/local/bin/sunflower
		echo "./Sunflower.py" >> /usr/local/bin/sunflower
		chmod 755 /usr/local/bin/sunflower

	else
		echo "   - Skipped installing launcher"
	fi

	# print good bye message
	echo -e "\nDone! That's about it. You should be able to run Sunflower now."
	echo "If you are unable to start it please let us know and we'll fix it"
	echo -e "but first make sure you have the following packages installed:\n"
	cat Sunflower/DEPENDS
	echo -e "\nPlease note that package names will depend on distribution."

	exit 0
}

# get params
while (( "$#" )); do
	if [ "$1" = "--install" ]; then
		operation="install"

	elif [ "$1" = "--remove" -o "$1" = "--uninstall" ]; then
		operation="remove"

	elif [ "$1" = "--location" ]; then
		shift
		location="$1"

	elif [ "$1" = "--create-path" ]; then
		create_path=1
	fi

	shift
done

# check command line parameters
if [ $operation = "install" ]; then
	install_program

elif [ $operation = "remove" ]; then
	remove_program

else
	echo "You need to specify operation. Script usage:"
	echo -e "\n   sudo ${0} <OPERATION> [OPTION]"

	echo -e "\nOperations:"
	echo "   --install              Download and install Sunflower"
	echo "   --uninstall, --remove  Remove Sunflower from your system"
	echo -e "\nOptions:"
	echo "   --location <PATH>      Specify directory where Sunflower is located or to be installed"
    echo "   --create-path          Allow installation to create directories"
fi
