rsa_archer - library to work with Archer REST and GRC api
===========================================

The original objective of rsa_archer was to create a package to support connector between Office365 mailbox to Archer Incidents application.
Python script captures the email, check if there is an incident ID assigned and add new email to comments (sub form) in archer record.
Here is the archer part of this connector, if someone interested I can share the whole thing.

##How it works:
1. You need to create "api" user in your Archer Instance first
1. Then get authorized in your Archer Instance
1. And continue to work with Archer Instance object
```python
from rsa_archer.archer_instance import ArcherInstance
import getpass
archer_pass = getpass.getpass(prompt="Archer api user password: ")
archer_instance = ArcherInstance("<DOMAIN NAME, e.g. app.com>",
                                                  "<ARCHER INSTANCE NAME, find it in you archer admin panel>",
                                                  "api", archer_pass)
```

###Working with content records

Select Archer application you will be working on (one application per Archer Instance object) and do stuff.

**NOTE** - right now working natively with record's fields is limited to text fields and attachments, for values list and other types of fields you need to check the code, anyway some of the functions might be missing, since I didn't need them at that time.

```python
#don't forget to select application, without it it'll not work

archer_instance.from_application("APPLICATION, e.g. Incidents")

#create new record in selected application
#prepare json with field names and their values

record_json = {"FIELD NAME": "VALUE", "Field 1. Incident Summary": "desired text", "Field 2. Reporter email": "email",
 "...Incident Details": "HTML text" etc}
record_id = archer_instance.create_content_record(record_json)

#working with existing records

existing_record = archer_instance.get_record(record_id)
existing_record.get_field_content("field_name")

# it returns, value of the text field
#       array of user internal ids for user field
#       proper value for values list
#       internal ids for other types of fields
#       TODO other types of fields

#update existing records

updater_json = {"FIELD NAME": "VALUE", "Field 1. Incident Summary": "desired text", "Field 2. Reporter email": "email",
 "...Incident Details": "HTML text" etc}
archer_instance.update_content_record(updater_json, record_id)

#post attachments to archer instance

attachment_id = archer_instance.post_attachment("NAME of the file", fileinbase64_string)

#put ids in array

attachment_ids = []
attachment_ids.append(attachment_id)

#assosiate it with the existing record for example

updater_json = {"FIELD NAME, e.g. Attachments": attachment_ids}
archer_instance.update_content_record(updater_json, record_id)
```

### Working with sub forms in content records
```python
#create sub_form

sub_form_json = {"SUB FORM FIELD NAME": "VALUE", etc}
new_sub_form_id = archer_instance.create_sub_record(sub_form_json, "APPLICATION FIELD NAME")

#assosiate it with content record, in this case existing record

updater_json = {"APPLICATION FIELD NAME": sub_record_id}
archer_instance.update_content_record(updater_json, record_id)

#but it will replace the existing subrecords in application, so you should get the existing subrecords first:

current_sub_records_ids = record.get_field_content("APPLICATION FIELD NAME")
if current_sub_records:
    final_sub_records = current_sub_records_ids + new_sub_record_id
else:
    final_sub_records = new_sub_record_id

updater_json = {"APPLICATION FIELD NAME": final_sub_records}
archer_instance.update_content_record(updater_json, record_id)

#same thing with attachments to sub records
#post attachments to archer instance

attachment_id = archer_instance.post_attachment("NAME of the file", fileinbase64_string)

#put attachment ids into array

attachment_ids = []
attachment_ids.append(attachment_id)

#assosiate it with the new sub_record

sub_form_json = {"SUB FORM FIELD NAME": attachment_ids}
archer_instance.create_sub_record(sub_form_json, "APPLICATION FIELD NAME")
```
### Working with users
```python
#get all user objects

users = archer_instance.get_users()

#get individual user object

user = archer_instance.get_user_by_id("UNIQUE ARCHER ID")

#get users with parameters, find full list of parameters in Archer REST API documentation

users = archer_instance.get_users("?$select=Id,DisplayName&$orderby=LastName")

#there is one more method to get active users with no login, but it is easier to play with parameters

users = archer_instance.get_active_users_with_no_login()

#user object methods, added for convenience, all information could be found in user.json

email = user.get_user_email()
id = user.get_user_id()
display_name = user.get_gisplay_name()
user_name = user.get_username()
last_login = user.get_last_login_date()

#active methods

user.assign_role_to_user("ROLE ID")
user.activate_user()
archer_instance.get_all_groups() #loads all groups first
user.put_user_to_group("GROUP NAME")
```
### Archer GRC API methods (it's a different api, can do stuff that REST can't)
```python
# to start working in GRC api you need set an endpoint, analog of application we used in REST

archer_instance.find_grc_endpoint_url("APPLICATION NAME")

# it'll print the similar endpoint names

#with endpoint name you can get content records of the application

array_of_jsons = archer_instance.get_grc_endpoint_records("ENDPOINT NAME", skip=None)

#it'll give you only 1000 records at a time, use skip to get more
#I used this api only to get key field to id mapping, since there is no normal search in REST API
#so method returns array of array_of_jsons instead of record objects
#also I don't think that returned jsons from REST and GRC are equal

#so building uniques field value to if mapping

archer_instance.build_unique_value_to_id_mapping("ENDPOINT NAME", "APPLICATION UNIQUE FIELD", "PREFIX")

# for incidents "APPLICATION UNIQUE FIELD" was incident # or INC-xxx, but uniques field stored only number
# so I needed to add prefix "INC-" to the method

#result

record_id = archer_instance.get_record_id_by_unique_value("UNIQUE VALUE, in my case INC-xxx")
```