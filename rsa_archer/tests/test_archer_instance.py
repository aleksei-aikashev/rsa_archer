from .config import USERNAME,PASSWORD,ARCHER_DOMAIN,INSTANCE_NAME, APPLICATION

from rsa_archer.archer_instance import ArcherInstance
from urllib3 import disable_warnings, exceptions
disable_warnings(exceptions.InsecureRequestWarning)  # Suppress InsecureRequestWarning

class TestArcherInstance:
	def test_setup_class(self):
		self.archer_instance = ArcherInstance(ARCHER_DOMAIN, INSTANCE_NAME,USERNAME, PASSWORD)

		assert len(self.archer_instance.session_token) > 0

	def test_from_application(self):
		self.archer_instance = ArcherInstance(ARCHER_DOMAIN, INSTANCE_NAME, USERNAME, PASSWORD)
		self.archer_instance.from_application(APPLICATION)

		assert self.archer_instance.application_level_id != ""

	def test_create_content_record(self):
#		self.archer_instance.create_content_record(record_json)
#		self.archer_instance.update_content_record(updater_json, record_id)
		pass

	def test_post_attachment(self):
		self.archer_instance = ArcherInstance(ARCHER_DOMAIN, INSTANCE_NAME, USERNAME, PASSWORD)
		id = self.archer_instance.post_attachment("TEST.TXT", """RXJyb3IsIHBsZWFzZSByZXNlbmQgZmlsZSBpbiB6aXAgZm9ybWF0LiBUaGlzIHR5cGVzIG9mIGZp
								bGVzIGFyZSBub3QgYWNjZXB0ZWQgYnkgQXJjaGVyIGFzIGlzLg==""")

		assert id

	def	test_create_sub_record(self):
#		self.archer_instance.create_sub_record(sub_form_json, "APPLICATION FIELD NAME")
		pass

	def test_get_users(self):
		self.archer_instance = ArcherInstance(ARCHER_DOMAIN, INSTANCE_NAME, USERNAME, PASSWORD)
		users = self.archer_instance.get_users()

		assert len(users) > 0 and users[0].get_user_id() is not None

	def test_get_groups(self):
		self.archer_instance = ArcherInstance(ARCHER_DOMAIN, INSTANCE_NAME, USERNAME, PASSWORD)
		self.archer_instance.get_all_groups()

		assert len(self.archer_instance.archer_groups_name_to_id) > 0

	def test_get_grc_endpoint_records(self):
		self.archer_instance = ArcherInstance(ARCHER_DOMAIN, INSTANCE_NAME, USERNAME, PASSWORD)
		jsons = self.archer_instance.get_grc_endpoint_records(APPLICATION)

		assert len(jsons) > 0



