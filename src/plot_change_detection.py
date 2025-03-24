# -*- coding: utf-8 -*-
#
# This script is a python executable computing a change detection algorithm on time series of SAR images.
# Usage: python plot_change_detection.py --result_path [PATH_TO_RESULTS] --output_path [OUTPUT_PATH]
#
# Author: Matthieu Verlynde
# Email: matthieu.verlynde@univ-smb.fr
# Date: 26 Feb 2025
# Version: 1.0.0

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--result_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    args = parser.parse_args()

# Load data
data = pd.read_csv(args.result_path, index_col=None)
if 'Energy (plug)' in data.columns:
    data['Energy total'] = (data['Energy (plug)'])/(3.6*1e6) # Convert to kWh
else:
    data['Energy total'] = (data['Energy (CodeCarbon)'])/(3.6*1e6) # Convert to kWh
energy = 'Energy total'

# replace method values by names
data['Method'] = data['Method'].replace({0: 'G-GLRT', 1: 'NG-GLRT', 2: 'LogDiff'})

# legend_all = ['GLRT5','GLRT7','GLRT21','RobustGLRT5','RobustGLRT7','RobustGLRT21','LogDiff']

# Plot data with error bars
data_grouped = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack() # Group data by 'Number images' and 'Method'
data_grouped[energy].plot(kind='bar', yerr=2*data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()[energy], capsize=5)
plt.ylabel('Energy (kWh)')
plt.xticks(rotation=0)
plt.title('Energy consumption per method')
plt.show()
plt.close()

data_grouped = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack() # Group data by 'Number images' and 'Method'
data_grouped['Duration'].plot(kind='bar', yerr=2*data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()['Duration'], capsize=5)
plt.ylabel('Duration')
plt.xticks(rotation=0)
plt.title('Duration per method')
plt.show()
plt.close()

data_grouped = data.groupby(['Number images','Window size', 'Threads','Method']).mean().unstack()
data_grouped['AUC'].plot(kind='bar', yerr=2*data.groupby(['Number images','Window size', 'Threads', 'Method']).std().unstack()['AUC'], capsize=5)
plt.ylabel('AUC')
plt.xticks(rotation=0)
plt.title('AUC per method')
plt.show()
plt.close()

# Calculate frugality scores
data_grouped = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()

# Normalize energy consumption
data['Energy total norm'] = data['Energy total'] / data['Energy total'].max()

epsilon = 0.5
data['FrugWS'] = (1 - epsilon) * data['AUC'] + epsilon * (1 - data['Energy total norm'])
kappa = 1
data['FrugHM'] = (1 + kappa**2) * (data['AUC'] * (1 - data['Energy total norm']))/(kappa**2*data['AUC'] + (1 - data['Energy total norm']))

# Group data by 'Number images' and 'Method'
data_grouped = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()

# Plot frugality scores
data_grouped['FrugWS'].plot(kind='bar', yerr=2*data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()['FrugWS'], capsize=5)
plt.ylabel('Frugality score')
plt.xticks(rotation=0)
plt.title('Frugality score (WS)')
plt.show()
plt.close()

data_grouped['FrugHM'].plot(kind='bar', yerr=2*data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()['FrugHM'], capsize=5)
plt.ylabel('Frugality score')
plt.xticks(rotation=0)
plt.title('Frugality score (HM)')
plt.show()
plt.close()


frug_ws = []
frug_ws_yerr = []
for epsilon in np.arange(0, 1.1, 0.1):
    data['FrugWS'] = (1 - epsilon) * data['AUC'] + epsilon * (1 - data['Energy total norm'])
    data_grouped = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()
    frug_ws.append(data_grouped['FrugWS'].values.reshape(-1))
    frug_ws_yerr.append(data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()['FrugWS'].values.reshape(-1))

frug_ws = np.array(frug_ws)
frug_ws_yerr = np.array(frug_ws_yerr)
plt.plot(frug_ws)
for i in range(frug_ws.shape[1]):
    plt.fill_between(np.arange(0, 11, 1), frug_ws[:,i] - 2*frug_ws_yerr[:,i], frug_ws[:,i] + 2*frug_ws_yerr[:,i], alpha=0.5)
plt.xticks(np.arange(0, 11, 1), np.arange(0, 11)/10)
plt.ylabel('Frugality score')
plt.xlabel('Epsilon')
plt.title('Frugality score (WS)')
# Make legend with thread number data_grouped.index
legend = []
for i in range(len(data_grouped.columns)):
    
    for j in range(len(data_grouped.index)):
        legend_j = tuple(data_grouped.columns[i]) + data_grouped.index[j]
        legend.append(str(legend_j[1:]))
plt.legend(legend)
plt.savefig(args.output_path + '/frugality_ws.png')
plt.show()
plt.close()

frug_hm = []
frug_hm_yerr = []
for kappa in np.arange(0, 2.2, 0.2):
    data['FrugHM'] = (1 + kappa**2) * (data['AUC'] * (1 - data['Energy total norm']))/(kappa**2*data['AUC'] + (1 - data['Energy total norm']))
    data_grouped = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()
    frug_hm.append(data_grouped['FrugHM'].values.reshape(-1))
    frug_hm_yerr.append(data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()['FrugHM'].values.reshape(-1))

frug_hm = np.array(frug_hm)
frug_hm_yerr = np.array(frug_hm_yerr)
plt.plot(frug_hm)
for i in range(frug_hm.shape[1]):
    plt.fill_between(np.arange(0, 11, 1), frug_hm[:,i] - 2*frug_hm_yerr[:,i], frug_hm[:,i] + 2*frug_hm_yerr[:,i], alpha=0.5)
plt.xticks(np.arange(0, 11, 1), np.arange(0, 22, 2)/10)
plt.ylabel('Frugality score')
plt.xlabel('Kappa')
plt.title('Frugality score (HM)')
# make legend with thread number data_grouped.index
legend = []
for i in range(len(data_grouped.columns)):
    
    for j in range(len(data_grouped.index)):
        legend_j = tuple(data_grouped.columns[i]) + data_grouped.index[j]
        legend.append(str(legend_j[1:]))
plt.legend(legend)
plt.savefig(args.output_path + '/frugality_hm.png')
plt.show()
plt.close()

# data_energy = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()[energy]
# data_energy.to_csv(args.output_path + '/energy.csv', index=False)

# Plot energy consumption and AUC in a table

data_energy = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()[energy]*1000
data_auc = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()['AUC']
data_energy_auc = pd.concat([data_energy, data_auc], axis=1).astype(str)
data_energy_auc_error = pd.concat([
    2*data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()[energy]*1000, 
    2*data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()['AUC']], 
    axis=1)
data_energy_auc.columns = ['Energy (Wh)', 'AUC']
for i in range(len(data_energy_auc.columns)):
    for j in range(len(data_energy_auc.index)):
        data_energy_auc.iloc[j,i] = '{:.3f} ± {:.3f}'.format(float(data_energy_auc.iloc[j,i]), float(data_energy_auc_error.iloc[j,i]))
data_energy_auc.to_csv(args.output_path + '/energy_auc.csv', index=True)



frug_fs = []
frug_fs_yerr = []
for w in np.arange(0, 1.1, 0.1):
    data['FrugFS'] = data['AUC'] - w/(1 + 1/(data['Energy total']*1000*3600)) # Convert energy to J
    data_grouped = data.groupby(['Method','Number images','Window size', 'Threads']).mean().unstack()
    frug_fs.append(data_grouped['FrugFS'].values.reshape(-1))
    frug_fs_yerr.append(data.groupby(['Method','Number images','Window size', 'Threads']).std().unstack()['FrugFS'].values.reshape(-1))

frug_fs = np.array(frug_fs)
frug_fs_yerr = np.array(frug_fs_yerr)
plt.plot(frug_fs)
for i in range(frug_fs.shape[1]):
    plt.fill_between(np.arange(0, 11, 1), frug_fs[:,i] - 2*frug_fs_yerr[:,i], frug_fs[:,i] + 2*frug_fs_yerr[:,i], alpha=0.5)
# plt.xticks(np.arange(0, 11, 1), np.arange(0, 11, 1)/10)
# plt.ylabel('Frugality score')
# plt.xlabel('W')
# plt.title('Frugality score (FS)')

# legend = []
# threads = np.unique([x[1] for x in data_grouped.columns])
# groups = len(data_grouped.columns)//len(data_grouped.index)
# for i in range(len(threads)):
#     for j in range(len(data_grouped.index)):
#         print(data_grouped.index[j])
#         legend_j = tuple([threads[i]]) + data_grouped.index[j]
#         legend.append(str(legend_j))
# plt.legend(legend)
# plt.savefig(args.output_path + '/frugality_fs.png')
# plt.show()
# plt.close()

plt.xticks(np.arange(0, 11, 1), np.arange(0, 22, 2)/10)
plt.ylabel('Frugality score')
plt.xlabel('X')
plt.title('Frugality score (FS)')
# make legend with thread number data_grouped.index
legend = []
for i in range(len(data_grouped.columns)):
    for j in range(len(data_grouped.index)):
        legend_j = tuple(data_grouped.columns[i]) + data_grouped.index[j]
        legend.append(str(legend_j[1:]))
plt.legend(legend)
plt.savefig(args.output_path + '/frugality_fs.png')
plt.show()
plt.close()

# frug_ws = pd.DataFrame(frug_ws, columns=legend)
# frug_hm = pd.DataFrame(frug_hm, columns=legend)
# frug_fs = pd.DataFrame(frug_fs, columns=legend)

# frug_ws.to_csv(args.output_path + '/frugality_ws.csv', index=False)
# frug_hm.to_csv(args.output_path + '/frugality_hm.csv', index=False)
# frug_fs.to_csv(args.output_path + '/frugality_fs.csv', index=False)

# frug_ws_yerr = pd.DataFrame(frug_ws_yerr, columns=legend)
# frug_hm_yerr = pd.DataFrame(frug_hm_yerr, columns=legend)
# frug_fs_yerr = pd.DataFrame(frug_fs_yerr, columns=legend)

# frug_ws_yerr.to_csv(args.output_path + '/frugality_ws_yerr.csv', index=False)
# frug_hm_yerr.to_csv(args.output_path + '/frugality_hm_yerr.csv', index=False)
# frug_fs_yerr.to_csv(args.output_path + '/frugality_fs_yerr.csv', index=False)