#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 26 16:39:14 2022

@author: marcovitali
"""


import numpy as np
from get_h5_data import get_h5_dataset, get_h5_attr
# import tifffile as tiff
import time
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 300
plt.rcParams.update({'font.size': 9})

# from skimage.restoration import denoise_tv_chambolle

import pylops
# from scipy.sparse.linalg import aslinearoperator
# from scipy.sparse.linalg import LinearOperator

import sys
import os
import h5py
import pyqtgraph as pg
import qtpy.QtCore
from qtpy.QtWidgets import QApplication



def time_it(method):
    """Fucntion decorator to time a methos""" 
       
    def inner(*args,**kwargs):
        
        start_time = time.time() 
        result = method(*args, **kwargs) 
        end_time = time.time()
        print(f'Execution time for method "{method.__name__}": {end_time-start_time:.6f} s \n') 
        return result        
    return inner


images = []
plots = []
QAPP = None

def show_image(image,  **kwargs):
    
    
    show_params = {'ordinate': 'X',
                   'ascisse' : 'Y',
                   'scale_ord' : 1,
                   'scale_asc' : 1}
    
    
    for key, val in kwargs.items():
        show_params[key] = val
    
    
    app = pg.mkQApp()
    plot = pg.PlotItem()
    
    ordinate_text = f'<strong style="font-size: 20px;">{show_params["ordinate"]} axis</strong>'
    ascisse_text = f'<strong style="font-size: 20px;">{show_params["ascisse"]} axis</strong>'
    plot.setLabel(axis='left', text= ascisse_text,  units = 'm')
    plot.setLabel(axis='bottom', text=  ordinate_text, units = 'm')
    
    
    w = pg.ImageView(view = plot)
    img = w.getImageItem()
    tlabel = pg.InfLineLabel(w.timeLine, text="{value:.0f}")
    
    windowTitle = kwargs.pop("title", "ImageView")
    w.setWindowTitle(windowTitle)
    w.setImage(image, scale = (show_params["scale_ord"], show_params["scale_asc"]), pos = (0, 0))
    images.append(w)
    w.show()
    
    
    def imageHoverEvent(event):
        """Show the position, pixel, and value under the mouse cursor.
        """
        if event.isExit():
            plot.setTitle("")
            return
        pos = event.pos()
        i, j  = pos.y(), pos.x()
        time_index = w.currentIndex
        # print(dir(pos))
        
        if len(image.shape) == 2:
        
            # i = int(np.clip(i, 0, image.shape[0] - 1))
            # j = int(np.clip(j, 0, image.shape[1] - 1))
            # val = image[i, j]
            # print(val)
            ppos = img.mapToParent(pos)
            x, y = ppos.x(), ppos.y()
            
        else:
            
            # i = int(np.clip(i, 0, image.shape[1] - 1))
            # j = int(np.clip(j, 0, image.shape[2] - 1))
            # val = image[time_index ,i, j]
            # print(val)
            ppos = img.mapToParent(pos)
            x, y = ppos.x(), ppos.y()
            
        plot.setTitle("pos: (%.1f, %.1f)um  -- pixel: (%d, %d, %d)" % (x*1e6, y*1e6, time_index, i, j), font = 15)
        
        # plot.setTitle("value: %d" % ( val))

    # Monkey-patch the image to use our custom hover function. 
    # This is generally discouraged (you should subclass ImageItem instead),
    # but it works for a very simple use like this. 
    img.hoverEvent = imageHoverEvent
    
    
    return w


class DMD_light_sheet_analysis:
    
    name = 'DMD_light_sheet_analysis'

    def __init__(self, fname, **kwargs ):
        
        #default values
        self.params = {'select_ROI': False,
                       'denoise' : False,
                       'X0': 0,
                       'Y0': 0,
                       'delta_x' : 0,
                       'delta_y' : 0,
                       'mu': 0.01,
                       'lamda': 0.5,
                       'niter_out': 15,
                       'niter_in': 2,
                       'lsqr_niter': 5,
                       'lsqr_damp': 1e-4,
                       'single_volume_time_index' : 0,
                       'save_label': '',
                       'time_lapse_save_label': '',
                       'time_lapse_mode': 'sum',
                       'time_lapse_view': 0,
                       'time_lapse_plane': 0}
        
        # update any specified parameter
        for key, val in kwargs.items():
            self.params[key] = val
        
        self.file_path  = fname
        
        
    @time_it   
    def load_h5_file(self, dataset_index = 0):
        
        self.imageRaw = get_h5_dataset(self.file_path, max(0,dataset_index)) 

    
    def show_im_raw(self):
                
        show_image(self.imageRaw.transpose(0,1,2), title="Raw image", ordinate = 'X', ascisse = 'Y', 
                   scale_ord = 0.65e-6, scale_asc = 0.65e-6)    
        
        if self.name == 'DMD_light_sheet_analysis':
            #keeps the window open running a QT application
            if sys.flags.interactive != 1 or not hasattr(qtpy.QtCore, 'PYQT_VERSION'):
                QApplication.exec_()
            sys.exit ( "End of test")


    @time_it
    def show_im_raw_cc(self):
        
        fig1=plt.figure()
        fig1.clf()
        
        ax1=fig1.add_subplot(111)
        fig1.suptitle('Raw image uniform illumination')
        xy = ax1.imshow(self.imageRaw[0,:,:].transpose(), cmap = 'gray', aspect = 1, interpolation = 'none') 
        ax1.set_xlabel('x (px)')
        ax1.set_ylabel('y (px)')
        cbar = fig1.colorbar(xy, ax = ax1, shrink=1, format='%.0e')
        cbar.ax.set_ylabel('Counts', rotation=270)
    
    
    @time_it
    def setROI(self, **kwargs):
        
        # update any specified parameter
        for key, val in kwargs.items():
            self.params[key] = val
        
        self.imageRaw = self.imageRaw[:,
                                      self.params['X0'] : self.params['X0'] + self.params['delta_x'],
                                      self.params['Y0'] : self.params['Y0'] + self.params['delta_y']]
    
    
    @time_it
    def invert_and_denoise1D_no_for(self, **kwargs):
        

        Iop = pylops.Identity(self.imageRaw.shape)
        Dop = pylops.FirstDerivative(np.prod(self.imageRaw.shape), self.imageRaw.shape,  0, edge=True, kind="backward")
        
        self.params['denoise_type'] =  '1D'
        
        # t = time.time()
        
        self.image_denoised, _ = pylops.optimization.sparsity.SplitBregman(
                                    Iop,
                                    [Dop],
                                    self.imageRaw.ravel(),
                                    self.params['niter_out'],
                                    self.params['niter_in'],
                                    mu = self.params['mu'],
                                    epsRL1s=[self.params['lamda']],
                                    tol=1e-4,
                                    tau=1.0,
                                    **dict(iter_lim=self.params['lsqr_niter'], damp=self.params['lsqr_damp'])
                                )
        # print(f'time for one line: {(time.time()  - t)/(shape[1] * shape[2])}')
        
        
        self.image_denoised = self.image_denoised.reshape(self.imageRaw.shape)
        self.image_denoised = self.image_denoised.transpose(0,2,1)
        
        self.clipped = False
        
    
    @time_it
    def invert_and_denoise3D_v2(self, **kwargs):
        
        # update any specified parameter
        for key, val in kwargs.items():
            self.params[key] = val
        
   

        
        Iop = pylops.Identity(self.imageRaw.shape)
        
        Dop = [
            pylops.FirstDerivative(np.prod(self.imageRaw.shape), self.imageRaw.shape,  0, edge=True, kind="backward"),
            pylops.FirstDerivative(np.prod(self.imageRaw.shape), self.imageRaw.shape,  1, edge=True, kind="backward"),
            pylops.FirstDerivative(np.prod(self.imageRaw.shape), self.imageRaw.shape,  2, edge=True, kind="backward")
        ]
        
        
        # t = time.time()
        
        self.image_denoised, _ = pylops.optimization.sparsity.SplitBregman(
                                    Iop,
                                    Dop,
                                    self.imageRaw.ravel(),
                                    self.params['niter_out'],
                                    self.params['niter_in'],
                                    mu = self.params['mu'],
                                    epsRL1s = [self.params['lamda']]*3,
                                    tol=1e-4,
                                    tau=1.0,
                                    **dict(iter_lim=self.params['lsqr_niter'], damp=self.params['lsqr_damp'])
                                )
        # print(f'time for one line: {(time.time()  - t)/(shape[1] * shape[2])}')
        # print(Nz,ny, nx)
        
        self.image_denoised = self.image_denoised.reshape(self.imageRaw.shape)
        # self.image_denoised = self.image_denoised.transpose(0,2,1)
        
        self.params['denoise_type'] =  '3D'
        self.clipped = False
    

    
    
    
    @time_it
    def cut_negatives(self):
        
        self.image_denoised = self.image_denoised.clip(min = 0)
        self.clipped = True
    
    
    
    @time_it
    def show_inverted_proj(self):
        
        inverted_xy = np.sum(self.image_denoised, 0)
        inverted_xz = np.sum(self.image_denoised, 2)
        
        c_min = min( np.amin(np.amin(inverted_xy, 1), 0) , np.amin(np.amin(inverted_xz, 1), 0) )
        c_max = max(np.amax(np.amax(inverted_xy, 1), 0) , np.amax(np.amax(inverted_xz, 1), 0) )
        
        
        fig1, (ax1, ax2) =plt.subplots(2, 1, gridspec_kw={'height_ratios': [ 4, 1]})
        # fig1.clf()
        fig1.text(0.1,0.2, f'Inverted image projections\n{self.params}')
        
        xy = ax1.imshow(inverted_xy.transpose(), cmap = 'gray', aspect = 1, vmin = c_min, vmax = c_max)
        ax1.set_xlabel('x (px)')
        ax1.set_ylabel('y (px)')
        cbar = fig1.colorbar(xy, ax = ax1, format='%.0e')
        cbar.ax.set_ylabel('Counts', rotation=270)
        
        xz = ax2.imshow(inverted_xz, cmap = 'gray', aspect = 12.82,  vmin = c_min, vmax = c_max) #aspect = 12.82
        ax2.set_xlabel('x (px)')
        ax2.set_ylabel('z (px)')
        # fig1.colorbar(xz, ax = ax1)
        
    @time_it    
    def show_inverted_xy(self, plane = 'sum'):
        
        if plane == 'sum':
            inverted_xy = np.sum(self.image_denoised, 0)
        else:
            inverted_xy = self.image_denoised[plane,:,:] # to show just one xy plane
        
        fig1=plt.figure()
        fig1.clf()
        fig1.suptitle(f'Inverted image XY projection\n{self.params}')
        ax1=fig1.add_subplot(111)
        xy = ax1.imshow(inverted_xy.transpose(), cmap = 'gray', aspect = 1)
        ax1.set_xlabel('x (px)')
        ax1.set_ylabel('y (px)')
        cbar = fig1.colorbar(xy, ax = ax1, format='%.0e')
        cbar.ax.set_ylabel('Counts', rotation=270)
    
    @time_it
    def show_inverted_xz(self, plane = 'sum', **kwargs):
        
        # if kwargs is not None:
        #     for key, value in kwargs.items():
        #         print( key, '==>', value)
        
        if plane == 'sum':
            inverted_xz = np.sum(self.image_denoised, 2)
        else:
            inverted_xz = self.image_denoised[:,:,plane] # to show just one xz plane
        
        dmdPx_to_sample_ratio = 1.247 # (um/px)
        aspect_xz = (self.ROI_s_z * dmdPx_to_sample_ratio / self.image_denoised.shape[0] )/0.65
        
        # aspect_xz = 0.5
        
        # fig1=plt.figure( figsize = (3, 6) , constrained_layout=True) 
        if __name__ == 'DMD_light_sheet_analysis':
        
            fig1=plt.figure( constrained_layout=False) 
            fig1.clf()
            ax1=fig1.add_subplot(111)
            
        else:
            
            fig1 = kwargs.get('fig')
            ax1 = kwargs.get('ax')
            
            # print(fig1 is None)
            # print(ax1 is None)
        
        
        fig1.suptitle(f'Inverted image XZ projection\n{self.params}')
        
        xz = ax1.imshow(inverted_xz, cmap = 'gray', aspect = aspect_xz, interpolation = 'none') #aspect = 12.82 for 24 z pixels, aspect = 6.6558 for 61 z pixels, aspect = 11.80 for tests in 61px, aspect = 30 for testing in 24 px
        ax1.set_xlabel('x (px)')
        ax1.set_ylabel('z (px)')
        cbar = fig1.colorbar(xz, ax = ax1, shrink=1, format='%.0e')
        cbar.ax.set_ylabel('Counts', rotation=270)
    

    # @time_it
    def save_denoised(self):
        
        try:
            head, tail = os.path.split(self.file_path)
            
            newpath = self.file_path[:-3] + '_ANALYSED'
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            
            if len(self.params["save_label"]) >0:
                fname = os.path.join(newpath, f'volume_{self.params["single_volume_time_index"]}_denoised_{self.params["save_label"]}.h5')
            else:
                fname = os.path.join(newpath, f'volume_{self.params["single_volume_time_index"]}_denoised.h5')
            
            while os.path.exists(fname):
                fname = fname[:-3] + '_bis.h5'
            
            parent = h5py.File(fname,'w')
    
            # create groups
            analysis_parameters = parent.create_group('analysis_parameters') 
            
            for key, val in self.params.items():
                analysis_parameters.attrs[key] = val
     
            # create a dataset
            name = 't000/c000/' + tail[:-3]
            h5dataset = parent.create_dataset(name = name, shape=self.image_denoised.shape, data = self.image_denoised)
            h5dataset.dims[0].label = "z"
            h5dataset.dims[1].label = "y"
            h5dataset.dims[2].label = "x"
            
            self.ROI_s_z = get_h5_attr(self.file_path, 'ROI_s_z')[0]
            dmdPx_to_sample_ratio = 1.247 # (um/px)
            z_sample_period = self.ROI_s_z * dmdPx_to_sample_ratio / self.image_denoised.shape[0] 
            h5dataset.attrs['element_size_um'] =  [z_sample_period,0.65,0.65]


        finally:
            parent.close()
            
            
    def invert_time_lapse(self, **kwargs):
        
        # update any specified parameter
        for key, val in kwargs.items():
            self.params[key] = val
        
        if kwargs.get('progress_bar') is not None:
            progress_bar = kwargs.get('progress_bar')
            progress_bar.setValue(0)
        
        try:
            self.params['time_frames_n'] = get_h5_attr(self.file_path, 'time_frames_n')[0]
            
        except:
            print('>> Warning: Could not find the number of time frames.')
            
        else:
                
            self.tl_stack = []
            
            for time_index in range(self.params['time_frames_n']):
                
                self.load_h5_file(time_index)
                
                if self.select_ROI: self.setROI()
                
                
                if self.params['time_lapse_mode'] == 'sum':
                    self.tl_stack.append(np.sum(self.image_denoised, self.params['time_lapse_view'])) # view z = 0, y = 1, x = 2
                
                elif self.params['time_lapse_view'] == 0:
                    self.tl_stack.append(self.image_denoised[self.params['time_lapse_plane'],:,:])
                elif self.params['time_lapse_view'] == 1:
                    self.tl_stack.append(self.image_denoised[:, self.params['time_lapse_plane'],:])
                elif self.params['time_lapse_view'] == 2:
                    self.tl_stack.append(self.image_denoised[:,:,self.params['time_lapse_plane']])
            
            self.tl_stack = np.array(self.tl_stack)
       
            
        
    def show_time_lapse(self):
            
        pg.image(self.tl_stack, title= f"Inverted Time Lapse (base: {self.params['base']})")        
        
        if self.name == 'DMD_light_sheet_analysis':
            #keeps the window open running a QT application
            if sys.flags.interactive != 1 or not hasattr(qtpy.QtCore, 'PYQT_VERSION'):
                QApplication.exec_()
            sys.exit ( "End of test")
    
    def save_time_lapse(self):
        
        try:
            head, tail = os.path.split(self.file_path)
            
            newpath = self.file_path[:-3] + '_ANALYSED'
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            
            if len(self.params["time_lapse_save_label"]) >0:
                fname = os.path.join(newpath, f'time_lapse_inverted_{self.params["time_lapse_mode"]}_{self.params["time_lapse_save_label"]}.h5')
            else:
                fname = os.path.join(newpath, f'time_lapse_inverted_{self.params["time_lapse_mode"]}.h5')
            
            while os.path.exists(fname):
                fname = fname[:-3] + '_bis.h5'
            
            parent = h5py.File(fname,'w')
    
            # create groups
            analysis_parameters = parent.create_group('analysis_parameters') 
            
            for key, val in self.params.items():
                analysis_parameters.attrs[key] = val
     
            # create a dataset
            name = 't000/c000/' + tail[:-3]
            h5dataset = parent.create_dataset(name = name, shape=self.image_denoised.shape, data = self.image_denoised)
            h5dataset.dims[0].label = "t"
            h5dataset.dims[1].label = "y"
            h5dataset.dims[2].label = "x"
            
            h5dataset.attrs['element_size_um'] =  [1,0.65,0.65]
        
        finally:
            parent.close()

        
        
#%%    
 
if __name__ == "__main__" :
    

        
        file_name = '/Users/marcovitali/Documents/Poli/tesi/ScopeFoundy/coherentSVIM/data/220523_cuma_fluo_test/220523_113202_coherent_SVIM_no_diff_300ul_transp.h5'
        
        
        dataset = DMD_light_sheet_analysis(file_name)
        dataset.load_h5_file()
        
        
            
        