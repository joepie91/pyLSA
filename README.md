# pyLSA

A simple server statistics agent for Linux. Serves statistics over HTTP. 
The goal is to keep it small and not require anything but the Python 
standard libraries.

## Current status

**In development.**  Most is already there, but it still needs stuff 
like configuration file reading, authentication, etc.

## How does it work?

PySFX is used to create a self-extracting 'transparent' installer that
compiles psutil locally (without installing it system-wide), and then
puts all the files for pyLSA (including your config!) in place. It
automatically starts pyLSA afterwards, and if you run the installer
again, it'll detect that pyLSA is already installed, and run the
existing installation.

## How can I use it?

1. (in the future) Modify the `pylsa.conf` file in the `installer/`
directory.
2. Run `build.sh`.
3. Upload the created `pylsa_sfx.py` file to any server that you'd like
to run your statistics agent on.
4. Run the SFX on each of those servers. If you are root, it will create
an unprivileged user for PyLSA and run it as that user. If you are an
unprivileged user, it will run it as your user. Future attempts to start
pyLSA using the installer will behave the same.
5. Done!
