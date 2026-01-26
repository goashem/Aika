#!/usr/bin/env python3
"""
Debug script to examine actual SILAM pollen data values
"""

import xarray as xr
import numpy as np

def examine_pollen_data():
    print("Examining SILAM pollen data values...")
    
    # Access the dataset
    url = 'https://thredds.silam.fmi.fi/thredds/dodsC/silam_regional_pollen_v5_9_1/files/SILAM-POLLEN-regional_v5_9_1_2026012600.nc4'
    
    try:
        print(f"Accessing: {url}")
        ds = xr.open_dataset(url, decode_times=False)
        print("Dataset opened successfully!")
        
        # Check time dimension
        print(f"Time steps available: {len(ds.time)}")
        print(f"Time range: {ds.time.values[0]} to {ds.time.values[-1]}")
        
        # Examine a sample of the data at different time steps
        for time_idx in [0, 12, 24, -1]:  # First, middle, and last time steps
            try:
                print(f"\n--- Time step {time_idx} ---")
                # Extract data at a sample grid point (representing Finland)
                sample_rlat, sample_rlon = 400, 375  # Approximate for central Finland
                
                birch_val = ds['cnc_POLLEN_BIRCH_m22'].isel(time=time_idx, height=0, rlat=sample_rlat, rlon=sample_rlon).values
                grass_val = ds['cnc_POLLEN_GRASS_m32'].isel(time=time_idx, height=0, rlat=sample_rlat, rlon=sample_rlon).values
                alder_val = ds['cnc_POLLEN_ALDER_m22'].isel(time=time_idx, height=0, rlat=sample_rlat, rlon=sample_rlon).values
                
                print(f"Birch concentration: {birch_val}")
                print(f"Grass concentration: {grass_val}")
                print(f"Alder concentration: {alder_val}")
                
                # Convert to our 0-5 scale
                def concentration_to_level(concentration):
                    if concentration <= 0:
                        return 0
                    elif concentration <= 10:
                        return 1
                    elif concentration <= 50:
                        return 2
                    elif concentration <= 200:
                        return 3
                    elif concentration <= 1000:
                        return 4
                    else:
                        return 5
                
                print(f"Birch level (0-5): {concentration_to_level(birch_val)}")
                print(f"Grass level (0-5): {concentration_to_level(grass_val)}")
                print(f"Alder level (0-5): {concentration_to_level(alder_val)}")
                
            except Exception as e:
                print(f"Error at time step {time_idx}: {e}")
        
        ds.close()
        
    except Exception as e:
        print(f"Failed to access dataset: {e}")

if __name__ == "__main__":
    examine_pollen_data()