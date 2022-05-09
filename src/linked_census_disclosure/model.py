import numpy as np
import pandas as pd

from pyomo.environ import *

def test_cbc():
    """test that pyomo and cbc are installed correctly

    they are a pain something, and restarting jupyter notebook from an
    environment with cbc installed might help
    """

    model = ConcreteModel()
    model.x = Var(within=Binary)
    model.y = Var([0,1], within=NonNegativeReals)
    model.obj = Objective(expr = -model.x + model.y[0] + model.y[1])
    opt = SolverFactory('cbc')  # choose a solver, install from conda https://anaconda.org/conda-forge/coincbc
    results = opt.solve(model)  # solve the model with the selected solver
    value(model.x)  # if this is minimizing objective, x will be 1.0


def reconstruct_block(table_dict, state, county, tract, block):
    """Use COIN-CBC to reconstruct microdata for a single census block
    """
    geo_query_str = f'STATE == {state} and COUNTY == {county} and TRACT == {tract} and BLOCK == {block}'

    ### extract series from table_dict that will be part of the optimization

    # P8 is race in 63 categories
    t = table_dict['P8'].query(geo_query_str).sort_values('P80001')
    assert len(t) == 1
    s_p8 = t.iloc[0]

    # P9 is race in 63 categories * non-hispanic
    t = table_dict['P9'].query(geo_query_str)
    assert len(t) == 1
    s_p9 = t.iloc[0]

    # P10 is race in 63 categories for 18+
    t = table_dict['P10'].query(geo_query_str)
    assert len(t) == 1
    s_p10 = t.iloc[0]

    # P11 is race in 63 categories*non-hispanic for 18+
    t = table_dict['P11'].query(geo_query_str)
    assert len(t) == 1
    s_p11 = t.iloc[0]

    p12_iterations = [
        dict(table='P12', race=range(63), ethnicity=[0,1]),
        # P12A is SEX BY AGE FOR SELECTED AGE CATEGORIES (WHITE ALONE) [49]
        # it has age groups that need to be decoded in a somewhat complex way
        # and there are many other variants of race and ethnicity
        dict(table='P12A', race=[0], ethnicity=[0,1]), # race 0 = white
        dict(table='P12B', # SEX BY AGE FOR SELECTED AGE CATEGORIES (BLACK OR AFRICAN AMERICAN ALONE) [49]
             race=[1], ethnicity=[0,1]), # race 1 = black
        dict(table='P12C', # SEX BY AGE FOR SELECTED AGE CATEGORIES (AMERICAN INDIAN AND ALASKA NATIVE ALONE) [49]
             race=[2], ethnicity=[0,1]), # race 2 = AIAN
        dict(table='P12D', # SEX BY AGE FOR SELECTED AGE CATEGORIES (ASIAN ALONE) [49]
             race=[3], ethnicity=[0,1]), # race 3 = ASIAN
        dict(table='P12E', # SEX BY AGE FOR SELECTED AGE CATEGORIES (NATIVE HAWAIIAN AND OTHER PACIFIC ISLANDER ALONE) [49]
             race=[4], ethnicity=[0,1]), # race 4 = NHPI
        dict(table='P12F', # SEX BY AGE FOR SELECTED AGE CATEGORIES (SOME OTHER RACE ALONE) [49]
             race=[5], ethnicity=[0,1]), # race 5 = SOR
        dict(table='P12G', # SEX BY AGE FOR SELECTED AGE CATEGORIES (TWO OR MORE RACES) [49]
             race=range(6,63), ethnicity=[0,1]), # race 6+ = two or more
        dict(table='P12H', # SEX BY AGE FOR SELECTED AGE CATEGORIES (HISPANIC OR LATINO) [49]
             race=range(63), ethnicity=[1]), # ethnicity 1 == hispanic
        dict(table='P12I', # SEX BY AGE FOR SELECTED AGE CATEGORIES (WHITE ALONE, NOT HISPANIC OR LATINO) [49]
             race=[0], ethnicity=[0]), # race,ethnicity == 0,0 white, non-hispanic
        # P12J white alone or in combination, non-hispanic
        # in DHC, but not in SF1
        dict(table='P12K', # SEX BY AGE FOR SELECTED AGE CATEGORIES (BLACK OR AFRICAN AMERICAN ALONE, NOT HISPANIC OR LATINO) [49]
             race=[1], ethnicity=[0]), # race,ethnicity == 1,0 == black, non-hispanic
        dict(table='P12M', # SEX BY AGE FOR SELECTED AGE CATEGORIES (AMERICAN INDIAN AND ALASKA NATIVE ALONE, NOT HISPANIC OR LATINO) [49]
             race=[2], ethnicity=[0]),
        dict(table='P12O',
             race=[3], ethnicity=[0]),
        dict(table='P12Q',
             race=[4], ethnicity=[0]),
        dict(table='P12S',
             race=[5], ethnicity=[0]),
        dict(table='P12U', # SEX BY AGE FOR SELECTED AGE CATEGORIES (TWO OR MORE RACES, NOT HISPANIC OR LATINO) [49]
             race=range(6,63), ethnicity=[0]), # race 6+ = two or more
    ]

    for p12 in p12_iterations:
        if p12['table'] in table_dict:
            t = table_dict[p12['table']].query(geo_query_str)
            assert len(t) == 1
            p12['s'] = t.iloc[0]

    # P14 is SEX BY AGE FOR THE POPULATION UNDER 20 YEARS [43]
    t = table_dict['P14'].query(geo_query_str)
    assert len(t) == 1
    s_p14 = t.iloc[0]


    ### now form the integer program

    n_ages = 19 # single ages up to 17, and 18+
    n_sexes = 2
    n_races = 63  # all combinations
    n_eths = 2  

    model = ConcreteModel()
    model.x = Var(range(n_ages), range(n_sexes), range(n_races), range(n_eths),
                  within=NonNegativeIntegers)

    model.total_count = ConstraintList()
    model.total_count.add(
            sum(model.x[a,s,r,e,] for a in range(n_ages) for s in range(n_sexes) for r in range(n_races) for e in range(n_eths)
                ) == s_p8.P80001
        )  # HACK: would be more elegant to use P1 for the overall count


    P8_rows = [ 3, 4, 5, 6, 7, 8,] # race alone for white, black, aian, asian, nhpi, sor
    P8_rows += [ 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, # bi-racial
             ]
    P8_rows += list(range(27, 47))  # three races    
    #P8_rows += [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 21, 62]  # four races
    #P8_rows += [64, 65, 66, 67, 68, 69]  # five races
    #P8_rows += [71] # six races
    #assert len(P8_rows) == 63

    model.p8_race  = ConstraintList()
    for race_code, data_ref in enumerate(P8_rows):
        #if race_code in [53, 54, ]:
            #print(race_code, s_p8[f'P8{data_ref:04d}'])
            #continue
        model.p8_race.add(
            sum(model.x[a,s,race_code,e,] for a in range(n_ages) for s in range(n_sexes) for e in range(n_eths)
            ) == s_p8[f'P8{data_ref:04d}']
        )


    # again for P9, but all shifted slightly
    P9_rows = [val+2 for val in P8_rows]
    model.p9_race_non_hisp = ConstraintList()
    for race_code, data_ref in enumerate(P9_rows):
        model.p9_race_non_hisp.add(
                sum(model.x[a,s,race_code,0] for a in range(n_ages) for s in range(n_sexes)
                    ) == s_p9[f'P9{data_ref:04d}']
            )


    # again for P10, now all for the 18+ age count
    #model.p10 = ConstraintList()
    #for race_code, data_ref in enumerate(P8_rows):
    #    model.p10.add(
    #            sum(model.x[18,s,race_code,e] for s in range(n_sexes) for e in range(n_eths)
    #                ) == s_p10[f'P10{data_ref:04d}']
    #        )


    # again for P11, now all for the 18+ age count
    model.p11 = ConstraintList()
    for race_code, data_ref in enumerate(P9_rows):
        model.p11.add(
                sum(model.x[18,s,race_code,0] for s in range(n_sexes)
                    ) == s_p11[f'P11{data_ref:04d}']
            )

    # something a little different for P12 iterations
    model.p12  = ConstraintList()
    P12_rows = [dict(ref_name=3, ages=[0,1,2,3,4], sex=0),
                dict(ref_name=4, ages=[5,6,7,8,9], sex=0),
                dict(ref_name=5, ages=[10,11,12,13,14], sex=0),
                dict(ref_name=6, ages=[15,16,17], sex=0),
                dict(ref_name=27, ages=[0,1,2,3,4], sex=1),
                dict(ref_name=28, ages=[5,6,7,8,9], sex=1),
                dict(ref_name=29, ages=[10,11,12,13,14], sex=1),
                dict(ref_name=30, ages=[15,16,17], sex=1),
               ]

    for p12 in p12_iterations:
        if 's' not in p12:
            continue # some P12X iterations are in DHC and not in SF1

        s_p12  = p12['s']
        races = p12['race']
        ethnicities = p12['ethnicity']
        table = p12['table']

        for row_dict in P12_rows:
            s = row_dict['sex']
            ages = row_dict['ages']
            data_ref = row_dict['ref_name']
    #         print(ages, s, races, ethnicities, s_p12[f'{table}{data_ref:04d}'])
            model.p12.add(
                sum(model.x[a, s, r, e] for a in ages for r in races for e in ethnicities
                   ) == s_p12[f'{table}{data_ref:04d}']
            )
            

    # and last, but not least, P14
    model.p14_sex_age = ConstraintList()
    P14_male_rows = list(range(3, 21))
    P14_female_rows = list(range(24, 42))

    for sex, P14_rows in enumerate([P14_male_rows, P14_female_rows]):
        for age, data_ref in enumerate(P14_rows):
            model.p14_sex_age.add(
                sum(model.x[age, sex, r, e] for r in range(n_races) for e in range(n_eths)
                    ) == s_p14[f'P14{data_ref:04d}']
            )


    # objective with a random direction, to break ties
    model.obj = Objective(expr=sum(np.random.normal() * model.x[a,s,r,e,]
                                   for a in range(n_ages) for s in range(n_sexes)
                                   for r in range(n_races) for e in range(n_eths)
                               )
                      )


    opt = SolverFactory('cbc')  # choose a solver, install from conda https://anaconda.org/conda-forge/coincbc
    results = opt.solve(model)  # solve the model with the selected solver

    results = []
    for a in range(n_ages):
        for s in range(n_sexes):
            for r in range(n_races):
                for e in range(n_eths):
                    x_asre = value(model.x[a,s,r,e])
                    if x_asre > 0:
                        results.append(dict(age=a, sex=s, race=r, eth=e, n=x_asre))
    df_results = pd.DataFrame(results)

    return df_results
    try:
        pass
    except ValueError:
        return None # failed to find a solution
