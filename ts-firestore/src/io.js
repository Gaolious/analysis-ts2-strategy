"use strict";
exports.__esModule = true;
exports.writeConfig = exports.getArgs = void 0;
function getArgs() {
    var args = {};
    process.argv
        .slice(2, process.argv.length)
        .forEach(function (arg) {
        // long arg
        if (arg.slice(0, 2) === '--') {
            var longArg = arg.split('=');
            var longArgFlag = longArg[0].slice(2, longArg[0].length);
            args[longArgFlag] = longArg.length > 1 ? longArg[1] : true;
        }
        // flags
        else if (arg[0] === '-') {
            var flags = arg.slice(1, arg.length).split('');
            flags.forEach(function (flag) {
                args[flag] = true;
            });
        }
    });
    return args;
}
exports.getArgs = getArgs;
function writeConfig(out) {
}
exports.writeConfig = writeConfig;
