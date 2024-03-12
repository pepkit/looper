#!/bin/bash

branch='dev_derive'

wget https://github.com/pepkit/hello_looper/archive/refs/heads/${branch}.zip
mv ${branch}.zip data/
cd data/
rm -rf hello_looper-${branch}
unzip ${branch}.zip
rm ${branch}.zip