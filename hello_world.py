print("hello world")
from scipy.special import erfinv
print("from numpy import pi, log, sqrt")
from numpy import pi, log, sqrt
print("import pypolychord")
import pypolychord
print("from pypolychord.settings import PolyChordSettings")
from pypolychord.settings import PolyChordSettings
print("from pypolychord.priors import UniformPrior")
from pypolychord.priors import UniformPrior
try:
    from mpi4py import MPI
except ImportError:
    pass


#| Define a four-dimensional spherical gaussian likelihood,
#| width sigma=0.1, centered on the 0 with one derived parameter.
#| The derived parameter is the squared radius

nDims = 4
nDerived = 1
sigma = 0.1

def likelihood(theta):
    """ Simple Gaussian Likelihood"""

    nDims = len(theta)
    r2 = sum(theta**2)
    logL = -log(2*pi*sigma*sigma)*nDims/2.0
    logL += -r2/2/sigma/sigma

    return logL, [r2]

#| Define a box uniform prior from -1 to 1

def prior(hypercube):
    """ Uniform prior from [-1,1]^D. """
    return UniformPrior(-1, 1)(hypercube)

#| Optional dumper function giving run-time read access to
#| the live points, dead points, weights and evidences

def dumper(live, dead, logweights, logZ, logZerr):
    print("Last dead point:", dead[-1])

#| Initialise the settings
print("about to create settings")
settings = PolyChordSettings(nDims, nDerived)
settings.file_root = 'gaussian'
settings.nlive = 200
settings.do_clustering = True
settings.read_resume = False

#| Run PolyChord
print("about to run_pypolychord", flush=True)
output = pypolychord.run_polychord(likelihood, nDims, nDerived, settings, prior, dumper)