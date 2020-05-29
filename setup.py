from setuptools import setup
import re

with open('requirements.txt') as f:
  requirements = f.readlines()

with open('guildmanager/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

with open('README.md') as f:
    readme = f.read()

setup(
    name='guildmanager-v2',
    version=version,
    packages=['guildmanager'],
    url='https://github.com/dragdev-studios/guildmanager_v2',
    license='Apache License 2.0',
    author='EEKIM10',
    author_email='discordebotdev@gmail.com',
    description='Version 2 of guildmanager, with actual quality.',

    long_description=readme,
    long_description_content_type="text/markdown",
    project_urls={
        "Issue Tracker": "https://github.com/dragdev-studios/guildmanager_v2/issues",
        "Documentation": "https://github.com/dragdev-studios/guildmanager_v2/wiki"
    },
    install_requires=requirements
)
