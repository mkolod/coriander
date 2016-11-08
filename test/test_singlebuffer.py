# Copyright Hugh Perkins 2016
"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import numpy as np
import pyopencl as cl
import os
import subprocess
from test import test_common


def test_singlebuffer_sqrt(context, queue):
    """
    Test doing stuff with one single large buffer for destination and source, just offset a bit
    """
    code = """
__global__ void myKernel(float *data0, float *data1, int N) {
    if(threadIdx.x < N) {
        data0[threadIdx.x] = sqrt(data1[threadIdx.x]);
    }
}
"""
    prog = test_common.compile_code(cl, context, code)

    N = 10

    src_host = np.random.uniform(0, 1, size=(N,)).astype(np.float32) + 1.0
    dst_host = np.zeros(N, dtype=np.float32)

    src_offset = 128
    dst_offset = 256

    huge_buf_gpu = cl.Buffer(context, cl.mem_flags.READ_WRITE, size=4096)

    test_common.enqueue_write_buffer_ext(cl, queue, huge_buf_gpu, src_host, device_offset=src_offset, size=N * 4)

    global_size = 256
    workgroup_size = 256
    # scratch = workgroup_size * 4

    mangledName = '_Z8myKernelPfS_i'
    prog.__getattr__(mangledName)(
        queue, (global_size,), (workgroup_size,),
        huge_buf_gpu, np.int64(dst_offset),
        huge_buf_gpu, np.int64(src_offset),
        np.int32(N),
        cl.LocalMemory(4)
    )
    queue.finish()
    test_common.enqueue_read_buffer_ext(cl, queue, huge_buf_gpu, dst_host, device_offset=dst_offset, size=N * 4)

    queue.finish()
    print('src_host', src_host)
    print('dst_host', dst_host)
    print('np.sqrt(src_host)', np.sqrt(src_host))

    assert np.abs(np.sqrt(src_host) - dst_host).max() <= 1e-4