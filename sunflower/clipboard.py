from gi.repository import Gtk, Gdk

class Clipboard:
    def __init__(self):
        self._operation=None
        self._uri_list=[]

        self._gtk_clipboard=Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._gtk_clipboard.connect('owner_change',self._owner_changed)

    def _owner_changed(self,clipboard,ev):
        self._clear_clipboard()

    def _clear_clipboard(self):
        self._operation=None
        self._uri_list.clear()

    def set_text(self,*args,**kwds):
        return self._gtk_clipboard.set_text(*args,**kwds)

    def set_with_data(self,operation,uri_list):
        self._clear_clipboard()
        self._operation=operation
        self._uri_list[:]=uri_list

    def wait_for_contents(self,*args,**kwds):
        if self._operation is None:
            return
        return '\n'.join([self._operation]+self._uri_list)

    def wait_for_text(self):
        return self._gtk_clipboard.wait_for_text()

    def wait_is_text_available(self):
        return self._gtk_clipboard.wait_is_text_available()

    def wait_is_uris_available(self):
        return self._gtk_clipboard.wait_is_uris_available()
