from setuptools import setup
import os
from glob import glob

package_name = 'rdd_detector'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', 'smartdashcam', 'config', 'model'), 
         glob('config/model/*')),
        (os.path.join('share', package_name, 'srv'),
         glob('srv/*.srv')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='Advanced road damage detection using computer vision',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'rdd_detector = rdd_detector.rdd_detector_node:main'
        ],
    },
)