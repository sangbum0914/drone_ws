from setuptools import find_packages, setup

package_name = "drone_estimator"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/estimator.launch.py"]),
        ("share/" + package_name + "/config", ["config/topics_airsim.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="sangbum",
    maintainer_email="sangbum.lee.robot@naverlabs.com",
    description="자작 state estimator 를 시뮬레이터에 꽂는 ROS2 파이프라인",
    license="Proprietary",
    entry_points={
        "console_scripts": [
            "estimator_node = drone_estimator.estimator_node:main",
            "evaluator_node = drone_estimator.evaluator_node:main",
        ],
    },
)
