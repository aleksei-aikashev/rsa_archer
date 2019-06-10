import logging
import json
import requests

from .user import User
from .record import Record

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)

# PART BELOW IS USING ARCHER REST API

class ArcherInstance:
	"""
	Creates archer instance object using following arguments:
		:param inst_url - archer instance base url, without https://
		:param instance_name - archer instance name
		:param username - of api user
		:param password - of api user
	"""

	def __init__(self, inst_url, instance_name, username, password):

		self.api_url_base = f"https://{inst_url}/RSAarcher/api/"
		self.content_api_url_base = f"https://{inst_url}/RSAarcher/contentapi/"
		self.username = username
		self.password = password
		self.instance_name = instance_name

		self.session_token = ""
		self.header = ""
		self.url = ""

		self.application_level_id = ""
		self.application_fields_json = {}
		self.all_application_fields_array = []
		self.application_fields_json = {}
		self.vl_name_to_vl_id = {}
		self.subforms_json_by_sf_name = {}
		self.key_field_value_to_system_id = {}

		self.archer_groups_name_to_id = {}

		self.get_session_token()

	def get_session_token(self):
		"""
		Refresh Session Token, should be invoked periodically
		"""

		api_url = f"{self.api_url_base}core/security/login"
		header = {"Accept": "application/json,text/html,application/xhtml+xml,application/xml;q =0.9,*/*;q=0.8",
				  "Content-type": "application/json"}
		try:
			response = requests.post(api_url, headers=header, json={"InstanceName": self.instance_name,
																	"Username": self.username, "UserDomain": "",
																	"Password": self.password}, verify=False)

			data = json.loads(response.content.decode("utf-8"))

			self.session_token = data["RequestedObject"]["SessionToken"]
			self.header = {
				"Accept": "application/json,text/html,application/xhtml+xml,application/xml;q =0.9,*/*;q=0.8",
				"Content-type": "application/json",
				"Authorization": "Archer session-id={0}".format(self.session_token),
				"X-Http-Method-Override": "GET"}

		except Exception as e:
			log.error("Request for Archer session token failed, %s", e)

	def get_users(self, params=""):
		"""
		:param params: like "?$select=Id,UserName,DisplayName&$filter=AccountStatus eq '1' "
							  "and LastLoginDate eq null&$orderby=LastName"
		:returns list of User objects
		"""

		api_url = f"{self.api_url_base}core/system/user/" + params

		try:
			response = requests.post(api_url, headers=self.header, verify=False)

			data = json.loads(response.content.decode("utf-8"))
			list_of_users = []
			for user in data:
				list_of_users.append(User(self, user))

			return list_of_users

		except Exception as e:
			log.error("Function get_users didn't worked, %s", e)

	def get_all_groups(self):
		"""
		:return: populate Archer_instance object with json >  self.archer_groups_name_to_id[name] = id
		"""
		api_url = f"{self.api_url_base}core/system/group/"

		try:
			response = requests.post(api_url, headers=self.header, verify=False)
			data = json.loads(response.content)
			for group in data:
				name = group["RequestedObject"]["Name"]
				id = group["RequestedObject"]["Id"]
				self.archer_groups_name_to_id[name] = id
			log.info("Groups are downloaded")
			return self

		except Exception as e:
			log.error("Function get_all_groups didn't worked, %s", e)

	def find_group(self, name=None):
		"""
		:param name: possible name of the group
		:return: True if name exist and False if name is not found, also prints existing or similar groups
		"""
		not_found = ""
		found = ""

		for i in self.archer_groups_name_to_id.keys():
			if name is i:
				return True
			elif not name:
				not_found += i + ", "
			elif name in i:
				found += i + ", "
			else:
				not_found = i + ", "

		if not name:
			print(f"Name not provided, here are all groups:\n", not_found)
		elif found != "":
			print(f"Matches for group '{name}':\n", found)
		else:
			print(f"Cannot find group '{name}', please try:\n", not_found)

		return False

	def get_group_id(self, group_name):
		"""
		:param group_name: Name of Archer Group
		:return: the name, or False and prints all groups
		"""
		try:
			return self.archer_groups_name_to_id[group_name]
		except:
			print("No such name, try...")
			for key in self.archer_groups_name_to_id.keys():
				print(key, ", ", end="")
			print()
			return False

	def get_user_by_id(self, user_id):
		"""
		:param user_id: internal Archer user id
		:return: User object
		"""
		api_url = f"{self.api_url_base}core/system/user/" + str(user_id)

		try:
			response = requests.post(api_url, headers=self.header, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			return User(self, data)

		except Exception as e:
			log.error("Function get_user_by_id didn't worked, %s", e)

	def get_active_users_with_no_login(self):
		"""
		:return: list of User objects
		"""
		return self.get_users("?$select=Id,UserName,DisplayName&$filter=AccountStatus eq '1' "
							  "and LastLoginDate eq null&$orderby=LastName")

	def from_application(self, app_name=None):
		"""
		:param app_name: sets app you will be working on; type name how it appears in Archer
		:return: self, fills Archer_instance object with proper app_id and fields_ids
		"""
		api_url = f"{self.api_url_base}core/system/application/"

		try:
			response = requests.get(api_url, headers=self.header, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			all_folders = []
			application_id = None

			for application in data:
				if application["RequestedObject"]["Name"] == app_name:
					application_id = application["RequestedObject"]["Id"]
					self.get_application_fields(application_id)
					break
				all_folders.append(application["RequestedObject"]["Name"])

			if not application_id:
				raise RuntimeError(f'Application "{app_name}" is not found, available applications are {all_folders}')

		except Exception as e:
			log.error("Function from_application() didn't worked, %s", e)

		return self

	def get_application_fields(self, application_id):
		"""
		:param application_id: Internal Archer application id, I found it in LevelId if I remember correctly
		:return: Fills the object with all active application fields:
				all_application_fields_array - array of active fields [id1, id2, id3]
				application_fields_json - {{name:id}, {id: {"Type": f_type, "FieldId": id}}}
				subforms_json_by_sf_name - {subform_name: {name:id}, {id: {"Type": f_type, "FieldId": id}},{"LevelId": level_id})
		"""

		api_url = f"{self.api_url_base}core/system/fielddefinition/application/" + str(
				application_id) + "?$filter=IsActive eq true"

		try:
			response = requests.get(api_url, headers=self.header, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			for field in data:
				name = field["RequestedObject"]["Name"]
				id = field["RequestedObject"]["Id"]
				level_id = field["RequestedObject"]["LevelId"]
				f_type = field["RequestedObject"]["Type"]

				self.all_application_fields_array.append(id)
				self.application_fields_json.update({name: id})
				self.application_fields_json.update({id: {"Type": f_type, "FieldId": id}})

				if f_type == 4: #populate values for values list
					self.vl_name_to_vl_id.update({name: field["RequestedObject"]["RelatedValuesListId"]})

				elif f_type == 24: #populate fileds from subforms, up to text fields
					subform_name = field["RequestedObject"]["Name"]
					subform_id = field["RequestedObject"]["RelatedSubformId"]
					subform_fields_json, all_fields = self.get_subform_fields_by_id(subform_id)
					self.subforms_json_by_sf_name.update({subform_name: subform_fields_json})
					self.subforms_json_by_sf_name[subform_name].update({"AllFields": all_fields})

			self.application_level_id = str(level_id) # set the application ID, I found it here

		except Exception as e:
			log.error("Function get_application_fields() didn't worked, %s", e)

	def get_subform_fields_by_id(self, sub_form_id):
		"""
		:param sub_form_id: Gets from parent application field ("RelatedValuesListId"). Note:
		 								I was only interested in text fields and attachments
		:return: {{name:id}, {id: {"Type": f_type, "FieldId": id}, {"LevelId": level_id}}}
		"""
		api_url = f"{self.api_url_base}core/system/fielddefinition/application/" + str(
				sub_form_id) + "?$filter=IsActive eq true"

		try:
			response = requests.get(api_url, headers=self.header, verify=False)
			data = json.loads(response.content.decode("utf-8"))
			subform_fields_names = {}
			fields_ids = []
			for field in data:
				f_name = field["RequestedObject"]["Name"]
				id = field["RequestedObject"]["Id"]
				f_type = field["RequestedObject"]["Type"]
				level_id = field["RequestedObject"]["LevelId"]
				fields_ids.append(id)
				subform_fields_names.update({f_name: id})
				subform_fields_names.update({"LevelId": level_id})
				subform_fields_names.update({id: {"Type": f_type, "FieldId": id}})
			return subform_fields_names, fields_ids

		except Exception as e:
			log.error("Function get_subform_fields_by_id didn't worked, %s", e)

	def get_vl_id_by_field_name(self, vl_field_name):
		"""
		:param vl_field_name: values list name
		:return: vl_id
		"""
		return self.vl_name_to_vl_id[vl_field_name]

	def get_value_id_by_field_name_and_value(self,field_name, value):
		values_list_id = self.get_vl_id_by_field_name(field_name)
		api_url = self.api_url_base + "core/system/valueslistvalue/flat/valueslist/" + str(values_list_id)

		try:
			response = requests.get(api_url, headers=self.header, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			for ind_value in data:
				if  ind_value["RequestedObject"]["Name"]== value:
					ret_arr = []
					ret_arr.append(ind_value["RequestedObject"]["Id"])
					return ret_arr

		except Exception as e:
			log.error("Function get_value_id_by_field_name_and_value didn't worked, %s", e)

	def get_field_id_by_name(self, field_name, sub_form_name=None):
		"""
		:param sub_form_name: Add only if you need id of a subform of application, how you see it on the app
		:param field_name: How you see it in app
		:return: field_id
		"""
		if sub_form_name:
			return self.subforms_json_by_sf_name[sub_form_name][field_name]
		else:
			return self.application_fields_json[f"{field_name}"]

	def add_value_to_field(self, id, value_content):
		"""
		:param id: uniques internal Archer field_id
		:param value_content: could be text, [value for vl], [sub_record_content_id1, sub_record_content_id2, ...]
		"""
		template_for_field_update = dict(self.application_fields_json[id])
		template_for_field_update["Value"] = value_content
		return template_for_field_update

	def create_content_record(self, fields_json, record_id=None):
		"""
		:param fields_json: {field name how you see it in the app: value content
										(for text it text, for others it's internal unique ids)}
		:param record_id:
		:returns int - record_id
		"""
		api_url = f"{self.api_url_base}core/content/"
		post_header = dict(self.header)

		transformed_json = {}
		for key in fields_json.keys():
			current_key_id = self.get_field_id_by_name(key)
			transformed_json[current_key_id] = self.add_value_to_field(current_key_id, fields_json[key])

		if record_id:
			post_header["X-Http-Method-Override"] = "PUT"
			body = json.dumps({"Content": {"Id": record_id, "LevelId": self.application_level_id,
										   "FieldContents": transformed_json}})
		else:
			post_header["X-Http-Method-Override"] = "POST"
			body = json.dumps({"Content": {"LevelId": self.application_level_id, "FieldContents": transformed_json}})

		try:
			if record_id:
				response = requests.put(api_url, headers=post_header, data=body, verify=False)
				data = json.loads(response.content.decode("utf-8"))
				log.info("Record updated, %s", data["RequestedObject"]["Id"])
			else:
				response = requests.post(api_url, headers=post_header, data=body, verify=False)
				data = json.loads(response.content.decode("utf-8"))
				log.info("Function create_content_record created record, %s", data["RequestedObject"]["Id"])

			return data["RequestedObject"]["Id"]

		except Exception as e:
			log.info("Function create_content_record didn't worked, %s", e)

	def create_sub_record(self, fields_json, subform_name):
		"""LevelID is an application
				:param fields_json: {field name how you see it in the app: value content
										(for text it text, for others it's internal unique ids)}
				:param subform_name: how you see it in the app
				:returns sub_record_id
		"""
		api_url = f"{self.api_url_base}core/content/"
		post_header = dict(self.header)
		post_header["X-Http-Method-Override"] = "POST"

		subform_field_id = self.get_field_id_by_name(subform_name)

		transformed_json = {}
		for key in fields_json.keys():
			current_id = self.subforms_json_by_sf_name[subform_name][key]
			current_json = dict(self.subforms_json_by_sf_name[subform_name][current_id])
			current_json["Value"] = fields_json[key]
			subform_level_id = self.subforms_json_by_sf_name[subform_name]["LevelId"]
			transformed_json.update({current_id: current_json})

		body = json.dumps({"Content": {"LevelId": subform_level_id, "FieldContents": transformed_json},
						   "SubformFieldId": subform_field_id})

		try:
			response = requests.post(api_url, headers=post_header, data=body, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			log.info("Function create_sub_record created record, %s", data["RequestedObject"]["Id"])

			return [data["RequestedObject"]["Id"]]

		except Exception as e:
			log.error("Function create_sub_record didn't worked, %s", e)

	def post_attachment(self, name, base64_string):
		"""
		:param name: Name of the attachment
		:param base64_string: File in base64_string
		:return:
		"""
		api_url = f"{self.api_url_base}core/content/attachment"
		post_header = dict(self.header)
		post_header["X-Http-Method-Override"] = "POST"
		body = json.dumps({"AttachmentName": name, "AttachmentBytes": base64_string})

		try:
			response = requests.post(api_url, headers=post_header, data=body, verify=False)
			data = response.json()

			log.info("Attachment %s posted to Archer", data["RequestedObject"]["Id"])
			return data["RequestedObject"]["Id"]

		except Exception as e:
			log.error("Function post_attachment didn't worked, %s; Response content: %s", e, response.content)

	def update_content_record(self, updated_json, record_id):
		"""LevelID is an application
		:param updated_json: see function create_content_record()
		:param record_id: internal archer ID
		:returns record_id
		"""
		return self.create_content_record(updated_json, record_id)

	def get_record(self, record_id):
		"""
		:param record_id: internal archer record id
		:return: record object
		"""
		api_url = f"{self.api_url_base}core/content/fieldcontent/"
		cont_id = [str(record_id)]
		body = json.dumps({"FieldIds": self.all_application_fields_array, "ContentIds": cont_id})

		post_header = dict(self.header)
		post_header["X-Http-Method-Override"] = "POST"

		try:
			response = requests.post(api_url, headers=post_header, data=body, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			return Record(self, data[0]["RequestedObject"])

		except Exception as e:
			log.error("Function get_record() didn't worked, %s", e)

	def get_sub_record(self, sub_record_id, sub_record_name):
		"""
		:param sub_record_id:
		:param sub_record_name:
		:return: record object
		"""
		api_url = f"{self.api_url_base}core/content/fieldcontent/"
		cont_id = [str(sub_record_id)]
		all_fields_arr = self.subforms_json_by_sf_name[sub_record_name]["AllFields"]
		body = json.dumps({"FieldIds": all_fields_arr, "ContentIds": cont_id})

		post_header = dict(self.header)
		post_header["X-Http-Method-Override"] = "POST"

		try:
			response = requests.post(api_url, headers=post_header, data=body, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			return Record(self, data[0]["RequestedObject"])

		except Exception as e:
			log.error("Function get_sub_record() didn't worked, %s", e)

# THIS PART IS USING ARCHER GRC API, NOT REST API USED ABOVE

	def find_grc_endpoint_url(self, app_name):
		"""
		:param app_name: Try a name you see in the app
		:return: You will get printout of all similar grc_api endpoints urls that
				 might be slightly different from the app name, don't ask me why.
				 For all grc_api calls use the name you get.
		"""

		response = requests.get(self.content_api_url_base, headers=self.header, verify=False)
		data = json.loads(response.content.decode("utf-8"))

		print("I've found the following: ")

		for endpoint in data["value"]:
			if app_name in endpoint["name"]:
				print("endpoint_url: ", endpoint["url"])

	def get_grc_endpoint_records(self, endpoint_url, skip=None):
		"""
		By default gets 1000 records from the endpoint.
		:param endpoint_url: get from find_grc_endpoint_url()
		:param skip: number of records to skip in thousands (1,2,3)
		:return: array of record jsons
		"""
		if skip:
			api_url = self.content_api_url_base + endpoint_url + "?$skip=" + str(skip)

		else:
			api_url = self.content_api_url_base + endpoint_url

		response = requests.get(api_url, headers=self.header, verify=False)
		data = json.loads(response.content.decode("utf-8"))
		array_jsons = []

		for record in data["value"]:
			array_jsons.append(record)

		return array_jsons

	def build_unique_value_to_id_mapping(self, endpoint_url, key_value_field=None, prefix=None):
		"""
		:param endpoint_url: get from find_grc_endpoint_url()
		:param key_value_field: name of the field with unique value that you
						identified in your application(e.g. "Incident #")
		:param prefix: adding prefix in front of key_value_field, sometimes in Archer
		 				tranp_key fields are shown like INC-xxx, but in app they only have xxx,
		 				so to solve that add prefix here, in our case it's INC-
		:return: Populate Archer_Instance object with self.key_field_value_to_system_id with {field_value:content_record_id}
		"""

		i = 0
		for_equal_numbers = 0  # breaks out of the loop if the number of records are equal to 1000
		all_records = []

		while True:
			current_records = self.get_grc_endpoint_records(endpoint_url, i)
			all_records += current_records
			if len(current_records) != 1000 or for_equal_numbers > 21: # Attention, if records are more than 21000 increase the value
				break

			i += 1000
			for_equal_numbers += 1

		for record in all_records:
			if key_value_field:
				if prefix:
					field_value = prefix + str(record[key_value_field])
				else:
					field_value = str(record[key_value_field])

				system_id = record[endpoint_url + "_Id"]
				self.key_field_value_to_system_id.update({field_value: system_id})

			else:
				print(record)
				print('Please choose your key_field above: {"KEY_FIELD": "unique value"}')
				break

		log.info("Updated the mapping between record id and KEY_FIELD")

	def get_record_id_by_unique_value(self, key_value_field):
		"""
		:param key_value_field: field you used in build_unique_value_to_id_mapping()
		:return: record id or False
		"""
		try:
			return self.key_field_value_to_system_id[key_value_field]
		except:
			return False

	def add_record_id_to_mapping(self, key_value_field, system_id, prefix=None):
		"""
		:param key_value_field: field you used in build_unique_value_to_id_mapping()
		:param system_id: redord id
		:param prefix:
		:return: populate self.key_field_value_to_system_id
		"""
		if prefix:
			field_value = prefix + str(key_value_field)
		else:
			field_value = str(key_value_field)

		self.key_field_value_to_system_id.update({field_value: system_id})
