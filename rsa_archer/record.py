import logging
import json
import requests

from .user import User

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)


class Record:
	"""
		:param archer_instance - archer incstance object
		:param json:
					{'Id': 305943, 'LevelId': 67, 'SequentialId': 2, 'FieldContents':
					{'18974': {'Type': 9, 'Value': [{'ContentId': 212724, 'LevelId': 34}], 'FieldId': 18974}}
	"""

	def __init__(self, archer_instance, json):
		self.archer_instance = archer_instance
		self.json = json
		self.record_sequential_id = json["SequentialId"]  # just a sequesntial number of record created in application, in my case it was used for uniquly identify a record

	def get_field_content(self, field_name):
		"""
		:param field_name: name how you see it in app
		:returns    value of the field
					array of Users for user field
					LIST of values for values list, including parent value in leveled values list. Looks like this [Parent Value:Value]
					TODO other types of fields
		"""

		field_id = self.archer_instance.get_field_id_by_name(field_name)
		field_type = self.json["FieldContents"][str(field_id)]["Type"]

		try:
			if field_type == 4:  # Values List return ValuesListIds, which should be returned {'ValuesListIds': [69809], 'OtherText': None}
				values_list_id = self.archer_instance.get_vl_id_by_field_name(field_name)
				list_of_value_ids = self.json["FieldContents"][str(field_id)]["Value"]["ValuesListIds"]

				if len(list_of_value_ids) > 1:
					multiple_values = []
					for one_id in list_of_value_ids:
						returned_value = self.get_value_from_valueslistid(one_id, values_list_id)
						multiple_values.append(returned_value)

					return multiple_values
				else:
					value_id = self.json["FieldContents"][str(field_id)]["Value"]["ValuesListIds"][0]
					return [self.get_value_from_valueslistid(value_id, values_list_id)]

			if field_type == 8:  # User/group list {'UserList': [{'Id': 11077, 'HasRead': True, 'HasUpdate': True, 'HasDelete': False}], 'GroupList': []}
				user_ids = self.json["FieldContents"][str(field_id)]["Value"]["UserList"]
				users = []
				for user in user_ids:
					users.append(User(self.archer_instance, user_id=user["Id"]))

				return users
			else:
				return self.json["FieldContents"][str(field_id)]["Value"]

		except Exception as e:
			log.info(f"The field {field_name} is empty, return None. Exception %s", e)
			return None


	def get_value_from_valueslistid(self, value_id, values_list_id):
		"""

		:param value_id: internal values id
		:param values_list_id: internal field id
		:return:
		"""
		api_url = self.archer_instance.api_url_base + "core/system/valueslistvalue/flat/valueslist/" + str(values_list_id)

		try:
			response = requests.get(api_url, headers=self.archer_instance.header, verify=False)
			data = json.loads(response.content.decode("utf-8"))

			for value in data:
				if value["RequestedObject"]["Id"] == value_id:
					if value["RequestedObject"]["ParentId"]:
						parent_value_in_multi_layer_setup = self.get_value_from_valueslistid(value["RequestedObject"]["ParentId"], values_list_id)
						return parent_value_in_multi_layer_setup + ":" + value["RequestedObject"]["Name"]
					else:
						return value["RequestedObject"]["Name"]

		except Exception as e:
			log.error("Function get_value_from_valueslistid didn't work, %s", e)

	def get_sequential_id(self):
		"""
		:return: I forgot why I added this
		"""
		return self.record_sequential_id
