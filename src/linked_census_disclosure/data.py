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
            # set the column names to match the DHC Table Shell https://www2.census.gov/programs-surveys/decennial/2020/program-management/data-product-planning/2010-demonstration-data-products/02-Demographic_and_Housing_Characteristics/2022-03-16_Summary_File/2022-03-16_Technical%20Document/2010_Demonstration_Data_Product-DHC_Table_Shells_person_file.xlsx
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

    file_path = '/share/scratch/users/abie/projects/2022/dhc'
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
            # set the column names to match the DHC Table Shell https://www2.census.gov/programs-surveys/decennial/2020/program-management/data-product-planning/2010-demonstration-data-products/02-Demographic_and_Housing_Characteristics/2022-03-16_Summary_File/2022-03-16_Technical%20Document/2010_Demonstration_Data_Product-DHC_Table_Shells_person_file.xlsx
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
    df_synth = pd.read_csv(f'/share/scratch/users/abie/projects/2021/das_files/{state_abbr}_synth.csv')

    # some parts of the simulation will be easier if each household id was unique
    # to accomplish this, I will merge in the geoid

    df_synth['hh_id'] = df_synth.geoid.astype(str) + '-' + df_synth.hh_id.astype(int).astype(str)

    return df_synth


def read_dhc_remf(state_abbr):
    assert state_abbr == 'tx'

    file_path = '/share/scratch/users/abie/projects/2022/remf_april_dhc/'

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

    file_path = '/share/scratch/users/abie/projects/2022/remf_april_dhc/'

    sf1 = []
    for fname in glob.glob(f'{file_path}/sf1*.csv.gz'):
        df = pd.read_csv(fname)
        sf1.append(df)
    sf1 = pd.concat(sf1)

    column_names = ['state', 'county', 'tract', 'block', 'row_num', 'age', 'sex', 'race', 'eth', 'n']
    sf1.columns = column_names
    return sf1
