from __future__ import print_function
import subprocess
from subprocess import Popen, PIPE, STDOUT
import logging
import re


# Constants
TMP_DIR = "/tmp/input-source"
PUB_DIR = TMP_DIR + "/public"


def lambda_handler(event, context):
    """Execute Lambda."""
    site_gen(event)
    return 'Site Generated!'


def site_gen(event):
    """Generate the Hugo site."""
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']

    # Create directory structure
    subprocess.run(["mkdir", "-p", TMP_DIR + "/static"])

    input_bucket = bucket
    dst_bucket = input_bucket[6:]

    print('\n\nRunning Hugo generation on bucket: ' + input_bucket)
    print('Destination bucket will be: ' + dst_bucket)
    download_input(input_bucket, TMP_DIR)
    run_hugo()
    upload_website(dst_bucket, PUB_DIR)

def download_input(input_bucket, tmp_dir):
    """Check for object in input bucket, a directory called 'hugo'."""
    print('Downloading Input!\n')

    try:
        command = ["./aws s3 sync s3://" + input_bucket + "/hugo/" + " " + "tmp_dir"]
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        quit('Error downloading from input bucket')


def run_hugo():
    """Build Hugo site."""
    print('Running Hugo!\n')
    subprocess.run(["./hugo", "-v", "--source=" + TMP_DIR, "--destination=" + PUB_DIR])


def upload_website(dst_bucket, pub_dir):
    """Upload Hugo site in 'public' directory of destination bucket."""
    print('Publishing site!\n')
    command = ["./aws s3 sync --acl public-read --delete" + " " + pub_dir + "/" + " " + "s3://" + dst_bucket + "/"]
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        quit('Error uploading site')
