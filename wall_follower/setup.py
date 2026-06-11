from setuptools import setup

package_name = 'wall_follower'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Harun Teper',
    maintainer_email='harun.teper@cs.tu-dortmund.de',
    description='Editable wall-following node for the ROS 2 hands-on lecture (F1TENTH).',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'wall_follow = wall_follower.wall_follow:main',
        ],
    },
)
