import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wsshuttle",
    version="0.0.1",
    author="Jamie Hill-Daniel",
    author_email="clubby789@gmail.com",
    description="A tool to tunnel TCP via WinRM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clubby789/wsshuttle",
    project_urls={
        "Bug Tracker": "https://github.com/clubby789/wsshuttle/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=["wsshuttle"],
    python_requires=">=3.5",
    install_requires=["pywinrm==0.4.2", "requests-ntlm"],
)
