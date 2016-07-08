from setuptools import setup, find_packages

def readme():
    with open('README.org') as f:
        return f.read()

setup(name='Fixture Monitor',
      version='0.1',
      description='Log Arduino output',
      long_description='Take JSON formatted Arduino output, and selectively distribute it.',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Topic :: Communications',
      ],
      keywords='arduino thingspeak email',
      url='http://github.com/kcjuntunen/fmon',
      author='K. C. Juntunen',
      author_email='kcjuntunen@amstore.com',
      license='GPLv2',
      packages=['fmon'],
      install_requires=[
          'python-dateutil',
      ],
      include_package_data=True,
      zip_safe=False,
      scripts=['bin/fmon'],
      test_suite='nose.collector',
      tests_require=['nose'],
)
