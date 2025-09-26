import subprocess
import time
import datetime
from django.test import TestCase

# Create your tests here.
subprocess.Popen(
            "appium",
            shell=True,
            stdout=subprocess.PIPE
        )