"""Setup configuration for task-queue Python package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="task-queue",
    version="0.1.0-alpha",
    author="Task Queue Contributors",
    author_email="contributors@task-queue.dev",
    description="High-performance distributed task processing library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/task-queue/task-queue",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "redis": ["redis>=4.5.0", "aioredis>=2.0.0"],
        "rabbitmq": ["aio-pika>=9.0.0"],
        "postgresql": ["asyncpg>=0.28.0"],
        "all": [
            "redis>=4.5.0",
            "aioredis>=2.0.0",
            "aio-pika>=9.0.0",
            "asyncpg>=0.28.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-benchmark>=4.0.0",
            "black>=23.0.0",
            "pylint>=2.17.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "taskqueue-worker=taskqueue.cli:worker_cli",
            "taskqueue-scheduler=taskqueue.cli:scheduler_cli",
            "taskqueue-api=taskqueue.cli:api_cli",
            "taskqueue-inspect=taskqueue.cli:inspect_cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="task queue distributed celery bull redis rabbitmq async",
    project_urls={
        "Bug Reports": "https://github.com/task-queue/task-queue/issues",
        "Source": "https://github.com/task-queue/task-queue",
        "Documentation": "https://docs.task-queue.dev",
    },
)
