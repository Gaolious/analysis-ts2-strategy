#!/bin/bash

NODE=`which node` || '/usr/bin/node'

tmp=`realpath "${0}"`
pushd `dirname "${tmp}"`

echo `pwd`

"${NODE}" ./dist/index.js $@
