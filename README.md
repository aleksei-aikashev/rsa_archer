Library to work with Archer REST and Content APIs
===========================================
My original objective was to create Office365 mailbox to Archer Incidents application connector.Script captures the email, checks if there is an incident ID assigned and add the email to comments section (sub form) in archer record.
This package supports archer part of this connector, if someone interested I can share the whole thing.

# Archer REST API  
## 1. Create Archer Instance
Firstly create "api" user in Archer
And create Archer Instance object and continue to work with it
```python
from rsa_archer.archer_instance import ArcherInstance
archer_instance = ArcherInstance("domain","archer instance","api username", "password")
# e.g. 
archer_instance = ArcherInstance("archer.companyzxc.com","risk_management","api", "123456")
```

## 2. Working with content records
### 2.1 Selecting application
To start working with content records you need to select Archer application (one application per Archer Instance object), without it it'll not work.
```python
archer_instance.from_application("application name")
# e.g.
archer_instance.from_application("Incidents") #same name as in archer application list
```
### 2.2 Create new record
**NOTE** - right now working natively with record's fields is limited to text fields and attachments, for values list and other types of fields you need to check the code, anyway some of the functions might be missing, since I didn't need them at that time.
Preparing json with field names and their values:
```python
record_json = {"field name1": "value1", "field name2": "value2", ...}
# e.g.
record_json = {"Incident Summary": "desired text", "Reporter email": "email","Incident Details": "HTML text"}
```
Creating the record and getting its id:
```python
record_id = archer_instance.create_content_record(record_json)
```

### 2.2 Working with existing records
#### 2.2.1 Getting record content
Getting record object by id:
```python
existing_record = archer_instance.get_record(record_id)
```
Getting values of record fields:
```python
existing_record.get_field_content("field_name")

# it returns, value of the text field
#       array of user internal ids for user field
#       proper value for values list
#       internal ids for other types of fields
#       TODO other types of fields
```

#### 2.2.2 Updating existing record
Preparing updater json
```python
updater_json = {"field name1": "value1", "field name2": "value2", ...}
#e.g.
updater_json = {"Incident Summary": "desired text", "Reporter email": "email","Incident Details": "HTML text"}
 ```

Updating the record values:
```python
archer_instance.update_content_record(updater_json, record_id)
```
#### 2.2.3 Post attachments to archer instance
Uploading attachment to Archer and getting its id:
```python
attachment_id = archer_instance.post_attachment("file name", fileinbase64_string)
```
Put attachment ids into array, you might want to get existing record atttachments ids first and append additional attachment id to it or you will lose the existing ones:
```python
attachment_ids = []
attachment_ids.append(attachment_id)
```
Assosiate the ids with the existing record for example:
```python
updater_json = {"Attachments": attachment_ids}
archer_instance.update_content_record(updater_json, record_id)
```

## 3. Working with sub forms in content records
### 3.1 Creating subrecords
Creating sub_record and getting its id:
```python
sub_form_json = {"subform field name1": "value1", "subform field name1": "value1", ...}
sub_record_id = archer_instance.create_sub_record(sub_form_json, "subform field name in target application")
```
Assosiate subrecord with content record, in this case existing record:
```python
updater_json = {"subform field name in target application": sub_record_id}
archer_instance.update_content_record(updater_json, record_id)
```
But it will replace the existing subrecords in application, so you should get the existing subrecords first:
```python
current_sub_records_ids = record.get_field_content("subform field name in target application") #get the array of existing attachments ids
if current_sub_records:
    final_sub_records = current_sub_records_ids + sub_record_id
else:
    final_sub_records = sub_record_id
```
And then update the original application record: 
```python
updater_json = {"subform field name in target application": sub_record_id}
archer_instance.update_content_record(updater_json, record_id)
```
### 3.2 Attachments to subrecords
Uploading attachment to Archer and getting its id:
```python
attachment_id = archer_instance.post_attachment("file name", fileinbase64_string)
```
Put attachment ids into array:
```python
attachment_ids = []
attachment_ids.append(attachment_id)
```

Assosiate it with the new sub_record
```python
sub_form_json = {"sub form attachment field name": attachment_ids}
archer_instance.create_sub_record(sub_form_json, "APPLICATION FIELD NAME")
```

## 4. Working with users
### 4.1 Get user objects:
Get all user objects:
```python
users = archer_instance.get_users()
```
Get individual user object:
```python
user = archer_instance.get_user_by_id("user id")
```
Get users using filters, find full list of filters in Archer REST API documentation:
```python
users = archer_instance.get_users("?$select=Id,DisplayName&$orderby=LastName")
```
Get active users with no login:
```python
users = archer_instance.get_active_users_with_no_login()
```
### 4.2 Get users info
Get user object parameters, added for convenience, all information could be found in user.json:
```python
email = user.get_user_email()
id = user.get_user_id()
display_name = user.get_gisplay_name()
user_name = user.get_username()
last_login = user.get_last_login_date()
```
### 4.3 Active user methods
Assign user to role:
```python
user.assign_role_to_user("role id")
```
Activate user:
```python
user.activate_user()
```
Add user to group:
```python
archer_instance.get_all_groups() #loads all groups first
user.put_user_to_group("group name")
```
# Archer Content API  
To start working in Content api you need set an endpoint, analog of application we used in REST.
To find the exact name use the following method, it'll print the similar endpoint names:
```python
archer_instance.find_grc_endpoint_url("application name")
```
With endpoint name you can get content records of the application:
* it'll give you only 1000 records at a time, use skip to get more
* I used this api only to get key field to id mapping, since there is no normal search in REST API
* so method returns array_of_jsons instead of record objects, since these jsons are different from REST jsons and I don't use them
```python
array_of_jsons = archer_instance.get_grc_endpoint_records("endpoint name", skip=None)
```
Building key field value to record id mapping:
* for Incidents application "application key field" was incident #INC-xxx, but key field stored only integer
* so I added prefix "INC-" to the method
```python
archer_instance.build_unique_value_to_id_mapping("endpoint name", "application key field", "prefix"=None)
```
So based on key field value I can get record id:
```python
record_id = archer_instance.get_record_id_by_unique_value("key field value")
```