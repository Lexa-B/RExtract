from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rextract",
    version="0.0.1",
    author="Lexa Baldwin",
    author_email="Lexa.40@proton.me",
    description="A runnable extraction module for slot-filling extraction using LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Lexa-B/RExtract/",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Attribution-ShareAlike 4.0 International",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=[
        "langchain-core",
        "pydantic>=2.0.0",
    ],
) 