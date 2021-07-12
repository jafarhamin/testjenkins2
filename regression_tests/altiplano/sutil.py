import os
import sys
import subprocess
import time
import json
import re

RELEASES_PATH = 'data/releases.json'


def info(message):
    print('\n######################################## {} ##########\n'.format(message))


def error(message, immediate_exit=True, return_code=1, print_output=True):
    if not immediate_exit:
        if print_output:
            print('Error: {}'.format(message))
        return
    print('########## FATAL ERROR ##########\n{}'.format(message))
    sys.exit(return_code)

def run(cmd, immediate_exit=True, print_output=True):
    print('======================= {}'.format(cmd))
    proc = subprocess.Popen(cmd,
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
    print('Waiting for {} seconds ...'.format(sec))
    time.sleep(sec)


def download_file(file_name, file_url, path_to_save):
    if os.path.exists('{}/{}'.format(path_to_save, file_name)):
        return
    run('cd {}; wget {} --no-proxy'.format(path_to_save, file_url))



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


def search_in_configuration(configuration, key_path):
    index = 0
    for item in key_path:
        index = configuration.find(item, index)
        if index == -1:
            return None
    end_index = configuration.find('\n', index)
    result = configuration[index: end_index].split(':')
    return result[1].strip()


def calculete_lt_nt_extension_name_url(lt_release, lt_extension):
    release = lt_release.split('.')
    release = '{}{}.{}'.format(release[0], release[1], lt_extension)
    extensions = read_eval_file(RELEASES_PATH)
    url = extensions['lt_nt_extensions']
    extension_name = 'lightspan_{}.extra.tar'.format(release)
    extension_url = '{}_{}/{}'.format(url, release, extension_name)
    return extension_name, extension_url


def download_lt_nt_extension(lt_release, lt_extension, path_to_save):
    extension_name, extension_url = calculete_lt_nt_extension_name_url(lt_release, lt_extension)
    download_file(extension_name, extension_url, path_to_save)
    return extension_name


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
    return data[start_index + 7: start_index + 11].strip().zfill(4)
