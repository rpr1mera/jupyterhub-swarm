# WOOMBAT Consulting Group CDH 5.15.x Cluster JupyterHub Configuration
import os
import swarmspawnergdb
import shutil
import sys
import logging
sys.path.append("/srv/jupyterhub")
import imgprep

#### Logging
c.JupyterHub.log_level = logging.DEBUG

#### IP/Networking Settings
## The Proxy runs on a different container, reachable through the docker network at hostname 'proxy'
c.ConfigurableHTTPProxy.should_start = False
c.ConfigurableHTTPProxy.api_url = 'http://proxy:8001'

## Listen on every available IP address
c.JupyterHub.hub_ip = '0.0.0.0'

## JupyterHub Hostname address. This is the name of the jupyterhub service in docker-compose.yml.
## This hostname is reachable as is through the docker network
c.JupyterHub.hub_connect_ip = 'hub'


#### General purpose variables
# Create user directories and mount them on the container
root_shared_notebook_dir = '/jupyterhub/user'
user_uid = 1000
user_gid = 10240

#### LDAP Configuration
from ldapauthenticator import LDAPAuthenticator

class KerberosLDAPAuthenticator(LDAPAuthenticator):
    def authenticate(self, handler, data):
        ret = super().authenticate(handler, data)
        self.log.warn('ret: ' + str(ret))

        if ret != None:
            pass
            runtime_volume = os.path.join(root_shared_notebook_dir, ".runtime")
            self.log.info("runtime_volume = {}".format(runtime_volume))
            # Location of the user's kerberos credential cache
            kerberos_ccache = os.path.join(
                runtime_volume, "kerberos",
                data["username"],
                "krb5cc_%s" % user_uid
            )

            kerberos_ccache_parent_path = os.path.dirname(kerberos_ccache)
            if not os.path.exists(kerberos_ccache_parent_path):
                self.log.info(
                    "Creating ccache directory = {}".format(
                        kerberos_ccache_parent_path
                    )
                )
                os.makedirs(kerberos_ccache_parent_path)

            self.log.info("kerberos_ccache = {}".format(kerberos_ccache))
            # kerberos_ccache_name = os.path.basename(kerberos_ccache)
            self.log.debug("Executing Kerberos Initialization")
            imgprep.kinit(data["username"], data["password"], kerberos_ccache)

            # Important: Allow group access to the credential cache
            os.chmod(kerberos_ccache, 0o660)

        return ret


# c.JupyterHub.authenticator_class = 'ldapauthenticator.LDAPAuthenticator'

#c.JupyterHub.authenticator_class = LDAPAuthenticator
c.JupyterHub.authenticator_class = KerberosLDAPAuthenticator

c.LDAPAuthenticator.server_address = "10.128.0.6"
# c.LDAPAuthenticator.server_port = 389

# Active Directory
# c.LDAPAuthenticator.user_attribute = 'sAMAccountName'
# OpenLDAP
c.LDAPAuthenticator.user_attribute = 'uid'

c.LDAPAuthenticator.bind_dn_template = [
    'cn={username},cn=WOOMBAT.COM,cn=kerberos,dc=woombat,dc=com'
]
# c.LDAPAuthenticator.bind_dn_template = []

# Lookup Settings
# c.LDAPAuthenticator.lookup_dn = True
# c.LDAPAuthenticator.user_search_base = 'dc=woombat,dc=com'
# c.LDAPAuthenticator.lookup_dn_user_dn_attribute = "uid"
c.LDAPAuthenticator.lookup_dn_search_user = "cn=ldapadm,dc=woombat,dc=com"
c.LDAPAuthenticator.lookup_dn_search_password = "Cloudera2018*"

# c.LDAPAuthenticator.allowed_groups = [
#     "cn=researcher,ou=groups,dc=wikimedia,dc=org",
#     "cn=operations,ou=groups,dc=wikimedia,dc=org",
# ]

## If set to True, and server_port is not specified, it connects to
## port 636. If set to false, it connects to port 389.
c.LDAPAuthenticator.use_ssl = True


#### Spawner Settings
# c.JupyterHub.spawner_class = 'dockerspawner.SwarmSpawner'
c.JupyterHub.spawner_class = swarmspawnergdb.SwarmSpawnerGDB

# this is the network name for jupyterhub in docker-compose.yml
# with a leading 'swarm_' that docker-compose adds
# c.SwarmSpawner.network_name = 'swarm_jupyterhub-net'
c.Spawner.network_name = 'woombat_jupyterhub-net'

# c.SwarmSpawner.image = os.environ['DOCKER_NOTEBOOK_IMAGE']
c.Spawner.image = os.environ['DOCKER_NOTEBOOK_IMAGE']

c.Spawner.image_whitelist = {
    'Jupyter Sparkmagic': 'localhost:5000/notebook:test',
    'Jupyter Pyspark': 'jupyter/pyspark-notebook:latest',
    'Jupyter Scipy': 'jupyter/scipy-notebook:latest',
    'Jupyter Tensorflow': 'jupyter/tensorflow-notebook:latest',
    'a': 'localhost:5000/jhub:robinson'
}

# c.Spawner.extra_placement_spec = { 'constraints' : ['node.role==worker'] }
# c.SwarmSpawnerGDB.extra_placement_spec = { 'constraints' : ['node.role==worker'] }

## Timeouts
c.Spawner.start_timeout = 300
c.Spawner.http_timeout = 300
c.Spawner.poll_interval = 30

c.JupyterHub.tornado_settings = {
    'slow_spawn_timeout': 1000
}

#### Preparation hook, called before launching the container with the user's notebook server.
## Configures mount points and prepares directory structures inside the shared filesystem.
def pre_spawn_hook(spawner):
    username = spawner.user.name

    # Base directory where the shared gluster volume is mounted
    base_volume = os.path.join(root_shared_notebook_dir, username)

    # Base directory for the runtime structures
    runtime_volume = os.path.join(root_shared_notebook_dir, ".runtime")

    # Location of the user's kerberos credential cache
    kerberos_ccache = os.path.join(
        runtime_volume,
        "kerberos",
        username,
        "krb5cc_{}".format(user_uid)
    )
    kerberos_ccache_name = os.path.basename(kerberos_ccache)

    # Location of the user's persistent work volume in the host
    work_volume = os.path.join(base_volume, "work")

    # Location of the sparkmagic configuration directory inside the container
    sparkmagic_volume = os.path.join(base_volume, ".sparkmagic")

    def chgrp(filepath, gid):
        uid = os.stat(filepath).st_uid
        os.chown(filepath, uid, gid)

    if not os.path.exists(base_volume):
        volumes = [base_volume, work_volume, sparkmagic_volume]
        for volume in volumes:
            os.mkdir(volume)
            os.chmod(volume, 0o775)
            chgrp(volume, user_gid)

        shutil.copy2("/jupyterhub/user/.runtime/sparkmagic/config.json", sparkmagic_volume)
        chgrp(os.path.join(sparkmagic_volume, "config.json"), user_gid)

    mounts_user = [
        {'type': 'bind',
         'source': work_volume,
         'target': '/home/jovyan/work'},
        {'type': 'bind',
         'source': sparkmagic_volume,
         'target': '/home/jovyan/.sparkmagic'},
        {'type': 'bind',
         'source': '/jupyterhub/user/.runtime/kerberos/krb5.conf',
         'target': '/etc/krb5.conf'},
        {'type': 'bind',
         'source': kerberos_ccache,
         'target': '/tmp/{}'.format(kerberos_ccache_name)}
    ]
    spawner.extra_container_spec = {
        'mounts': mounts_user
    }


# c.Spawner.pre_spawn_hook = create_dir_hook
c.Spawner.pre_spawn_hook = pre_spawn_hook

notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR') or '/home/jovyan/work'
c.DockerSpawner.notebook_dir = notebook_dir

# start jupyterlab
c.Spawner.cmd = ["jupyter", "labhub"]
