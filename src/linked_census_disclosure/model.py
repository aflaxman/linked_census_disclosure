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

