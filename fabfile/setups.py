# Author: Richard Primera
# Company: WOOMBAT Consulting Group
# Email: richard.primera@woombatcg.com

from fabric import task
import os
import logging

logger = logging.getLogger(__name__)


@task
def install_jdk(c):
    """
    Configuration:
    file: The local file name must match the inner folder of the tar.gz
    file_url: If present, takes precedence over 'file'. The file is downloaded
    from this url via wget
    remote: Remote parent directory for the jdk directory
    symbolic_link: Create a symbolic link at this location

    Usage:
    From the command line run:
        fab -f setup_jdk.py -H clusternode1,clusternode2,clusternode3 setup-jdk
    :param c:
    :return:
    """

    config = {
        "file": "/programs/jdk1.8.0_241.tar.gz",
        "file_url": "http://rprimera.com:8000/jdk1.8.0_241.tar.gz",
        "remote": "/usr/java",
        "symbolic_link": "/opt/cloudera/java8"
    }

    tar_name = os.path.basename(config["file"])
    base_name = tar_name.strip(".tar.gz")
    jdk_dir = "{}/{}".format(
        config["remote"],
        base_name
    )

    logger.info("Running at {0.host}".format(c))

    if c.run("test -L {}".format(config["symbolic_link"]), warn=True).failed:
        logger.info("Symbolic link: {} doesn't exist".format(config["symbolic_link"]))

        if c.run(
                "test -d {}".format(
                    jdk_dir
                ),
                warn=True
        ).failed:
            logger.info("JDK directory {} doesn't exist either".format(jdk_dir))

            try:
                logger.info("Downloading file from {}".format(config["file_url"]))
                c.run("wget {}".format(config["file_url"]), hide=True)
            except KeyError:
                logger.info("Uploading file {}".format(config["file"]))
                c.put(
                    config["file"],
                )


            logger.info("Moving file {} to {}".format(config["file"],config["remote"]))
            c.sudo(
                "mv -v {} {}".format(
                    tar_name,
                    config["remote"]
                ),
                pty=True
            )

            logger.info("Unpacking {}".format(os.path.basename(config["file"])))
            c.sudo(
                "tar -C {} -xzvf  {}/{} --owner=0 --group=0".format(
                    config["remote"],
                    config["remote"],
                    tar_name
                ),
                pty=True,
                hide=True
            )

        logger.info("Creating symbolic link")
        proc = c.sudo(
            "ln -sv {target} {link_name}".format(
                target="{}/{}".format(config["remote"], base_name),
                link_name=config["symbolic_link"]
            ),
            pty=True
        )


@task
def upload_unzip(c, file="swarm_runtime.zip", dest="/jupyterhub/user/.runtime"):
    logger.info("Running at {0.host}".format(c))
    basename = os.path.basename(file)
    logger.info("Uploading %s" % file)
    c.put(file)
    logger.info("Extracting to directory %s" % dest)
    c.sudo(
        "unzip -d {} {}".format(
            dest,
            basename
        )
    )