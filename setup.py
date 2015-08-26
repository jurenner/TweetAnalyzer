try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'name': 'TweetAnalyzer',
    'description': 'Python tool to collect and analyze tweets',
    'author': 'Juliana Renner',
    'version': '1.0',
    'install_requires': ['tweepy'],
    'packages': ['TweetAnalyzer'],
    'scripts': []
}