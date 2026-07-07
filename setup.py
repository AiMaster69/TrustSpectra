from setuptools import setup, find_packages
from pathlib import Path

# Читаем README файл
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Читаем requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="TrustSpectra",
    version="0.9.0",
    author="???",
    author_email="???",
    description="Desktop application for audio analysis using machine learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TrustSpectra/TrustSpectra",
    packages=find_packages(),
    classifiers=[
    "Development Status :: Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12.6",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
    "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
    },
    entry_points={
    "console_scripts": [
            "audio-analyzer=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
    "": ["*.json", "*.yaml", "*.yml"],
    },
    zip_safe=False,
) 