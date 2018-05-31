# -*- coding: utf-8 -*-

# by wangweicheng

from setuptools import setup
from setuptools import find_packages
 
setup(name='ipublish',
      version='1.0.0',
      description='ios 发布工具',
      url='https://github.com/wangweicheng7/publish',
      author='wang weicheng',
      author_email='809405366@qq.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests',
      'poster',],
      entry_points={
        'console_scripts': [
            'ipublish-pgy = ipublish:add_pgy_key',
            'ipublish-fir = ipublish:add_fir_key',
            'ipublish = ipublish:publish',
        ],
      },
      # project_urls=[],
      zip_safe=False)