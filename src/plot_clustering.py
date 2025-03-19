# -*- coding: utf-8 -*-
#
# This script is a python executable computing a change detection algorithm on time series of SAR images.
# Usage: python plot_clustering.py --result_path [PATH_TO_RESULTS] --output_path [OUTPUT_PATH]
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

    data['CPU'] = data['CPU']/data['Repeat']
    data['Duration'] = data['Duration']/data['Repeat']
    data['Energy (plug)'] = data['Energy (plug)']/data['Repeat']
    data['Energy (CodeCarbon)'] = data['Energy (CodeCarbon)']/data['Repeat']
    data['Temperature'] = data['Temperature']/data['Repeat']
    data['Reads'] = data['Reads']/data['Repeat']
    data['Emissions'] = data['Emissions']/data['Repeat']

    data['Adjusted Rand Index norm'] = (data['Adjusted Rand Index']-(0))/(1-(0))
    data['Energy total'] = (data['Energy (plug)'])/(3.6*1e6) # Convert to kWh

    energy = 'Energy total'
    legend_all = ['Agglomerative Clustering', 'Ward', 'DBSCAN', 'HDBSCAN', 'OPTICS', 'GMM', 'K-Means', 'K-Means++']

    data=data.where(data['CPU'].isna() == False)

    # Plot data with error bars
    data_grouped = data.groupby(['Model']).mean().unstack() # Group data by 'Number images' and 'Model'
    data_grouped[energy].plot(kind='bar', yerr=2*data.groupby(['Model']).std().unstack()[energy], capsize=5)
    plt.ylabel('Energy (kWh)')
    plt.xticks(rotation=0)
    plt.title('Energy consumption per model')
    plt.show()

    data_grouped = data.groupby(['Model']).mean().unstack() # Group data by 'Number images' and 'Model'
    data_grouped['Duration'].plot(kind='bar', yerr=2*data.groupby(['Model']).std().unstack()['Duration'], capsize=5)
    plt.ylabel('Duration')
    plt.xticks(rotation=0)
    plt.title('Duration per model')
    plt.show()

    data_grouped['Adjusted Rand Index'].plot(kind='bar', yerr=2*data.groupby(['Model']).std().unstack()['Adjusted Rand Index'], capsize=5)
    plt.ylabel('Adjusted Rand Index')
    plt.xticks(rotation=0)
    plt.title('Adjusted Rand Index per model')
    plt.show()

    # Calculate frugality scores

    # Normalize energy consumption
    data['Energy total norm'] = (data['Energy total'] - data['Energy total'].min())  /  (data['Energy total'].max() - data['Energy total'].min())
    data_grouped = data.groupby(['Model']).mean().unstack() 
    data_grouped['Energy total norm'].plot(kind='bar', yerr=2*data.groupby(['Model']).std().unstack()['Energy total norm'], capsize=5)
    plt.ylabel('Energy')
    plt.xticks(rotation=0)
    plt.title('Normalized energy consumption per model')
    plt.show()

    data_energy = data.groupby(['Model']).min().unstack()['Adjusted Rand Index']
    data_energy.to_csv(args.output_path + '/energy.csv', index=False)

    epsilon = 0.5
    data['FrugWS'] = (1 - epsilon) * data['Adjusted Rand Index norm'] + epsilon * (1 - data['Energy total norm'])
    kappa = 1
    data['FrugHM'] = (1 + kappa**2) * (data['Adjusted Rand Index norm'] * (1 - data['Energy total norm']))/(kappa**2*data['Adjusted Rand Index norm'] + (1 - data['Energy total norm']))

    # Group data by 'Number images' and 'Model'
    data_grouped = data.groupby(['Model']).mean().unstack()

    # Plot frugality scores
    data_grouped['FrugWS'].plot(kind='bar', yerr=2*data.groupby(['Model']).std().unstack()['FrugWS'], capsize=5)
    plt.ylabel('Frugality score')
    plt.xticks(rotation=0)
    plt.title('Frugality score (WS)')
    plt.show()

    data_grouped['FrugHM'].plot(kind='bar', yerr=2*data.groupby(['Model']).std().unstack()['FrugHM'], capsize=5)
    plt.ylabel('Frugality score')
    plt.xticks(rotation=0)
    plt.title('Frugality score (HM)')
    plt.show()


    frug_ws = []
    frug_ws_yerr = []
    for epsilon in np.arange(0, 1.1, 0.1):
        data['FrugWS'] = (1 - epsilon) * data['Adjusted Rand Index norm'] + epsilon *  (1 - data['Energy total norm'])
        data_grouped = data.groupby(['Model']).mean().unstack()
        frug_ws.append(data_grouped['FrugWS'].values.reshape(-1))
        frug_ws_yerr.append(data.groupby(['Model']).std().unstack()['FrugWS'].values.reshape(-1))

    legend = [x for x in data_grouped['CPU'].index]

    frug_ws = np.array(frug_ws)
    frug_ws_yerr = np.array(frug_ws_yerr)
    plt.plot(frug_ws)
    for i in range(frug_ws.shape[1]):
        plt.fill_between(np.arange(0, 11, 1), frug_ws[:,i] - 2*frug_ws_yerr[:,i], frug_ws[:,i] + 2*frug_ws_yerr[:,i], alpha=0.5)
    plt.xticks(np.arange(0, 11), np.arange(0, 11)/10)
    plt.ylabel('Frugality score')
    plt.xlabel('Epsilon')
    plt.title('Frugality score (WS)')
    plt.legend(legend_all)
    plt.show()

    frug_hm = []
    frug_hm_yerr = []
    for kappa in np.arange(0, 4.4, 0.4):
        data['FrugHM'] = (1 + kappa**2) * (data['Adjusted Rand Index norm'] * (1 - data['Energy total norm']))/(kappa**2*data['Adjusted Rand Index norm'] + (1 - data['Energy total norm']))
        data_grouped = data.groupby(['Model']).mean().unstack()
        frug_hm.append(data_grouped['FrugHM'].values.reshape(-1))
        frug_hm_yerr.append(data.groupby(['Model']).std().unstack()['FrugHM'].values.reshape(-1))

    frug_hm = np.array(frug_hm)
    frug_hm_yerr = np.array(frug_hm_yerr)
    plt.plot(frug_hm)
    for i in range(frug_hm.shape[1]):
        plt.fill_between(np.arange(0, 11, 1), frug_hm[:,i] - 2*frug_hm_yerr[:,i], frug_hm[:,i] + 2*frug_hm_yerr[:,i], alpha=0.5)
    plt.xticks(np.arange(0, 11, 1), np.arange(0, 22, 2)/10)
    plt.ylabel('Frugality score')
    plt.xlabel('Kappa')
    plt.title('Frugality score (HM)')

    # Make legend with thread number data_grouped.index
    plt.legend(legend_all)
    plt.show()


    frug_fs = []
    frug_fs_yerr = []
    for w in np.arange(0, 1.1, 0.1):
        data['FrugFS'] = data['Adjusted Rand Index'] - w/(1 + 1/(data['Energy total']*1000*3600))
        data_grouped = data.groupby(['Model']).mean().unstack()
        frug_fs.append(data_grouped['FrugFS'].values.reshape(-1))
        frug_fs_yerr.append(data.groupby(['Model']).std().unstack()['FrugFS'].values.reshape(-1))

    frug_fs = np.array(frug_fs)
    frug_fs_yerr = np.array(frug_fs_yerr)
    plt.plot(frug_fs)
    # Add y error bars
    for i in range(frug_fs.shape[1]):
        plt.fill_between(np.arange(0, 11, 1), frug_fs[:,i] - 2*frug_fs_yerr[:,i], frug_fs[:,i] + 2*frug_fs_yerr[:,i], alpha=0.5)
    plt.xticks(np.arange(0, 11, 1), np.arange(0, 11, 1)/10)
    plt.ylabel('Frugality score')
    plt.xlabel('W')
    plt.title('Frugality score (FS)')
    # Make legend with thread number data_grouped.index
    plt.legend(legend_all)
    plt.show()

    frug_ws = pd.DataFrame(frug_ws, columns=legend)[['AgglomerativeClustering', 'Ward', 'DBSCAN', 'HDBSCAN', 'OPTICS', 'GMM', 'k-means', 'k-means++']]
    frug_hm = pd.DataFrame(frug_hm, columns=legend)[['AgglomerativeClustering', 'Ward', 'DBSCAN', 'HDBSCAN', 'OPTICS', 'GMM', 'k-means', 'k-means++']]
    frug_fs = pd.DataFrame(frug_fs, columns=legend)[['AgglomerativeClustering', 'Ward', 'DBSCAN', 'HDBSCAN', 'OPTICS', 'GMM', 'k-means', 'k-means++']]

    frug_ws.to_csv(args.output_path + '/frugality_ws.csv', index=False)
    frug_hm.to_csv(args.output_path + '/frugality_hm.csv', index=False)
    frug_fs.to_csv(args.output_path + '/frugality_fs.csv', index=False)

    frug_ws_yerr = pd.DataFrame(frug_ws_yerr, columns=legend)[['AgglomerativeClustering', 'Ward', 'DBSCAN', 'HDBSCAN', 'OPTICS', 'GMM', 'k-means', 'k-means++']]
    frug_hm_yerr = pd.DataFrame(frug_hm_yerr, columns=legend)[['AgglomerativeClustering', 'Ward', 'DBSCAN', 'HDBSCAN', 'OPTICS', 'GMM', 'k-means', 'k-means++']]
    frug_fs_yerr = pd.DataFrame(frug_fs_yerr, columns=legend)[['AgglomerativeClustering', 'Ward', 'DBSCAN', 'HDBSCAN', 'OPTICS', 'GMM', 'k-means', 'k-means++']]

    frug_ws_yerr.to_csv(args.output_path + '/frugality_ws_yerr.csv', index=False)
    frug_hm_yerr.to_csv(args.output_path + '/frugality_hm_yerr.csv', index=False)
    frug_fs_yerr.to_csv(args.output_path + '/frugality_fs_yerr.csv', index=False)

    pd.concat([frug_ws, frug_ws_yerr], axis=1).to_csv(args.output_path + '/frugality_ws_tot.csv', index=False)
    pd.concat([frug_hm, frug_hm_yerr], axis=1).to_csv(args.output_path + '/frugality_hm_tot.csv', index=False)
    pd.concat([frug_fs, frug_fs_yerr], axis=1).to_csv(args.output_path + '/frugality_fs_tot.csv', index=False)

    print('Done!')