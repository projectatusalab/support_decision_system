from setuptools import setup, find_packages

setup(
    name="support_decision_system",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "pandas",
        "pyvis",
        "neo4j",
        "plotly"
    ],
) 