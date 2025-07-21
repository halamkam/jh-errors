from setuptools import setup, find_packages

setup(
    name='jh-errors',
    version='0.1.0',
    author='Marek Halamka',
    description='Custom KubeSpawner modifications for better error handling',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'kubespawner>=4.0.0',
        'jupyterhub>=4.0.0',
        'kubernetes_asyncio>=26.1.0',
    ],
    include_package_data=True,
    zip_safe=False,  # Usually False for packages that include templates, configs, etc.
    python_requires='>=3.9',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Change if using another license
        "Operating System :: OS Independent",
    ],
    setup_requires=[
        'setuptools>=42',
        'wheel',
    ],
)
