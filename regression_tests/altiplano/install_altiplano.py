import requests
from ncclient import manager
from ncclient.xml_ import to_ele
import sutil

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
EXTRA_APPS = []
TASKS = []


# GLOGBAL VARIABLES
GUI_APPS_PATH = 'data/gui_apps.json'
KUBERNETES_PATH = 'data/kubernetes.json'
LICENSES_PATH = 'data/licenses.json'
DEVICE_EXTENSIONS_PATH = 'data/device_extensions.json'

CONNECT_AV_AC_RPC = 'rpcs/connect_av_ac.xml'
DEVICE_PLUG_RPC = 'rpcs/device_plug.xml'
KIBANA_VIRTUALIZER_RPC = 'rpcs/kubana_virtualizer.xml'
LICENSE_RPC = 'rpcs/license.xml'
TIMEOUT_RPC = 'rpcs/timeout.xml'
VPROXY_GUI_RPC = 'rpcs/vproxy_gui.xml'




def read_arguments():
    parser = ArgumentParser()
    parser.add_argument('--HOST_PATH', dest='HOST_PATH', help='')
    parser.add_argument('--PUBLIC_IP', dest='PUBLIC_IP', help='virtual|embed')
    parser.add_argument('--PRIVATE_IP', dest='PRIVATE_IP', help='')
    parser.add_argument('--AV_RELEASE', dest='AV_RELEASE', help='')
    parser.add_argument('--AV_BUILD', dest='AV_BUILD', help='')
    parser.add_argument('--LT_RELEASE', dest='LT_RELEASE', help='')
    parser.add_argument('--LT_EXTENSION', dest='LT_EXTENSION', default='', help='')
    parser.add_argument('--VONU_PLUG', dest='VONU_PLUG', help='')
    parser.add_argument('--EXTRA_APPS', dest='EXTRA_APPS', help='')
    parser.add_argument('--TASKS', dest='TASKS', help='')
    args = parser.parse_args()

    global HOST_PATH, LOCATION, PUBLIC_IP, PRIVATE_IP, AV_RELEASE, AV_BUILD, LT_RELEASE, LT_EXTENSION, VONU_PLUG, EXTRA_APPS, TASKS
    HOST_PATH = args.HOST_PATH
    PUBLIC_IP = args.PUBLIC_IP
    PRIVATE_IP = args.PRIVATE_IP
    AV_RELEASE = args.AV_RELEASE
    AV_BUILD = args.AV_BUILD
    LT_RELEASE = args.LT_RELEASE
    LT_EXTENSION = args.LT_EXTENSION
    VONU_PLUG = args.VONU_PLUG
    EXTRA_APPS = args.EXTRA_APPS.split(',')
    TASKS = args.TASKS.split(',')


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
    run('sudo docker rmi $(docker images -a -q)', immediate_exit=False, print_output=False)


def uninstall_release():    
    release = run('sudo helm list | grep -v NAME | tail -1 | awk \'{print $1}\'')
    while release != '':
        run('sudo helm uninstall --no-hooks {}'.format(release))
        wait(10)
        release = run('sudo helm list | grep -v NAME | tail -1 | awk \'{print $1}\'')


def calculate_av_version():
    if AV_BUILD == 'latest':
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
            run('cd {}; sudo helm pull {}/{} --version {}'.format(HOST_PATH, repository, chart_name, av_version))
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
        wait(30)


def get_pod_info(pod):
    run('sudo kubectl get pods', immediate_exit=False)
    attempts = 20
    info = run('sudo kubectl get pods --all-namespaces | grep {}'.format(pod), immediate_exit=False)
    while info == '' and attempts > 0:
        attempts -= 1
        wait(30)
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
        wait(30)
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
    info('RPC Request ???\n{}'.format(rpc))
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
    info('RPC Response !!!\n{}'.format(response))
    return True


def attempt_sending_rpc(rpc, attempts=5, port='6514', mode='config'):
    counter = attempts
    while counter > 0 and not send_rpc(rpc, port, mode):
        wait(30)
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
    apps = read_eval_file(GUI_APPS_PATH)
    for app in apps['apps']:
        app_name = app['name']
        if app_name == 'basic' or app_name in EXTRA_APPS:
            app_rpc = read_eval_file('rpcs/{}'.format(app['rpc']), {'AV_IP': PUBLIC_IP, 'VPORXYMGMT_PORT': vproxymgmt_port})
            keep_sending_rpc(app_rpc)


def calculate_onu_tag():
    if VONU_PLUG != '' and VONU_PLUG is not None:
        return VONU_PLUG
    yml_path = '{}/altiplano-solution/values.yaml'.format(HOST_PATH)
    with open(yml_path, 'r') as f:
        content = f.read()
    index = content.find('\naltiplano-vonuproxy')
    index = content.find('tag', index)
    end_index = content.find('\n', index)
    return content[index:end_index].split('_')[1]    


def download_tar_lt_nt_extension(lt_release, lt_extension, path_to_save):
    extension_name = download_lt_nt_extension(lt_release, lt_extension, path_to_save)
    run('cd {}; sudo rm -rf {}/internal'.format(path_to_save, HOST_PATH))
    run('cd {}; sudo tar xvf {}'.format(path_to_save, extension_name), print_output=False)


def calculete_lt_nt_extension_names_to_install():
    extension_patterns = read_eval_file(DEVICE_EXTENSIONS_PATH)
    extension_patterns = extension_patterns['device_extensions']
    extension_patterns = '|'.join(v['name'] for v in extension_patterns)
    extensions = run('cd {}/internal/YANG; find . -name "*.zip" | grep -i -E "{}"'.format(HOST_PATH, extension_patterns))
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
    extensions = calculete_lt_nt_extension_names_to_install()
    for extension in extensions:
        configure_device_exentsion(extension, 'internal/YANG/{}'.format(extension), av_pod)
        wait(20)


def restart_pods():
    run('sudo kubectl delete pods `sudo kubectl get pods --all-namespaces |egrep \'vonum|vonup|-av-\'| awk \'{print $2}\'`')
    info('Waiting for AV pod to get ready')
    wait_for_pod('altiplano-av')
    info('Waiting for AC pod to get ready')
    wait_for_pod('altiplano-ac')

def main():
    info('Initializing AV information')
    read_arguments()
    info('Checking Minikube status')
    minikube = minikube_is_running()
    if 'upgrade-minikube' in TASKS or not minikube:
        info('Upgrading Minikube')
        remove_minikube()
        prunes_dockers()
        start_minikube()
        wait(30)
        start_helm()
    if 'upgrade-av' in TASKS:
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
        wait(30)
        info('Setting SSH keys')
        set_ssh_env_for_av_ac()
        wait(200)
        info('Installing License')
        install_license()
        info('Connecting AV and AC')
        connect_av_ac()
        info('Installing other GUI applications')
        install_gui_applications()
    if 'upgrade-device-extensions' in TASKS:
        info('Installing device extensions')
        install_device_extensions()
    if 'restart-pods' in TASKS:
        restart_pods()
    info('Finish')


def test_main():
    os.environ['HOST_PATH'] = '/home/hamin/install_altiplano'
    os.environ['LOCATION'] = 'antwerp'
    os.environ['PUBLIC_IP'] = '10.157.49.55'
    os.environ['PRIVATE_IP'] = '192.168.0.31'
    os.environ['AV_RELEASE'] = '21.9.0-SNAPSHOT'
    os.environ['AV_BUILD'] = 'latest'
    os.environ['VONU_PLUG'] = ''
    os.environ['LT_RELEASE'] = '21.06'
    os.environ['LT_EXTENSION'] = '304'
    os.environ['EXTRA_APPS'] = 'light-verion,vproxy-GUI'
    os.environ['TASKS'] = 'upgrade-minikube,upgrade-av,upgrade-device-extensions'
    main()

if __name__ == "__main__":
    main()
