"""AWS Lambda function for running Hugo static website."""
import subprocess
from subprocess import Popen, PIPE, STDOUT
import logging
import re


# Constants
TMP_DIR = "/tmp/input-source"
PUB_DIR = TMP_DIR + "/public"
# LOGGER, provides more info than print()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


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

    LOGGER.info('\n\nRunning Hugo generation on bucket: ' + input_bucket + '\n')
    LOGGER.info('\n\nDestination bucket will be: ' + dst_bucket + '\n')

    download_input(input_bucket, TMP_DIR)
    check_hugo_dir(input_bucket, TMP_DIR)
    check_content_dir(input_bucket, TMP_DIR)
    run_hugo()
    upload_website(dst_bucket, PUB_DIR)


def check_hugo_dir(input_bucket, tmp_dir):
    """Check for a directory called 'hugo'."""
    LOGGER.info("Checking 'hugo' directory!")

    try:
        command = ['./aws s3 ls s3://' + input_bucket + ' | grep hugo']
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # TODO: Better to change this to checking for empty bytestring because a return code of 1 is for any general error
        if int(e.returncode) == 1:
            LOGGER.error("No directory called 'hugo' found!")

        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output.decode('utf-8')))


def check_content_dir(input_bucket, tmp_dir):
    """Check for a directory called 'content' with at least 1 file."""
    LOGGER.info("Checking 'content' directory!")

    try:
        # Should return at least 1 result
        cmd = ['./aws s3 ls s3://' + input_bucket + '/hugo/content/ | grep content']
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # TODO: Better to change this to checking for empty bytestring because a return code of 1 is for any general error
        if int(e.returncode) == 1:
            LOGGER.error("No directory called 'content' and/or no files in content!")

        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output.decode('utf-8')))


def download_input(input_bucket, tmp_dir):
    """Check for object in input bucket, a directory called 'hugo'."""
    LOGGER.info('Downloading Input!\n')

    try:
        command = ["./aws s3 sync s3://" + input_bucket + "/hugo/ " + tmp_dir + "/"]
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output.decode('utf-8')))
        quit('Error downloading from input bucket')


def run_hugo():
    """Build Hugo site."""
    LOGGER.info('Running Hugo!\n')
    cmd = ['./hugo', '-v', '--source=' + TMP_DIR, '--destination=' + PUB_DIR]
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    formatted_output = p.stdout.read().decode('utf-8')
    # Read output of `hugo`
    if re.search("warning", formatted_output, re.IGNORECASE):
        LOGGER.warning('Hugo build warnings:\n %s \n', formatted_output)
    elif re.search("error", formatted_output, re.IGNORECASE):
        LOGGER.error('Hugo build errors:\n %s \n', formatted_output)
    elif re.search("info", formatted_output):
        LOGGER.info('Hugo info on build:\n %s \n', formatted_output)


def upload_website(dst_bucket, pub_dir):
    """Upload Hugo site in 'public' directory of destination bucket."""
    LOGGER.info('Publishing site!\n')
    command = ["./aws s3 sync --acl public-read --delete" + " " + pub_dir + "/" + " " + "s3://" + dst_bucket + "/"]
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        quit('Error uploading site')
