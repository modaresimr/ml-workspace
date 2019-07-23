#!/usr/bin/python

"""
Main Workspace Run Script
"""

from subprocess import call
import os
import logging, sys

print("Starting Workspace")

logging.basicConfig(stream=sys.stdout, format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

def set_env_variable(env_variable: str, value: str):
    # TODO is export needed as well?
    call('export ' + env_variable + '="' + value + '"', shell=True)
    os.environ[env_variable] = value

# Manage base path dynamically
ENV_JUPYTERHUB_BASE_URL = os.getenv("JUPYTERHUB_BASE_URL")
ENV_JUPYTERHUB_SERVICE_PREFIX = os.getenv("JUPYTERHUB_SERVICE_PREFIX")

ENV_NAME_WORKSPACE_BASE_URL = "WORKSPACE_BASE_URL"
base_url = os.environ[ENV_NAME_WORKSPACE_BASE_URL]

if not base_url:
    base_url = ""

if ENV_JUPYTERHUB_BASE_URL and ENV_JUPYTERHUB_SERVICE_PREFIX:
    # Installation with Jupyterhub -> use combination as base path
    base_url = ENV_JUPYTERHUB_BASE_URL.rstrip('/') + ENV_JUPYTERHUB_SERVICE_PREFIX

# Add leading slash
if not base_url.startswith("/"):
    base_url = "/" + base_url

# Remove trailing slash
base_url = base_url.rstrip('/').strip()

set_env_variable(ENV_NAME_WORKSPACE_BASE_URL, base_url)

# Dynamically set MAX_NUM_THREADS
ENV_MAX_NUM_THREADS = os.getenv("MAX_NUM_THREADS", 8)
set_env_variable("OMP_NUM_THREADS", ENV_MAX_NUM_THREADS) # OpenMP
set_env_variable("OPENBLAS_NUM_THREADS", ENV_MAX_NUM_THREADS) # OpenBLAS
set_env_variable("MKL_NUM_THREADS", ENV_MAX_NUM_THREADS) # MKL
set_env_variable("VECLIB_MAXIMUM_THREADS", ENV_MAX_NUM_THREADS) # Accelerate
set_env_variable("NUMEXPR_NUM_THREADS", ENV_MAX_NUM_THREADS) # Numexpr
set_env_variable("NUMBA_NUM_THREADS", ENV_MAX_NUM_THREADS) # Numba

ENV_RESOURCES_PATH = os.getenv("RESOURCES_PATH", "/resources")

log.info("Configure ssh service")
call("python " + ENV_RESOURCES_PATH + "/scripts/configure_ssh.py", shell=True)

log.info("Configure nginx service")
call("python " + ENV_RESOURCES_PATH + "/scripts/configure_nginx.py", shell=True)

log.info("Configure tools")
call("python " + ENV_RESOURCES_PATH + "/scripts/configure_tools.py", shell=True)

log.info("Configure cron scripts")
call("python " + ENV_RESOURCES_PATH + "/scripts/configure_cron_scripts.py", shell=True)

log.info("Configure and run custom scripts")
call("python " + ENV_RESOURCES_PATH + "/scripts/run_custom_scripts.py", shell=True)

# TODO vnc server fails to start via supervisor process:
# spawnerr: unknown error making dispatchers for 'vncserver': ENOENT
call("/usr/bin/vncserver $DISPLAY -autokill -depth $VNC_COL_DEPTH -geometry $VNC_RESOLUTION", shell=True)
# Disable screensaver and power management - needs to run after the vnc server is started
call('xset -dpms && xset s noblank && xset s off', shell=True)

# Run supervisor process - main container process
call('supervisord -n -c /etc/supervisor/supervisord.conf', shell=True)