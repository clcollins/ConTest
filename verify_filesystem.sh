#!/bin/bash

rpm -V filesystem > /tmp/filesystem

# Only / can be modifed
# Only /boot can be missing

[[ $(md5sum /tmp/filesystem) == "2ba2da559bb489db4c52e4bbeb888fe0  /tmp/filesystem" ]] || exit 1


