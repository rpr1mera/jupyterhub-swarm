import subprocess as subp
import logging

# create logger
logger = logging.getLogger("jupyter_imageprep")


## Kerberos Initializer function
def kinit(username, password, ccache=None):
    kinit = "/usr/bin/kinit"
    kinit_args = [kinit, "{}".format(username)]

    if ccache is not None:
        [kinit_args.append(x) for x in ["-c", ccache]]

    proc = subp.Popen(kinit_args, stdout=subp.PIPE, stderr=subp.STDOUT, stdin=subp.PIPE, shell=False)

    try:
        proc.stdin.write(bytes('{}\n'.format(password), "UTF-8"))
        out, _ = proc.communicate()
    except Exception as e:
        raise e

    if proc.returncode == 0:
        logger.info("Kerberos Initialization successful for user {}".format(username))
    else:
        logger.error("Kerberos Initialization failed for user {}".format(username))
        logger.error(out)

    return proc.returncode
