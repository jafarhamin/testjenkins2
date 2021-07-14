import requests
from ncclient import manager
from ncclient.xml_ import to_ele
import argparse
import sutil

# INPUT ARGUMENTS
HOST_PATH = ''
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--HOST_PATH', dest='HOST_PATH', required=True, help='Working directory path')
    parser.add_argument('--PUBLIC_IP', dest='PUBLIC_IP', required=True, help='Public IP address of AV')
    parser.add_argument('--PRIVATE_IP', dest='PRIVATE_IP', required=False, help='Private IP address of AV (needed if AV GUI is not accessible through public IP)')
    parser.add_argument('--AV_RELEASE', dest='AV_RELEASE', required=True, help='AV release, i.e. 21.9.0-SNAPSHOT')
    parser.add_argument('--AV_BUILD', dest='AV_BUILD', required=True, help='AV build, i.e. latest')
    parser.add_argument('--LT_RELEASE', dest='LT_RELEASE', required=True, help='LT release, i.e. 21.06')
    parser.add_argument('--LT_EXTENSION', dest='LT_EXTENSION', required=True, help='LT extension, i.e. 304')
    parser.add_argument('--VONU_PLUG', dest='VONU_PLUG', required=False, help='VONU plug (optional)')
    parser.add_argument('--EXTRA_APPS', dest='EXTRA_APPS', required=True, help='Extra applications to install, i.e. light-verion,vproxy-GUI')
    parser.add_argument('--TASKS', dest='TASKS', required=True, help='Tasks to be done, i.e. upgrade-minikube,upgrade-av,upgrade-device-extensions') 
    args = parser.parse_args()

    global HOST_PATH, PUBLIC_IP, PRIVATE_IP, AV_RELEASE, AV_BUILD, LT_RELEASE, LT_EXTENSION, VONU_PLUG, EXTRA_APPS, TASKS
    HOST_PATH = args.HOST_PATH
    PUBLIC_IP = args.PUBLIC_IP
    PRIVATE_IP = args.PRIVATE_IP
    if PRIVATE_IP is None or PRIVATE_IP =='':
        PRIVATE_IP = PUBLIC_IP
    AV_RELEASE = args.AV_RELEASE
    AV_BUILD = args.AV_BUILD
    LT_RELEASE = args.LT_RELEASE
    LT_EXTENSION = args.LT_EXTENSION
    VONU_PLUG = args.VONU_PLUG
    EXTRA_APPS = args.EXTRA_APPS.split(',')
    TASKS = args.TASKS.split(',')
    print(PRIVATE_IP)

def read_kubernetes_settings_file():
    return sutil.read_eval_file((KUBERNETES_PATH, {'AV_PUBLIC_IP': PUBLIC_IP}))


def minikube_is_running():
    status = sutil.run('sudo minikube status', immediate_exit=False)
    if status.find('Running') == -1:
        return False
    return True


def remove_minikube():
	sutil.run('sudo kubeadm reset all')
	sutil.run('sudo minikube stop')
	sutil.run('sudo minikube delete')


def prunes_dockers():
	sutil.run('docker system prune')
	sutil.run('docker rm -f local-registry', False)
	sutil.run('sudo rm -rf /mnt/registry')


def start_minikube():
    sutil.run('unset http_proxy')
    sutil.run('unset https_proxy')
    sutil.run('unset no_proxy')
    sutil.run('unset HTTPS_PROXY')
    sutil.run('unset HTTP_PROXY')
    sutil.run('unset NO_PROXY')
    sutil.run('sudo swapoff -a')
    sutil.run('sudo rm -rf  ~/.kube ~/.minikube')
    sutil.run('sudo -E minikube start --vm-driver=none')
    sutil.run('sudo chown -R $USER:$USER ~/.kube ~/.minikube')
    sutil.run('sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config')
    sutil.run('sudo chown $(id -u):$(id -g) $HOME/.kube/config')


def start_helm():
    sutil.run('curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3')
    sutil.run('chmod 700 get_helm.sh')
    sutil.run('./get_helm.sh')
    repository = read_kubernetes_settings_file()
    name = repository['chart_repository']['name']
    url = repository['chart_repository']['url']
    sutil.run('helm repo add {} {}'.format(name, url))


def create_kubernetes_services():
    sutil.run('sudo helm repo update')
    sutil.run('sudo helm list')
    sutil.run('sudo kubectl create serviceaccount --namespace kube-system tiller', immediate_exit=False)
    sutil.run('sudo kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller', False)
    sutil.run('sudo kubectl patch deploy --namespace kube-system tiller-deploy -p \'{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}\' ', immediate_exit=False)
    sutil.run('sudo kubectl create clusterrolebinding add-on-cluster-admin --clusterrole=cluster-admin --serviceaccount=kube-system:default', immediate_exit=False)


def remove_images():
    sutil.run('sudo docker rmi $(docker images -a -q)', immediate_exit=False, print_output=False)


def uninstall_release():    
    release = sutil.run('sudo helm list | grep -v NAME | tail -1 | awk \'{print $1}\'')
    while release != '':
        sutil.run('sudo helm uninstall --no-hooks {}'.format(release))
        sutil.wait(10)
        release = sutil.run('sudo helm list | grep -v NAME | tail -1 | awk \'{print $1}\'')


def calculate_av_version():
    if AV_BUILD == 'latest':
        return AV_RELEASE + '-' + sutil.calculate_latest_av_built()
    return AV_RELEASE + '-' + AV_BUILD


def pull_charts():
    av_version = calculate_av_version()
    resources = read_kubernetes_settings_file()
    repository = resources['chart_repository']['name']
    for chart in resources['helm_charts']:
        chart_name = chart['name']
        file_name = chart_name + '-' + av_version + '.tgz'
        if not os.path.exists('{}/{}'.format(HOST_PATH, file_name)):
            sutil.run('cd {}; sudo helm pull {}/{} --version {}'.format(HOST_PATH, repository, chart_name, av_version))
        sutil.run('sudo rm -rf {}/'.format(chart_name))
        sutil.run('sudo tar xzvf {}-{}.tgz'.format(chart_name, av_version), print_output=False)


def clean_kubernets_resources():
    resources = read_kubernetes_settings_file()
    for k_res in resources['kubernets_resources']:
        res_name = k_res['name']
        res_type = k_res['type']
        sutil.run('sudo kubectl delete {} {}'.format(res_type, res_name), immediate_exit=False)
    for release in resources['helm_charts']:
        release_name = release['name']
        sutil.run('sudo helm uninstall --no-hooks {}'.format(release_name), immediate_exit=False)


def calculate_helm_parameters(json_parameters):
    parameters = ''
    for parameter in json_parameters:
        if parameter["condition"] == 'true' or parameter["condition"] in EXTRA_APPS:
            parameters += ' --set ' + parameter['parameter']
    return parameters


def install_release():
    sutil.run('sudo ip link set docker0 promisc on')
    resources = read_kubernetes_settings_file()
    resources['helm_charts'].sort(key=lambda k: k['order'])
    for chart in resources['helm_charts']:
        chart_name = chart['name']
        chart_release = chart['release']
        chart_path = '{}/{}'.format(HOST_PATH,chart_name)
        parameters = calculate_helm_parameters(chart['parameters'])
        sutil.run('sudo helm upgrade -i {} -f {}/values.yaml {} --timeout 1000s {}'.format(chart_release, chart_path, chart_path, parameters))
        sutil.wait(30)


def get_pod_info(pod):
    sutil.run('sudo kubectl get pods', immediate_exit=False)
    attempts = 20
    info = sutil.run('sudo kubectl get pods --all-namespaces | grep {}'.format(pod), immediate_exit=False)
    while info == '' and attempts > 0:
        attempts -= 1
        sutil.wait(30)
        info = sutil.run('sudo kubectl get pods --all-namespaces | grep {}'.format(pod), immediate_exit=False)
    info = sutil.run('sudo kubectl get pods --all-namespaces | grep {}'.format(pod))
    info = (" ".join(info.split())).split(' ')
    pod_name = info[1].split('-')
    pod_name = '{}-{}-{}'.format(pod_name[0], pod_name[1], pod_name[2])
    return {'name': pod_name, 'name_space': info[0], 'full_name': info[1], 'ready': info[2], 'status': info[3], 'restarts': info[4]}


def wait_for_pod(pod_name):
    pod_info = get_pod_info(pod_name)
    attempts = 20
    while attempts > 0 and (pod_info['ready'] != '1/1' or pod_info['status'] != 'Running'):
        attempts -= 1
        sutil.wait(30)
        pod_info = get_pod_info(pod_name)
    if attempts == 0:
        sutil.error('Pod {} failed to get ready'.format(pod_name))


def set_ssh_env_for_av_ac():
    resources = read_kubernetes_settings_file()
    pod_info = get_pod_info('altiplano-av')
    for ssh_key in resources['ssh_keys']:
        sutil.run('sudo kubectl set env deployment/{} {}={}'.format(pod_info['name'], ssh_key['name'], ssh_key['value']))
    sutil.wait(30)
    pod_info = get_pod_info('altiplano-ac')
    for ssh_key in resources['ssh_keys']:
        sutil.run('sudo kubectl set env deployment/{} {}={}'.format(pod_info['name'], ssh_key['name'], ssh_key['value']))


def send_rpc(rpc, port='6514', mode='config'):
    sutil.info('RPC Request ???\n{}'.format(rpc))
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
            sutil.error(err, immediate_exit=False)
            return False
    sutil.info('RPC Response !!!\n{}'.format(response))
    return True


def attempt_sending_rpc(rpc, attempts=5, port='6514', mode='config'):
    counter = attempts
    while counter > 0 and not send_rpc(rpc, port, mode):
        sutil.wait(30)
        counter -= 1
    return (counter != 0)


def keep_sending_rpc(rpc, attempts=5, port='6514', mode='config'):
    if attempt_sending_rpc(rpc, attempts, port, mode):
        return True
    sutil.info('Failed to send RPC, Lets increase the request time out and try again')
    timeout_rpc = sutil.read_eval_file((TIMEOUT_RPC)
    if not attempt_sending_rpc(timeout_rpc, attempts):
        sutil.info('Failed to increase the request time out. Failed to send RPC')
        return False
    if not attempt_sending_rpc(rpc, attempts, port, mode):
        sutil.info('Failed to send RPC')
        return False
    return True


def install_license():
    release_year = AV_RELEASE.split('.')
    release_year = release_year[0]
    licence_key = ''
    licence_keys = sutil.read_eval_file((LICENSES_PATH)
    for licence in licence_keys['licenses']:
        if licence['release'] == release_year:
            licence_key = licence['key']
            break
    if licence_key == '':
        sutil.error('Licence {} not found'.format(release_year), immediate_exit=False)
        return
    license_rpc = sutil.read_eval_file((LICENSE_RPC, {'LICENCE_KEY': licence_key})
    keep_sending_rpc(license_rpc)
    keep_sending_rpc(license_rpc, port='6515')


def connect_av_ac():
    connect_av_ac_rpc = sutil.read_eval_file((CONNECT_AV_AC_RPC, {'AV_IP': PRIVATE_IP})
    return keep_sending_rpc(connect_av_ac_rpc, port='6515')


def install_gui_applications():
    vproxymgmt_port = sutil.run('sudo kubectl get svc|grep vonuproxy-mgmt | awk \'{print $(NF-1)}\' | cut -d \':\' -f 2 | cut -d \'/\' -f 1')
    apps = sutil.read_eval_file((GUI_APPS_PATH)
    for app in apps['apps']:
        app_name = app['name']
        if app_name == 'basic' or app_name in EXTRA_APPS:
            app_rpc = sutil.read_eval_file(('rpcs/{}'.format(app['rpc']), {'AV_IP': PUBLIC_IP, 'VPORXYMGMT_PORT': vproxymgmt_port})
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
    extension_name = sutil.download_lt_nt_extension(lt_release, lt_extension, path_to_save)
    sutil.run('cd {}; sudo rm -rf {}/internal'.format(path_to_save, HOST_PATH))
    sutil.run('cd {}; sudo tar xvf {}'.format(path_to_save, extension_name), print_output=False)


def calculete_lt_nt_extension_names_to_install():
    extension_patterns = sutil.read_eval_file((DEVICE_EXTENSIONS_PATH)
    extension_patterns = extension_patterns['device_extensions']
    extension_patterns = '|'.join(v['name'] for v in extension_patterns)
    extensions = sutil.run('cd {}/internal/YANG; find . -name "*.zip" | grep -i -E "{}"'.format(HOST_PATH, extension_patterns))
    extensions = extensions.split('\n')
    extensions = [i[2:] for i in extensions]
    return extensions


def configure_device_exentsion(extension_name, extension_path, av_pod):
    sutil.run('sudo kubectl cp {} {}:/root'.format(extension_path, av_pod))
    extension_rpc = sutil.read_eval_file((DEVICE_PLUG_RPC, {'PLUG_NAME': extension_name})
    keep_sending_rpc(extension_rpc, mode = 'dispatch')


def install_device_extensions():
    av_pod = get_pod_info('altiplano-av')['full_name']
    onu_extension_name, onu_extension_url= sutil.calculete_onu_extension_name_url()
    sutil.download_file(onu_extension_name, onu_extension_url)
    configure_device_exentsion(onu_extension_name, onu_extension_name, av_pod)
    download_tar_lt_nt_extension()
    extensions = calculete_lt_nt_extension_names_to_install()
    for extension in extensions:
        configure_device_exentsion(extension, 'internal/YANG/{}'.format(extension), av_pod)
        sutil.wait(20)


def restart_pods():
    sutil.run('sudo kubectl delete pods `sudo kubectl get pods --all-namespaces |egrep \'vonum|vonup|-av-\'| awk \'{print $2}\'`')
    sutil.info('Waiting for AV pod to get ready')
    wait_for_pod('altiplano-av')
    sutil.info('Waiting for AC pod to get ready')
    wait_for_pod('altiplano-ac')


def main():
    sutil.info('Initializing AV information')
    read_arguments()
    sutil.info('Checking Minikube status')
    minikube = minikube_is_running()
    sutil.info(minikube)
    if 'upgrade-minikube' in TASKS or not minikube:
        sutil.info('Upgrading Minikube')
        remove_minikube()
        prunes_dockers()
        start_minikube()
        sutil.wait(30)
        start_helm()
    if 'upgrade-av' in TASKS:
        sutil.info('Creating Kubernetes servicies')
        create_kubernetes_services()
        sutil.info('Removing images')
        remove_images()
        sutil.info('Uninstalling Releases')
        uninstall_release()
        sutil.info('Cleaning Kubernetes resources')
        clean_kubernets_resources()
        sutil.info('Pulling charts')
        pull_charts()
        sutil.info('Installing release')
        install_release()
        sutil.info('Waiting for AV pod to get ready')
        wait_for_pod('altiplano-av')
        sutil.info('Waiting for AC pod to get ready')
        wait_for_pod('altiplano-ac')
        sutil.wait(30)
        sutil.info('Setting SSH keys')
        set_ssh_env_for_av_ac()
        sutil.wait(200)
        sutil.info('Installing License')
        install_license()
        sutil.info('Connecting AV and AC')
        connect_av_ac()
        sutil.info('Installing other GUI applications')
        install_gui_applications()
    if 'upgrade-device-extensions' in TASKS:
        sutil.info('Installing device extensions')
        install_device_extensions()
    if 'restart-pods' in TASKS:
        restart_pods()
    sutil.info('Finish')


def test_main():
    example = '''
        python install_altiplano.py --HOST_PATH /home/hamin/install_altiplano --PUBLIC_IP 10.157.49.55 --PRIVATE_IP 192.168.0.31 
        --AV_RELEASE 21.9.0-SNAPSHOT --AV_BUILD latest --LT_RELEASE 21.06 --LT_EXTENSION 304  --EXTRA_APPS light-verion,vproxy-GUI
        --TASKS upgrade-minikube,upgrade-av,upgrade-device-extensions
        '''
    print(example.replace('\n', ' '))


if __name__ == "__main__":
    main()
