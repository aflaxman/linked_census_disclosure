""" Methods for data ETL for linked census disclosure experiment"""

import glob

import numpy as np
import pandas as pd

def load_sf1_tables(state_abbr, state):
    """Load all the tables from the SF1 data product from disk
    
    Parameters
    ----------
    state_abbr : str, two-letter abbreviation in lower case
    state : int, FIPS code

    Results
    -------
    returns dict of DataFrames
    """

    file_path = '/share/scratch/users/abie/projects/2022/sf1'

    col_names = ('FILEID,STUSAB,SUMLEV,GEOCOMP,CHARITER,'
                 'CIFSN,LOGRECNO,'
                 'REGION,DIVISION,STATE,'
                 'COUNTY,COUNTYCC,COUNTYSC,COUSUB,COUSUBCC,COUSUBSC,'
                 'PLACE,PLACECC,PLACESC,'
                 'TRACT,BLKGRP,BLOCK'
             ).split(',')
             
    widths = [6,2,3,2,3,
              2,7,
              1,1,2,
              3,2,2,5,2,2,
              5,2,2,
              6,1,4
          ]
    df_geo = pd.read_fwf(f'{file_path}/{state_abbr}geo2010.sf1',
                         header=None,
                         names=col_names,
                         widths=widths,
                         encoding='latin1'
                     )

    df_segments = pd.read_csv(f'{file_path}/table_segments_2010_sf1.csv')
    def load_sf1_segment(seg : int):
        """Load a 'segment' of SF1 data

        Note to self: I only mapped a few of the SF1 tables
        in my table_segments csv.  I think I got what I need, though.

        Implemented as a function within a function to avoid annoying
        passing of config parameters.

        Parameters
        ----------
        seg : int, the segment to use, i in {1, ..., 5}

        Results
        -------
        add some pd.DataFrames to table_dict

        """

        print('Loading segment', seg)
        df_seg = pd.read_csv(f'{file_path}/{state_abbr}{seg:05d}2010.sf1',
                             sep=',',
                             header=None,
                             low_memory=False,
                         )
        col_start = 5  # first five columns are 'FILEID', 'STUSAB', 'CHARITER', 'CIFSN', 'LOGRECNO'

        for i in df_segments[df_segments.SEGMENT_NUMBER==seg].index: # NOTE: df_segments is also global here
            table_id = df_segments.loc[i, 'TABLE_ID']
            total_records = df_segments.loc[i, 'TOTAL_RECORDS']
            print('Extracting table', table_id)

            # move specific columns into the table_dict for this table_id
            table_dict[table_id] = df_seg.iloc[:, col_start:(col_start+total_records)]
            # set the column names to match the DHC Table Matrix https://www2.census.gov/programs-surveys/decennial/2020/program-management/data-product-planning/2010-demonstration-data-products/02-Demographic_and_Housing_Characteristics/2022-08-25_Summary_File/2022-08-25_Technical%20Document/20220825_2010%20Demonstration%20Data%20Product%20-DHC_Table%20Matrix.xlsx
            table_dict[table_id].columns = [f'{table_id}{i+1:04d}' for i in range(total_records)]

            # merge in the geographic identifiers
            table_dict[table_id] = pd.merge(df_geo.filter(['STATE', 'COUNTY', 'TRACT', 'BLOCK']),
                                            table_dict[table_id], left_index=True, right_index=True)
            # keep only the rows for block-level values (will this drop everything for certain tables? revisit if it does...)
            table_dict[table_id] = table_dict[table_id].dropna()

            # advance col_start to be ready for next table
            col_start += total_records
        print()


    # I'm going to load each table into this table dictionary
    # I'll initialize it here to keep things simple, if inelegant
    table_dict = {}


    for i in range(8):
        load_sf1_segment(i+1)

    return table_dict


def load_dhc_tables(state_abbr, state):
    """Load all the tables from the DHC data product from disk
    
    Parameters
    ----------
    state_abbr : str, two-letter abbreviation in lower case
    state : int, FIPS code

    Results
    -------
    returns dict of DataFrames
    """
    # I extracted the column names from the SAS example code https://www2.census.gov/programs-surveys/decennial/2020/program-management/data-product-planning/2010-demonstration-data-products/02-Demographic_and_Housing_Characteristics/2022-03-16_Summary_File/2022-03-16_Technical%20Document/2010_demo_dhc_per.zip

    col_names = 'FILEID,STUSAB,SUMLEV,GEOVAR,GEOCOMP,CHARITER,CIFSN,LOGRECNO,GEOID,GEOCODE,REGION,DIVISION,STATE,STATENS,COUNTY,COUNTYCC,COUNTYNS,COUSUB,COUSUBCC,COUSUBNS,SUBMCD,SUBMCDCC,SUBMCDNS,ESTATEFP,ESTATECC,ESTATENS,CONCIT,CONCITCC,CONCITNS,PLACE,PLACECC,PLACENS,TRACT,BLKGRP,BLOCK,AIANHH,AIHHTLI,AIANHHFP,AIANHHCC,AIANHHNS,AITS,AITSFP,AITSCC,AITSNS,TTRACT,BTBG,ANRC,ANRCCC,ANRCNS,CBSA,MEMI,CSA,METDIV,NECTA,NMEMI,CNECTA,NECTADIV,CBSAPCI,NECTAPCI,UA,UATYPE,UR,CD111,CD113,CD114,CD115,CD116,SLDU11,SLDU12,SLDU14,SLDU16,SLDU18,SLDL11,SLDL12,SLDL14,SLDL16,SLDL18,VTD,VTDI,ZCTA,SDELM,SDSEC,SDUNI,PUMA,AREALAND,AREAWATR,BASENAME,NAME,FUNCSTAT,GCUNI,POP100,HU100,INTPTLAT,INTPTLON,LSADC,PARTFLAG,UGA'.split(',')

    file_path = '/share/scratch/users/abie/projects/2022/dhc_08_2022'
    df_geo = pd.read_csv(f'{file_path}/{state_abbr}geo2010.dhc',
                         sep='|',
                         header=None,
                         names=col_names,
                         low_memory=False,
                         encoding='latin1'
                     )

    df_segments = pd.read_csv(f'{file_path}/table_segments_2010_demo_per.csv')

    def load_dhc_segment(seg : int):
        """Load a 'segment' of DHC data

        Implemented as a function within a function to avoid annoyance
        of passing lots of config data

        Parameters
        ----------
        seg : int, the segment to use, i in {1, ..., 20}

        Results
        -------
        add some pd.DataFrames to table_dict

        """
        print('Loading segment', seg)
        df_seg = pd.read_csv(f'{file_path}/{state_abbr}{seg:05d}2010.dhc',
                             sep='|',
                             header=None,
                             low_memory=False,
                            )
        col_start = 5  # I'm not sure what is in the first 5 columns, but they don't seem important

        for i in df_segments[df_segments.SEGMENT_NUMBER==seg].index: # NOTE: df_segments is also global here
            table_id = df_segments.loc[i, 'TABLE_ID']
            total_records = df_segments.loc[i, 'TOTAL_RECORDS']
            print('Extracting table', table_id)

            # move specific columns into the table_dict for this table_id
            table_dict[table_id] = df_seg.iloc[:, col_start:(col_start+total_records)]
            # set the column names to match the DHC Table Shell https://www2.census.gov/programs-surveys/decennial/2020/program-management/data-product-planning/2010-demonstration-data-products/02-Demographic_and_Housing_Characteristics/2022-03-16_Summary_File/2022-03-16_Technical%20Document/2010_Demonstration_Data_Product-DHC_Table_Shells_person_file.xlsx (on the Table_Segments tab)
            table_dict[table_id].columns = [f'{table_id}{i+1:04d}' for i in range(total_records)]

            # merge in the geographic identifiers
            table_dict[table_id] = pd.merge(df_geo.filter(['STATE', 'COUNTY', 'TRACT', 'BLOCK']),
                                            table_dict[table_id], left_index=True, right_index=True)
            # keep only the rows for block-level values (will this drop everything for certain tables? revisit if it does...)
            table_dict[table_id] = table_dict[table_id].dropna()

            # advance col_start to be ready for next table
            col_start += total_records
        print()



    table_dict = {}

    for i in range(20):
        load_dhc_segment(i+1)

    return table_dict


def read_synth_data(state_abbr : str) -> pd.DataFrame:
    """ load pd.DataFrame of synthetic population for given state

    Parameters
    ----------
    state_abbr : str, two-letters, e.g. 'tx'

    Note: not all state work currently
    """
    # next line only works within IHME, email Abie to get access outside (it is in his decennial_census_synthetic_data Dropbox file)
    df_synth = pd.read_csv(f'/share/scratch/users/abie/projects/2021/das_files/{state_abbr}_synth.csv')

    # some parts of the simulation will be easier if each household id was unique
    # to accomplish this, I will merge in the geoid

    df_synth['hh_id'] = df_synth.geoid.astype(str) + '-' + df_synth.hh_id.astype(int).astype(str)

    return df_synth


def read_dhc_remf(state_abbr):
    assert state_abbr == 'tx'

    file_path = '/share/scratch/users/abie/projects/2022/remf_august_dhc/'

    dhc = []
    for fname in glob.glob(f'{file_path}/dhc*.csv.gz'):
        df = pd.read_csv(fname)
        dhc.append(df)
    dhc = pd.concat(dhc)

    column_names = ['state', 'county', 'tract', 'block', 'row_num', 'age', 'sex', 'race', 'eth', 'n']
    dhc.columns = column_names
    return dhc


def read_sf1_remf(state_abbr):
    assert state_abbr == 'tx'

    file_path = '/share/scratch/users/abie/projects/2022/remf_august_dhc/'

    sf1 = []
    for fname in glob.glob(f'{file_path}/sf1*.csv.gz'):
        df = pd.read_csv(fname)
        sf1.append(df)
    sf1 = pd.concat(sf1)

    column_names = ['state', 'county', 'tract', 'block', 'row_num', 'age', 'sex', 'race', 'eth', 'n']
    sf1.columns = column_names
    return sf1

# mapping dictionary to collapse ages into age-groups published in
# P12 series of SF1 tables
p12_age_group_map = {
    0:0,
    1:0,
    2:0,
    3:0,
    4:0,
    5:1,
    6:1,
    7:1,
    8:1,
    9:1,
    10:2,
    11:2,
    12:2,
    13:2,
    14:2,
    15:3,
    16:3,
    17:3,
    18:4,
    19:4,
}


# functions to simulate introduction of aggregation error by
# tabulating key SF1 tables and then reconstructing from them (for
# each census block)

def add_geo_columns(df, state, county, tract, block):
    df['STATE'] = state
    df['COUNTY'] = county
    df['TRACT'] = tract
    df['BLOCK'] = block


def add_race_cols(df):
    white_alone_or_in_combination = [0, 6, 7, 8, 9, 10, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    black_alone_or_in_combination = [1, 6, 11, 12, 13, 14, 21, 22, 23, 24, 31, 32, 33, 34, 35, 36]
    aian_alone_or_in_combination = [2, 7, 11, 15, 16, 17, 21, 25, 26, 27, 31, 32, 33, 37, 38, 39]
    asn_alone_or_in_combination = [3, 8, 12, 15, 18, 19, 22, 25, 28, 29, 31, 34, 35, 37, 40]
    nhpi_alone_or_in_combination = [4, 9, 13, 16, 18, 20, 23, 26, 28, 30, 32, 34, 36, 38, 40]
    sor_alone_or_in_combination = [5, 10, 14, 17, 19, 20, 24, 27, 29, 30, 33, 35, 36, 39, 40]
    
    df['racwht'] = df.race.isin(white_alone_or_in_combination).astype(int)
    df['racblk'] = df.race.isin(black_alone_or_in_combination).astype(int)
    df['racaian'] = df.race.isin(aian_alone_or_in_combination).astype(int)
    df['racasn'] = df.race.isin(asn_alone_or_in_combination).astype(int)
    df['racnhpi'] = df.race.isin(nhpi_alone_or_in_combination).astype(int)
    df['racsor'] = df.race.isin(sor_alone_or_in_combination).astype(int)

    return df


def make_sf1_tables(df):
    t = {}
    t['P8'] = pd.DataFrame({
	'P80001': [len(df)], # total population
	'P80003': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0'))],  # White alone
	'P80004': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0'))],  # Black or African American alone
	'P80005': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P80006': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P80007': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P80008': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P80011': [np.sum(df.eval('racwht == 1 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P80012': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P80013': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P80014': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P80015': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P80016': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P80017': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P80018': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P80019': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P80020': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P80021': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P80022': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P80023': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P80024': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P80025': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P80027': [np.sum(df.eval('racwht == 1 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P80028': [np.sum(df.eval('racwht == 1 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P80029': [np.sum(df.eval('racwht == 1 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P80030': [np.sum(df.eval('racwht == 1 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P80031': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P80032': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P80033': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P80034': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P80035': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P80036': [np.sum(df.eval('racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P80037': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P80038': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P80039': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P80040': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P80041': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P80042': [np.sum(df.eval('racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P80043': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P80044': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P80045': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P80046': [np.sum(df.eval('racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 1'))],
    })
    t['P9'] = pd.DataFrame({
	'P90005': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0'))],  # White alone
	'P90006': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0'))],  # Black or African American alone
	'P90007': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P90008': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P90009': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P90010': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P90013': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P90014': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P90015': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P90016': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P90017': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P90018': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P90019': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P90020': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P90021': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P90022': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P90023': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P90024': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P90025': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P90026': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P90027': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P90029': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0'))],
	'P90030': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P90031': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P90032': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P90033': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P90034': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P90035': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P90036': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P90037': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P90038': [np.sum(df.eval('hispanic == 0 and racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P90039': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 0'))],
	'P90040': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 0'))],
	'P90041': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 1'))],
	'P90042': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P90043': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P90044': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P90045': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 1 and racsor == 0'))],
	'P90046': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 1 and racasn == 1 and racnhpi == 0 and racsor == 1'))],
	'P90047': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 1 and racsor == 1'))],
	'P90048': [np.sum(df.eval('hispanic == 0 and racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 1 and racsor == 1'))],
    })
    t['P11'] = pd.DataFrame({
	f'P11{i:04d}': [0] for i in range(50) # no one over 18 in this data
    })

    # add P12 tables
    def add_p12_series(name, race_query):
        race_query += ' and '  # HACK: make this query appendable
        t[name] = pd.DataFrame({
	    f'{name}0003': [np.sum(df.eval(race_query + 'age >= 0 and age <= 4 and sex_id == 1'))],
	    f'{name}0004': [np.sum(df.eval(race_query + 'age >= 5 and age <= 9 and sex_id == 1'))],
	    f'{name}0005': [np.sum(df.eval(race_query + 'age >= 10 and age <= 14 and sex_id == 1'))],
	    f'{name}0006': [np.sum(df.eval(race_query + 'age >= 15 and age <= 17 and sex_id == 1'))],
	    f'{name}0027': [np.sum(df.eval(race_query + 'age >= 0 and age <= 4 and sex_id == 2'))],
	    f'{name}0028': [np.sum(df.eval(race_query + 'age >= 5 and age <= 9 and sex_id == 2'))],
	    f'{name}0029': [np.sum(df.eval(race_query + 'age >= 10 and age <= 14 and sex_id == 2'))],
	    f'{name}0030': [np.sum(df.eval(race_query + 'age >= 15 and age <= 17 and sex_id == 2'))],
        })

    # P12A: SEX BY AGE FOR SELECTED AGE CATEGORIES (WHITE ALONE) [49]
    add_p12_series('P12A', race_query='racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0')
    add_p12_series('P12B', race_query='racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0')
    add_p12_series('P12C', race_query='racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0')
    add_p12_series('P12D', race_query='racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0')
    add_p12_series('P12E', race_query='racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0')
    add_p12_series('P12F', race_query='racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1')
    # P12U: SEX BY AGE FOR SELECTED AGE CATEGORIES (SOME OTHER RACE ALONE, HISPANIC OR LATINO) [49]
    add_p12_series('P12U', race_query='racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1 and hispanic == 1')
    add_p12_series('P12H', race_query='hispanic == 1')
    add_p12_series('P12I', race_query='racwht == 1 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0 and hispanic == 0')
    add_p12_series('P12J', race_query='racwht == 0 and racblk == 1 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 0 and hispanic == 0')
    add_p12_series('P12K', race_query='racwht == 0 and racblk == 0 and racaian == 1 and racasn == 0 and racnhpi == 0 and racsor == 0 and hispanic == 0')
    add_p12_series('P12L', race_query='racwht == 0 and racblk == 0 and racaian == 0 and racasn == 1 and racnhpi == 0 and racsor == 0 and hispanic == 0')
    add_p12_series('P12M', race_query='racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 1 and racsor == 0 and hispanic == 0')
    add_p12_series('P12N', race_query='racwht == 0 and racblk == 0 and racaian == 0 and racasn == 0 and racnhpi == 0 and racsor == 1 and hispanic == 0')


    t['P14'] = pd.DataFrame({
	'P140003': [np.sum(df.eval('sex_id == 1 and age == 0'))],
	'P140004': [np.sum(df.eval('sex_id == 1 and age == 1'))],
	'P140005': [np.sum(df.eval('sex_id == 1 and age == 2'))],
	'P140006': [np.sum(df.eval('sex_id == 1 and age == 3'))],
	'P140007': [np.sum(df.eval('sex_id == 1 and age == 4'))],
	'P140008': [np.sum(df.eval('sex_id == 1 and age == 5'))],
	'P140009': [np.sum(df.eval('sex_id == 1 and age == 6'))],
	'P140010': [np.sum(df.eval('sex_id == 1 and age == 7'))],
	'P140011': [np.sum(df.eval('sex_id == 1 and age == 8'))],
	'P140012': [np.sum(df.eval('sex_id == 1 and age == 9'))],
	'P140013': [np.sum(df.eval('sex_id == 1 and age == 10'))],
	'P140014': [np.sum(df.eval('sex_id == 1 and age == 11'))],
	'P140015': [np.sum(df.eval('sex_id == 1 and age == 12'))],
	'P140016': [np.sum(df.eval('sex_id == 1 and age == 13'))],
	'P140017': [np.sum(df.eval('sex_id == 1 and age == 14'))],
	'P140018': [np.sum(df.eval('sex_id == 1 and age == 15'))],
	'P140019': [np.sum(df.eval('sex_id == 1 and age == 16'))],
	'P140020': [np.sum(df.eval('sex_id == 1 and age == 17'))],
	'P140024': [np.sum(df.eval('sex_id == 2 and age == 0'))],
	'P140025': [np.sum(df.eval('sex_id == 2 and age == 1'))],
	'P140026': [np.sum(df.eval('sex_id == 2 and age == 2'))],
	'P140027': [np.sum(df.eval('sex_id == 2 and age == 3'))],
	'P140028': [np.sum(df.eval('sex_id == 2 and age == 4'))],
	'P140029': [np.sum(df.eval('sex_id == 2 and age == 5'))],
	'P140030': [np.sum(df.eval('sex_id == 2 and age == 6'))],
	'P140031': [np.sum(df.eval('sex_id == 2 and age == 7'))],
	'P140032': [np.sum(df.eval('sex_id == 2 and age == 8'))],
	'P140033': [np.sum(df.eval('sex_id == 2 and age == 9'))],
	'P140034': [np.sum(df.eval('sex_id == 2 and age == 10'))],
	'P140035': [np.sum(df.eval('sex_id == 2 and age == 11'))],
	'P140036': [np.sum(df.eval('sex_id == 2 and age == 12'))],
	'P140037': [np.sum(df.eval('sex_id == 2 and age == 13'))],
	'P140038': [np.sum(df.eval('sex_id == 2 and age == 14'))],
	'P140039': [np.sum(df.eval('sex_id == 2 and age == 15'))],
	'P140040': [np.sum(df.eval('sex_id == 2 and age == 16'))],
	'P140041': [np.sum(df.eval('sex_id == 2 and age == 17'))],
    })
    
    return t
