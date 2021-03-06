import os
import sys
import subprocess
import argparse
import sutil

# INPUT ARGUMENTS
TEST_CASE_TYPE = ''
TEST_DOMAIN = ''
ONU_MGMT_MODE = ''
TARGET_IP = ''
HOST_PATH = ''
HOST_REPO_PATH = ''
LT_RELEASE = ''
LT_EXTENSION = ''
SETUP_FILE_PATH = ''


def read_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--TEST_CASE_TYPE', dest='TEST_CASE_TYPE', required=True, help='')
    parser.add_argument('--TEST_DOMAIN', dest='TEST_DOMAIN', required=True, help='')
    parser.add_argument('--ONU_MGMT_MODE', dest='ONU_MGMT_MODE', required=True, help='virtual|embed')
    parser.add_argument('--TARGET_IP', dest='TARGET_IP', required=True, help='')
    parser.add_argument('--HOST_PATH', dest='HOST_PATH', required=True, help='')
    parser.add_argument('--HOST_REPO_PATH', dest='HOST_REPO_PATH', required=True, help='')
    parser.add_argument('--LT_RELEASE', dest='LT_RELEASE', required=True, help='')
    parser.add_argument('--LT_EXTENSION', dest='LT_EXTENSION', required=True, help='')
    parser.add_argument('--SETUP_FILE_PATH', dest='SETUP_FILE_PATH', required=True, help='')
    args = parser.parse_args()

    global TEST_CASE_TYPE, TEST_DOMAIN, ONU_MGMT_MODE, TARGET_IP, HOST_PATH, HOST_REPO_PATH, LT_RELEASE, LT_EXTENSION, SETUP_FILE_PATH
    TEST_CASE_TYPE = args.TEST_CASE_TYPE
    TEST_DOMAIN = args.TEST_DOMAIN
    ONU_MGMT_MODE = args.ONU_MGMT_MODE
    TARGET_IP = args.TARGET_IP
    HOST_PATH = args.HOST_PATH
    HOST_REPO_PATH = args.HOST_REPO_PATH
    LT_RELEASE = args.LT_RELEASE
    LT_EXTENSION = args.LT_EXTENSION
    SETUP_FILE_PATH = args.SETUP_FILE_PATH
    print(HOST_REPO_PATH)

def clone_repositories():
    if not os.path.exists('{}/atc'.format(HOST_REPO_PATH)):
        sutil.run('cd {}; hg clone ssh://remoteuser@135.249.31.114//repo/isamtestserver/atc'.format(HOST_REPO_PATH))
    if not os.path.exists('{}/robot'.format(HOST_REPO_PATH)):
        sutil.run('cd {}; hg clone ssh://remoteuser@135.249.31.114//repo/isamtestserver/robot'.format(HOST_REPO_PATH))


def pull_repositories():
    sutil.run('cd {}/atc; hg pull -u'.format(HOST_REPO_PATH))
    sutil.run('cd {}/robot; hg pull -u'.format(HOST_REPO_PATH))


def launch_test_parameters():
    ONT_RELEASE = '6.2.03'
    TEST_DOMAIN_PARAM = 'ROBOT:suite-FIBER,{},variable-IS_HOST:False,variable-ONU_MGNT:{}'.format(TEST_DOMAIN, ONU_MGMT_MODE)
    TEST_TYPE = 'MOSWA_FIBER'

    with open(SETUP_FILE_PATH, 'r') as f:
        setup_file = f.read()
    NT_TYPE = sutil.search_in_configuration(setup_file, ['NTData', 'Type'])
    LT_TYPE = sutil.search_in_configuration(setup_file, ['LTData', 'Type'])
    TRAFFIC_GEN_TYPE = sutil.search_in_configuration(setup_file, ['TrafficGenData', 'Type'])
    TRAFFIC_GEN_IP = sutil.search_in_configuration(setup_file, ['TrafficGenData', 'IP'])

    LOG_DIR = 'logs'
    LOG_PATH = '{}/{}'.format(HOST_PATH, LOG_DIR)
    if not os.path.exists(LOG_PATH):
        sutil.run('cd {}; mkdir {}'.format(HOST_PATH, LOG_DIR))

    extension_file_name = sutil.download_lt_nt_extension(LT_RELEASE, LT_EXTENSION, HOST_PATH)
    DEVICE_EXTENSION_PATH = '{}/{}'.format(HOST_PATH, extension_file_name)

    parameters = ' -k -f'
    parameters += ' -r {}'.format(NT_TYPE)
    parameters += ' -N {}'.format(LT_TYPE)
    parameters += ' -T {}'.format(TEST_CASE_TYPE)
    parameters += ' -R {}'.format(ONT_RELEASE)
    parameters += ' -A legacy'
    parameters += ' -d {}'.format(TEST_DOMAIN_PARAM)
    parameters += ' -G {}'.format(TARGET_IP)
    parameters += ' -V {}:{}'.format(TEST_TYPE, SETUP_FILE_PATH)
    parameters += ' -P {}:{}'.format(TRAFFIC_GEN_TYPE, TRAFFIC_GEN_IP)
    parameters += ' -a --framework ROBOT'
    parameters += ' -K {}'.format(DEVICE_EXTENSION_PATH)
    parameters += ' -e MERC'
    parameters += ' -D {}'.format(LOG_PATH)
    return parameters


def launch_test_batch():
    cmds = []
    cmds.append('export ROBOTREPO={}/robot'.format(HOST_REPO_PATH))
    cmds.append('export REPO={}/atc'.format(HOST_REPO_PATH))
    cmds.append('source {}/atc/env/.profile.common'.format(HOST_REPO_PATH))
    cmds.append('source {}/robot/.robot.profile'.format(HOST_REPO_PATH))
    parameters = launch_test_parameters()
    cmds.append('launchTestBatch {}'.format(parameters))
    cmds = '; '.join(cmds)    
    sutil.run(cmds)
    'launchTestBatch -k -f -r FANT-F -N FGLT-B -T ${TYPE} -R 6.2.03 -A legacy -d ROBOT:suite-FIBER,${DOMAIN},variable-IS_HOST:False,variable-ONU_MGNT:${ONU_MGNT}, -G ${LITESPAN_IP} -V MOSWA_FIBER:${SETUP} -P PCTA:${PCTA} -a --framework ROBOT -K $EXTRA -e MERC -D ${LOGDIR}'
    '/repo/atc/cm8/auto/tools/pbscript/launchTestBatch -v -k -R 21.06 -r NFXS-E -N FANT-F -V MOSWA_FIBER:NFXSD_FANTF_MOSWA_FIBER_WEEKLY_01_ATH_MOSWA_NT_LT3.yaml -K /repo/lightspan_2106.271.extra.tar -a --framework ROBOT -e MERC -G 10.80.89.40 -P PCTA:10.80.89.9 -A legacy' 
    '-d ROBOT:suite-IPFIX_NFR,variable-NFR_DB:True,variable-ONU_MGNT:embed'


def main():
    sutil.info('Initializing setup information')
    read_arguments()
    sutil.info('Pulling repositories')
    clone_repositories()
    pull_repositories()
    sutil.info('Launching test batch')
    launch_test_batch()


def test_main():
    global TEST_CASE_TYPE, TEST_DOMAIN, ONU_MGMT_MODE, TARGET_IP, HOST_PATH, HOST_REPO_PATH, LT_RELEASE, LT_EXTENSION, SETUP_FILE_PATH
    TEST_CASE_TYPE = 'smoke'
    TEST_DOMAIN = 'l2fwd'
    ONU_MGMT_MODE = 'virtual'
    TARGET_IP = '138.203.76.194'
    HOST_PATH = '/home/hamin/test_atc'
    HOST_REPO_PATH = '/home/hamin/atc_repo'
    LT_RELEASE = '21.09'
    LT_EXTENSION = '409'
    main()
    'python run_atc.py --TEST_CASE_TYPE smoke --TEST_DOMAIN l2fwd --ONU_MGMT_MODE virtual --TARGET_IP 138.203.76.194 --HOST_PATH /home/hamin/test_atc --HOST_REPO_PATH /home/hamin/atc_repo --LT_RELEASE 21.09 --LT_EXTENSION 409  --SETUP_FILE_PATH test/setup_data.yml'


main()
