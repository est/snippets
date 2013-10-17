#!/bin/bash

for dir in ./*/;
do
  pushd  $dir >/dev/null
  echo project is called $dir
  (hg log||sudo -u www-data hg log ) | grep user: | sort | uniq
  popd >/dev/null
done;
