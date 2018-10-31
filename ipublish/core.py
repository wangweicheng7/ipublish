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

from ipublish.pyipa import Ipa
from ipublish import data
from ipublish.util import HUD, ProgressBar, IterableToFileAdapter

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
    try:
        opts, args = getopt.getopt(sys.argv[1:], "fpbvhf:p:s:", ["fir=", "pgy=","upload=", "scheme=", "help","version", "init"])
        for op, value in opts:
            if op == "--upload":
                upload_type = 1
                if value is not None:
                    upload_script = value
                    data.add_custom_upload(value)
            elif op in ('-f','--fir'):
                upload_type = 2
                if value is not None:
                    fir_token = value
                    data.add_fir_key(value)
            elif op in ('-p', '--pgy'):
                upload_type = 3
                if value is not None:
                    pgy_key = value
                    data.add_pgy_key(value)
            elif op == '-b':
                upload_type = 0
            elif op in ('-s', '--scheme'):
                target_name = value
            elif op in ('-v', '--version'):
                print('ipublish: v1.0.7')
                sys.exit()
            elif op in ('-h', '--help'):
                usage()
                sys.exit()
            elif op in ('--init'):
                curr_dir = os.getcwd()
                set_paths(curr_dir)
                mkdir_build()
                init_export_options()
                sys.exit()
            else:
                usage()
                sys.exit()
    except getopt.GetoptError:
        print('Wrong commond!!!')
        usage()
        sys.exit()

def usage():
    print('Use ipublish [-f [value]|--fir=value]\n\
    [-p [value]|--gpy=value]\n\
    [-s [value]|--scheme=value]\n\
    [--upload=value]\n\
    [--init]\n\
commond:\n\
    -b\t\t\tJust export ipa.\n\
    -f or --fir\t\tfir.im api_token.\n\
    -p or --pgy\t\tpgyer.com api key.\n\
    -s or --scheme\tXcode project scheme.\n\
          --upload\tCustom upload python script.\n\
          --init\tAutomatic generation export options plist.\
        ')

bar = ProgressBar(total = 200)

def error(msg):
    HUD().stop()
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
    os.system('rm -rf %s' % build_path)
    os.system('mkdir -p %s | tee %s/dir.log >/dev/null 2>&1' % (log_dir, log_dir))
    os.system('mkdir -p %s | tee %s/dir.log >/dev/null 2>&1' % (build_path, log_dir))
    os.system('mkdir -p %s | tee %s/dir.log >/dev/null 2>&1' % (targerIPA_parth, log_dir))

def clean_project():
    '''清理工程缓存
    '''
    bar.log('Clean compiled caches...')
    code = os.system('xcodebuild clean | tee %s/clean.log >/dev/null 2>&1' % log_dir)
    if code != 0:
        error('Damn! Check the log %s' % log_dir)

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

def get_plist_info():
    '''获取export options plist信息
    '''
    global profile_name
    global team_id
    global bundle_id
    # 初始化export options plist
    init_export_options()
    info = None
    if sys.version_info < (3, 0):
        from biplist import readPlist
        info = readPlist(exportOptionsPlist)
    else:
        import plistlib
        info = plistlib.readPlist(exportOptionsPlist)
    team_id = info['teamID']
    build_type = info['signingStyle']
    if build_type == 'automatic':
        return False
    elif build_type != 'manual':
        error('[Error] The export option plist key \'signingStyle\' is invalid')
    if info.has_key('provisioningProfiles'):
        profile_info = info['provisioningProfiles']
    else:
        error('[Error] The export option plist key \'signingStyle\' is \'manual\', \n\tbut missed key \'provisioningProfiles\'.\
        \n\tOr you can set \'signingStyle\' to \'automatic\'.')
    profile_name = None
    bundle_id = profile_info.keys()
    keys = profile_info.keys()
    if len(keys) == 0:
        sys.exit()
    bundle_id = keys[0]
    profile_name = profile_info[bundle_id]
    if profile_name == None:
        sys.exit()
    return True

def init_export_options():
    global bundle_id
    bar.log("Read project configuration...")
    team_id = None
    signing_style = 'Automatic'
    strip_swift_symbols = False
    bitcode_enable = False
    code = os.system('xcodebuild -showBuildSettings| tee %s/settings.log >/dev/null 2>&1' % log_dir)
    if code != 0:
        error('Damn! Check the log %s/settings.log' % log_dir)
    f = open('%s/settings.log' % log_dir,'r')
    settings_info = ''
    for line in f.readlines():
        settings_info += line
    s = re.search(r'PRODUCT_BUNDLE_IDENTIFIER = (.+)\n', settings_info)
    result = s.group(1)
    if len(result) > 0:
        bundle_id = result
    else:
        error('[Error]Please input the project\'s bundle id.')

    if os.path.isfile(exportOptionsPlist):
        return
    s = re.search(r'DEVELOPMENT_TEAM = (.+)\n', settings_info)
    
    result = s.group(1)
    if len(result) > 0:
        team_id = result
    else:
        error('[Error]Development team is invalid.')
    s = re.search(r'CODE_SIGN_STYLE = (.+)\n', settings_info)
    result = s.group(1)
    if len(result) > 0:
        signing_style = result
    s = re.search(r'STRIP_SWIFT_SYMBOLS = (.+)\n', settings_info)
    result = s.group(1)
    if len(result) > 0:
        strip_swift_symbols = result
    s = re.search(r'ENABLE_BITCODE = (.+)\n', settings_info)
    result = s.group(1)
    if len(result) > 0:
        bitcode_enable = result
    f.close()

    if sys.version_info < (3, 0):
        from biplist import writePlist
    plist = {
        'compileBitcode': bitcode_enable,
        'method':'ad-hoc',
        'signingStyle': signing_style.lower(),
        'stripSwiftSymbols': strip_swift_symbols,
        'teamID': team_id,
        'thinning': '<none>',
    }
    bar.log("Init export options plist...")
    writePlist(plist, exportOptionsPlist)

def has_workspace():
    path = './'
    for filename in os.listdir(path):
        re_filename = re.findall(r'\w+.xcworkspace', str(filename))
        if len(re_filename) == 0:
            pass
        else:
            
            return re_filename[0]
    return ''

def build_project():
    '''构建并导出 ipa
    '''
    global target_name
    if target_name is None:
        target_name = get_scheme()
    bar.log("Compiling...")
    '''获取export options信息
    '''
    flag = get_plist_info()
    # 选择编译方式
    buildStr = 'xcodebuild -project '+ target_name +'.xcodeproj '
    workspace = has_workspace()
    if len(workspace) > 0:
        bar.log("%s will be compiled..." % workspace)
        buildStr = 'xcodebuild -workspace '+target_name+'.xcworkspace '
    
    if flag:
        buildStr = buildStr +'-scheme '+ target_name +' \
        -scheme '+ target_name +' \
        -configuration Release clean archive build \
        -archivePath '+ app_path +' \
        DEVELOPMENT_TEAM='+ team_id +' \
        CODE_SIGN_IDENTITY="iPhone Distribution" \
        PROVISIONING_PROFILE='+ profile_name +' \
        CODE_SIGN_STYLE="Manual" \
        PRODUCT_BUNDLE_IDENTIFIER='+ bundle_id +' \
        ONLY_ACTIVE_ARCH=NO'
        print(buildStr)
        code = os.system('('+ buildStr +' | \
        tee '+ log_dir +'/build.log >/dev/null 2>&1)|| exit')
    else:
        buildStr = buildStr +'-scheme '+ target_name +' \
        -configuration Release clean archive build \
        -archivePath '+ app_path +' \
        DEVELOPMENT_TEAM='+ team_id +' \
        CODE_SIGN_IDENTITY="iPhone Developer" \
        CODE_SIGN_STYLE="Automatic" \
        PRODUCT_BUNDLE_IDENTIFIER='+ bundle_id +' \
        ONLY_ACTIVE_ARCH=NO'
        print(buildStr)
        code = os.system('('+ buildStr +' | \
        tee '+ log_dir +'/build.log >/dev/null 2>&1)|| exit')
    if code != 0:
        error('Damn! Check the log '+ log_dir +'/build.log')
        
    bar.log("Export ipa...")
    
    code = os.system('xcodebuild -exportArchive \
    -archivePath '+ app_path +' \
    -exportPath '+ targerIPA_parth +' \
    -exportOptionsPlist '+ exportOptionsPlist +' | \
    tee '+ log_dir +'/export.log >/dev/null 2>&1')
    if code != 0:
        error('Damn! Check the log '+ log_dir +'/export.log')

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
    HUD().stop()
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
        elif method == 'enterprise':
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
        error('[Error]Upload failed %s' % msg)

def upload_custom():
    import subprocess
    if not os.path.isfile(upload_script):
        error('[Error]File is not exist.\n%s' % upload_script)
    cmd = 'python %s' % upload_script
    HUD().stop()
    subprocess.call(cmd, shell=True) 
    print('end upload!!!')

def openDownloadUrl(url=None):
    webbrowser.open(url,new=1,autoraise=True)

def main():
    getParmater()
    curr_dir = os.getcwd()
    set_paths(curr_dir)
    HUD().start()
    read_local_data()
    mkdir_build()
    clean_project()
    build_project()
    HUD().stop()
    if target_name is None:
        bar.log('[Error]Please run in the project\'s root directory.')
        return
    if upload_type == 0:
        # 不上传到任何服务器
        bar.log('Congratulations🍻\nPlease check the directory %s ' % targerIPA_parth)
    elif upload_type == 1:
        upload_custom() # 自定义上传
    elif upload_type == 2:
        upload_fir()    # 上传到 fir.im
    elif upload_type == 3:
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
    HUD().stop()

if __name__ == '__main__':
    # main()
    curr_dir = os.getcwd()
    # set_paths(curr_dir)
    # get_plist_info()
    # init_export_options()
    # usage()