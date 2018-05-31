# -*- coding: utf-8 -*-

# by wangweicheng

import os
import optparse
import sys
import getopt
import time
import hashlib
import requests
import webbrowser
import json
import re
import zipfile
from poster.encode import multipart_encode

from iipublish.pyipa import Ipa
from ipublish import data
from ipublish.progress import ProgressBar
from ipublish.progress import IterableToFileAdapter

upload_script = None
fir_token = None
pgy_key = None
target_name = None
upload_type = -1

def getParmater():
    global upload_script
    global fir_token
    global pgy_key
    global target_name
    global upload_type
    opts, args = getopt.getopt(sys.argv[1:], "hf:p:s:fpb", ["fir=", "pgy=","upload=", "scheme=", "help"])
    for op, value in opts:
        if op == "--upload":
            upload_type = 0
            if value is not None:
                upload_script = value
                data.add_custom_upload(value)
        elif op == '-f' or op == '--fir':
            upload_type = 1
            if value is not None:
                fir_token = value
                data.add_fir_key(value)
        elif op == '-p' or op == '--pgy':
            upload_type = 2
            if value is not None:
                pgy_key = value
                data.add_pgy_key(value)
        elif op == '-b':
            upload_type = -1
        elif op == '-s' or op == '--scheme':
            target_name = value
        elif op == '-h' or op == '--help':
            usage()
            sys.exit()
        else:
            usage()
            sys.exit()

def usage():
    print('Use ipublish [-f [value]|--fir=value]\n\
    [-p [value]|--gpy=value]\n\
    [-s [value]|--scheme=value]\n\
    [--upload=value]\n\
commond:\n\
    -b\t\t\tJust export ipa.\n\
    -f or --fir\t\tfir.im api_token.\n\
    -p or --pgy\t\tpgyer.com api key.\n\
    -s or --scheme\tXcode project scheme.\n\
          --upload\tCustom upload python script.\
        ')

bar = ProgressBar(total = 200)

def error(msg):
    bar.stop()
    bar.log(msg)
    sys.exit(0)

def set_paths(project_path):
    '''设置环境变量
    '''
    # 项目根目录
    global project_root
    # 编译成功后.app所在目录
    global app_path
    # 指定项目下编译目录
    global build_path
    # 打包后ipa存储目录
    global targerIPA_parth
    # info.plist 路径
    global exportOptionsPlist
    # 日志路径
    global log_dir
    bar.log('Configuring...')
    project_root =  project_path
    app_path = project_root + "/build/build.xcarchive"
    build_path = project_root + "/build"
    targerIPA_parth = project_root + "/build/ipa"
    exportOptionsPlist = project_root + "/ExportOptions.plist"
    log_dir = build_path + '/logs'

def read_local_data():
    '''读取本地数据
    '''
    global fir_token
    global pgy_key
    global upload_script
    if fir_token is None:
        fir_token = data.fir_key()
    if pgy_key is None:
        pgy_key = data.pgy_key()
    if upload_script is None:
        upload_script = data.custom_upload()


def mkdir_build():
    '''清理打包缓存文件，创建构建文件夹
    '''
    bar.log('Generating compiled directory...')
    os.system('mkdir -p %s | tee %s/dir.log >/dev/null 2>&1' % (log_dir, log_dir))
    os.system('mkdir -p %s | tee %s/dir.log >/dev/null 2>&1' % (build_path, log_dir))
    os.system('mkdir -p %s | tee %s/dir.log >/dev/null 2>&1' % (targerIPA_parth, log_dir))

def clean_project():
    bar.log('Clean compiled caches...')
    code = os.system('xcodebuild clean | tee %s/clean.log >/dev/null 2>&1' % log_dir)
    if code != 0:
        error('Damn! Check the log %s' % log_dir)
    os.system('rm -rf %s' % build_path)

def get_scheme():
    bar.log("Read project infomations...")
    code = os.system('xcodebuild -list| tee %s/info.log >/dev/null 2>&1' % log_dir)
    if code != 0:
        error('Damn! Check the log %s/info.log' % log_dir)
    f = open('%s/info.log' % log_dir,'r')
    proj = ''
    proj_info = ''
    for line in f.readlines():
        proj_info += line
    f.close()
    arr = re.findall(r"project \"(.+?)\":", proj_info)
    if len(arr) > 0:
        proj = arr[0]
    else:
        error('[Error]Please run in the project\'s root directory.')
    return proj

def build_project():
    '''构建并导出 ipa
    '''
    global target_name
    if target_name is None:
        target_name = get_scheme()
    bar.log("Compiling...")
    code = os.system('(xcodebuild -project %s.xcodeproj \
    -scheme %s \
    -configuration Release clean archive \
    -archivePath %s \
    ONLY_ACTIVE_ARCH=NO | tee %s/build.log >/dev/null 2>&1)|| exit' % (target_name,target_name,app_path, log_dir))
    if code != 0:
        error('Damn! Check the log %s/build.log' % log_dir)
        
    bar.log("Export ipa...")
    code = os.system('xcodebuild -exportArchive -archivePath %s \
    -exportPath %s -exportOptionsPlist %s | tee %s/export.log >/dev/null 2>&1' % (app_path,targerIPA_parth, exportOptionsPlist, log_dir))
    if code != 0:
        error('Damn! Check the log %s/export.log' % log_dir)

def multipart_encode_for_requests(params, boundary=None, cb=None):
    datagen, headers = multipart_encode(params, boundary, cb)
    return IterableToFileAdapter(datagen), headers

def progress(param, current, total=0):
    if not param:
        return
    bar.total = total
    bar.move(current)

def upload_pgy():
    # TODO: -p 时，没有key
    bar.log('Uploading pgyer.com ...')
    bar.stop()
    path = targerIPA_parth + '/' + target_name + '.ipa'
    if not os.path.isfile(path):
        error('[Error]File is not exist.%s' % path)
    datagen, headers = multipart_encode_for_requests({
        'file': open(path, 'rb'),
        '_api_key': pgy_key,
    }, cb=progress)

    url = 'https://www.pgyer.com/apiv2/app/upload'

    r = requests.post(
        url,
        data=datagen,
        headers=headers
    )
    res = json.loads(r.text)
    code = res['code']
    if code == 0:
        _path = res['data']['buildShortcutUrl']
        bar.log('Upload successful🍻')
        open_url = r'https://www.pgyer.com/'+_path
        openDownloadUrl(open_url)
    else:
        msg = res['message']
        bar.log('Upload failed %s' % msg)

def upload_fir():
    bar.log('Uploading fir.im ...')
    path = targerIPA_parth + '/' + target_name + '.ipa'
    if not os.path.isfile(path):
        error('[Error]File is not exist.%s' % path)
    if fir_token is None:
        error('[Error] fir.im api token is None')
    ipa = Ipa(path)

    url = 'http://api.fir.im/apps'
    param = {
        'type':'ios', 
        'bundle_id':ipa.bundleId, 
        'api_token': fir_token
    }
    r = requests.post(url,json=param)
    ret = json.loads(r.text)
    cert = ret['cert']
    binary = cert['binary']
    key = binary['key']
    token = binary['token']
    upload_url = binary['upload_url']

    method = 'Unknow'
    if sys.version_info < (3, 0):
        from biplist import readPlist
        ipa_info = readPlist(exportOptionsPlist)
        if 'method' in ipa_info:
            method = ipa_info['method']
        if method == 'ad-hoc':
            method = 'Adhoc'
        elif method == 'inhouse':
            method = 'Inhouse'
    bar.log('Will upload ' + method + ' ipa')
    bar.log('Uploading ' + ipa.displayName + ' ' + method + ' to fir.im ...')
    datagen, headers = multipart_encode_for_requests({
        'key': key,
        'token': token,
        'file': open(path, 'rb'),
        'x:name': ipa.displayName,
        'x:version': ipa.version,
        'x:build': ipa.build,
        'x:release_type': method,
    }, cb=progress)

    ret = requests.post(
        upload_url,
        data=datagen,
        headers=headers)
    res = json.loads(ret.text)
    # code = res['code']
    if 'is_completed' in res:
        release_id = res['release_id']
        print('Upload successful🍻')
        open_url = r'https://fir.im/apps/' + release_id
        openDownloadUrl(open_url)
    else:
        msg = res['message']
        print('[Error]Upload failed %s' % msg)

def upload_custom():
    import subprocess
    if not os.path.isfile(upload_script):
        error('[Error]File is not exist.\n%s' % upload_script)
    cmd = 'python %s' % upload_script
    bar.stop()
    subprocess.call(cmd, shell=True) 
    print('end upload!!!')

def openDownloadUrl(url=None):
    webbrowser.open(url,new=1,autoraise=True)

def main():
    getParmater()
    curr_dir = os.getcwd()
    set_paths(curr_dir)
    bar.start()
    read_local_data()
    clean_project()
    mkdir_build()
    build_project()
    bar.stop()
    if target_name is None:
        bar.log('[Error]Please run in the project\'s root directory.')
        return
    if upload_type == -1:
        # 不上传到任何服务器
        bar.log('Congratulations🍻\nPlease check in %s ' % targerIPA_parth)
    elif upload_type == 0:
        upload_custom() # 自定义上传
    elif upload_type == 1:
        upload_fir()    # 上传到 fir.im
    elif upload_type == 2:
        upload_pgy()    # 上传到蒲公英
    elif upload_script is not None:
        upload_custom() # 自定义上传
    elif fir_token is not None:
        upload_fir()    # 上传到 fir.im
    elif pgy_key is not None:   
        upload_pgy()    # 上传到蒲公英
    else:
        # 不上传到任何服务器
        bar.log('Congratulations🍻\nPlease check in %s ' % targerIPA_parth)
    bar.stop()

if __name__ == '__main__':
    main()
    # usage()