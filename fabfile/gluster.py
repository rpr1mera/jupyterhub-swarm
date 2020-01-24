# Author: Richard Primera
# Company: WOOMBAT Consulting Group
# Email: richard.primera@woombatcg.com

from fabric import task
import logging
import os

logger = logging.getLogger(__name__)

@task
def install(c, os="centos"):
    logger.info("Running on {0.host}".format(c))

    config = {
        "centos": "yum install -y glusterfs-server"
    }

    c.sudo(config[os], pty=True, echo=False)
    logger.info("Enabling glusterd service")
    c.sudo("systemctl enable --now glusterd")
    c.sudo("systemctl status glusterd")


@task
def update_fstab(c, line, file="/etc/fstab", desc=None):
    logger.info("Running on {0.host}".format(c))
    if "{hostname}" in line:
        line = line.format(hostname=c.host)

    if desc is not None:
        c.sudo("""sh -c "echo '\n# {desc}' >> {file}" """.format(desc=desc, file=file))
    c.sudo("""sh -c "echo '{line}' >> {file}" """.format(line=line, file=file))


@task
def install_systemd_service(c, file):
    logger.info("Running on {0.host}".format(c))
    basename = os.path.basename(file)

    logger.info("Uploading service file {}".format(file))
    c.put(file, "/tmp/{}".format(basename))
    c.sudo("mv /tmp/{0} /usr/lib/systemd/system/{0}".format(basename))

    logger.info("Reloading systemd's service definitions")
    c.sudo("systemctl daemon-reload")

    logger.info("Enabling service")
    c.sudo("systemctl enable {}".format(basename))

    c.sudo("systemctl status {}".format(basename))


@task
def probe(c, peers, delimiter=","):
    """
    Gluster probe a list of peers
    :param c:
        Context provided by fabric
    :param peers:
        Delimiter separated list of hostnames
    :param delimiter:
        String delimiter between hostnames, comma by default
    :return:
    """
    logger.info("Running on {0.host}".format(c))

    hostnames = [x for x in peers.split(delimiter)]
    for hostname in hostnames:
        c.sudo("gluster peer probe {}".format(hostname))



@task(default=True)
def volume_info(c):
    logger.info("Running on {0.host}".format(c))
    c.sudo("gluster volume info", echo=False)

