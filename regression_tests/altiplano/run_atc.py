import os
import sys
import subprocess
import sutil

# Input arguments
TEST_CASE_TYPE = ''
TEST_DOMAIN = ''
ONU_MGMT_MODE = ''
TARGET_IP = ''
HOST_PATH = ''
HOST_REPO_PATH = ''
LT_RELEASE = ''
LT_EXTENSION = ''
SETUP_DATA = ''


def read_arguments():
    parser = ArgumentParser()
    parser.add_argument('--TEST_CASE_TYPE', dest='TEST_CASE_TYPE', help='')
    parser.add_argument('--TEST_DOMAIN', dest='TEST_DOMAIN', help='')
    parser.add_argument('--ONU_MGMT_MODE', dest='ONU_MGMT_MODE', help='virtual|embed')
    parser.add_argument('--TARGET_IP', dest='TARGET_IP', help='')
    parser.add_argument('--HOST_PATH', dest='HOST_PATH', help='')
    parser.add_argument('--HOST_REPO_PATH', dest='HOST_REPO_PATH', help='')
    parser.add_argument('--LT_RELEASE', dest='LT_RELEASE', help='')
    parser.add_argument('--LT_EXTENSION', dest='LT_EXTENSION', help='')
    parser.add_argument('--SETUP_DATA', dest='SETUP_DATA', help='')
    args = parser.parse_args()

    global TEST_CASE_TYPE, TEST_DOMAIN, ONU_MGMT_MODE, TARGET_IP, HOST_PATH, HOST_REPO_PATH, LT_RELEASE, LT_EXTENSION, SETUP_DATA
    TEST_CASE_TYPE = args.TEST_CASE_TYPE
    TEST_DOMAIN = args.TEST_DOMAIN
    ONU_MGMT_MODE = args.ONU_MGMT_MODE
    TARGET_IP = args.TARGET_IP
    HOST_PATH = args.HOST_PATH
    HOST_REPO_PATH = args.HOST_REPO_PATH
    LT_RELEASE = args.LT_RELEASE
    LT_EXTENSION = args.LT_EXTENSION
    SETUP_DATA = args.SETUP_DATA


def clone_repositories():
    if not os.path.exists('{}/atc'.format(HOST_REPO_PATH)):
        sutil.run('cd {}; hg clone ssh://Devws114//repo/atc/atc'.format(HOST_REPO_PATH))
    if not os.path.exists('{}/robot'.format(HOST_REPO_PATH)):
        sutil.run('cd {}; hg clone ssh://Devws114//repo/atc/robot'.format(HOST_REPO_PATH))


def pull_repositories():
    sutil.run('cd {}/atc; hg pull -u'.format(HOST_REPO_PATH))
    sutil.run('cd {}/robot; hg pull -u'.format(HOST_REPO_PATH))


def launch_test_parameters():
    ONT_RELEASE = '6.2.03'
    DOMAIN_PARAM = 'ROBOT:suite-FIBER,${DOMAIN},variable-IS_HOST:False,variable-ONU_MGNT:${ONU_MGNT}'
    TEST_TYPE = 'MOSWA_FIBER'

    NT_TYPE = sutil.search_in_configuration(SETUP_DATA, ['NTData', 'Type'])
    LT_TYPE = sutil.search_in_configuration(SETUP_DATA, ['LTData', 'Type'])

    LOG_DIR = 'logs'
    LOG_PATH = '{}/{}'.format(HOST_PATH, LOG_DIR)
    if not os.path.exists(LOG_DIR):
        sutil.run('cd {}; sudo mkdir {}'.format(HOST_PATH, LOG_DIR))

    SETUP_FILE_PAHT = '{}/SETUP_INFO.yml'.format(HOST_PATH)
    with open(SETUP_FILE_PAHT, "w") as f:
        f.write(SETUP_DATA)

    extension_file_name = sutil.download_lt_nt_extension(LT_RELEASE, LT_EXTENSION, HOST_PATH)
    DEVICE_EXTENSION_PATH = '{}/{}'.format(HOST_PATH, extension_file_name)

    parameters = '-k -f'
    parameters += ' -A legacy'
    parameters += ' -a --framework ROBOT'
    parameters += ' -e MERC'
    parameters += ' -r {}'.format(NT_TYPE)
    parameters += '- N {}'.format(LT_TYPE)
    parameters += ' -T {}'.format(TEST_CASE_TYPE)
    parameters += ' -R {}'.format(ONT_RELEASE)
    parameters += ' -d {}'.format(TEST_DOMAIN)
    parameters += ' -G {}'.format(TARGET_IP)
    parameters += ' -V {}:{}'.format(TEST_TYPE, SETUP_FILE_PAHT)
    parameters += ' -K {}'.format(DEVICE_EXTENSION_PATH)
    parameters += ' -D {}'.format(LOG_PATH)
    return parameters


def launch_test_batch():
    script_path = '{}/atc/cm8/auto/tools/pbscript/launchTestBatch'.format(HOST_REPO_PATH)
    sutil.run('chmod +x {}'.format(script_path))
    parameters = launch_test_parameters()
    sutil.run('{} {}'.format(script_path, parameters))
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
    global TEST_CASE_TYPE, TEST_DOMAIN, ONU_MGMT_MODE, TARGET_IP, HOST_PATH, HOST_REPO_PATH, LT_RELEASE, LT_EXTENSION, SETUP_DATA
    TEST_CASE_TYPE = 'smoke'
    TEST_DOMAIN = 'ROBOT:suite-FIBER,${DOMAIN},variable-IS_HOST:False,variable-ONU_MGNT:${ONU_MGNT}'
    ONU_MGMT_MODE = 'virtual'
    TARGET_IP = '138.203.76.194'
    HOST_PATH = '/home/hamin/test_atc'
    HOST_REPO_PATH = '/home/hamin/atc_repo'
    LT_RELEASE = '21.09'
    LT_EXTENSION = '409'
    with open('test/setup_data.yml', 'r') as f:
        SETUP_DATA = f.read()
    main()


main()
