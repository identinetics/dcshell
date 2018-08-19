import os.path
import pytest
import subprocess

def test_build1():
    script = os.path.abspath('build')
    subprocess.call([script, '-D', 'test', '-f', 'testenv/dc_build1.yaml', '-v'])
