# -*- coding: utf-8 -*-

# by wangweicheng

__all__ = ['Ipa']

import zipfile, plistlib, sys, re

class Ipa:
    '''解析ipa文件中的信息
    '''
    def __init__(self, path=None):
        '''传入ipa路径
        '''
        self.ipa_path = path
        self.info = {}
        ipa_file = zipfile.ZipFile(path)
        plist_path = self.get_plist_path(ipa_file)
        plist_data = ipa_file.read(plist_path)
        ipa_info = None
        if sys.version_info > (3, 0):
            import plistlib
            ipa_info = plistlib.loads(plist_data)
        else:
            from biplist import readPlistFromString
            try:
                ipa_info = readPlistFromString(plist_data)
            except Exception as e :
                print("Not a plist: %s" % e)
                return -1
        self.version = ipa_info['CFBundleShortVersionString']
        self.build = ipa_info['CFBundleVersion']
        if 'CFBundleDisplayName' in ipa_info:
            self.displayName = ipa_info['CFBundleDisplayName']
        else:
            self.displayName = ipa_info['CFBundleName']
        self.bundleName = ipa_info['CFBundleName']
        self.bundleId = ipa_info['CFBundleIdentifier']

    def get_plist_path(self, zip_file):
        '''获取plist文件位置
        '''
        name_list = zip_file.namelist()
        pattern = re.compile(r'Payload/[^/]*.app/Info.plist')
        for path in name_list:
            m = pattern.match(path)
            if m is not None:
                return m.group()

# def print_ipa_info(plist_root):
#     if 'CFBundleDisplayName' in plist_root:
#         print ('Display Name: %s' % plist_root['CFBundleDisplayName'])
#     else:
#         print ('Display Name: %s' % plist_root['CFBundleName'])
#     print ('Bundle Identifier: %s' % plist_root['CFBundleIdentifier'])
#     print ('Version: %s' % plist_root['CFBundleShortVersionString'])

# if __name__ == '__main__':
#     args = sys.argv[1:]
#     if len(args) < 1:
#         print ('Usage: python3 ipaanalyze.py /path/to/ipa')

#     ipa_path = args[0]
#     ipa = Ipa(ipa_path)
#     print_ipa_info(ipa.info)