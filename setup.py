from setuptools import setup,find_packages

def readme():
    with open('README.md') as f:
        return f.read()

requires = [
    'requests'
]

setup(
		name='rsa_archer',
		version='0.1.2',
		author='Aleksei Aikashev',
		author_email='a.aykashev@gmail.com',
		description='RSA Archer REST and GRC API library',
		long_description=readme(),
		long_description_content_type="text/markdown",
		url='https://github.com/mwa21/rsa_archer',
		keywords='RSA Archer GRC Library',
		packages=find_packages(),
		classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
		'Intended Audience :: Developers',
		'Topic :: Software Development :: Libraries :: Python Modules',
    	'Topic :: Software Development :: Libraries'
    	],
		install_requires=requires,
)
