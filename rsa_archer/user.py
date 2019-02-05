import logging
import json
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)


class User:
	"""
		:param archer_instance - archer instance object
		:param json:
		:param user_id: if you know it you can create user object directly
	"""
	def __init__(self, archer_instance=None, json=None, user_id=None):
		self.user_id = None
		self.json = {}
		self.archer_instance = archer_instance
		self.email = ""

		if json:
			self.json = json["RequestedObject"]
			self.user_id = self.json["Id"]

		if user_id:
			self.user_id = str(user_id)
			response = self.archer_instance.get_user_by_id(self.user_id)
			self.json = response.json

		self.capture_user_email()

	def capture_user_email(self):
		api_url = f"{self.archer_instance.api_url_base}core/system/usercontact/{self.user_id}"
		try:
			response = requests.get(api_url, headers=self.archer_instance.header, verify=False)
			if response.status_code != 200:
				self.email = ""
				log.debug("Cannot load email for user ID %s", self.user_id)
			else:
				data = json.loads(response.content.decode("utf-8"))
				self.email = data[0]["RequestedObject"]["Value"]

		except Exception as e:
			self.email =""
			log.error("Exception %s. Guess there is no email for user %s", e, self.json["DisplayName"])

	def get_user_email(self):
		return self.email

	def get_user_id(self):
		return self.user_id

	def get_gisplay_name(self):
		try:
			return self.json["DisplayName"]
		except:
			log.error("Returning None for DisplayName for %s", self.user_id)
			return None

	def get_username(self):
		try:
			return self.json["UserName"]
		except:
			log.error("Returning None for UserName for %s", self.get_gisplay_name())
			return None

	def get_last_login_date(self):
		try:
			return self.json["LastLoginDate"]
		except:
			log.error("Returning None for LastLoginDate for %s", self.get_gisplay_name())
			return None

	def assign_role_to_user(self, role_id):
		"""
		:param role_id: internal system id
		:return: log message of success oe failure
		"""
		api_url = f"{self.archer_instance.api_url_base}core/system/userrole"
		request_body = {"UserId": f"{self.user_id}", "RoleId": f"{role_id}", "IsAdd": "true"}

		try:
			response = requests.put(api_url, headers=self.archer_instance.header, json=request_body, verify=False)
			if response.status_code != 200:
				log.error("User with ID %s can not be added a role %s", self.user_id, role_id)
			else:
				log.info("User %s assigned a role_id %s", self.get_user_email(), role_id)
		except Exception as e:
			log.error("Exception %s", e)

	def put_user_to_group(self, group):
		"""
		:param group: Name of the group how you see it in Archer
		:return: log message of success oe failure
		"""
		group_id = self.archer_instance.get_group_id(group) #just in case

		api_url = f"{self.archer_instance.api_url_base}core/system/usergroup"
		request_body = {"UserId": f"{self.user_id}", "GroupId": f"{group_id}", "IsAdd": "true"}

		try:
			response = requests.put(api_url, headers=self.archer_instance.header, json=request_body, verify=False)
			if response.status_code != 200:
				print(response)
				log.error("User %s can not be added to a group %s", self.get_user_email(), group)
			else:
				log.info("User %s assigned to a group %s", self.get_user_email(), group)
		except Exception as e:
			log.error("Exception %s", e)

	def activate_user(self):
		"""
		:return: log message of success or failure
		"""
		post_header = dict(self.archer_instance.header)
		del post_header["X-Http-Method-Override"]

		api_url = f"{self.archer_instance.api_url_base}core/system/user/status/active/{self.user_id}"

		try:
			response = requests.post(api_url, headers=post_header, verify=False)
			if response.status_code != 200:
				print(response)
				log.error("User %s can not be activated", self.user_id)
			else:
				log.info("User %s is activated", self.get_gisplay_name())
		except Exception as e:
			log.error("Exception in activate_user() %s", e)

	def deactivate_user(self):
		"""
		:return: log message of success or failure
		"""
		post_header = dict(self.archer_instance.header)
		del post_header["X-Http-Method-Override"]

		api_url = f"{self.archer_instance.api_url_base}core/system/user/status/inactive/{self.user_id}"

		try:
			response = requests.post(api_url, headers=post_header, verify=False)
			if response.status_code != 200:
				print(response)
				log.error("User %s can not be deactivated", self.user_id)
			else:
				log.info("User %s is deactivated", self.get_gisplay_name())
		except Exception as e:
			log.error("Exception in deactivate_user() %s", e)