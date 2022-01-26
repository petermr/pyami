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

setup(
    name='py4ami',
    url='https://github.com/petermr/pyami',
    version='0.0.17',
    description='Semantic Reader of the Scientific Literature.',
    long_description_content_type='text/markdown',
    long_description=readme,
    author="Peter Murray-Rust",
    author_email='petermurrayrust@googlemail.com',
    license='Apache2',
    install_requires=["beautifulsoup4","braceexpand","lxml","matplotlib","nltk","pdfminer3","Pillow","psutil","PyPDF2","python-rake","setuptools","SPARQLWrapper","tkinterhtml","tkinterweb"],
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
)
