import os
import sys
import gtk

class ChangeLogDialog(gtk.Dialog):
	"""Window used to display application change log"""

	def __init__(self, parent, modifications, show_modifications=False):
		gtk.Dialog.__init__(self)

		self.set_title(_('Version Overview'))
		self.set_size_request(500, 400)
		self.set_resizable(False)
		self.set_modal(True)
		self.set_skip_taskbar_hint(True)

		self.realize()

		self.vbox.set_spacing(5)

		# program logo
		image_file = os.path.join(
								os.path.dirname(sys.argv[0]),
								'images',
								'sunflower_hi-def_64x64.png'
								)
		image = gtk.Image()
		image.set_from_file(image_file)
		image.set_size_request(70, 70)

		# program label
		style = self.get_style().copy()
		program_label = gtk.Label(
							'<span color="{0}">'
							'<span size="x-large" weight="bold">'
							'{2}</span>\n{3} {1[major]}.{1[minor]}{1[stage]} '
							'<span size="small"><i>({1[build]})</i></span>'
							'</span>'.format(
										style.fg[gtk.STATE_SELECTED].to_string(),
										parent.version,
										_('Sunflower'),
										_('Version')
									)
							)
		program_label.set_use_markup(True)

		# notebook which contains changelog and modifications tab
		notebook = gtk.Notebook()

		# modifications
		if show_modifications:
			vbox = gtk.VBox(False, 5)
			vbox.set_border_width(5)

			# label to give some more information
			label_info = gtk.Label(_(
								'Selected modifications will be applied before starting program. '
								'Applying all modifications is strongly suggested. If you manually '
								'changed config files this is a good time to backup them.'
							))
			label_info.set_alignment(0, 0.5)
			label_info.set_justify(gtk.JUSTIFY_LEFT)
			label_info.connect('size-allocate', self._adjust_label)
			label_info.set_line_wrap(True)

			# create viewport to hold all the options for modifications
			modifications_label = gtk.Label(_('Modifications'))
			modifications_window = gtk.Viewport()
			modifications_window.add(modifications)

			vbox.pack_start(label_info, False, False, 0)
			vbox.pack_start(modifications_window, True, True, 0)

			notebook.append_page(vbox, modifications_label)

		# change log
		font = pango.FontDescription('monospace 9')
		changelog = gtk.TextView()
		changelog.set_editable(False)
		changelog.set_cursor_visible(False)
		changelog.set_wrap_mode(gtk.WRAP_WORD)
		changelog.modify_font(font)

		# load change log if it exists
		changelog_file = os.path.join(os.path.dirname(sys.argv[0]), 'change.log')
		if os.path.isfile(changelog_file):
			data = open(changelog_file, 'r').read()
		else:
			# change log was not found
			data = _('Change log was not found!')

		changelog.get_buffer().set_text(data)

		# create tab and container
		changelog_label = gtk.Label(_('Change log'))
		changelog_window = gtk.ScrolledWindow()
		changelog_window.set_shadow_type(gtk.SHADOW_IN)
		changelog_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
		changelog_window.set_border_width(5)
		changelog_window.add(changelog)

		notebook.append_page(changelog_window, changelog_label)

		# top horizontal box containing image and program title
		frame = gtk.EventBox()
		frame.modify_bg(gtk.STATE_NORMAL, style.bg[gtk.STATE_SELECTED])

		hbox1 = gtk.HBox(False, 0)
		frame.add(hbox1)

		hbox1.pack_start(image, False, False, 0)
		hbox1.pack_start(program_label, False, False, 5)

		# actions buttons
		button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
		button_close.set_can_default(True)

		# pack interface
		self.vbox.pack_start(frame, False, False, 0)
		self.vbox.pack_start(notebook, True, True, 0)

		self.add_action_widget(button_close, gtk.RESPONSE_CLOSE)

		self.show_all()

	def get_response(self):
		"""Show dialog and return response"""
		code = self.run()

		self.destroy()

		return code

	def _adjust_label(self, widget, data=None):
		"""Adjust label size"""
		widget.set_size_request(data.width-1, -1)
