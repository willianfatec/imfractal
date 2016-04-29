"""
Copyright (c) 2016 Rodrigo Baravalle
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

################
# test_3dMFS_stability.py: used to test SandBox 3D Implementation for stability
# i.e. run N times 3dMFS with the same input and check for variations
################

# Args:
# compile_cython: if to compile the multifractal spectrum or not (cython)
# path_mats: path to the matlab matrices with the BioAsset Bones data


import sys, getopt

def handle_args(argv):

    compile_cython = False
    path_mats = ''
    num_trials = 1
    total_pixels = 1500

    test_name = "test_3dMFS_stability.py"

    test_usage_str = test_name + " -c <compile_cython> -p <path_mats> -t <num_trials> -n <total_pixels>"

    try:
        opts, args = getopt.getopt(argv, "hc:p:t:n:", ["compile_cython=", "path_mats=", "num_trials=", "total_pixels="])
    except getopt.GetoptError:
        print test_usage_str
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print test_usage_str
            sys.exit()
        elif opt in ("-c", "--compile_cython"):
            compile_cython = arg
        elif opt in ("-p", "--path_mats"):
            path_mats = arg
        elif opt in ("-t", "--num_trials"):
            num_trials = arg
        elif opt in ("-n", "--total_pixels"):
            total_pixels = arg

    print path_mats

    if path_mats == '' :
        print "Please specify path to matlab matrices with option -p"
        print test_usage_str
        exit()

    if compile_cython in ("True", "T", "true", "t"):
        import os
        arr = [ "imfractal/Algorithm/qs3D", "imfractal/Algorithm/qs"]

        for i in range(len(arr)):

            command1 = "cython "+arr[i]+".pyx "
            command2 = "gcc -c -fPIC -I/usr/include/python2.7/ "+arr[i]+".c"+" -o "+arr[i]+".o"
            command3 = "gcc -shared "+arr[i]+".o -o "+arr[i]+".so"

            print command1
            os.system(command1)
            print command2
            os.system(command2)
            print command3
            os.system(command3)

    return path_mats, num_trials, total_pixels

if __name__ == "__main__":
    path_mats, num_trials, total_pixels = handle_args(sys.argv[1:])

    import tests.test_3dMFS_stability as t3d_mfs
    t3d_mfs.do_test(path_mats, num_trials, int(total_pixels))
