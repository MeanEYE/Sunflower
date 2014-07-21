try:
	dbus_available = True
	from dbus_interface import DBus_Client, DBus_Service

except:
	dbus_available = False


class DBus:
	"""General DBus methods."""

	service = None
	client = None

	@classmethod
	def is_available(cls):
		"""Check if DBus is available."""
		return dbus_available

	@classmethod
	def get_client(cls, application):
		"""Get DBus client."""
		if cls.client is None and dbus_available:
			cls.client = DBus_Client(application)

		return cls.client

	@classmethod
	def get_service(cls, application):
		"""Get DBus service."""
		if cls.service is None and dbus_available:
			cls.service = DBus_Service(application)

		return cls.service
