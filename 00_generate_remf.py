#!/homes/abie/.conda/envs/pyomo_env/bin/python
#SBATCH -t 24:00:00
#SBATCH --mem=64G
#SBATCH -c 1
#SBATCH -A proj_csu
#SBATCH -p all.q
#SBATCH -o /share/scratch/users/abie/projects/2022/remf_august_dhc/output.txt

import sys

file_path = '/share/scratch/users/abie/projects/2022/remf_august_dhc'

n_splits = int(sys.argv[1])
i_split = int(sys.argv[2])

print('running 00_generate_remf.py with', n_splits, 'splits.')
print('processing part', i_split, flush=True)

import numpy as np, pandas as pd
import linked_census_disclosure.data as lcd_data
import linked_census_disclosure.model as lcd_model

np.random.seed(12345)

dhc_tables = lcd_data.load_dhc_tables('tx', 48)
sf1_tables = lcd_data.load_sf1_tables('tx', 48)

t = dhc_tables['P1'].set_index(
    ['STATE', 'COUNTY', 'TRACT', 'BLOCK']).P10001.sort_values(
    ascending=False    
)
rows = t[t>0].index

t = sf1_tables['P1'].set_index(
    ['STATE', 'COUNTY', 'TRACT', 'BLOCK']).P10001.sort_values(
    ascending=False
)
rows = rows.append(t[t>0].index).drop_duplicates()

results_dhc = {}
for i, location_tuple in enumerate(rows[i_split::n_splits]):
    if i % 60 == 0:
        print('.', end=' ', flush=True)
    results_dhc[location_tuple] = lcd_model.reconstruct_block(dhc_tables, *location_tuple)

pd.concat(results_dhc).to_csv(f'{file_path}/dhc_{n_splits}_{i_split}.csv.gz')

results_sf1 = {}


for i, location_tuple in enumerate(rows[i_split::n_splits]):
    if i % 60 == 0:
        print('.', end=' ', flush=True)
    results_sf1[location_tuple] = lcd_model.reconstruct_block(sf1_tables, *location_tuple)

pd.concat(results_sf1).to_csv(f'{file_path}/sf1_{n_splits}_{i_split}.csv.gz')
