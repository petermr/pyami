try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

with open('README.md') as readme_file:
    readme = readme_file.read()

long_desc = """
Pyami is a commandline/GUI-based tool for analysing scientific papers
in XML, TXT or PDF. It splitrs them into semantic sections which are searchable, transformable and can
be further processed by standard Python and other tools. Sections include text, images, tables, etc. 
"""

requirements = [
 'beautifulsoup4~=4.10.0',
 'braceexpand==0.1.7',
 'lxml',
 'matplotlib~=3.5.1',
 'nltk',
 'pdfminer3',
 'Pillow~=9.1.1',
 'psutil~=5.9.0',
 'PyPDF2==1.26.0',
 'python-rake',
 'setuptools~=60.3.1',
 'SPARQLWrapper==1.8.5',
 'tkinterhtml',
 'tkinterweb==3.10.7',

 'future~=0.18.2',
 'pdfplumber',
 # 'requests~=2.27.1',
 'requests',
 # 'pip~=22.2.2',
 # 'pip',
 'configparser~=5.0.2',
 #'zlib-state~=1.2.11',
 'wheel~=0.35.1',
 'openssl-python',
 'cryptography~=37.0.2',
 'py~=1.9.0',
 'keyring~=21.4.0',
 'cython~=0.29.21',
 'bs4~=0.0.1',
 'pyamiimage',
 'numpy~=1.22.0',
 'sklearn~=0.0',
 'scikit-learn~=0.23.2',
 #'backports',

]

setup(
    name='py4ami',
    url='https://github.com/petermr/pyami',
    version='0.0.44',
    description='Semantic Reader of the Scientific Literature.',
    long_description_content_type='text/markdown',
    long_description=readme,
    author="Peter Murray-Rust",
    author_email='petermurrayrust@googlemail.com',
    license='Apache2',
    install_requires=requirements,
    include_package_data=True,
    zip_safe=False,
    keywords='text and data mining',
    packages=[
        'py4ami'
    ],
    package_dir={'py4ami': 'py4ami'},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points={
        'console_scripts': [
            'py4ami=py4ami.pyamix:main',
        ],
    },
    python_requires='>=3.7',
)
