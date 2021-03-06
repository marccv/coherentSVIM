# -*- coding: utf-8 -*-
"""
Created on Tue May 24 15:54:03 2022

@author: SPIM-OPT
 
   Written by Michele Castriotta, Alessandro Zecchi, Andrea Bassi (Polimi).
   Code for creating the measurement class of ScopeFoundry for the Orca Flash 4V3
   11/18
"""

from base_SVIM_Measurement import BaseSvimMeasurement
import numpy as np
from scipy.linalg import hadamard



def scramble(H, N):
    
    np.random.seed(222)
    
    I = np.eye(N)
    Pr = I[np.random.permutation(N), :]
    Pc = I[np.random.permutation(N), :]
    return Pr @ H @ Pc


# def walsh_gen_old(n):
    
#     from numpy import genfromtxt
#     return genfromtxt(f'/Users/marcovitali/Documents/Poli/tesi/coherentSVIM/hadamard/wh{n}.csv', delimiter=',')

def walsh_gen(n):
    
    H = hadamard(n)
    diffs = np.diff(H)
    norm = np.linalg.norm(diffs, axis = 1)
    order = np.argsort(norm)
     
    return H[order,:]

def create_hadamard_patterns(num_of_patterns = 32, had_type = 'normal' , transpose_pattern=False, cropped_field_size = [256, 512],
                             im_size = [1080, 1920]):
    
    """
    had types: [ 'normal', 'walsh', 'scrambled']
    """
    
    s_y = im_size[0]
    s_x = im_size[1]
    
    # dimentions of the rectangle to be cropped out in units of pizel diagonal (same as unit_period)
    s_diag = cropped_field_size[0] #dimension of the border parallel to the diagonal direction
    s_anti = cropped_field_size[1] #dimension of the border parallel to the antidiagonal direction  

    
    if had_type == 'normal':
        H = hadamard(num_of_patterns)
    elif had_type == 'walsh':
        H = walsh_gen(num_of_patterns)
    elif had_type == 'scrambled':
        H = scramble(hadamard(num_of_patterns), num_of_patterns)


    H[H<0] = 0 # the DMD only accepts 0 and 1, so to create the real pattern I will have to operate in PosNeg mode
    
    images = []
    
    if not transpose_pattern:
        #antidiag
        
        repetitions = s_diag/num_of_patterns * 2
        
        for i in range(num_of_patterns):
            
            image = np.zeros(im_size, dtype = 'uint8')
            
            strip = np.uint8(np.repeat(H[i], repetitions).reshape(1,s_diag*2).copy())
            
            pad_len = s_y + 0.5*(s_x - s_y - s_diag*2)
            padding = np.zeros([1,int(pad_len)])
            
            strip = np.concatenate((padding, strip, padding), axis = 1)
            
            # print(strip)
            
            for j in range(s_y):
                image[j, :] = strip[0, (s_y-j-1):(s_y + s_x -j-1)]
                
            images.append(image)
    else:
        #transpose: diag
        repetitions = s_anti/num_of_patterns * 2
        
        for i in range(num_of_patterns):
            
            image = np.zeros(im_size, dtype = 'uint8')
            
            strip = np.uint8(np.repeat(H[i], repetitions).reshape(1,s_anti * 2).copy())
            
            pad_len = s_y + 0.5*(s_x - s_y - s_anti * 2)
            padding = np.zeros([1,int(pad_len)])
            
            strip = np.concatenate((padding, strip, padding), axis = 1)
            
            # print(strip)
            
            for j in range(s_y):
                image[j, :] = strip[0, j :( s_x +j)]
                
            images.append(image)
        
            
    return images







class coherentSvim_Hadamard_Measurement(BaseSvimMeasurement):     
    
    name = "coherentSvim_Hadamard"
    
    def calculate_num_frames(self):
        return (1 + self.settings['PosNeg']) *  self.settings['had_pat_num']
    
    
    def set_had_pat_num(self, had_pat_num):
        
        if np.log2(had_pat_num)%1 != 0:
            
            higher = int(2**(np.ceil(np.log2(had_pat_num))))
            lower = int(higher/2)
            
            if had_pat_num ==  higher - 1:
                self.settings['had_pat_num'] = lower
            else:
                self.settings['had_pat_num'] = higher
        else:
            self.settings['num_frames']  =(1 + self.settings['PosNeg']) * had_pat_num
            
            if hasattr(self, 'time_frames_n'):
                self.settings['time_frames_n'] = self.calculate_time_frames_n()
            
         
  
        
    def setup_svim_mode_settings(self):
        
        self.had_pat_num = self.settings.New('had_pat_num', dtype=int, initial=64 , vmin = 1 )
        self.had_pat_num.hardware_set_func = self.set_had_pat_num
        
        # self.settings.New('reorder_test', dtype = bool, initial = True )
        self.settings.New('had_type', dtype = str, choices = [ 'normal', 'walsh', 'scrambled'], initial = 'normal')
   
    def run_svim_mode_function(self):
        transpose_pattern = self.settings['transpose_pattern']
        cropped_field_size = [self.settings['ROI_s_z'], self.settings['ROI_s_y']]
            
            
        if self.settings['PosNeg'] == False:
              
            images = create_hadamard_patterns( self.settings['had_pat_num'], self.settings['had_type'], transpose_pattern, cropped_field_size )
        
        else:
            #PosNeg
            images = []
            im_pos = create_hadamard_patterns( self.settings['had_pat_num'], self.settings['had_type'], transpose_pattern, cropped_field_size )
                    
            for im in im_pos:
                images.append(im)
                im_neg = np.uint8(np.logical_not(im)*1)
                images.append(im_neg)
        return images
        
    # def run_iteration_settings(self, time_index):
        
    #     if self.settings['reorder_test'] == True:
            
    #         sequence = [2,1] # random(?) subset of hadamard patterns to use in the current time frame
            
    #         if self.settings['PosNeg'] == True:
                
    #             temp = []
    #             for i in sequence:
    #                 temp.append(i*2-1)
    #                 temp.append(i*2)
                    
    #             sequence = temp
            
    #         repeatnum = len(sequence)
            
            
    #         self.dmd_hw.dmd.reorderlut(sequence, repeatnum)         
        