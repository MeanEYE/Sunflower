#!/usr/bin/env python

# text and image viewer 
# 2011-12-15
# Torsten Funck


#Python Imports (Standard Library)
import pygtk
import sys
import magic
pygtk.require('2.0')

#Gtk Imports (External Library)
import gtk


class Viewer:

    def close_application(self, widget):
        gtk.main_quit()

    def __init__(self):
        # Create and parameterise main window
        main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        main_window.set_size_request(1024, 512)
        main_window.set_resizable(True)  
        main_window.connect("destroy", self.close_application)
        main_window.set_title("Viewer")
        main_window.set_border_width(0)

        # Create and parameterise scrollable window, place into main window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.show()
        main_window.add(scrolled_window)

        # Load file specified in command line
        if (len(sys.argv) > 1):
            file_path = sys.argv[1]

        # Open file_path
        infile = open(file_path, "r")

        if infile:
            # Check file type
            magic_string = magic.open(magic.MAGIC_NONE)
            magic_string.load()
            file_type = magic_string.file(file_path)
#            print file_type

            if 'text' in file_type:
                # Create and parameterise text viewer, place into scrollable window
                text_view = gtk.TextView()
                text_view.set_left_margin(10)
                text_view.show()
                scrolled_window.add(text_view)

               # Load text from file into the text viewer 
                string = infile.read()
                text_buffer = text_view.get_buffer()
                text_buffer.set_text(string)

            elif 'image' in file_type:
                # Load image from file into the scrollable window 
                image = gtk.Image()
                image.set_from_file(file_path)
                image.show()
                scrolled_window.add_with_viewport(image)

            # close file_path
            infile.close()

        # Show everything
        main_window.show()

def main():
    gtk.main()
    return 0       

if __name__ == "__main__":
    Viewer()
    main()
