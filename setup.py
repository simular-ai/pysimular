from setuptools import setup, find_packages

setup(
    name="pysimular",
    version="0.1.2",
    packages=find_packages(),
    license_files=["LICENSE"],
    install_requires=["requests>=2.25.1", "aiohttp>=3.8.0", "pyobjc"],
    author="Simular",
    author_email="support@simular.ai",
    description="Python API for Simular agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/simular-ai/pysimular",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
