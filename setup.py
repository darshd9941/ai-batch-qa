from setuptools import setup, find_packages

setup(
    name="ai-batch-qa",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1",
        "rich>=13.0",
        "Pillow>=10.0",
        "numpy>=1.24",
    ],
    entry_points={
        "console_scripts": [
            "ai-batch-qa=batch_qa.cli:cli",
        ],
    },
    python_requires=">=3.9",
    author="darshd9941",
    description="Auto-detect quality issues in batch AI image generation",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/darshd9941/ai-batch-qa",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Graphics",
    ],
)
