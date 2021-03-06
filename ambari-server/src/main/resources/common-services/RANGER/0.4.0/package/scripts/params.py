#!/usr/bin/env python
"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
import os
from resource_management.libraries.script import Script
from resource_management.libraries.functions.version import format_hdp_stack_version
from resource_management.libraries.functions.format import format
from resource_management.libraries.functions.default import default

# a map of the Ambari role to the component name
# for use with /usr/hdp/current/<component>
SERVER_ROLE_DIRECTORY_MAP = {
  'RANGER_ADMIN' : 'ranger-admin',
  'RANGER_USERSYNC' : 'ranger-usersync'
}

component_directory = Script.get_component_from_role(SERVER_ROLE_DIRECTORY_MAP, "RANGER_ADMIN")

config  = Script.get_config()
tmp_dir = Script.get_tmp_dir()

stack_name = default("/hostLevelParams/stack_name", None)
version = default("/commandParams/version", None)
host_sys_prepped = default("/hostLevelParams/host_sys_prepped", False)

stack_version_unformatted = str(config['hostLevelParams']['stack_version'])
hdp_stack_version = format_hdp_stack_version(stack_version_unformatted)

xml_configurations_supported = config['configurations']['ranger-env']['xml_configurations_supported']

stack_is_hdp22_or_further = Script.is_hdp_stack_greater_or_equal("2.2")
stack_is_hdp23_or_further = Script.is_hdp_stack_greater_or_equal("2.3")

if stack_is_hdp22_or_further:
  ranger_home    = '/usr/hdp/current/ranger-admin'
  ranger_conf    = '/usr/hdp/current/ranger-admin/conf'
  ranger_stop    = '/usr/bin/ranger-admin-stop'
  ranger_start   = '/usr/bin/ranger-admin-start'
  usersync_home  = '/usr/hdp/current/ranger-usersync'
  usersync_start = '/usr/bin/ranger-usersync-start'
  usersync_stop  = '/usr/bin/ranger-usersync-stop'
  ranger_ugsync_conf = '/etc/ranger/usersync/conf'
  
usersync_services_file = "/usr/hdp/current/ranger-usersync/ranger-usersync-services.sh"

java_home = config['hostLevelParams']['java_home']
unix_user  = config['configurations']['ranger-env']['ranger_user']
unix_group = config['configurations']['ranger-env']['ranger_group']
ranger_pid_dir = config['configurations']['ranger-env']['ranger_pid_dir']
usersync_log_dir = config['configurations']['ranger-env']['ranger_usersync_log_dir']

ambari_server_hostname = config['clusterHostInfo']['ambari_server_host'][0]

db_flavor =  (config['configurations']['admin-properties']['DB_FLAVOR']).lower()
usersync_exturl =  config['configurations']['admin-properties']['policymgr_external_url']
ranger_host = config['clusterHostInfo']['ranger_admin_hosts'][0]
ranger_external_url = config['configurations']['admin-properties']['policymgr_external_url']
ranger_db_name = config['configurations']['admin-properties']['db_name']
ranger_auditdb_name = config['configurations']['admin-properties']['audit_db_name']

sql_command_invoker = config['configurations']['admin-properties']['SQL_COMMAND_INVOKER']
db_root_user = config['configurations']['admin-properties']['db_root_user']
db_root_password = unicode(config['configurations']['admin-properties']['db_root_password'])
db_host =  config['configurations']['admin-properties']['db_host']
ranger_db_user = config['configurations']['admin-properties']['db_user']
ranger_audit_db_user = config['configurations']['admin-properties']['audit_db_user']
ranger_db_password = unicode(config['configurations']['admin-properties']['db_password'])

#ranger-env properties
oracle_home = default("/configurations/ranger-env/oracle_home", "-")

#For curl command in ranger to get db connector
jdk_location = config['hostLevelParams']['jdk_location'] 
java_share_dir = '/usr/share/java'
if db_flavor.lower() == 'mysql':
  jdbc_symlink_name = "mysql-jdbc-driver.jar"
  jdbc_jar_name = "mysql-connector-java.jar"
  db_jdbc_url = format('jdbc:log4jdbc:mysql://{db_host}/{ranger_db_name}')
  audit_jdbc_url = format('jdbc:log4jdbc:mysql://{db_host}/{ranger_auditdb_name}')
  jdbc_driver = "net.sf.log4jdbc.DriverSpy"
  jdbc_dialect = "org.eclipse.persistence.platform.database.MySQLPlatform"
elif db_flavor.lower() == 'oracle':
  jdbc_jar_name = "ojdbc6.jar"
  jdbc_symlink_name = "oracle-jdbc-driver.jar"
  db_jdbc_url = format('jdbc:oracle:thin:\@//{db_host}')
  audit_jdbc_url = format('jdbc:oracle:thin:\@//{db_host}')
  jdbc_driver = "oracle.jdbc.OracleDriver"
  jdbc_dialect = "org.eclipse.persistence.platform.database.OraclePlatform"
elif db_flavor.lower() == 'postgres':
  jdbc_jar_name = "postgresql.jar"
  jdbc_symlink_name = "postgres-jdbc-driver.jar"
  db_jdbc_url = format('jdbc:postgresql://{db_host}/{ranger_db_name}')
  audit_jdbc_url = format('jdbc:postgresql://{db_host}/{ranger_auditdb_name}')
  jdbc_driver = "org.postgresql.Driver"
  jdbc_dialect = "org.eclipse.persistence.platform.database.PostgreSQLPlatform"
elif db_flavor.lower() == 'sqlserver':
  jdbc_jar_name = "sqljdbc4.jar"
  jdbc_symlink_name = "mssql-jdbc-driver.jar"
  db_jdbc_url = format('jdbc:sqlserver://{db_host};databaseName={ranger_db_name}')
  audit_jdbc_url = format('jdbc:sqlserver://{db_host};databaseName={ranger_auditdb_name}')
  jdbc_driver = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
  jdbc_dialect = "org.eclipse.persistence.platform.database.SQLServerPlatform"

downloaded_custom_connector = format("{tmp_dir}/{jdbc_jar_name}")

driver_curl_source = format("{jdk_location}/{jdbc_symlink_name}")
driver_curl_target = format("{java_share_dir}/{jdbc_jar_name}")

#for db connection
check_db_connection_jar_name = "DBConnectionVerification.jar"
check_db_connection_jar = format("/usr/lib/ambari-agent/{check_db_connection_jar_name}")
ranger_jdbc_connection_url = config["configurations"]["ranger-env"]["ranger_jdbc_connection_url"]
ranger_jdbc_driver = config["configurations"]["ranger-env"]["ranger_jdbc_driver"]

ranger_credential_provider_path = config["configurations"]["ranger-admin-site"]["ranger.credential.provider.path"]
ranger_jpa_jdbc_credential_alias = config["configurations"]["ranger-admin-site"]["ranger.jpa.jdbc.credential.alias"]
ranger_ambari_db_password = unicode(config["configurations"]["admin-properties"]["db_password"])

ranger_jpa_audit_jdbc_credential_alias = config["configurations"]["ranger-admin-site"]["ranger.jpa.audit.jdbc.credential.alias"]
ranger_ambari_audit_db_password = unicode(config["configurations"]["admin-properties"]["audit_db_password"])

ugsync_jceks_path = config["configurations"]["ranger-ugsync-site"]["ranger.usersync.credstore.filename"]
cred_lib_path = os.path.join(ranger_home,"cred","lib","*")
cred_setup_prefix = format('python {ranger_home}/ranger_credential_helper.py -l "{cred_lib_path}"')
ranger_audit_source_type = config["configurations"]["ranger-admin-site"]["ranger.audit.source.type"]

if xml_configurations_supported:
  ranger_usersync_keystore_password = unicode(config["configurations"]["ranger-ugsync-site"]["ranger.usersync.keystore.password"])
  ranger_usersync_ldap_ldapbindpassword = unicode(config["configurations"]["ranger-ugsync-site"]["ranger.usersync.ldap.ldapbindpassword"])
  ranger_usersync_truststore_password = unicode(config["configurations"]["ranger-ugsync-site"]["ranger.usersync.truststore.password"])
