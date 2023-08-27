from CUDA_FILE.cuda_kernel_wrapper import get_combined_cuda_kernel_code
import pycuda.driver as drv
import pycuda.autoinit
import pycuda.compiler as cmp
import numpy as np
from parameters import params


def GPU_KERNEL_MCScatteringSimulation(pixels,
            E_i, 
            ProbeDiameter, 
            MinimumEnergy, 
            pixel_dimensions, 
            dE_threshold, 
            perfect_image_0, 
            perfect_image_1, 
            Density, 
            t_counting):
    
    # Create a 2D array from the 'pixels' list
    pixels_array = np.vstack((
    [pixel.electron_count for pixel in pixels],      # Column 0: Number of electrons in the pixel
    [pixel.i for pixel in pixels],                   # Column 1: Pixel index i
    [pixel.j for pixel in pixels],                   # Column 2: Pixel index j
    [pixel.x_dimension for pixel in pixels],         # Column 3: Dimension along the x-axis      
    [pixel.y_dimension for pixel in pixels],         # Column 4: Dimension along the y-axis
    [pixel.z_dimension for pixel in pixels]          # Column 5: Dimension along the z-axis
    )).T 

    

    print('Pixel data prepared ...')

    # Load the CUDA kernel code
    kernel_code = get_combined_cuda_kernel_code()

    # Compile the kernel code
    module = cmp.SourceModule(kernel_code, no_extern_c=True)

    # Get the kernel function
    MCScatteringSimulationKernel = module.get_function("MCScatteringSimulationKernel")


    # Transfer the 'pixels' array to the GPU memory
    pixels_gpu = drv.to_device(pixels_array)

    # Other variables needed for the kernel (example, replace with your actual data)
    numPixels = pixels_array.size
  
    new_image_MCS_gpu = drv.mem_alloc(perfect_image_0 * perfect_image_1 * np.dtype(np.float64).itemsize)

    new_image_MCS = np.zeros((perfect_image_0, perfect_image_1), dtype=np.float64)

    drv.memcpy_htod(new_image_MCS_gpu, new_image_MCS)

    # 2D block and grid sizes
    block_size_x = 16
    block_size_y = 16
    grid_size_x = (perfect_image_0 + block_size_x - 1) // block_size_x
    grid_size_y = (perfect_image_1 + block_size_y - 1) // block_size_y


    print('Beginning simulation ...')

    # Launch the CUDA kernel
    MCScatteringSimulationKernel(pixels_gpu, np.int32(numPixels), np.float64(E_i), np.float64(ProbeDiameter),
                                np.float64(MinimumEnergy), np.float64(dE_threshold), np.int32(perfect_image_0),
                                np.int32(perfect_image_1), np.float64(Density), np.float64(t_counting), new_image_MCS_gpu,
                                block=(block_size_x, block_size_y, 1), grid=(grid_size_x, grid_size_y))

    

    print('Transferring data from GPU device back to host...')
    drv.memcpy_dtoh(new_image_MCS, new_image_MCS_gpu)
    return new_image_MCS


