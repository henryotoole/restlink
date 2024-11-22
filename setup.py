from setuptools import setup, find_packages
import os
import glob

setup(
	# This is NOT the module name e.g. 'import hacutils'. This is the library name as
	# it would appear in pip etc.
	name='restlink',
	version='0.1.0',
	license="GNUv3",
	description="Automation layer expose resources via REST API on a backend framework.",
	author='Josh Reed (henryotoole)',
	url='https://github.com/henryotoole/restlink',
	packages=find_packages('src'),
	package_dir={'': 'src'},
	py_modules=[os.path.splitext(os.path.basename(path))[0] for path in glob.glob('src/*.py')],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		"apispec",
		"Flask",
		"SQLAlchemy",
		"marshmallow"
	],
	classifiers=[
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python :: 3',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
	]
)