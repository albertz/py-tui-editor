

"""
Usage:

Create ~/.pypirc with info:

    [distutils]
    index-servers =
        pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: ...
    password: ...

(Not needed anymore) Registering the project: python3 setup.py register
New release: python3 setup.py sdist upload

I had some trouble at some point, and this helped:
pip3 install --user twine
python3 setup.py sdist
twine upload dist/*.tar.gz

See also MANIFEST.in for included files.

For debugging this script:

python3 setup.py sdist
pip3 install --user dist/*.tar.gz -v
(Without -v, all stdout/stderr from here will not be shown.)

"""

from distutils.core import setup
import time
from pprint import pprint
import os
import sys
import shutil
from subprocess import Popen, check_output, PIPE


def debug_print_file(fn):
    print("%s:" % fn)
    if not os.path.exists(fn):
        print("<does not exist>")
        return
    if os.path.isdir(fn):
        print("<dir:>")
        pprint(os.listdir(fn))
        return
    print(open(fn).read())


def parse_pkg_info(fn):
    """
    :param str fn:
    :rtype: dict[str,str]
    """
    res = {}
    for ln in open(fn).read().splitlines():
        if not ln or not ln[:1].strip() or ":" not in ln:
            continue
        key, value = ln.split(": ", 1)
        res[key] = value
    return res


def git_commit_rev(commit="HEAD", git_dir="."):
    if commit is None:
        commit = "HEAD"
    return check_output(["git", "rev-parse", "--short", commit], cwd=git_dir).decode("utf8").strip()


def git_is_dirty(git_dir="."):
    proc = Popen(["git", "diff", "--no-ext-diff", "--quiet", "--exit-code"], cwd=git_dir, stdout=PIPE)
    proc.communicate()
    if proc.returncode == 0:
        return False
    if proc.returncode == 1:
        return True
    raise Exception("unexpected return code %i" % proc.returncode)


def git_commit_date(commit="HEAD", git_dir="."):
    out = check_output(["git", "show", "-s", "--format=%ci", commit], cwd=git_dir).decode("utf8")
    out = out.strip()[:-6].replace(":", "").replace("-", "").replace(" ", ".")
    return out


def git_head_version(git_dir=".", long=False):
    commit_date = git_commit_date(git_dir=git_dir)  # like "20190202.154527"
    # rev = git_commit_rev(git_dir=git_dir)
    # is_dirty = git_is_dirty(git_dir=git_dir)
    # Make this distutils.version.StrictVersion compatible.
    version = "1.%s" % commit_date
    if long:
        # Keep SemVer compatible.
        rev = git_commit_rev(git_dir=git_dir)
        version += "+git.%s" % rev
        if git_is_dirty(git_dir=git_dir):
            version += ".dirty"
    return version


def load_setup_info_generated(filename: str):
    code = compile(open(filename).read(), filename, "exec")
    info = {}
    eval(code, info)
    version = info["version"]
    long_version = info["long_version"]
    return version, long_version


def main():
    if os.path.exists("_setup_info_generated.py"):
        version, long_version = load_setup_info_generated("_setup_info_generated.py")
        print("Version via _setup_info_generated:", version, long_version)
    elif os.path.exists("tui_editor/_setup_info_generated.py"):
        version, long_version = load_setup_info_generated("tui_editor/_setup_info_generated.py")
        print("Version via tui_editor/_setup_info_generated:", version, long_version)
    else:
        try:
            version = git_head_version()
            long_version = git_head_version(long=True)
            print("Version via Git:", version, long_version)
        except Exception as exc:
            print("Exception while getting Git version:", exc)
            sys.excepthook(*sys.exc_info())
            version = time.strftime("1.%Y%m%d.%H%M%S", time.gmtime())
            long_version = version + "+unknown"
            print("Version via current time:", version, long_version)

    if os.environ.get("DEBUG", "") == "1":
        debug_print_file(".")
        debug_print_file("PKG-INFO")

    with open("_setup_info_generated.py", "w") as f:
        f.write("version = %r\n" % version)
        f.write("long_version = %r\n" % long_version)
    shutil.copy("_setup_info_generated.py", "tui_editor/")
    package_data = ["MANIFEST", "_setup_info_generated.py"]

    setup(
        name='tui-editor',
        version=version,
        packages=['tui_editor'],
        include_package_data=True,
        package_data={'tui_editor': package_data},  # filtered via MANIFEST.in
        description='Simple Python terminal (TUI) multi-line editor',
        author='Albert Zeyer',
        author_email='albzey@gmail.com',
        url='https://github.com/albertz/py-tui-editor',
        license='MIT License',
        long_description=open('README.rst').read(),
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Intended Audience :: Education",
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: POSIX',
            'Operating System :: Unix',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Software Development :: User Interfaces',
            'Topic :: System :: Shells',
            'Topic :: Terminals',
            'Topic :: Text Editors',
        ]
    )


if __name__ == "__main__":
    main()
