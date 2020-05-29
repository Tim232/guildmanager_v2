from distutils.core import setup


with open("./guildmanager/__init__.py") as rfile:
    lines = rfile.readlines()
    for line in lines:
        if line.startswith("__version__ = "):
            ver = line.split(" ")[-1]
            break
    else:
        ver = "0.1a"

if ver.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            ver += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            ver += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

setup(
    name='guildmanager_v2',
    version=ver,
    packages=['guildmanager'],
    url='https://github.com/dragdev-studios/guildmanager_v2',
    license='Apache License 2.0',
    author='EEKIM10',
    author_email='',
    description='Version 2 of guildmanager, with actual quality.'
)