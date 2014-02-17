APP_NAME = 'widgetry'
DESCRIPTION = "An experimental set of widgets for django admin"

from setuptools import setup, find_packages
import os

version = __import__(APP_NAME).__version__

media_files = []
for dir in ['%s/media' % APP_NAME,'%s/templates' % APP_NAME]:
    for dirpath, dirnames, filenames in os.walk(dir):
        media_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

def read(fname):
    # read the contents of a text file
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

install_requires = [
    
]

setup(
    name = "django-%s"  % APP_NAME,
    version = version,
    url = 'http://github.com/stefanfoulis/django-%s' % APP_NAME,
    license = 'BSD',
    platforms=['OS Independent'],
    description = DESCRIPTION,
    long_description = read('README.rst'),
    author = 'Stefan Foulis',
    author_email = 'stefan@foulis.ch',
    packages=find_packages(exclude=['ez_setup']),
    install_requires = install_requires,
    package_data={
        '': ['*.txt', '*.rst',],
    },
    include_package_data = True,
    package_dir = {
        APP_NAME:APP_NAME,
    },
    data_files = media_files,
    zip_safe=False,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
