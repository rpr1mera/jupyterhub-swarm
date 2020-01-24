from fabfile import setups, docker, gluster, jupyterhub
from invoke import Collection
import logging

logger = logging.getLogger("fabfile")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

namespace = Collection(
    setups,
    docker,
    gluster,
    jupyterhub
)