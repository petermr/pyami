try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name='py4ami',
    url='https://github.com/petermr/pyami',
    version='0.0.4',
    description='Semantic Reader of the Scientific Literature.',
    author="Peter Murray-Rust",
    author_email='petermurrayrust@googlemail.com',
    license='Apache2',
    install_requires=[],
    zip_safe=False,
    keywords='text and data mining',
    packages=[
        'pyami_m',
    ],
    package_data={"pyami_m": ['section_templates.json']},
    classifiers=[
        'Development Status :: 0.1 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.8',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'py4ami=pyami_m.pyamix:main',
        ],
    },
)
