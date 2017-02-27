#!/usr/bin/env python

import sys
import yaml
import subprocess
import collections

class FailedTest(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class BadTestYAMLData(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def id_os_family():
    return "rhel7"


def id_package_manager(os_family):
  if os_family == 'rhel7':
    return 'yum'
  elif os_family == 'fedora':
    return 'dnf'
  elif os_family == 'ubuntu':
    return 'apt'
  else:
    return 'unknown'


def load(infile):

  with open(infile, 'r') as input:
    try:
      return(yaml.load(input))
    except yaml.YAMLError as exc:
      return(exc)


def install_packages(list):
    os_family = id_os_family()
    package_manager = id_package_manager(os_family)

    if package_manager in ('yum', 'dnf'):
        package_string = ' '.join(list)
        run_command("{} install -y {}".format(package_manager, package_string))
    else:
        return False


def run_command(command):
    ReturnResult = collections.namedtuple("ReturnResult", ['returncode', 'stdout', 'stderr'])
    # Run the command, with shell since we don't know if users
    # will do output redirection or shell expansion
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    out, err = process.communicate()
    returncode = process.returncode

    return_tuple = ReturnResult(returncode, out, err)
    return return_tuple


def validate(name, expected, result):
    if expected == result:
        print "Test passed: '{}'".format(name)
        return 0
    else:
        print "Test FAILED: '{}'".format(name)
        print ">> expected: '{}'".format(expected)
        print ">> returned: '{}'".format(result)
        raise FailedTest("{}:{}".format(name,result))


def run_tests(list):
    for test in list:
        for name, data in test.items():
            command=data["cmd"]
            result = run_command(command)

            if len(data['validate']) > 1:
                raise BadTestYAMLData("{} has too many validations - only one allowed".format(name))

            if 'exit' in data['validate']:
                validate(name, data['validate']['exit'], result.returncode)
            elif "stdout" in data['validate']:
                validate(name, data['validate']['stdout'], result.stdout)
            elif "stderr" in data['validate']:
                validate(name, data['validate']['stderr'], result.stderr)
            else:
                print("Unknown Validation")
                raise BadTestYAMLData(data['validate'])


def run_pre(dict):
    if 'packages' in dict:
        install_packages(dict['packages'])

    if 'cmds' in dict:
        for command in dict['cmds']:
            run_command(command)


def run_post(dict):
    if 'cmds' in dict:
        for command in dict['cmds']:
            run_command(command)


def doit():
    yml = load("/tests/tests.yml")
    fail = False

    if 'pre' in yml:
        try:
            run_pre(yml['pre'])
        except BadTestYAMLData as e:
            print("There is an error in the test.yml syntax:")
            print e
            fail = True
        except FailedTest as e:
            print('One or more tests have failed.')
            print e
            fail = True


    if 'tests' in yml:
        try:
            run_tests(yml['tests'])
        except BadTestYAMLData as e:
            print("There is an error in the test.yml syntax:")
            print e
            fail = True
        except FailedTest as e:
            print('One or more tests have failed.')
            print e
            fail = True

        if 'post' in yml:
           run_post(yml['post'])

    if fail:
        sys.exit(1)

if __name__ == '__main__':
  doit()
