#!/bin/bash

NODE=`which node` || '/usr/bin/node'

tmp=`realpath "${0}"`
BASE=`dirname "${tmp}"`

#echo "Current Path : `pwd`"
#echo "Current Param : $@"

export NODE_PATH="${BASE}/node_modules"

echo "${NODE}" "${BASE}/dist/index.js" $@
"${NODE}" "${BASE}/dist/index.js" $@
