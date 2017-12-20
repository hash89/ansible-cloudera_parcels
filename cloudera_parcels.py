#!/usr/bin/python

ANSIBLE_METADATA = {
    "metadata_version"  : "1.0",
    "supported_by"      : "community",
    "status"            : ["preview"],
    "version"           : "1.1.0"
}

DOCUMENTATION = """
---
module: cloudera_parcels
short_description: Deploy parcels for cloudera distribution
description:
    - This module allows downloading, deploying and activating parcels
version_added: "2.4"
author: Hadrien Puissant (Twitter @hadrienpuissant, Github hash89)
options:
    api_version:
        description:
            - Version of the Cloudera Manager API to use
            - fDepend on the Cloudera Manager version
        required: true
    cm_login:
        description:
            - Login to autheticate against the Cloudera Manager
            - The account need at least read access to the Cloudera Manager
        required: true
    cm_password:
        description:
            - The password to authenticate against the Cloudera Manager
        required: true
    cm_host:
        description:
            - Host for the Cloudera Manager server
        required: true
    cluster_name:
        description:
            - The cluster you want to deploy parcels
        required: true
    product:
        description:
            - The name of the parcel as it appear in the Cloudera Manager server
        required: true if state is not infos
    version:
        description:
            - The version of the parcel you want to manipulate or
            - "latest" to target the latest version available on the Cloudera Manager server
        required: true if state is not infos
	choices:
	    - 'the exact version string'
	    - latest
    state:
        description:
            - If `present`, the module will ensure parcel is downloaded or more on the cluster
            - If `distributed`, the module will ensure the parcel is distributed on all host or more
            - If `activated`, the module will ensure the parcel is actvated
            - If `absent`, The module will ensure the parcel is not present on the cluster
            - it will desactivate the parcel, undistributed it and remove from hosts
            - Info will give you informations about the parcel you target
            - Information available : product, version, stage
            - If you do not specify product or version the module will collect informations about all parcels available
        default: present
        choices:
            - present
            - distributed
            - activated
            - absent
            - infos
notes:
    - check_mode not supported yet
"""

EXAMPLES = """

- name: Download parcel for latest CDH parcel (available on the Cloudera Manager)
  cloudera_parcels:
    cm_login: john
    cm_password: toto18
    api_version: 18
    cm_host: cloudera.mycompany.com
    cluster_name: test
    product: CDH
    version: latest
    state: present

- name: Distribute parcel for CDH
  cloudera_parcels:
    cm_login: john
    cm_password: toto18
    api_version: 18
    cm_host: cloudera.mycompany.com
    cluster_name: test
    product: CDH
    version: 5.13.0-1.cdh5.13.0.p0.29
    state: distributed

- name: Activate parcel for CDH
  cloudera_parcels:
    cm_login: john
    cm_password: toto18
    api_version: 18
    cm_host: cloudera.mycompany.com
    cluster_name: test
    product: CDH
    version: 5.13.0-1.cdh5.13.0.p0.29
    state: activated

- name: Remove parcel for CDH
  cloudera_parcels:
    cm_login: john
    cm_password: toto18
    api_version: 18
    cm_host: cloudera.mycompany.com
    cluster_name: test
    product: CDH
    version: 5.13.0-1.cdh5.13.0.p0.29
    state: absent

- name: Retreive informations for all parcels on a cluster
  cloudera_parcels:
    cm_login: john
    cm_password: toto18
    api_version: 18
    cm_host: cloudera.mycompany.com
    cluster_name: test
    state: infos

- name: Retreive informations for a sspecific parcel on a cluster
  cloudera_parcels:
    cm_login: john
    cm_password: toto18
    api_version: 18
    cm_host: cloudera.mycompany.com
    cluster_name: test
    product: CDH
    version: 5.13.0-1.cdh5.13.0.p0.29
    state: infos
"""


import sys
import time
from natsort import natsorted

from ansible.module_utils.basic import AnsibleModule

from cm_api.api_client import ApiResource, ApiException


def build_module():
    fields = {
        "api_version": {"required": True, "type": "str"},
        "cm_login": {"required": True, "type": "str", "no_log": False},
        "cm_password": {"required": True, "type": "str", "no_log": True},
        "cm_host": {"required": True, "type": "str"},
        "cluster_name" : {"required": True, "type": "str"},
        "product": {"required": False, "type": "str"},
        "version": {"required": False, "tye": "str"},
        "state": {
            "default": "present",
            "choices": ['present', 'distributed', 'activated', 'absent', 'infos'],
            "type": 'str'
        }
    }
    required_if = [
      [ "state", "present", [ "product", "version" ] ],
      [ "state", "distributed", [ "product", "version" ] ],
      [ "state", "activated", [ "product", "version" ] ],
      [ "state", "absent", [ "product", "version" ] ]
    ]
    mutually_exclusive = []
    module = AnsibleModule(
        argument_spec=fields,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True
    )

    return module

def main():
    module = build_module()
    choice_map = {'present': present, 'distributed': distributed, 'activated': activated, 'absent': absent, 'infos': infos}
    params = module.params
    has_changed = False

    api = ApiResource(params["cm_host"], username=params["cm_login"], password=params["cm_login"], version=params["api_version"])

    try:
        cluster = api.get_cluster(params["cluster_name"])
    except ApiException as e:
        module.fail_json(msg="Cluster error : {0}".format(e))

    if params["product"] and params["version"]:
        parcel = get_parcel(cluster, params["product"], params["version"])
        if params["state"] != "infos":
            error, has_changed, result, meta = choice_map.get(params['state'])(cluster, parcel)

            if error:
                module.fail_json(msg=result)
            module.exit_json(changed=has_changed, msg=result, meta=meta)
        else:
            meta = {
                "product": parcel.product,
                "version": parcel.version,
                "stage": parcel.stage
            }
            module.exit_json(changed=False, msg="Parcel informations gathered", meta=meta)
    elif not params["product"] and not params["version"] and params["state"] == "infos":
        module.exit_json(changed=has_changed, msg="Parcel informations gathered", meta=infos(cluster))

def get_parcel(cluster, product, version):
    if version == "latest":
        versions = []
        for parcel in cluster.get_all_parcels():
            versions.append(parcel.version)
        version = natsorted(versions)[-1]
    try:
        return cluster.get_parcel(product, version)
    except ApiException as e:
        module.fail_json(msg="Parcel error : {0}".format(e))

def format_meta_parcel(parcel):
	return {
		"product": parcel.product,
		"version": parcel.version,
		"stage": parcel.stage
	}

def infos(cluster):
    parcel_list = []
    for parcel in cluster.get_all_parcels():
        parcel_list.append({
            "version": parcel.version,
            "product": parcel.product,
            "stage": parcel.stage
        })
    return parcel_list

def distributed(cluster, parcel):
	changed = False
	error = False
	msg = ""

	if parcel.stage == "DOWNLOADED":
		if parcel.start_distribution().wait(3000).success:
			while cluster.get_parcel(parcel.product, parcel.version).stage == "DISTRIBUTING":
				time.sleep(1)
				pass
			changed = True
			msg = "Parcel distributed"
		else:
			error = True
			msg = "{0}".format(e)
	elif parcel.stage in ["DISTRIBUTED", "ACTIVATED"]:
		msg = "Parcel already distributed"
	else:
		error = True
		msg = "Parcel not in correct stage for distribution. Stage : {0}".format(parcel.stage)

	return error, changed, msg, format_meta_parcel(cluster.get_parcel(parcel.product, parcel.version))


def activated(cluster, parcel):
	changed = False
	error = False
	msg = ""

	if parcel.stage == "DISTRIBUTED":
		if parcel.activate().wait(3000).success:
			while cluster.get_parcel(parcel.product, parcel.version).stage == "ACTIVATING":
				time.sleep(1)
				pass
			changed = True
			msg = "Parcel activated"
		else:
			error = True
			msg = "{0}".format(e)
	elif parcel.stage == "ACTIVATED":
		msg = "Parcel already activated"
	else:
		error = True,
		msg = "Parcel not in correct stage for distribution. Stage : {0}".format(parcel.stage)

	return error, changed, msg, format_meta_parcel(cluster.get_parcel(parcel.product, parcel.version))


def absent(cluster, parcel):
	changed = False
	error = False
	msg = ""

	# If parcel is activated, deactivate it first
	if parcel.stage == "ACTIVATED":
		if parcel.deactivate().wait(3000).success:
			while cluster.get_parcel(parcel.product, parcel.version).stage == "ACTIVATING":
				time.sleep(1)
				pass
			changed = True
	# If parcel has been deactivated or is just distributed
	if cluster.get_parcel(parcel.product, parcel.version).stage == "DISTRIBUTED":
		if parcel.start_removal_of_distribution().wait(3000).success:
			while cluster.get_parcel(parcel.product, parcel.version).stage != "DOWNLOADED":
				time.sleep(1)
				pass
			changed = True
	# If parcel has been undistributed or is just downloaded
	if cluster.get_parcel(parcel.product, parcel.version).stage == "DOWNLOADED":
		if parcel.remove_download().wait(3000).success:
			while cluster.get_parcel(parcel.product, parcel.version).state.progress > 0:
				time.sleep(1)
				pass
			changed = True
			msg = "Parcel removed successfully"
		else:
			error = True
			msg = "Parcel remove error : {0}".format(e)
	elif parcel.stage in ["AVAILABLE_REMOTELY"]:
		msg = "Parcel already absent"

	return error, changed, msg, format_meta_parcel(cluster.get_parcel(parcel.product, parcel.version))


def present(cluster, parcel):
	changed = False
	error = False
	msg = ""

	if parcel.stage == "AVAILABLE_REMOTELY":
		if parcel.start_download().wait(3000).success:
			while cluster.get_parcel(parcel.product, parcel.version).stage == "DOWNLOADING":
				time.sleep(1)
				pass
			changed = True
			msg = "Parcel downloded"
		else:
			error = True
			msg = "Parcel downlod error : {0}".format(e)
	elif parcel.stage in ["DOWNLOADING", "DISTRIBUTING", "UNDISTRIBUTING", "ACTIVATING"]:
		msg = "Parcel in transient state = {0}".format(parcel.stage)
	else:
		msg = "Parcel already present"

	return error, changed, msg, format_meta_parcel(cluster.get_parcel(parcel.product, parcel.version))


if __name__ == "__main__":
    main()
