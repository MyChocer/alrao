import sys
import subprocess
from pathlib import Path

# Utility
def getLastDot(U_str):
    for i in reversed(range(len(U_str))):
        if U_str[i] == '.':
            return i
    return -1

def createTempFileName(temp_file_name):
    i_dot = getLastDot(temp_file_name)
    if i_dot == -1:
        temp_type = ''
    else:
        l = len(temp_file_name)
        temp_type = temp_file_name[(i_dot - l):]
        ret_file_name = temp_file_name[:i_dot]
    temp_number = 0
    temp_suffix = ''
    while Path(ret_file_name + temp_suffix + temp_type).is_file():
        temp_number += 1
        temp_suffix = '_' + repr(temp_number)
    ret_file_name += temp_suffix + temp_type

    return ret_file_name

# General definitions
def build_args(argsDict):
    lstArgs = ''
    for name, key in argsDict.items():
        if isinstance(key, bool):
            if key:
                lstArgs += ' --' + name
        elif isinstance(key, str):
            if key != '':
                lstArgs += ' --' + name + '=' + key
        else:
            lstArgs += ' --' + name + '=' + repr(key)
    return lstArgs

def build_sbatch(runOpt, sbatchOpt, argsDict):
    runOpt['temp_file'] = createTempFileName(runOpt['temp_file'])
    f_sbatch = open(runOpt['temp_file'], 'w')

    # Slurm options
    f_sbatch.write('#!/bin/bash\n\n')
    for opt in sbatchOpt:
        f_sbatch.write('#SBATCH ' + opt + '\n')
    f_sbatch.write('\n')

    # Bash part
    f_sbatch.write('source activate ' + runOpt['env_name'] + '\n')

    str_args = build_args(argsDict)
    if 'ipython' in runOpt['command']:
        str_args = ' --' + str_args
    f_sbatch.write(runOpt['command'] + ' ' + runOpt['script'] + str_args + '\n')

    f_sbatch.write('source deactivate ' + runOpt['env_name'] + '\n')

    f_sbatch.close()

def build_srun(runOpt, sbatchOpt, argsDict):
    command_srun = 'srun'
    for opt in sbatchOpt:
        command_srun += ' ' + opt
    command_srun += ' --pty bash'

    runOpt['temp_file'] = createTempFileName(runOpt['temp_file'])
    f_sbatch = open(runOpt['temp_file'], 'w')

    f_sbatch.write('#!/bin/bash\n\n')
    f_sbatch.write('source activate ' + runOpt['env_name'] + '\n')

    str_args = build_args(argsDict)
    if 'ipython' in runOpt['command']:
        str_args = ' --' + str_args
    f_sbatch.write(runOpt['command'] + ' ' + runOpt['script'] + str_args + '\n')

    f_sbatch.write('source deactivate ' + runOpt['env_name'] + '\n')

    f_sbatch.close()
    return command_srun

def launch_exp(runOpt, sbatchOpt, argsDict):
    if runOpt['interactive']:
        command_srun = build_srun(runOpt, sbatchOpt, argsDict)
        print('Interactive job to launch: ' + runOpt['temp_file'] + '\n')
        proc = subprocess.Popen(command_srun.split(), stdout = subprocess.PIPE)
        output, error = proc.communicate()
    else:
        build_sbatch(runOpt, sbatchOpt, argsDict)
        bashCMD = 'sbatch ' + runOpt['temp_file']
        proc = subprocess.Popen(bashCMD.split(), stdout = subprocess.PIPE)
        output, error = proc.communicate()

        if not output is None:
            print(str(output, 'utf-8').strip())
        if not error is None:
            print(str(error, 'utf-8').strip(), file = sys.stderr)
