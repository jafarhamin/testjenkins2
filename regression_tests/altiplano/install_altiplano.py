import os
import sys
import subprocess
import json
import requests
import shutil
import time
import re
from ncclient import manager
from ncclient.xml_ import to_ele


# ENVRIRONMENT VARIABLES
HOST_PATH = ''
LOCATION = ''
PUBLIC_IP = ''
PRIVATE_IP = ''
AV_RELEASE = ''
AV_BUILD = ''
LT_RELEASE = ''
LT_EXTENSION = ''
VONU_PLUG = ''
EXTRA_APPS = ''


# GLOGBAL VARIABLES
LATEST = 'latest'
LIGHT_VERSION = 'light_version'
VONUPROXY_GUI = 'vonuproxy-GUI'

GUI_APPS_PATH = 'data/gui_apps.json'
KUBERNETES_PATH = 'data/kubernetes.json'
LICENSES_PATH = 'data/licenses.json'
NODES_PATH = 'data/nodes.json'
RELEASES_PATH = 'data/releases.json'

CONNECT_AV_AC_RPC = 'rpcs/connect_av_ac.xml'
DEVICE_PLUG_RPC = 'rpcs/device_plug.xml'
KIBANA_VIRTUALIZER_RPC = 'rpcs/kubana_virtualizer.xml'
LICENSE_RPC = 'rpcs/license.xml'
TIMEOUT_RPC = 'rpcs/timeout.xml'
VPROXY_GUI_RPC = 'rpcs/vproxy_gui.xml'


def info(message):
    print('\n############################## {} ##########\n'.format(message))


def error(message, immediate_exit=True, return_code=1, print_output=True):
    if not immediate_exit:
        if print_output:
            print('Error: {}'.format(message))
        return
    print('########## FATAL ERROR ##########\n{}'.format(message))
    sys.exit(return_code)

def run(cmd, immediate_exit=True, print_output=True):
    print('======================= {}'.format(cmd))
    host_path = HOST_PATH
    proc = subprocess.Popen('cd {}; {}'.format(host_path, cmd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True)
    proc.stdin.write('y\n yes\n')
    std_out, std_err = proc.communicate()
    if proc.returncode != 0:
        error(std_err, immediate_exit, return_code=proc.returncode, print_output=print_output)
    if print_output:
        print(std_out)
    return std_out.strip()


def wait(sec):
    print('waiting for {} seconds ...'.format(sec))
    time.sleep(sec)


def download_file(file_name, file_url):
    if os.path.exists('{}/{}'.format(HOST_PATH, file_name)):
        return
    run('sudo wget {} --no-proxy'.format(file_url))


def init_av_info():
    global HOST_PATH, LOCATION, PUBLIC_IP, PRIVATE_IP, AV_RELEASE, AV_BUILD, LT_RELEASE, LT_EXTENSION, VONU_PLUG, EXTRA_APPS
    HOST_PATH = os.environ.get('HOST_PATH')
    LOCATION = os.environ.get('LOCATION')
    PUBLIC_IP = os.environ.get('PUBLIC_IP')
    PRIVATE_IP = os.environ.get('PRIVATE_IP')
    AV_RELEASE = os.environ.get('AV_RELEASE')
    AV_BUILD = os.environ.get('AV_BUILD')
    LT_RELEASE = os.environ.get('LT_RELEASE')
    LT_EXTENSION = os.environ.get('LT_EXTENSION')
    VONU_PLUG = os.environ.get('VONU_PLUG')
    EXTRA_APPS = os.environ.get('EXTRA_APPS').split(',')


def eval_double_brackets(str, globals):
    for f in re.findall("[\[\{][\{].*?[\}][\}]", str):
        evaluated = eval(f[2:-2], globals)
        if evaluated is None:
            error('{} not found'.format(f[2:-2]))
        str = str.replace(f, evaluated)
    return str


def read_eval_file(path, globals={}):
    with open(path, 'r') as f:
        content = eval_double_brackets(f.read(), globals)
    if path.endswith('.json'):
        content = json.loads(content)
    return content


def read_kubernetes_settings_file():
    return read_eval_file(KUBERNETES_PATH, {'AV_PUBLIC_IP': PUBLIC_IP})


def minikube_is_running():
    status = run('sudo minikube status', immediate_exit=False)
    if status.find('Running') == -1:
        return False
    return True


def remove_minikube():
	run('sudo kubeadm reset all')
	run('sudo minikube stop')
	run('sudo minikube delete')


def prunes_dockers():
	run('docker system prune')
	run('docker rm -f local-registry', False)
	run('sudo rm -rf /mnt/registry')


def start_minikube():
    run('unset http_proxy')
    run('unset https_proxy')
    run('unset no_proxy')
    run('unset HTTPS_PROXY')
    run('unset HTTP_PROXY')
    run('unset NO_PROXY')
    run('sudo swapoff -a')
    run('sudo rm -rf  ~/.kube ~/.minikube')
    run('sudo -E minikube start --vm-driver=none')
    run('sudo chown -R $USER:$USER ~/.kube ~/.minikube')
    run('sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config')
    run('sudo chown $(id -u):$(id -g) $HOME/.kube/config')


def start_helm():
    run('curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3')
    run('chmod 700 get_helm.sh')
    run('./get_helm.sh')
    repository = read_kubernetes_settings_file()
    name = repository['chart_repository']['name']
    url = repository['chart_repository']['url']
    run('helm repo add {} {}'.format(name, url))


def create_kubernetes_services():
    run('sudo helm repo update')
    run('sudo helm list')
    run('sudo kubectl create serviceaccount --namespace kube-system tiller', immediate_exit=False)
    run('sudo kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller', False)
    run('sudo kubectl patch deploy --namespace kube-system tiller-deploy -p \'{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}\' ', immediate_exit=False)
    run('sudo kubectl create clusterrolebinding add-on-cluster-admin --clusterrole=cluster-admin --serviceaccount=kube-system:default', immediate_exit=False)


def remove_images():
    total, used, free = shutil.disk_usage("/")
    if (free // (2**30)) >= 50:
        return
    run('sudo docker rmi $(docker images -a -q)', immediate_exit=False, print_output=False)


def uninstall_release():    
    release = run('sudo helm list | grep -v NAME | tail -1 | awk \'{print $1}\'')
    while release != '':
        run('sudo helm uninstall --no-hooks {}'.format(release))
        wait(10)
        release = run('sudo helm list | grep -v NAME | tail -1 | awk \'{print $1}\'')


def calculate_latest_av_built():
    urls = read_eval_file(RELEASES_PATH)
    url = urls['av_release']
    release = AV_RELEASE.split('.')
    release = '{}.{}'.format(release[0], release[1])
    url1 = '{}-{}-release/lastStableBuild'.format(url, release)
    url2 = '{}/lastStableBuild'.format(url)
    if requests.get(url1).status_code == 200:
        release_url = url1
    elif requests.get(url2).status_code == 200:
        release_url = url2
    else:
        error('Release URL not found')
    build_info_file = 'build_info.html'
    run('wget -q -O {} {} --no-proxy'.format(build_info_file, release_url))
    with open('{}/{}'.format(HOST_PATH,build_info_file), 'r') as file:
        data = file.read()
    start_index = data.find("Build #")
    return data[start_index + 7: start_index + 11]


def calculate_av_version():
    if AV_BUILD == LATEST:
        return AV_RELEASE + '-' + calculate_latest_av_built()
    return AV_RELEASE + '-' + AV_BUILD


def pull_charts():
    av_version = calculate_av_version()
    resources = read_kubernetes_settings_file()
    repository = resources['chart_repository']['name']
    for chart in resources['helm_charts']:
        chart_name = chart['name']
        file_name = chart_name + '-' + av_version + '.tgz'
        if not os.path.exists('{}/{}'.format(HOST_PATH, file_name)):
            run('sudo helm pull {}/{} --version {}'.format(repository, chart_name, av_version))
        run('sudo rm -rf {}/'.format(chart_name))
        run('sudo tar xzvf {}-{}.tgz'.format(chart_name, av_version), print_output=False)


def clean_kubernets_resources():
    resources = read_kubernetes_settings_file()
    for k_res in resources['kubernets_resources']:
        res_name = k_res['name']
        res_type = k_res['type']
        run('sudo kubectl delete {} {}'.format(res_type, res_name), immediate_exit=False)
    for release in resources['helm_charts']:
        release_name = release['name']
        run('sudo helm uninstall --no-hooks {}'.format(release_name), immediate_exit=False)


def calculate_helm_parameters(json_parameters):
    parameters = ''
    for parameter in json_parameters:
        if parameter["condition"] == 'true' or parameter["condition"] in EXTRA_APPS:
            parameters += ' --set ' + parameter['parameter']
    return parameters


def install_release():
    run('sudo ip link set docker0 promisc on')
    resources = read_kubernetes_settings_file()
    resources['helm_charts'].sort(key=lambda k: k['order'])
    for chart in resources['helm_charts']:
        chart_name = chart['name']
        chart_release = chart['release']
        chart_path = '{}/{}'.format(HOST_PATH,chart_name)
        parameters = calculate_helm_parameters(chart['parameters'])
        run('sudo helm upgrade -i {} -f {}/values.yaml {} --timeout 1000s {}'.format(chart_release, chart_path, chart_path, parameters))


def get_pod_info(pod):
    run('sudo kubectl get pods', immediate_exit=False)
    attempts = 20
    info = run('sudo kubectl get pods --all-namespaces | grep {}'.format(pod), immediate_exit=False)
    while info == '' and attempts > 0:
        attempts -= 1
        wait(20)
        info = run('sudo kubectl get pods --all-namespaces | grep {}'.format(pod), immediate_exit=False)
    info = run('sudo kubectl get pods --all-namespaces | grep {}'.format(pod))
    info = (" ".join(info.split())).split(' ')
    pod_name = info[1].split('-')
    pod_name = '{}-{}-{}'.format(pod_name[0], pod_name[1], pod_name[2])
    return {'name': pod_name, 'name_space': info[0], 'full_name': info[1], 'ready': info[2], 'status': info[3], 'restarts': info[4]}


def wait_for_pod(pod_name):
    pod_info = get_pod_info(pod_name)
    attempts = 20
    while attempts > 0 and (pod_info['ready'] != '1/1' or pod_info['status'] != 'Running'):
        attempts -= 1
        wait(20)
        pod_info = get_pod_info(pod_name)
    if attempts == 0:
        error('Pod {} failed to get ready'.format(pod_name))

def set_ssh_env_for_av_ac():
    resources = read_kubernetes_settings_file()
    pod_info = get_pod_info('altiplano-av')
    for ssh_key in resources['ssh_keys']:
        run('sudo kubectl set env deployment/{} {}={}'.format(pod_info['name'], ssh_key['name'], ssh_key['value']))
    wait(30)
    pod_info = get_pod_info('altiplano-ac')
    for ssh_key in resources['ssh_keys']:
        run('sudo kubectl set env deployment/{} {}={}'.format(pod_info['name'], ssh_key['name'], ssh_key['value']))


def send_rpc(rpc, port='6514', mode='config'):
    print('======================= RPC Request:\n{}'.format(rpc))
    try:
        with manager.connect(host=PUBLIC_IP,
                            port=port,
                            username='adminuser',
                            password='password',
                            timeout=60,
                            hostkey_verify=False,
                            device_params={'name': 'nexus'}) as m:
            if mode == 'config':
                response = m.edit_config(target='running', config=rpc)
            else:
                response = m.dispatch(to_ele(rpc))
    except Exception as err:
            error(err, immediate_exit=False)
            return False
    print('======================= RPC Response:\n{}'.format(response))
    return True


def attempt_sending_rpc(rpc, attempts=5, port='6514', mode='config'):
    counter = attempts
    while counter > 0 and not send_rpc(rpc, port, mode):
        wait(10)
        counter -= 1
    return (counter != 0)


def keep_sending_rpc(rpc, attempts=5, port='6514', mode='config'):
    if attempt_sending_rpc(rpc, attempts, port, mode):
        return True
    info('Failed to send RPC, Lets increase the request time out and try again')
    timeout_rpc = read_eval_file(TIMEOUT_RPC)
    if not attempt_sending_rpc(timeout_rpc, attempts):
        info('Failed to increase the request time out. Failed to send RPC')
        return False
    if not attempt_sending_rpc(rpc, attempts, port, mode):
        info('Failed to send RPC')
        return False
    return True


def install_license():
    release_year = AV_RELEASE.split('.')
    release_year = release_year[0]
    licence_key = ''
    licence_keys = read_eval_file(LICENSES_PATH)
    for licence in licence_keys['licenses']:
        if licence['release'] == release_year:
            licence_key = licence['key']
            break
    if licence_key == '':
        error('Licence {} not found'.format(release_year), immediate_exit=False)
        return
    license_rpc = read_eval_file(LICENSE_RPC, {'LICENCE_KEY': licence_key})
    keep_sending_rpc(license_rpc)
    keep_sending_rpc(license_rpc, port='6515')


def connect_av_ac():
    connect_av_ac_rpc = read_eval_file(CONNECT_AV_AC_RPC, {'AV_IP': PRIVATE_IP})
    return keep_sending_rpc(connect_av_ac_rpc, port='6515')


def install_gui_applications():
    vproxymgmt_port = run('sudo kubectl get svc|grep vonuproxy-mgmt | awk \'{print $(NF-1)}\' | cut -d \':\' -f 2 | cut -d \'/\' -f 1')
    print(vproxymgmt_port)
    print('EXTRA_APPS', EXTRA_APPS)
    apps = read_eval_file(GUI_APPS_PATH)
    for app in apps['apps']:
        app_name = app['name']
        if app_name == 'basic' or app_name in EXTRA_APPS:
            app_rpc = read_eval_file('rpcs/{}'.format(app['rpc']), {'AV_IP': PUBLIC_IP, 'VPORXYMGMT_PORT': vproxymgmt_port})
            keep_sending_rpc(app_rpc)


def calculate_onu_tag():
    if VONU_PLUG != LATEST:
        return VONU_PLUG
    yml_path = '{}/altiplano-solution/values.yaml'.format(HOST_PATH)
    with open(yml_path, 'r') as f:
        content = f.read()
    index = content.find('\naltiplano-vonuproxy')
    index = content.find('tag', index)
    end_index = content.find('\n', index)
    return content[index:end_index].split('_')[1]    


def calculete_onu_extension_name_url():
    release = AV_RELEASE.split('.')
    year = release[0]
    month = release[1]
    onu_tag = calculate_onu_tag()
    vonu_plugin = '{}_{}'.format(AV_RELEASE, onu_tag)
    extension_name = 'device-extension-vonu-{}.{}-1-{}.zip'.format(year, month, vonu_plugin)
    extensions = read_eval_file(RELEASES_PATH)
    url = extensions['onu_extensions']
    extension_url = '{}/{}/{}/device-extensions/device-extension-vonu-{}.{}-1/{}/{}'.format(url, year, month, year, month, vonu_plugin, extension_name)
    return extension_name, extension_url


def download_lt_nt_extension():
    release = LT_RELEASE.split('.')
    release = '{}{}.{}'.format(release[0], release[1], LT_EXTENSION)
    extensions = read_eval_file(RELEASES_PATH)
    url = extensions['lt_nt_extensions']
    file_name = 'lightspan_{}.extra.tar'.format(release)
    file_url = '{}_{}/{}'.format(url, release, file_name)
    download_file(file_name, file_url)
    run('sudo rm -rf {}/internal'.format(HOST_PATH))
    run('sudo tar xvf {}'.format(file_name), print_output=False)
    return True


def calculete_lt_nt_extension_names():
    extensions = run('cd {}/internal/YANG; find . -name "*.zip"'.format(HOST_PATH))
    extensions = extensions.split('\n')
    extensions = [i[2:] for i in extensions]
    return extensions


def configure_device_exentsion(extension_name, extension_path, av_pod):
    run('sudo kubectl cp {} {}:/root'.format(extension_path, av_pod))
    extension_rpc = read_eval_file(DEVICE_PLUG_RPC, {'PLUG_NAME': extension_name})
    keep_sending_rpc(extension_rpc, mode = 'dispatch')


def install_device_extensions():
    av_pod = get_pod_info('altiplano-av')['full_name']
    onu_extension_name, onu_extension_url= calculete_onu_extension_name_url()
    download_file(onu_extension_name, onu_extension_url)
    configure_device_exentsion(onu_extension_name, onu_extension_name, av_pod)
    download_lt_nt_extension()
    extensions = calculete_lt_nt_extension_names()
    for extension in extensions:
        configure_device_exentsion(extension, 'internal/YANG/{}'.format(extension), av_pod)


def main():
    info('Initializing AV information')
    init_av_info()
    wait_for_pod('kibana')
    info('Checking Minikube status')
    if not minikube_is_running():
        info('Installing Minikube')
        remove_minikube()
        prunes_dockers()
        start_minikube()
        info('Starting Helm')
        start_helm()
    info('Creating Kubernetes servicies')
    create_kubernetes_services()
    info('Removing images')
    remove_images()
    info('Uninstalling Releases')
    uninstall_release()
    info('Cleaning Kubernetes resources')
    clean_kubernets_resources()
    info('Pulling charts')
    pull_charts()
    info('Installing release')
    install_release()
    info('Waiting for AV pod to get ready')
    wait_for_pod('altiplano-av')
    info('Waiting for AC pod to get ready')
    wait_for_pod('altiplano-ac')
    info('Setting SSH keys')
    set_ssh_env_for_av_ac()
    info('Installing License')
    install_license()
    info('Connecting AV and AC')
    connect_av_ac()
    info('Installing other GUI applications')
    install_gui_applications()
    info('Installing device extensions')
    install_device_extensions()
    info('Finish')


def test_main():
    os.environ['HOST_PATH'] = '/home/hamin/install_altiplano'
    os.environ['LOCATION'] = 'antwerp'
    os.environ['PUBLIC_IP'] = '10.157.49.55'
    os.environ['PRIVATE_IP'] = '192.168.0.31'
    os.environ['AV_RELEASE'] = '21.9.0-SNAPSHOT'
    os.environ['AV_BUILD'] = 'latest'
    os.environ['VONU_PLUG'] = 'latest'
    os.environ['LT_RELEASE'] = '21.06'
    os.environ['LT_EXTENSION'] = '304'
    os.environ['EXTRA_APPS'] = 'light_verion,vproxy_GUI'
    main()


if __name__ == "__main__":
    test_main()
