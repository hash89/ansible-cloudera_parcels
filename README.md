# ansible-cloudera_parcels
Ansible module to manage Cloudera Manager parcels, using the [cm_api](https://cloudera.github.io/cm_api/docs/python-client/) Python lib. 

This module come from my company internal Ansible toolbox. [Groupe Cyrès][1]

[1]: https://www.cyres.fr/

# Contributor

- Hadrien Puissant (@HadrienPuissant)
- Antoine Pointeau (@Rocketknow)
- Antoine Boudot (@AntoineBoudot)

# Instruction

1) Copy the file `cloudera_parcels.py` into the Ansible library folder. (located at: `/etc/ansible/library` dy default)
2) Ensure you have the `cm_api` python package installed on the host that execute the tasks

# Warnings

- Check mode not supported yet

# Usage

Examples:
```
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
```
