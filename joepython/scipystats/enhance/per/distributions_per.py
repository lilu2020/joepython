# Functions to implement several important functions for
#   various Continous and Discrete Probability Distributions
#
# Author:  Travis Oliphant  2002-2003


from __future__ import division

import scipy
from scipy.stats.plotbackend import plotbackend
from scipy.integrate import quad
from scipy.linalg import pinv2
from scipy.misc import comb, derivative
from scipy import special
from scipy import optimize
import numdifftools
import inspect
from numpy import alltrue, where, arange, put, putmask, \
     ravel, take, ones, sum, shape, product, repeat, reshape, \
     zeros, floor, logical_and, log, sqrt, exp, arctanh, tan, sin, arcsin, \
     arctan, tanh, ndarray, cos, cosh, sinh, newaxis, array, log1p, expm1
from numpy import atleast_1d, polyval, angle, ceil, place, extract, \
     any, argsort, argmax, vectorize, r_, asarray, nan, inf, pi, isnan, isinf, \
     power
import numpy
import numpy as np
import numpy.random as mtrand
from numpy import flatnonzero as nonzero
from scipy.special import gammaln as gamln
from copy import copy
#import vonmises_cython

__all__ = [
    'rv_continuous',
    'ksone', 'kstwobign', 'norm', 'alpha', 'anglit', 'arcsine',
    'beta', 'betaprime', 'bradford', 'burr', 'fisk', 'cauchy',
    'chi', 'chi2', 'cosine', 'dgamma', 'dweibull', 'erlang',
    'expon', 'exponweib', 'exponpow', 'fatiguelife', 'foldcauchy',
    'f', 'foldnorm', 'frechet_r', 'weibull_min', 'frechet_l',
    'weibull_max', 'genlogistic', 'genpareto', 'genexpon', 'genextreme',
    'gamma', 'gengamma', 'genhalflogistic', 'gompertz', 'gumbel_r',
    'gumbel_l', 'halfcauchy', 'halflogistic', 'halfnorm', 'hypsecant',
    'gausshyper', 'invgamma', 'invnorm', 'invweibull', 'johnsonsb',
    'johnsonsu', 'laplace', 'levy', 'levy_l', 'levy_stable',
    'logistic', 'loggamma', 'loglaplace', 'lognorm', 'gilbrat',
    'maxwell', 'mielke', 'nakagami', 'ncx2', 'ncf', 't',
    'nct', 'pareto', 'lomax', 'powerlaw', 'powerlognorm', 'powernorm',
    'rdist', 'rayleigh', 'reciprocal', 'rice', 'recipinvgauss',
    'semicircular', 'triang', 'truncexpon', 'truncnorm',
    'tukeylambda', 'uniform', 'vonmises', 'wald', 'wrapcauchy',
    'entropy', 'rv_discrete',
    'binom', 'bernoulli', 'nbinom', 'geom', 'hypergeom', 'logser',
    'poisson', 'planck', 'boltzmann', 'randint', 'zipf', 'dlaplace',
]

floatinfo = numpy.finfo(float)
longinfo = numpy.iinfo(long)
intinfo = numpy.iinfo(int)


errp = special.errprint
#arr = atleast_1d
arr = asarray
gam = special.gamma

import types
import stats as st


all = alltrue
sgf = vectorize
import new

def _build_random_array(fun, args, size=None):
# Build an array by applying function fun to
# the arguments in args, creating an array with
# the specified shape.
# Allows an integer shape n as a shorthand for (n,).
    if isinstance(size, types.IntType):
        size = [size]
    if size is not None and len(size) != 0:
        n = numpy.multiply.reduce(size)
        s = apply(fun, args + (n,))
        s.shape = size
        return s
    else:
        n = 1
        s = apply(fun, args + (n,))
        return s[0]

random = mtrand.random_sample
rand = mtrand.rand
random_integers = mtrand.random_integers
permutation = mtrand.permutation

## Internal class to compute a ppf given a distribution.
##  (needs cdf function) and uses brentq from scipy.optimize
##  to compute ppf from cdf.
class general_cont_ppf(object):
    def __init__(self, dist, xa=-10.0, xb=10.0, xtol=1e-14):
        self.dist = dist
        self.cdf = eval('%scdf'%dist)
        self.xa = xa
        self.xb = xb
        self.xtol = xtol
        self.vecfunc = sgf(self._single_call,otypes='d')
    def _tosolve(self, x, q, *args):
        return apply(self.cdf, (x, )+args) - q
    def _single_call(self, q, *args):
        return optimize.brentq(self._tosolve, self.xa, self.xb, args=(q,)+args, xtol=self.xtol)
    def __call__(self, q, *args):
        return self.vecfunc(q, *args)

# Frozen RV class
class rv_frozen(object):
    ''' Frozen continous or discrete 1D Random Variable object (RV)

    RV.rvs(size=1)
        - random variates

    RV.pdf(x)
        - probability density function (continous case)

    RV.pmf(x)
        - probability mass function (discrete case)

    RV.cdf(x)
        - cumulative density function

    RV.sf(x)
        - survival function (1-cdf --- sometimes more accurate)

    RV.ppf(q)
        - percent point function (inverse of cdf --- percentiles)

    RV.isf(q)
        - inverse survival function (inverse of sf)

    RV.stats(moments='mv')
        - mean('m',axis=0), variance('v'), skew('s'), and/or kurtosis('k')

    RV.entropy()
        - (differential) entropy of the RV.
    '''
    def __init__(self, dist, *args, **kwds):
        self.dist = dist
        loc0, scale0 = map(kwds.get, ['loc', 'scale'])
        if isinstance(dist,rv_continuous):
            args, loc0, scale0 = dist.fix_loc_scale(args, loc0, scale0)
            self.par = args + (loc0, scale0)
        else: # rv_discrete
            args, loc0 = dist.fix_loc(args, loc0)
            self.par = args + (loc0,)


    def pdf(self,x):
        ''' Probability density function at x of the given RV.'''
        return self.dist.pdf(x,*self.par)
    def cdf(self,x):
        '''Cumulative distribution function at x of the given RV.'''
        return self.dist.cdf(x,*self.par)
    def ppf(self,q):
        '''Percent point function (inverse of cdf) at q of the given RV.'''
        return self.dist.ppf(q,*self.par)
    def isf(self,q):
        '''Inverse survival function at q of the given RV.'''
        return self.dist.isf(q,*self.par)
    def rvs(self, size=None):
        '''Random variates of given type.'''
        kwds = dict(size=size)
        return self.dist.rvs(*self.par,**kwds)
    def sf(self,x):
        '''Survival function (1-cdf) at x of the given RV.'''
        return self.dist.sf(x,*self.par)
    def stats(self,moments='mv'):
        ''' Some statistics of the given RV'''
        kwds = dict(moments=moments)
        return self.dist.stats(*self.par,**kwds)
    def moment(self,n):
        par1 = self.par[:self.dist.numargs]
        return self.dist.moment(n,*par1)
    def entropy(self):
        return self.dist.entropy(*self.par)
    def pmf(self,k):
        '''Probability mass function at k of the given RV'''
        return self.dist.pmf(k,*self.par)


# Frozen RV class
class rv_frozen_old(object):
    def __init__(self, dist, *args, **kwds):
        self.args = args
        self.kwds = kwds
        self.dist = dist
    def pdf(self,x):
        return self.dist.pdf(x,*self.args,**self.kwds)
    def cdf(self,x):
        return self.dist.cdf(x,*self.args,**self.kwds)
    def ppf(self,q):
        return self.dist.ppf(q,*self.args,**self.kwds)
    def isf(self,q):
        return self.dist.isf(q,*self.args,**self.kwds)
    def rvs(self, size=None):
        kwds = self.kwds
        kwds.update({'size':size})
        return self.dist.rvs(*self.args,**kwds)
    def sf(self,x):
        return self.dist.sf(x,*self.args,**self.kwds)
    def stats(self,moments='mv'):
        kwds = self.kwds
        kwds.update({'moments':moments})
        return self.dist.stats(*self.args,**kwds)
    def moment(self,n):
        return self.dist.moment(n,*self.args,**self.kwds)
    def entropy(self):
        return self.dist.entropy(*self.args,**self.kwds)
    def pmf(self,k):
        return self.dist.pmf(k,*self.args,**self.kwds)


def ecross(t,f,ind,v):
    ''' Extracts exact level v crossings

    Parameters
    -----------
    t,f : vectors
        arguments and functions values, respectively.
    ind : scalar or vector of integers
        indices to level v crossings as found by findcross.
    v : scalar or vector (of size(ind))
        defining the level(s) to cross.

    Returns
    --------
    t0 : vector
        exact level v crossings.

    Description
    -----------
    ECROSS interpolates t and f linearly to find the exact level v
    crossings, i.e., the points where f(t0) = v

    Example
    -------
    >>> from matplotlib import pylab as plb
    >>> t = plb.linspace(0,7*pi,250)
    >>> x = sin(t);
    >>> ind = findcross(x,0.75)
    >>> t0 = ecross(t,x,ind,0.75);
    >>> plb.plot(t,x,'.',t[ind],x[ind],'r.',t, ones(t.shape)*.75, t0,ones(t0.shape)*0.75,'g.')

    See also
    --------
    findcross
    '''
    # Tested on: Python 2.5
    # revised pab Feb2004
    # By pab 18.06.2001

    return t[ind]+(v-f[ind])*(t[ind+1]-t[ind])/(f[ind+1]-f[ind])

def findcross(x,v=0.0):
    '''
    Return indices to level v up and downcrossings of a vector

    Parameters
    ----------
    x : vector
        sampled values.
    v : scalar
        crossing level. (Default 0).

    Returns
    -------
    ind : vector of integers
        indices to the crossings in the original sequence x.

    Example
    -------
    >>> from matplotlib import pylab as plb
    >>> v = 0.75
    >>> t = plb.linspace(0,7*pi,250); x = sin(t);
    >>> ind = findcross(x,v)
    >>> plb.plot(t,x,'.',t[ind],x[ind],'r.', t, ones(t.shape)*v)

    See also
    ---------
    crossdef
    '''

    xn = numpy.atleast_1d(x)
    xn  = numpy.int8(numpy.sign(xn.ravel()-v))
    ind = None
    n  = len(xn)
    if n>1:
        iz, = numpy.nonzero(xn==0)
        if any(iz):
            # Trick to avoid turning points on the crossinglevel.
            if iz[0]==0:
                if len(iz)==n:
                    #warning('All values are equal to crossing level!')
                    return ind


                diz = numpy.diff(iz)
                ix  = iz((diz>1).argmax())
                if not any(ix):
                    ix = iz[-1]

                #x(ix) is a up crossing if  x(1:ix) = v and x(ix+1) > v.
                #x(ix) is a downcrossing if x(1:ix) = v and x(ix+1) < v.
                xn[0:ix] = -xn[ix+1]
                iz = iz[ix::]

            for ix in iz.tolist():
                xn[ix] = xn[ix-1]

        #% indices to local level crossings ( without turningpoints)
        #ind, = numpy.nonzero(xn[:n-1]*xn[1:] < 0)
        ind, = (xn[:n-1]*xn[1:] < 0).nonzero()
    return ind
def stirlerr(n):
    """Return error of Stirling approximation, i.e., log(n!) - log( sqrt(2*pi*n)*(n/exp(1))**n )

    Example
    -------
    >>> stirlerr(2)
    array([ 0.0413407])

    See also
    ---------
    binom


    Reference
    -----------
    Catherine Loader (2000).
    'Fast and Accurate Computation of Binomial Probabilities'
    <http://www.citeseer.ist.psu.edu/312695.html>
    """

    S0 = 0.083333333333333333333   # /* 1/12 */
    S1 = 0.00277777777777777777778 # /* 1/360 */
    S2 = 0.00079365079365079365079365 # /* 1/1260 */
    S3 = 0.000595238095238095238095238 # /* 1/1680 */
    S4 = 0.0008417508417508417508417508  # /* 1/1188 */

    logical_and = numpy.logical_and
    atleast_1d = numpy.atleast_1d
    gammaln = special.gammaln
    pi = numpy.pi
    exp = numpy.exp
    sqrt = numpy.sqrt
    log = numpy.log

    n1 = atleast_1d(n)
#    if numpy.isscalar(n):
#        n1 = asfarray([n])
#    else:
#        n1 = asfarray(n)

    y = gammaln(n1+1) - log(sqrt(2*pi*n1)*(n1/exp(1))**n1 )


    nn = n1*n1

    n500    = 500<n1
    y[n500] = (S0-S1/nn[n500])/n1[n500]
    n80     = logical_and(80<n1 , n1<=500)
    if any(n80):
        y[n80]  = (S0-(S1-S2/nn[n80])/nn[n80])/n1[n80]
    n35     = logical_and(35<n1, n1<=80)
    if any(n35):
        nn35   = nn[n35]
        y[n35] = (S0-(S1-(S2-S3/nn35)/nn35)/nn35)/n1[n35]

    n15      = logical_and(15<n1, n1<=35)
    if any(n15):
        nn15   = nn[n15]
        y[n15] = (S0-(S1-(S2-(S3-S4/nn15)/nn15)/nn15)/nn15)/n1[n15]

    return y
def bd0(x,npr):
    """
    Return deviance term x*log(x/npr) + npr - x

    See also
    --------
    stirlerr,
    binom.pmf,
    poisson.pmf

    Reference
    ---------
    Catherine Loader (2000).
    'Fast and Accurate Computation of Binomial Probabilities'
    <http//www.citeseer.ist.psu.edu/312695.html>
    """
    def bd0_iter(x,np1):
        xmnp = x-np1
        v = (xmnp)/(x+np1)
        s1 = (xmnp)*v
        s = np.zeros_like(s1)
        ej = 2*x*v
        #v2 = v*v
        v = v*v
        j = 0
        ix, = (s!=s1).nonzero()
        while ix.size>0:
            j += 1
            s[ix]  = s1[ix].copy()
            ej[ix] = ej[ix]*v[ix]
            s1[ix] = s[ix]+ej[ix]/(2.*j+1.0)
            ix, = (s1!=s).nonzero()
        return s1
    x1,npr1 = atleast_1d(x,npr)
    y = x1*log(x1/npr1)+npr1-x1
    sml = nonzero(abs(x1-npr1)<0.1*(x1+npr1))
    if sml.size>0:
        if x1.size!=1:
            x1 = x1[sml]
        if npr1.size!=1:
            npr1 = npr1[sml]
        y.put(sml,bd0_iter(x1,npr1))
    return y


# internal class to profile parameters of a given distribution
class Profile(object):
    ''' Profile Log- likelihood or Product Spacing-function.
            which can be used for constructing confidence interval for
            either phat(i), probability or quantile.
    Call
    -----
      Lp = Profile(fit_dist,**kwds)

    Parameters
    ----------
    fit_dist : FitDistribution object with ML or MPS estimated distribution parameters.

    **kwds : named arguments with keys
          i          - Integer defining which distribution parameter to
                         profile, i.e. which parameter to keep fixed
                         (default index to first non-fixed parameter)
          pmin, pmax - Interval for either the parameter, phat(i), prb, or x,
                        used in the optimization of the profile function (default
                        is based on the 100*(1-alpha)% confidence interval
                        computed using the delta method.)
          N          - Max number of points used in Lp (default 100)
          x          - Quantile (return value)
          logSF      - log survival probability,i.e., SF = Prob(X>x;phat)
          link       - function connecting the quantile (x) and the
                         survival probability (SF) with the fixed distribution
                         parameter, i.e.: self.par[i] = link(x,logSF,self.par,i),
                         where logSF = log(Prob(X>x;phat)).
                         This means that if:
                          1) x is not None then x is profiled
                          2) logSF is not None then logSF is profiled
                          3) x and logSF both are None then self.par[i] is profiled (default)
          alpha       - confidence coefficent (default 0.05)
    Returns
    -------
    Lp : Profile log-likelihood function with parameters phat given
               the data, phat(i), probability (prb) and quantile (x) (if given), i.e.,
                 Lp = max(log(f(phat|data,phat(i)))),
               or
                 Lp = max(log(f(phat|data,phat(i),x,prb)))
    Member methods
      plot()
      get_CI()

    Member variables
      fit_dist - fitted data object.
      data - profile function values
      args - profile function arguments
      alpha - confidence coefficient
      Lmax - Maximum value of profile function
      alpha_cross_level -

    PROFILE is a utility function for making inferences either on a particular
    component of the vector phat or the quantile, x, or the probability, SF.
    This is usually more accurate than using the delta method assuming
    asymptotic normality of the ML estimator or the MPS estimator.


    Examples
    --------
    #MLE and better CI for phat.par[0]
    >>> import numpy as np
    >>> R = weibull_min.rvs(1,size=100);
    >>> phat = weibull_min.fit(R,1,1,par_fix=[np.nan,0.,np.nan])
    >>> Lp = Profile(phat,i=0)
    >>> Lp.plot()
    >>> Lp.get_CI(alpha=0.1)
    >>> SF = 1./990
    >>> x = phat.isf(SF)

    # CI for x
    >>> Lx = phat.profile(i=1,x=x,link=phat.dist.link)
    >>> Lx.plot()
    >>> Lx.get_CI(alpha=0.2)

    # CI for logSF=log(SF)
    >>> Lpr = phat.profile(i=1,logSF=log(SF),link = phat.dist.link)


    '''
    def __init__(self, fit_dist, **kwds):
        self.fit_dist = fit_dist
        self.data = None
        self.args = None
        self.title = 'Profile log'
        self.xlabel = ''
        self.ylabel = ''
        self.i_fixed, self.N, self.alpha, self.pmin,self.pmax,self.x,self.logSF,self.link = map(kwds.get,
                            ['i','N','alpha','pmin','pmax','x','logSF','link'],
                            [0,100,0.05,None,None,None,None,None])

        self.ylabel = '%g%s CI' % (100*(1.0-self.alpha), '%')
        if fit_dist.method.startswith('ml'):
            self.title = self.title + 'likelihood'
            Lmax = fit_dist.LLmax
        elif fit_dist.method.startswith('mps'):
            self.title = self.title + ' product spacing'
            Lmax = fit_dist.LPSmax
        else:
            raise ValueError("PROFILE is only valid for ML- or MPS- estimators")
        if fit_dist.par_fix==None:
            isnotfixed = valarray(fit_dist.par.shape,True)
        else:
            isnotfixed = 1-numpy.isfinite(fit_dist.par_fix)

        self.i_notfixed = nonzero(isnotfixed)

        self.i_fixed = atleast_1d(self.i_fixed)

        if 1-isnotfixed[self.i_fixed]:
            raise ValueError("Index i must be equal to an index to one of the free parameters.")

        isfree = isnotfixed
        isfree[self.i_fixed] = False
        self.i_free = nonzero(isfree)

        self.Lmax = Lmax
        self.alpha_Lrange = 0.5*chi2.isf(self.alpha,1)
        self.alpha_cross_level = Lmax - self.alpha_Lrange
        lowLevel = self.alpha_cross_level-self.alpha_Lrange/7.0

        ## Check that par are actually at the optimum
        phatv = fit_dist.par.copy()
        self._par = phatv.copy()
        phatfree = phatv[self.i_free].copy()


        ## Set up variable to profile and _local_link function

        self.profile_x = not self.x==None
        self.profile_logSF = not (self.logSF==None or self.profile_x)
        self.profile_par = not (self.profile_x or self.profile_logSF)

        if self.link==None:
            self.link = self.fit_dist.dist.link
        if self.profile_par:
            self._local_link = lambda fix_par, par : fix_par
            self.xlabel = 'phat(%d)'% self.i_fixed
            p_opt = self._par[self.i_fixed]
        elif self.profile_x:
            self.logSF = log(fit_dist.sf(self.x))
            self._local_link = lambda fix_par, par : self.link(fix_par,self.logSF,par,self.i_fixed)
            self.xlabel = 'x'
            p_opt = self.x
        elif self.profile_logSF:
            p_opt = self.logSF
            self.x = fit_dist.isf(exp(p_opt))
            self._local_link = lambda fix_par, par : self.link(self.x,fix_par,par,self.i_fixed)
            self.xlabel= 'log(R)'
        else:
            raise ValueError("You must supply a non-empty quantile (x) or probability (logSF) in order to profile it!")

        self.xlabel = self.xlabel + ' (' + fit_dist.dist.name + ')'

        pvec = self._get_pvec(p_opt)


        mylogfun = self._nlogfun
        self.data = numpy.empty_like(pvec)
        self.data[:] = nan
        k1 = (pvec>=p_opt).argmax()
        for ix in xrange(k1,-1,-1):
            phatfree = optimize.fmin(mylogfun,phatfree,args =(pvec[ix],) ,disp=0)
            self.data[ix] = -mylogfun(phatfree,pvec[ix])
            if self.data[ix]<self.alpha_cross_level:
                pvec[:ix] = nan
                break

        phatfree = phatv[self.i_free].copy()
        for ix in xrange(k1+1,pvec.size):
            phatfree = optimize.fmin(mylogfun,phatfree,args =(pvec[ix],) ,disp=0)
            self.data[ix] = -mylogfun(phatfree,pvec[ix])
            if self.data[ix]<self.alpha_cross_level:
                pvec[ix+1:] = nan
                break

        # prettify result
        ix = nonzero(numpy.isfinite(pvec))
        self.data = self.data[ix]
        self.args = pvec[ix]
        cond =self.data==-numpy.inf
        if any(cond):
            ind, = cond.nonzero()
            self.data.put(ind, numpy.finfo(float).min/2.0)
            ind1 = numpy.where(ind==0,ind,ind-1)
            cl = self.alpha_cross_level-self.alpha_Lrange/2.0
            t0 = ecross(self.args,self.data,ind1,cl)

            self.data.put(ind,cl)
            self.args.put(ind,t0)


    def _get_pvec(self,p_opt):
        ''' return proper interval for the variable to profile
        '''

        linspace = numpy.linspace
        if self.pmin==None or self.pmax==None:

            if self.profile_par:
                pvar = self.fit_dist.par_cov[self.i_fixed,:][:,self.i_fixed]
            else:
                i_notfixed = self.i_notfixed
                phatv = self._par

                if self.profile_x:
                    gradfun = numdifftools.Gradient(self._myinvfun)
                else:
                    gradfun = numdifftools.Gradient(self._myprbfun)
                drl = gradfun(phatv[self.i_notfixed])

                pcov = self.fit_dist.par_cov[i_notfixed,:][:,i_notfixed]
                pvar = sum(numpy.dot(drl,pcov)*drl)

            p_crit = norm.isf(self.alpha/2.0)*sqrt(numpy.ravel(pvar))*1.5
            if self.pmin==None:
                self.pmin = p_opt-5.0*p_crit
            if self.pmax==None:
                self.pmax = p_opt+5.0*p_crit

            N4 = numpy.floor(self.N/4.0)

            pvec1 = linspace(self.pmin,p_opt-p_crit,N4+1)
            pvec2 = linspace(p_opt-p_crit,p_opt+p_crit,self.N-2*N4)
            pvec3 = linspace(p_opt+p_crit,self.pmax,N4+1)
            pvec = numpy.unique(numpy.hstack((pvec1,p_opt,pvec2,pvec3)))

        else:
            pvec = linspace(self.pmin,self.pmax,self.N)
        return pvec
    def  _myinvfun(self,phatnotfixed):
        mphat = self._par.copy()
        mphat[self.i_notfixed] = phatnotfixed;
        prb = exp(self.logSF)
        return self.fit_dist.dist.isf(prb,*mphat);

    def _myprbfun(phatnotfixed):
        mphat = self._par.copy()
        mphat[self.i_notfixed] = phatnotfixed;
        return self.fit_dist.dist.sf(self.x,*mphat);


    def _nlogfun(self,free_par,fix_par):
        ''' Return negative of loglike or logps function

           free_par - vector of free parameters
           fix_par  - fixed parameter, i.e., either quantile (return level),
                      probability (return period) or distribution parameter

        '''
        par = self._par
        par[self.i_free] = free_par
        # _local_link: connects fixed quantile or probability with fixed distribution parameter
        par[self.i_fixed] = self._local_link(fix_par,par)
        return self.fit_dist.fitfun(par)

    def get_CI(self,alpha=0.05):
        '''Return confidence interval
        '''
        if alpha<self.alpha:
            raise ValueError('Unable to return CI with alpha less than %g' % self.alpha)

        cross_level = self.Lmax - 0.5*chi2.isf(alpha,1)
        ind = findcross(self.data,cross_level)
        N = len(ind)
        if N==0:
            #Warning('upper bound for XXX is larger'
            #Warning('lower bound for XXX is smaller'
            CI = (self.pmin,self.pmax)
        elif N==1:
            x0 = ecross(self.args,self.data,ind,cross_level)
            isUpcrossing = self.data[ind]>self.data[ind+1]
            if isUpcrossing:
                CI = (x0,self.pmax)
                #Warning('upper bound for XXX is larger'
            else:
                CI = (self.pmin,x0)
                #Warning('lower bound for XXX is smaller'

        elif N==2:
            CI = ecross(self.args,self.data,ind,cross_level)
        else:
            # Warning('Number of crossings too large!')
            CI = ecross(self.args,self.data,ind[[0,-1]],cross_level)
        return CI

    def plot(self):
        ''' Plot profile function with 100(1-alpha)% CI
        '''
        plotbackend.plot(self.args,self.data,
            self.args[[0,-1]],[self.Lmax,]*2,'r',
            self.args[[0,-1]],[self.alpha_cross_level,]*2,'r')
        plotbackend.title(self.title)
        plotbackend.ylabel(self.ylabel)
        plotbackend.xlabel(self.xlabel)

# internal class to fit given distribution to data
class FitDistribution(rv_frozen):
    def __init__(self, dist, data, *args, **kwds):
        extradoc = '''

    RV.plotfitsumry() - Plot various diagnostic plots to asses quality of fit.
    RV.plotecdf()     - Plot Empirical and fitted Cumulative Distribution Function
    RV.plotesf()      - Plot Empirical and fitted Survival Function
    RV.plotepdf()     - Plot Empirical and fitted Probability Distribution Function
    RV.plotresq()     - Displays a residual quantile plot.
    RV.plotresprb()   - Displays a residual probability plot.

    RV.profile()      - Return Profile Log- likelihood or Product Spacing-function.

    Member variables:
        data - data used in fitting
        alpha - confidence coefficient
        method - method used
        LLmax  - loglikelihood function evaluated using par
        LPSmax - log product spacing function evaluated using par
        pvalue - p-value for the fit
        search - True if search for distribution parameters (default)
        copydata - True if copy input data (default)

        par     - parameters (fixed and fitted)
        par_cov - covariance of parameters
        par_fix - fixed parameters
        par_lower - lower (1-alpha)% confidence bound for the parameters
        par_upper - upper (1-alpha)% confidence bound for the parameters

        '''
        self.__doc__ = rv_frozen.__doc__ + extradoc
        self.dist = dist
        numargs = dist.numargs

        self.method, self.alpha, self.par_fix, self.search, self.copydata= map(kwds.get,['method','alpha','par_fix','search','copydata'],['ml',0.05,None,True,True])
        self.data = ravel(data)
        if self.copydata:
            self.data = self.data.copy()
        self.data.sort()
        if self.method.lower()[:].startswith('mps'):
            self._fitfun = dist.nlogps
        else:
            self._fitfun = dist.nnlf

        allfixed  = False
        isfinite = numpy.isfinite
        somefixed = (self.par_fix !=None) and any(isfinite(self.par_fix))

        if somefixed:
            fitfun = self._fxfitfun
            self.par_fix = tuple(self.par_fix)
            allfixed = all(isfinite(self.par_fix))
            self.par = atleast_1d(self.par_fix)
            self.i_notfixed = nonzero(1-isfinite(self.par))
            self.i_fixed  = nonzero(isfinite(self.par))
            if len(self.par) != numargs+2:
                raise ValueError, "Wrong number of input arguments."
            if len(args)!=len(self.i_notfixed):
                raise ValueError("Length of args must equal number of non-fixed parameters given in par_fix! (%d) " % len(self.i_notfixed))
            x0 = atleast_1d(args)
        else:
            fitfun = self.fitfun
            loc0, scale0 = map(kwds.get, ['loc', 'scale'])
            args, loc0, scale0 = dist.fix_loc_scale(args, loc0, scale0)
            Narg = len(args)
            if Narg != numargs:
                if Narg > numargs:
                    raise ValueError, "Too many input arguments."
                else:
                    args += (1.0,)*(numargs-Narg)
            # location and scale are at the end
            x0 = args + (loc0, scale0)
            x0 = atleast_1d(x0)

        numpar = len(x0)
        if self.search and not allfixed:
            #args=(self.data,),
            par = optimize.fmin(fitfun,x0,disp=0)
            if not somefixed:
                self.par = par
        elif  (not allfixed) and somefixed:
            self.par[self.i_notfixed] = x0
        else:
            self.par = x0

        np = numargs+2

        self.par_upper = None
        self.par_lower = None
        self.par_cov = zeros((np,np))
        self.LLmax = -dist.nnlf(self.par,self.data)
        self.LPSmax = -dist.nlogps(self.par,self.data)
        self.pvalue = dist.pvalue(self.par,self.data,unknown_numpar=numpar)
        H = numpy.asmatrix(dist.hessian_nnlf(self.par,self.data))
        self.H = H
        try:
            if allfixed:
                pass
            elif somefixed:
                pcov = -pinv2(H[self.i_notfixed,:][...,self.i_notfixed])
                for row,ix in enumerate(list(self.i_notfixed)):
                    self.par_cov[ix,self.i_notfixed] = pcov[row,:]

            else:
                self.par_cov = -pinv2(H)
        except:
            self.par_cov[:,:] = nan

        pvar = numpy.diag(self.par_cov)
        zcrit = -norm.ppf(self.alpha/2.0)
        self.par_lower = self.par-zcrit*sqrt(pvar)
        self.par_upper = self.par+zcrit*sqrt(pvar)

    def fitfun(self,phat):
        return self._fitfun(phat,self.data)

    def _fxfitfun(self,phat10):
        self.par[self.i_notfixed] = phat10
        return self._fitfun(self.par,self.data)


    def profile(self,**kwds):
        ''' Profile Log- likelihood or Log Product Spacing- function,
            which can be used for constructing confidence interval for
            either phat(i), probability or quantile.

        CALL:  Lp = RV.profile(**kwds)


       RV = object with ML or MPS estimated distribution parameters.
       Parameters
       ----------
       **kwds : named arguments with keys:
          i          - Integer defining which distribution parameter to
                         profile, i.e. which parameter to keep fixed
                         (default index to first non-fixed parameter)
          pmin, pmax - Interval for either the parameter, phat(i), prb, or x,
                        used in the optimization of the profile function (default
                        is based on the 100*(1-alpha)% confidence interval
                        computed using the delta method.)
          N          - Max number of points used in Lp (default 100)
          x          - Quantile (return value)
          logSF       - log survival probability,i.e., R = Prob(X>x;phat)
          link       - function connecting the quantile (x) and the
                         survival probability (R) with the fixed distribution
                         parameter, i.e.: self.par[i] = link(x,logSF,self.par,i),
                         where logSF = log(Prob(X>x;phat)).
                         This means that if:
                          1) x is not None then x is profiled
                          2) logSF is not None then logSF is profiled
                          3) x and logSF both are None then self.par[i] is profiled (default)
          alpha       - confidence coefficent (default 0.05)
       Returns
       --------
         Lp = Profile log-likelihood function with parameters phat given
               the data, phat(i), probability (prb) and quantile (x) (if given), i.e.,
                 Lp = max(log(f(phat|data,phat(i)))),
               or
                 Lp = max(log(f(phat|data,phat(i),x,prb)))

          PROFILE is a utility function for making inferences either on a particular
          component of the vector phat or the quantile, x, or the probability, R.
          This is usually more accurate than using the delta method assuming
          asymptotic normality of the ML estimator or the MPS estimator.


          Examples
          --------
          # MLE and better CI for phat.par[0]
          >>> R = weibull_min.rvs(1,size=100);
          >>> phat = weibull_min.fit(R)
          >>> Lp = phat.profile(i=0)
          >>> Lp.plot()
          >>> Lp.get_CI(alpha=0.1)
          >>> R = 1./990
          >>> x = phat.isf(R)

          # CI for x
          >>> Lx = phat.profile(i=1,x=x,link=phat.dist.link)
          >>> Lx.plot()
          >>> Lx.get_CI(alpha=0.2)

          # CI for logSF=log(SF)
          >>> Lpr = phat.profile(i=1,logSF=log(R),link = phat.dist.link)

          See also
          --------
          Profile
        '''
        if not self.par_fix==None:
            i1 = kwds.setdefault('i',(1-numpy.isfinite(self.par_fix)).argmax())

        return Profile(self,**kwds)



    def plotfitsumry(self):
        ''' Plot various diagnostic plots to asses the quality of the fit.

        PLOTFITSUMRY displays probability plot, density plot, residual quantile
        plot and residual probability plot.
        The purpose of these plots is to graphically assess whether the data
        could come from the fitted distribution. If so the empirical- CDF and PDF
        should follow the model and the residual plots will be linear. Other
        distribution types will introduce curvature in the residual plots.
        '''
        plotbackend.subplot(2,2,1)
        #self.plotecdf()
        self.plotesf()
        plotbackend.subplot(2,2,2)
        self.plotepdf()
        plotbackend.subplot(2,2,3)
        self.plotresprb()
        plotbackend.subplot(2,2,4)
        self.plotresq()
        fixstr = ''
        if not self.par_fix==None:
            numfix = len(self.i_fixed)
            if numfix>0:
                format = '%d,'*numfix
                format = format[:-1]
                format1 = '%g,'*numfix
                format1 = format1[:-1]
                phatistr = format % tuple(self.i_fixed)
                phatvstr = format1 % tuple(self.par[self.i_fixed])
                fixstr = 'Fixed: phat[%s] = %s ' % (phatistr,phatvstr)


        infostr = 'Fit method: %s, Fit p-value: %2.2f %s' % (self.method,self.pvalue,fixstr)
        try:
            plotbackend.figtext(0.05,0.01,infostr)
        except:
            pass

    def plotesf(self):
        '''  Plot Empirical and fitted Survival Function

        The purpose of the plot is to graphically assess whether
        the data could come from the fitted distribution.
        If so the empirical CDF should resemble the model CDF.
        Other distribution types will introduce deviations in the plot.
        '''
        n = len(self.data)
        SF = (arange(n,0,-1))/n
        plotbackend.semilogy(self.data,SF,'b.',self.data,self.sf(self.data),'r-')
        #plotbackend.plot(self.data,SF,'b.',self.data,self.sf(self.data),'r-')

        plotbackend.xlabel('x');
        plotbackend.ylabel('F(x) (%s)' % self.dist.name)
        plotbackend.title('Empirical SF plot')

    def plotecdf(self):
        '''  Plot Empirical and fitted Cumulative Distribution Function

        The purpose of the plot is to graphically assess whether
        the data could come from the fitted distribution.
        If so the empirical CDF should resemble the model CDF.
        Other distribution types will introduce deviations in the plot.
        '''
        n = len(self.data)
        F = (arange(1,n+1))/n
        plotbackend.plot(self.data,F,'b.',self.data,self.cdf(self.data),'r-')


        plotbackend.xlabel('x');
        plotbackend.ylabel('F(x) (%s)' % self.dist.name)
        plotbackend.title('Empirical CDF plot')

    def plotepdf(self):
        '''Plot Empirical and fitted Probability Density Function

        The purpose of the plot is to graphically assess whether
        the data could come from the fitted distribution.
        If so the histogram should resemble the model density.
        Other distribution types will introduce deviations in the plot.
        '''

        bin,limits = numpy.histogram(self.data,normed=True,new=True)
        limits.shape = (-1,1)
        xx = limits.repeat(3,axis=1)
        xx.shape = (-1,)
        xx = xx[1:-1]
        bin.shape = (-1,1)
        yy = bin.repeat(3,axis=1)
        #yy[0,0] = 0.0 # pdf
        yy[:,0] = 0.0 # histogram
        yy.shape = (-1,)
        yy = numpy.hstack((yy,0.0))

        #plotbackend.hist(self.data,normed=True,fill=False)
        plotbackend.plot(self.data,self.pdf(self.data),'r-',xx,yy,'b-')

        plotbackend.xlabel('x');
        plotbackend.ylabel('f(x) (%s)' % self.dist.name)
        plotbackend.title('Density plot')


    def plotresq(self):
        '''PLOTRESQ displays a residual quantile plot.

        The purpose of the plot is to graphically assess whether
        the data could come from the fitted distribution. If so the
        plot will be linear. Other distribution types will introduce
        curvature in the plot.
        '''
        n=len(self.data)
        eprob = (arange(1,n+1)-0.5)/n
        y = self.ppf(eprob)
        y1 = self.data[[0,-1]]
        plotbackend.plot(self.data,y,'b.',y1,y1,'r-')

        plotbackend.xlabel('Empirical')
        plotbackend.ylabel('Model (%s)' % self.dist.name)
        plotbackend.title('Residual Quantile Plot');
        plotbackend.axis('tight')
        plotbackend.axis('equal')


    def plotresprb(self):
        ''' PLOTRESPRB displays a residual probability plot.

        The purpose of the plot is to graphically assess whether
        the data could come from the fitted distribution. If so the
        plot will be linear. Other distribution types will introduce curvature in the plot.
        '''
        n = len(self.data);
        #ecdf = (0.5:n-0.5)/n;
        ecdf = arange(1,n+1)/(n+1)
        mcdf = self.cdf(self.data)
        p1 = [0,1]
        plotbackend.plot(ecdf,mcdf,'b.',p1,p1,'r-')


        plotbackend.xlabel('Empirical')
        plotbackend.ylabel('Model (%s)' % self.dist.name)
        plotbackend.title('Residual Probability Plot');
        plotbackend.axis([0, 1, 0, 1])
        plotbackend.axis('equal')


##  NANs are returned for unsupported parameters.
##    location and scale parameters are optional for each distribution.
##    The shape parameters are generally required
##
##    The loc and scale parameters must be given as keyword parameters.
##    These are related to the common symbols in the .lyx file

##  skew is third central moment / variance**(1.5)
##  kurtosis is fourth central moment / variance**2 - 3


## References::

##  Documentation for ranlib, rv2, cdflib and
##
##  Eric Wesstein's world of mathematics http://mathworld.wolfram.com/
##      http://mathworld.wolfram.com/topics/StatisticalDistributions.html
##
##  Documentation to Regress+ by Michael McLaughlin
##
##  Engineering and Statistics Handbook (NIST)
##      http://www.itl.nist.gov/div898/handbook/index.htm
##
##  Documentation for DATAPLOT from NIST
##      http://www.itl.nist.gov/div898/software/dataplot/distribu.htm
##
##  Norman Johnson, Samuel Kotz, and N. Balakrishnan "Continuous
##      Univariate Distributions", second edition,
##      Volumes I and II, Wiley & Sons, 1994.


## Each continuous random variable as the following methods
##
## rvs -- Random Variates (alternatively calling the class could produce these)
## pdf -- PDF
## cdf -- CDF
## sf  -- Survival Function (1-CDF)
## ppf -- Percent Point Function (Inverse of CDF)
## isf -- Inverse Survival Function (Inverse of SF)
## stats -- Return mean, variance, (Fisher's) skew, or (Fisher's) kurtosis
## nnlf  -- negative log likelihood function (to minimize)
## fit   -- Model-fitting
##
##  Maybe Later
##
##  hf  --- Hazard Function (PDF / SF)
##  chf  --- Cumulative hazard function (-log(SF))
##  psf --- Probability sparsity function (reciprocal of the pdf) in
##                units of percent-point-function (as a function of q).
##                Also, the derivative of the percent-point function.

## To define a new random variable you subclass the rv_continuous class
##   and re-define the
##
##   _pdf method which will be given clean arguments (in between a and b)
##        and passing the argument check method
##
##      If postive argument checking is not correct for your RV
##      then you will also need to re-define
##   _argcheck

##   Correct, but potentially slow defaults exist for the remaining
##       methods but for speed and/or accuracy you can over-ride
##
##     _cdf, _ppf, _rvs, _isf, _sf
##
##   Rarely would you override _isf  and _sf but you could.
##
##   Statistics are computed using numerical integration by default.
##     For speed you can redefine this using
##
##    _stats  --- take shape parameters and return mu, mu2, g1, g2
##            --- If you can't compute one of these return it as None
##
##            --- Can also be defined with a keyword argument moments=<str>
##                  where <str> is a string composed of 'm', 'v', 's',
##                  and/or 'k'.  Only the components appearing in string
##                 should be computed and returned in the order 'm', 'v',
##                  's', or 'k'  with missing values returned as None
##
##    OR
##
##  You can override
##
##    _munp    -- takes n and shape parameters and returns
##             --  then nth non-central moment of the distribution.
##

def valarray(shape,value=nan,typecode=None):
    """Return an array of all value.
    """
    out = reshape(repeat([value],product(shape,axis=0),axis=0),shape)
    if typecode is not None:
        out = out.astype(typecode)
    if not isinstance(out, ndarray):
        out = asarray(out)
    return out

# # This should be rewritten
##def argsreduce(cond, *args):
##    """Return a sequence of arguments converted to the dimensions of cond
##    """
##    newargs = list(args)
##    expand_arr = (cond==cond)
##    for k in range(len(args)):
##        # make sure newarr is not a scalar
##        newarr = atleast_1d(args[k])
##        newargs[k] = extract(cond,newarr*expand_arr)
##    return newargs


def argsreduce(cond, *args):
    """ Return the sequence of ravel(args[i]) where ravel(condition) is True in 1D

    Example
      >>> import numpy as np
      >>> rand = np.random.random_sample
      >>> A = rand((4,5))
      >>> B = 2
      >>> C = rand((1,5))
      >>> cond = np.ones(A.shape)
      >>> [A1,B1,C1] = argsreduce(cond,A,B,C)
      >>> B1.shape
      (20,)
      >>> cond[2,:] = 0
      >>> [A2,B2,C2] = argsreduce(cond,A,B,C)
      >>> B2.shape
      (15,)

    """

    newargs = atleast_1d(*args)
    if not isinstance(newargs,list):
        newargs = [newargs,]
    expand_arr = (cond==cond)
    return [extract(cond,arr1*expand_arr) for arr1 in newargs]


def common_shape(*args,**kwds):
    ''' Return the common shape of a sequence of arrays

    Parameters
    -----------
    *args : arraylike
        sequence of arrays
    **kwds :
        shape

    Returns
    -------
    shape : tuple
        common shape of the elements of args.

    Raises
    ------
    An error is raised if some of the arrays do not conform
    to the common shape according to the broadcasting rules in numpy.

    Examples
    --------
    >>> import numpy as np
    >>> A = np.ones((4,1))
    >>> B = 2
    >>> C = np.ones((1,5))*5
    >>> common_shape(A,B,C)
    (4, 5)
    >>> common_shape(A,B,C,shape=(3,4,1))
    (3, 4, 5)

    See also
    --------
    broadcast, broadcast_arrays
    '''


    shape = kwds.get('shape')
    argsout = atleast_1d(*args)
    if not isinstance(argsout,list):
        argsout = [argsout,]
    args_shape = [arg.shape for arg in argsout] #map(shape, varargout)
    if shape!=None:
        if not isinstance(shape,(list,tuple)):
            shape = (shape,)
        args_shape.append(tuple(shape))

    if len(set(args_shape))==1:
        # Common case
        return tuple(args_shape[0])

    ndims = map(len, args_shape)
    ndim = max(ndims)
    Np = len(args_shape)

    all_shapes = ones((Np, ndim),dtype=int)
    for ix, Nt in enumerate(ndims):
        all_shapes[ix, ndim-Nt::] = args_shape[ix]

    ndims = atleast_1d(ndims)
    if any(ndims == 0):
        all_shapes[ndims == 0, :] = 0

    comn_shape = all_shapes.max(axis=0)

    arrays_do_not_conform2common_shape = any(logical_and(all_shapes!=comn_shape[newaxis,...], all_shapes!=1),axis=1)

    if any(arrays_do_not_conform2common_shape):
        raise ValueError('Non-scalar input arguments do not match in shape according to numpy broadcasting rules')

    return tuple(comn_shape)


class rv_generic(object):
    """Class which encapsulates common functionality between rv_discrete
    and rv_continuous.

    """
    def fix_loc_scale(self, args, loc, scale=1):
        N = len(args)
        if N > self.numargs:
            if N == self.numargs + 1 and loc is None:
                # loc is given without keyword
                loc = args[-1]
            if N == self.numargs + 2 and scale is None:
                # loc and scale given without keyword
                loc, scale = args[-2:]
            args = args[:self.numargs]
        if scale is None:
            scale = 1.0
        if loc is None:
            loc = 0.0
        return args, loc, scale

    def fix_loc(self, args, loc):
        args, loc, scale = self.fix_loc_scale(args, loc)
        return args, loc

    # These are actually called, and should not be overwritten if you
    # want to keep error checking.
    def rvs(self,*args,**kwds):
        """Random variates of given type.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        size  - number of random variates (default=1)
        loc   - location parameter (default=0)
        scale - scale parameter (default=1)
        """
        kwd_names = ['loc', 'scale', 'size', 'discrete']
        loc, scale, size, discrete = map(kwds.get, kwd_names,
                                         [None]*len(kwd_names))

        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        cond = logical_and(self._argcheck(*args),(scale >= 0))
        if not all(cond):
            raise ValueError, "Domain error in arguments."

        # self._size is total size of all output values
        self._size = product(size, axis=0)
        if self._size > 1:
            size = numpy.array(size, ndmin=1)

        if scale == 0:
            return loc*ones(size, 'd')

        vals = self._rvs(*args)
        if self._size is not None:
            vals = reshape(vals, size)

        vals = vals * scale + loc

        # Cast to int if discrete
        if discrete:
            if numpy.isscalar(vals):
                vals = int(vals)
            else:
                vals = vals.astype(int)

        return vals

##
##        loc,scale = map(arr,(loc,scale))
##        args = tuple(map(arr,args))
##
##
##        cshape = common_shape(loc,scale,shape=size,*args)
##        #self._size = product(cshape)
##        self._size = cshape
##
##        vals = self._rvs(*args)
##
##        return vals * scale + loc


class rv_continuous(rv_generic):
    """A Generic continuous random variable.

    Continuous random variables are defined from a standard form chosen
    for simplicity of representation.  The standard form may require
    some shape parameters to complete its specification.  The distributions
    also take optional location and scale parameters using loc= and scale=
    keywords (defaults: loc=0, scale=1)

    These shape, scale, and location parameters can be passed to any of the
    methods of the RV object such as the following:

    generic.rvs(<shape(s)>,loc=0,scale=1,size=1)
        - random variates

    generic.pdf(x,<shape(s)>,loc=0,scale=1)
        - probability density function

    generic.cdf(x,<shape(s)>,loc=0,scale=1)
        - cumulative density function

    generic.sf(x,<shape(s)>,loc=0,scale=1)
        - survival function (1-cdf --- sometimes more accurate)

    generic.ppf(q,<shape(s)>,loc=0,scale=1)
        - percent point function (inverse of cdf --- percentiles)

    generic.isf(q,<shape(s)>,loc=0,scale=1)
        - inverse survival function (inverse of sf)

    generic.stats(<shape(s)>,loc=0,scale=1,moments='mv')
        - mean('m',axis=0), variance('v'), skew('s'), and/or kurtosis('k')

    generic.entropy(<shape(s)>,loc=0,scale=1)
        - (differential) entropy of the RV.

    myrv = generic.fit(data,<shape(s)>,loc=0,scale=1,method='ml', par_fix=None, alpha=0.05)
         - Parameter estimates for generic data returned in a frozen RV object

    Alternatively, the object may be called (as a function) to fix
       the shape, location, and scale parameters returning a
       "frozen" continuous RV object:

    myrv = generic(<shape(s)>,loc=0,scale=1)
        - frozen RV object with the same methods but holding the
            given shape, location, and scale fixed

    Examples:
    # Random number generation
    >>> import matplotlib.pyplot as plt
    >>> numargs = generic.numargs
    >>> [ <shape(s)> ] = [0.9,]*numargs
    >>> R = generic.rvs(<shape(s)>,size=100)

    # Compare ML and MPS method
    >>> phat = generic.fit(R,method='ml');
    >>> phat.plotfitsumry();  plt.figure(plt.gcf().number+1)
    >>> phat2 = generic.fit(R,method='mps')
    >>> phat2.plotfitsumry(); plt.figure(plt.gcf().number+1)

    #Fix loc=0 and estimate shapes and scale
    >>> fix_par = tuple([nan]*numargs + [0,nan])
    >>> phat3 = generic.fit(R,<shape(s)>,1,par_fix=fix_par, method='mps')
    >>> phat3.plotfitsumry(); plt.figure(plt.gcf().number+1)

    #Accurate confidence interval with profile loglikelihood
    >>> lp = phat3.profile()
    >>> lp.plot()
    >>> lp.get_CI()

    """
    def __init__(self, momtype=1, a=None, b=None, xa=-10.0, xb=10.0,
                 xtol=1e-14, badvalue=None, name=None, longname=None,
                 shapes=None, extradoc=None):

        rv_generic.__init__(self)

        if badvalue is None:
            badvalue = nan
        self.badvalue = badvalue
        self.name = name
        self.a = a
        self.b = b
        if a is None:
            self.a = -inf
        if b is None:
            self.b = inf
        self.xa = xa
        self.xb = xb
        self.xtol = xtol
        self._size = 1
        self.m = 0.0
        self.moment_type = momtype

        self.expandarr = 1

        if not hasattr(self,'numargs'):
            #allows more general subclassing with *args
            cdf_signature = inspect.getargspec(self._cdf.im_func)
            numargs1 = len(cdf_signature[0]) - 2
            pdf_signature = inspect.getargspec(self._pdf.im_func)
            numargs2 = len(pdf_signature[0]) - 2
            self.numargs = max(numargs1, numargs2)
        #nin correction
        self.vecfunc = sgf(self._ppf_single_call,otypes='d')
        self.vecfunc.nin = self.numargs + 1
        self.vecentropy = sgf(self._entropy,otypes='d')
        self.vecentropy.nin = self.numargs + 1
        self.veccdf = sgf(self._cdf_single_call,otypes='d')
        self.veccdf.nin = self.numargs+1
        self.shapes = shapes
        self.extradoc = extradoc
        if momtype == 0:
            self.generic_moment = sgf(self._mom0_sc,otypes='d')
        else:
            self.generic_moment = sgf(self._mom1_sc,otypes='d')
        self.generic_moment.nin = self.numargs+1 # Because of the *args argument
        # of _mom0_sc, vectorize cannot count the number of arguments correctly.

        if longname is None:
            if name[0] in ['aeiouAEIOU']: hstr = "An "
            else: hstr = "A "
            longname = hstr + name
        if self.__doc__ is None:
            self.__doc__ = rv_continuous.__doc__
        if self.__doc__ is not None:
            if longname is not None:
                self.__doc__ = self.__doc__.replace("A Generic",longname)
            if name is not None:
                self.__doc__ = self.__doc__.replace("generic",name)
            if shapes is None:
                self.__doc__ = self.__doc__.replace("<shape(s)>,","")
            else:
                self.__doc__ = self.__doc__.replace("<shape(s)>",shapes)
            if extradoc is not None:
                self.__doc__ = self.__doc__ + extradoc

    def _ppf_to_solve(self, x, q,*args):
        return apply(self.cdf, (x, )+args)-q

    def _ppf_single_call(self, q, *args):
        return optimize.brentq(self._ppf_to_solve, self.xa, self.xb, args=(q,)+args, xtol=self.xtol)

    # moment from definition
    def _mom_integ0(self, x,m,*args):
        return x**m * self.pdf(x,*args)
    def _mom0_sc(self, m,*args):
        return quad(self._mom_integ0, self.a,
                                    self.b, args=(m,)+args)[0]
    #        return scipy.integrate.quad(self._mom_integ0, self.a,
    #                                    self.b, args=(m,)+args)[0]
    # moment calculated using ppf
    def _mom_integ1(self, q,m,*args):
        return (self.ppf(q,*args))**m
    def _mom1_sc(self, m,*args):
        return quad(self._mom_integ1, 0, 1,args=(m,)+args)[0]
        #return scipy.integrate.quad(self._mom_integ1, 0, 1,args=(m,)+args)[0]

    ## These are the methods you must define (standard form functions)
    def _argcheck(self, *args):
        # Default check for correct values on args and keywords.
        # Returns condition array of 1's where arguments are correct and
        #  0's where they are not.
        cond = 1
        for arg in args:
            cond = logical_and(cond,(arr(arg) > 0))
        return cond

    def _pdf(self,x,*args):
        return derivative(self._cdf,x,dx=1e-5,args=args,order=5)

    ## Could also define any of these (return 1-d using self._size to get number)
    def _rvs(self, *args):
        ## Use basic inverse cdf algorithm for RV generation as default.
        U = mtrand.sample(self._size)
        Y = self._ppf(U,*args)
        return Y

    def _cdf_single_call(self, x, *args):
        return quad(self._pdf, self.a, x, args=args)[0]
    #return scipy.integrate.quad(self._pdf, self.a, x, args=args)[0]

    def _cdf(self, x, *args):
        return self.veccdf(x,*args)

    def _sf(self, x, *args):
        return 1.0-self._cdf(x,*args)

    def _chf(self,x,*args):
        return -log1p(-self._cdf(x,*args))

    def _ppf(self, q, *args):
        return self.vecfunc(q,*args)

    def _isf(self, q, *args):
        return self._ppf(1.0-q,*args) #use correct _ppf for subclasses

    # The actual calcuation functions (no basic checking need be done)
    #  If these are defined, the others won't be looked at.
    #  Otherwise, the other set can be defined.
    def _stats(self,*args, **kwds):
        moments = kwds.get('moments')
        return None, None, None, None

    #  Central moments
    def _munp(self,n,*args):
        return self.generic_moment(n,*args)

    def pdf(self,x,*args,**kwds):
        """Probability density function at x of the given RV.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        scale - scale parameter (default=1)
        """
        loc,scale=map(kwds.get,['loc','scale'])
        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        x,loc,scale = map(arr,(x,loc,scale))
        args = tuple(map(arr,args))
        x = arr((x-loc)*1.0/scale)
        cond0 = self._argcheck(*args) & (scale > 0)
        cond1 = (scale > 0) & (x >= self.a) & (x <= self.b)
        cond = cond0 & cond1
        output = zeros(shape(cond),'d')
        putmask(output,(1-cond0)*array(cond1,bool),self.badvalue)
        goodargs = argsreduce(cond, *((x,)+args+(scale,)))
        scale, goodargs = goodargs[-1], goodargs[:-1]
        place(output,cond,self._pdf(*goodargs) / scale)
        if output.ndim == 0:
            return output[()]
        return output

    def cdf(self,x,*args,**kwds):
        """Cumulative distribution function at x of the given RV.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        scale - scale parameter (default=1)
        """
        loc,scale=map(kwds.get,['loc','scale'])
        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        x,loc,scale = map(arr,(x,loc,scale))
        args = tuple(map(arr,args))
        x = (x-loc)*1.0/scale
        cond0 = self._argcheck(*args) & (scale > 0)
        cond1 = (scale > 0) & (x > self.a) & (x < self.b)
        cond2 = (x >= self.b) & cond0
        cond = cond0 & cond1
        output = zeros(shape(cond),'d')
        place(output,(1-cond0)*(cond1==cond1),self.badvalue)
        place(output,cond2,1.0)
        if any(cond):  #call only if at least 1 entry
            goodargs = argsreduce(cond, *((x,)+args))
            place(output,cond,self._cdf(*goodargs))
        if output.ndim == 0:
            return output[()]
        return output

    def sf(self,x,*args,**kwds):
        """Survival function (1-cdf) at x of the given RV.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        scale - scale parameter (default=1)
        """
        loc,scale = map(kwds.get,['loc','scale'])
        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        x,loc,scale = map(arr,(x,loc,scale))
        args = tuple(map(arr,args))
        x = (x-loc)*1.0/scale
        cond0 = self._argcheck(*args) & (scale > 0)
        cond1 = (scale > 0) & (x > self.a) & (x < self.b)
        cond2 = cond0 & (x <= self.a)
        cond = cond0 & cond1
        output = zeros(shape(cond),'d')
        place(output,(1-cond0)*(cond1==cond1),self.badvalue)
        place(output,cond2,1.0)
        goodargs = argsreduce(cond, *((x,)+args))
        place(output,cond,self._sf(*goodargs))
        if output.ndim == 0:
            return output[()]
        return output

    def chf(self,x,*args,**kwds):
        """Cumulative hazard function -log(1-cdf) at x of the given RV.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        scale - scale parameter (default=1)
        """
        loc,scale = map(kwds.get,['loc','scale'])
        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        x,loc,scale = map(arr,(x,loc,scale))
        args = tuple(map(arr,args))
        x = (x-loc)*1.0/scale
        ok_shape_scale = self._argcheck(*args) & (scale > 0)
        cond1 = (scale > 0) & (x > self.a) & (x < self.b)
        cond2 = ok_shape_scale & (x <= self.a)
        cond = ok_shape_scale & cond1
        output = zeros(shape(cond),'d')
        place(output,(1-ok_shape_scale)*(cond1==cond1),self.badvalue)
        place(output,cond1,-inf)
        if any(cond):
            goodargs = argsreduce(cond, *((x,)+args))
            place(output,cond,self._chf(*goodargs))
        if output.ndim == 0:
            return output[()]
        return output
    def ppf(self,q,*args,**kwds):
        """Percent point function (inverse of cdf) at q of the given RV.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        scale - scale parameter (default=1)
        """
        loc,scale=map(kwds.get,['loc','scale'])
        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        q,loc,scale = map(arr,(q,loc,scale))
        args = tuple(map(arr,args))
        cond0 = self._argcheck(*args) & (scale > 0) & (loc==loc)
        cond1 = (q > 0) & (q < 1)
        cond2 = (q==1) & cond0
        cond = cond0 & cond1
        output = valarray(shape(cond),value=self.a*scale + loc)
        place(output,(1-cond0)+(1-cond1)*(q!=0.0), self.badvalue)
        place(output,cond2,self.b*scale + loc)
        if any(cond):  #call only if at least 1 entry
            goodargs = argsreduce(cond, *((q,)+args+(scale,loc)))
            scale, loc, goodargs = goodargs[-2], goodargs[-1], goodargs[:-2]
            place(output,cond,self._ppf(*goodargs)*scale + loc)
        if output.ndim == 0:
            return output[()]
        return output

    def isf(self,q,*args,**kwds):
        """Inverse survival function at q of the given RV.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        scale - scale parameter (default=1)
        """
        loc,scale=map(kwds.get,['loc','scale'])
        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        q,loc,scale = map(arr,(q,loc,scale))
        args = tuple(map(arr,args))
        cond0 = self._argcheck(*args) & (scale > 0) & (loc==loc)
        cond1 = (q > 0) & (q < 1)
        cond2 = (q==1) & cond0
        cond = cond0 & cond1
        output = valarray(shape(cond),value=self.b)
        #place(output,(1-cond0)*(cond1==cond1), self.badvalue)
        place(output,(1-cond0)*(cond1==cond1)+(1-cond1)*(q!=0.0), self.badvalue)
        place(output,cond2,self.a)
        if any(cond):  #call only if at least 1 entry
            goodargs = argsreduce(cond, *((q,)+args+(scale,loc)))  #PB replace 1-q by q
            scale, loc, goodargs = goodargs[-2], goodargs[-1], goodargs[:-2]
            place(output,cond,self._isf(*goodargs)*scale + loc) #PB use _isf instead of _ppf
        if output.ndim == 0:
            return output[()]
        return output

    def stats(self,*args,**kwds):
        """Some statistics of the given RV

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc     - location parameter (default=0)
        scale   - scale parameter (default=1)
        moments - a string composed of letters ['mvsk'] specifying
                   which moments to compute (default='mv')
                   'm' = mean,
                   'v' = variance,
                   's' = (Fisher's) skew,
                   'k' = (Fisher's) kurtosis.
        """
        loc,scale,moments=map(kwds.get,['loc','scale','moments'])

        N = len(args)
        if N > self.numargs:
            if N == self.numargs + 1 and loc is None:
                # loc is given without keyword
                loc = args[-1]
            if N == self.numargs + 2 and scale is None:
                # loc and scale given without keyword
                loc, scale = args[-2:]
            if N == self.numargs + 3 and moments is None:
                # loc, scale, and moments
                loc, scale, moments = args[-3:]
            args = args[:self.numargs]
        if scale is None: scale = 1.0
        if loc is None: loc = 0.0
        if moments is None: moments = 'mv'

        loc,scale = map(arr,(loc,scale))
        args = tuple(map(arr,args))
        cond = self._argcheck(*args) & (scale > 0) & (loc==loc)

        signature = inspect.getargspec(self._stats.im_func)
        if (signature[2] is not None) or ('moments' in signature[0]):
            mu, mu2, g1, g2 = self._stats(*args,**{'moments':moments})
        else:
            mu, mu2, g1, g2 = self._stats(*args)
        if g1 is None:
            mu3 = None
        else:
            mu3 = g1*np.power(mu2,1.5) #(mu2**1.5) breaks down for nan and nin
        default = valarray(shape(cond), self.badvalue)
        output = []

        # Use only entries that are valid in calculation
        goodargs = argsreduce(cond, *(args+(scale,loc)))
        scale, loc, goodargs = goodargs[-2], goodargs[-1], goodargs[:-2]
        if 'm' in moments:
            if mu is None:
                mu = self._munp(1.0,*goodargs)
            out0 = default.copy()
            place(out0,cond,mu*scale+loc)
            output.append(out0)

        if 'v' in moments:
            if mu2 is None:
                mu2p = self._munp(2.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                mu2 = mu2p - mu*mu
            if np.isinf(mu):
                #if mean is inf then var is also inf
                mu2 = np.inf
            out0 = default.copy()
            place(out0,cond,mu2*scale*scale)
            output.append(out0)

        if 's' in moments:
            if g1 is None:
                mu3p = self._munp(3.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                if mu2 is None:
                    mu2p = self._munp(2.0,*goodargs)
                    mu2 = mu2p - mu*mu
                mu3 = mu3p - 3*mu*mu2 - mu**3
                g1 = mu3 / mu2**1.5
            out0 = default.copy()
            place(out0,cond,g1)
            output.append(out0)

        if 'k' in moments:
            if g2 is None:
                mu4p = self._munp(4.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                if mu2 is None:
                    mu2p = self._munp(2.0,*goodargs)
                    mu2 = mu2p - mu*mu
                if mu3 is None:
                    mu3p = self._munp(3.0,*goodargs)
                    mu3 = mu3p - 3*mu*mu2 - mu**3
                mu4 = mu4p - 4*mu*mu3 - 6*mu*mu*mu2 - mu**4
                g2 = mu4 / mu2**2.0 - 3.0
            out0 = default.copy()
            place(out0,cond,g2)
            output.append(out0)

        if len(output) == 1:
            return output[0]
        else:
            return tuple(output)

    def moment(self, n, *args):
        if (floor(n) != n):
            raise ValueError, "Moment must be an integer."
        if (n < 0): raise ValueError, "Moment must be positive."
        if (n == 0): return 1.0
        if (n > 0) and (n < 5):
            signature = inspect.getargspec(self._stats.im_func)
            if (signature[2] is not None) or ('moments' in signature[0]):
                mdict = {'moments':{1:'m',2:'v',3:'vs',4:'vk'}[n]}
            else:
                mdict = {}
            mu, mu2, g1, g2 = self._stats(*args,**mdict)
            if (n==1):
                if mu is None: return self._munp(1,*args)
                else: return mu
            elif (n==2):
                if mu2 is None or mu is None: return self._munp(2,*args)
                else: return mu2 + mu*mu
            elif (n==3):
                if g1 is None or mu2 is None: return self._munp(3,*args)
                else: return g1*(mu2**1.5)
            else: # (n==4)
                if g2 is None or mu2 is None: return self._munp(4,*args)
                else: return (g2+3.0)*(mu2**2.0)
        else:
            return self._munp(n,*args)
    def pvalue(self,theta,x,unknown_numpar=None):
        ''' Return the P-value for the fit using Moran's negative log Product Spacings statistic

            where theta are the parameters (including loc and scale)

            Note: the data in x must be sorted
        '''
        dx = numpy.diff(x,axis=0)
        tie = (dx==0)
        if any(tie):
            disp('P-value is on the conservative side (i.e. too large) due to ties in the data!')

        T = self.nlogps(theta,x)

        n = len(x)
        np1 = n+1
        if unknown_numpar==None:
            k = len(theta)
        else:
            k = unknown_numpar

        isParUnKnown = True
        m = (np1)*(log(np1)+0.57722)-0.5-1.0/(12.*(np1))
        v = (np1)*(pi**2./6.0-1.0)-0.5-1.0/(6.*(np1))
        C1 = m-sqrt(0.5*n*v)
        C2 = sqrt(v/(2.0*n))
        Tn = (T + 0.5*k*isParUnKnown-C1)/C2 # chi2 with n degrees of freedom
        pvalue = chi2.sf(Tn,n)
        return pvalue

    def nlogps(self,theta,x):
        """ Moran's negative log Product Spacings statistic

            where theta are the parameters (including loc and scale)

            Note the data in x must be sorted

        References
        -----------

        R. C. H. Cheng; N. A. K. Amin (1983)
        "Estimating Parameters in Continuous Univariate Distributions with a
        Shifted Origin.",
        Journal of the Royal Statistical Society. Series B (Methodological),
        Vol. 45, No. 3. (1983), pp. 394-403.

        R. C. H. Cheng; M. A. Stephens (1989)
        "A Goodness-Of-Fit Test Using Moran's Statistic with Estimated
        Parameters", Biometrika, 76, 2, pp 385-392

        Wong, T.S.T. and Li, W.K. (2006)
        "A note on the estimation of extreme value distributions using maximum
        product of spacings.",
        IMS Lecture Notes Monograph Series 2006, Vol. 52, pp. 272-283
        """

        try:
            loc = theta[-2]
            scale = theta[-1]
            args = tuple(theta[:-2])
        except IndexError:
            raise ValueError, "Not enough input arguments."
        if not self._argcheck(*args) or scale <= 0:
            return inf
        x = arr((x-loc) / scale)
        cond0 = (x <= self.a) | (x >= self.b)
        if (any(cond0)):
            return inf
        else:
            linfo = numpy.finfo(float)
            realmax = floatinfo.machar.xmax

            lowertail = True
            if lowertail:
                prb = numpy.hstack((0.0, self.cdf(x,*args), 1.0))
                dprb = numpy.diff(prb)
            else:
                prb = numpy.hstack((1.0, self.sf(x,*args), 0.0))
                dprb = -numpy.diff(prb)

            logD = log(dprb)
            dx = numpy.diff(x,axis=0)
            tie = (dx==0)
            if any(tie):
                # TODO % implement this method for treating ties in data:
                # Assume measuring error is delta. Then compute
                # yL = F(xi-delta,theta)
                # yU = F(xi+delta,theta)
                # and replace
                # logDj = log((yU-yL)/(r-1)) for j = i+1,i+2,...i+r-1

                # The following is OK when only minimization of T is wanted

                i_tie = nonzero(tie)
                tiedata = x[i_tie]

                logD[(I_tie[0]+1,)]= log(self._pdf(tiedata,*args)) + log(scale)

            finiteD = numpy.isfinite(logD)
            nonfiniteD = 1-finiteD
            if any(nonfiniteD):
                T = -sum(logD[finiteD],axis=0) + 100.0*log(realmax)*sum(nonfiniteD,axis=0);
            else:
                T = -sum(logD,axis=0) #%Moran's negative log product spacing statistic
        return T
    def link(self,x,logSF,theta,i):
        ''' Return dist. par. no. i as function of quantile (x) and log survival probability (sf)

            Assumptions:
            ------------
             phat is list containing all parameters including location and scale.
        '''
        raise ValueError('Link function not implemented for the %s distribution' % self.name)
        return None
    def _nnlf(self, x, *args):
        return -sum(log(self._pdf(x, *args)),axis=0)

    def nnlf(self, theta, x):
        ''' Return negative loglikelihood function, i.e., - sum (log pdf(x, theta),axis=0)
           where theta are the parameters (including loc and scale)
        '''
        try:
            loc = theta[-2]
            scale = theta[-1]
            args = tuple(theta[:-2])
        except IndexError:
            raise ValueError, "Not enough input arguments."
        if not self._argcheck(*args) or scale <= 0:
            return inf
        x = arr((x-loc) / scale)
        cond0 = (x<=self.a) | (self.b<=x)
        newCall = False
        if newCall:
            goodargs = argsreduce(1-cond0, *((x,)))
            goodargs = tuple(goodargs + list(args))
            N = len(x)
            Nbad = sum(cond0)
            xmin = floatinfo.machar.xmin
            return self._nnlf(*goodargs) + N*log(scale) + Nbad*100.0*log(xmin)
        elif (any(cond0)):
            return inf
        else:
            N = len(x)
            return self._nnlf(x, *args) + N*log(scale)
    def hessian_nnlf(self,theta,data,eps=None):
        ''' approximate hessian of nnlf where theta are the parameters (including loc and scale)
        '''
        #Nd = len(x)
        np = len(theta)
        # pab 07.01.2001: Always choose the stepsize h so that
        # it is an exactly representable number.
        # This is important when calculating numerical derivatives and is
        #  accomplished by the following.

        if eps==None:
            eps = (floatinfo.machar.eps)**0.4
        xmin = floatinfo.machar.xmin
        #myfun = lambda y: max(y,100.0*log(xmin)) #% trick to avoid log of zero
        delta  = (eps+2.0)-2.0
        delta2 = delta**2.0
        #    % Approximate 1/(nE( (d L(x|theta)/dtheta)^2)) with
        #    %             1/(d^2 L(theta|x)/dtheta^2)
        #    %  using central differences

        LL = self.nnlf(theta,data)
        H = zeros((np,np))   #%% Hessian matrix
        theta = tuple(theta)
        for ix in xrange(np):
            sparam = list(theta)
            sparam[ix]= theta[ix]+delta
            fp  = self.nnlf(sparam,data)
            #fp = sum(myfun(x))

            sparam[ix] = theta[ix]-delta
            fm  = self.nnlf(sparam,data)
            #fm = sum(myfun(x))

            H[ix,ix] = (fp-2*LL+fm)/delta2
            for iy in range(ix+1,np):
                sparam[ix] = theta[ix]+delta
                sparam[iy] = theta[iy]+delta
                fpp  = self.nnlf(sparam,data)
                #fpp = sum(myfun(x))

                sparam[iy] = theta[iy]-delta
                fpm  = self.nnlf(sparam,data)
                #fpm = sum(myfun(x))

                sparam[ix] = theta[ix]-delta
                fmm  = self.nnlf(sparam,data)
                #fmm = sum(myfun(x));

                sparam[iy] = theta[iy]+delta
                fmp  = self.nnlf(sparam,data)
                #fmp = sum(myfun(x))
                H[ix,iy] = ((fpp+fmm)-(fmp+fpm))/(4.*delta2)
                H[iy,ix] = H[ix,iy]
                sparam[iy] = theta[iy];

        # invert the Hessian matrix (i.e. invert the observed information number)
        #pcov = -pinv(H);
        return -H

    def fit(self, data, *args, **kwds):
        ''' Return Maximum Likelihood or Maximum Product Spacing estimator object

          CALL  generic.fit(data,*args,**kwds)

        data   = data used in fitting

        *args
        =====
        list of initial non-fixed distribution parameter-values
        including loc and scale (see docstring of the
           instance object for more information)

        **kwds
        ======
        method  - String describing the method of estimation. Options are
                    'ml' : Maximum Likelihood method (default)
                    'mps': Maximum Product Spacing method
        alpha   - Confidence coefficent             (default 0.05)
        par_fix - List of fixed parameters. Non fixed parameters must be given as NaN's.
                  (Must have the same length as the number of parameters or be None)
                  (default None)
        search  - If true search for best estimator (default),
                    otherwise return object with initial distribution parameters
        copydata - If true copydata (default)

        Note: data is sorted using this function, so if copydata==False the data
            in your namespace will be sorted as well.
        '''
        return  FitDistribution(self, data, *args, **kwds)

#        loc0, scale0, method = map(kwds.get, ['loc', 'scale','method'],[none, none,'ml'])
#        args, loc0, scale0 = self.fix_loc_scale(args, loc0, scale0)
#        Narg = len(args)
#        if Narg != self.numargs:
#            if Narg > self.numargs:
#                raise ValueError, "Too many input arguments."
#            else:
#                args += (1.0,)*(self.numargs-Narg)
#        # location and scale are at the end
#        x0 = args + (loc0, scale0)
#        if method.lower()[:].startswith('mps'):
#            data.sort()
#            fitfun = self.nlogps
#        else:
#            fitfun = self.nnlf
#
#        return optimize.fmin(fitfun,x0,args=(ravel(data),),disp=0)

    def est_loc_scale(self, data, *args):
        mu, mu2 = self.stats(*args,**{'moments':'mv'})
        muhat = st.nanmean(data)
        mu2hat = st.nanstd(data)
        Shat = sqrt(mu2hat / mu2)
        Lhat = muhat - Shat*mu
        return Lhat, Shat

    def freeze(self,*args,**kwds):
        return rv_frozen(self,*args,**kwds)

    def __call__(self, *args, **kwds):
        return self.freeze(*args, **kwds)

    def _entropy(self, *args):
        def integ(x):
            val = self._pdf(x, *args)
            return val*log(val)
        entr = -quad(integ,self.a,self.b)[0]
	if np.isnan(entr):
            # try with different limits if integration problems
            low,upp = self.ppf([0.001,0.999],*args)
            if np.isinf(self.b):
                upper = upp
            else:
                upper = self.b
            if np.isinf(self.a):
                lower = low
            else:
                lower = self.a
            entr = -quad(integ,lower,upper)[0]
	return entr


    def entropy(self, *args, **kwds):
        loc,scale=map(kwds.get,['loc','scale'])
        args, loc, scale = self.fix_loc_scale(args, loc, scale)
        args = tuple(map(arr,args))
        cond0 = self._argcheck(*args) & (scale > 0) & (loc==loc)
        output = zeros(shape(cond0),'d')
        place(output,(1-cond0),self.badvalue)
        goodargs = argsreduce(cond0, *args)
        #I don't know when or why vecentropy got broken when numargs == 0
        if self.numargs == 0:
            place(output,cond0,self._entropy()+log(scale))
        else:
            place(output,cond0,self.vecentropy(*goodargs)+log(scale))
        return output

_EULER = 0.577215664901532860606512090082402431042  # -special.psi(1)
_ZETA3 = 1.202056903159594285399738161511449990765  # special.zeta(3,1)  Apery's constant

## Kolmogorov-Smirnov one-sided and two-sided test statistics

class ksone_gen(rv_continuous):
    def _cdf(self,x,n):
        return 1.0-special.smirnov(n,x)
    def _ppf(self,q,n):
        return special.smirnovi(n,1.0-q)
ksone = ksone_gen(a=0.0,name='ksone', longname="Kolmogorov-Smirnov "\
                  "A one-sided test statistic.", shapes="n",
                  extradoc="""

General Kolmogorov-Smirnov one-sided test.
"""
                  )

class kstwobign_gen(rv_continuous):
    def _cdf(self,x):
        return 1.0-special.kolmogorov(x)
    def _sf(self,x):
        return special.kolmogorov(x)
    def _ppf(self,q):
        return special.kolmogi(1.0-q)
kstwobign = kstwobign_gen(a=0.0,name='kstwobign', longname='Kolmogorov-Smirnov two-sided (for large N)', extradoc="""

Kolmogorov-Smirnov two-sided test for large N
"""
                          )


## Normal distribution

# loc = mu, scale = std
# Keep these implementations out of the class definition so they can be reused
# by other distributions.
def _norm_pdf(x):
    return exp(-x**2/2.0)/sqrt(2*pi)
def _norm_cdf(x):
    return special.ndtr(x)
def _norm_ppf(q):
    return special.ndtri(q)
class norm_gen(rv_continuous):
    def _rvs(self):
        return mtrand.standard_normal(self._size)
    def _pdf(self,x):
        return _norm_pdf(x)
    def _cdf(self,x):
        return _norm_cdf(x)
    def _ppf(self,q):
        return _norm_ppf(q)
    def _isf(self,q):
        return -_norm_ppf(q)
    def _stats(self):
        return 0.0, 1.0, 0.0, 0.0
    def _entropy(self):
        return 0.5*(log(2*pi)+1)
norm = norm_gen(name='norm',longname='A normal',extradoc="""

Normal distribution

The location (loc) keyword specifies the mean.
The scale (scale) keyword specifies the standard deviation.

normal.pdf(x) = exp(-x**2/2)/sqrt(2*pi)
""")


## Alpha distribution
##
class alpha_gen(rv_continuous):
    def _pdf(self, x, a):
        return 1.0/arr(x**2)/special.ndtr(a)*norm.pdf(a-1.0/x)
    def _cdf(self, x, a):
        return special.ndtr(a-1.0/x) / special.ndtr(a)
    def _ppf(self, q, a):
        return 1.0/arr(a-special.ndtri(q*special.ndtr(a)))
    def _stats(self, a):
        return [inf]*2 + [nan]*2
alpha = alpha_gen(a=0.0,name='alpha',shapes='a',extradoc="""

Alpha distribution

alpha.pdf(x,a) = 1/(x**2*Phi(a)*sqrt(2*pi)) * exp(-1/2 * (a-1/x)**2)
where Phi(alpha) is the normal CDF, x > 0, and a > 0.
""")

## Anglit distribution
##
class anglit_gen(rv_continuous):
    def _pdf(self, x):
        return cos(2*x)
    def _cdf(self, x):
        return sin(x+pi/4)**2.0
    def _ppf(self, q):
        return (arcsin(sqrt(q))-pi/4)
    def _stats(self):
        return 0.0, pi*pi/16-0.5, 0.0, -2*(pi**4 - 96)/(pi*pi-8)**2
    def _entropy(self):
        return 1-log(2)
anglit = anglit_gen(a=-pi/4,b=pi/4,name='anglit', extradoc="""

Anglit distribution

anglit.pdf(x) = sin(2*x+pi/2) = cos(2*x)    for -pi/4 <= x <= pi/4
""")


## Arcsine distribution
##
class arcsine_gen(rv_continuous):
    def _pdf(self, x):
        return 1.0/pi/sqrt(x*(1-x))
    def _cdf(self, x):
        return 2.0/pi*arcsin(sqrt(x))
    def _ppf(self, q):
        return sin(pi/2.0*q)**2.0
    def _stats(self):
        mup = 0.5, 3.0/8.0, 15.0/48.0, 35.0/128.0
        mu = 0.5
        mu2 = 1.0/8
        g1 = 0
        g2 = -3.0/2.0
        return mu, mu2, g1, g2
    def _entropy(self):
        return -0.24156447527049044468
arcsine = arcsine_gen(a=0.0,b=1.0,name='arcsine',extradoc="""

Arcsine distribution

arcsine.pdf(x) = 1/(pi*sqrt(x*(1-x)))
for 0 < x < 1.
""")


## Beta distribution
##
class beta_gen(rv_continuous):
    def _rvs(self, a, b):
        return mtrand.beta(a,b,self._size)
    def _pdf(self, x, a, b):
        Px = (1.0-x)**(b-1.0) * x**(a-1.0)
        Px /= special.beta(a,b)
        return Px
    def _cdf(self, x, a, b):
        return special.btdtr(a,b,x)
    def _ppf(self, q, a, b):
        return special.btdtri(a,b,q)
    def _stats(self, a, b):
        mn = a *1.0 / (a + b)
        var = (a*b*1.0)/(a+b+1.0)/(a+b)**2.0
        g1 = 2.0*(b-a)*sqrt((1.0+a+b)/(a*b)) / (2+a+b)
        g2 = 6.0*(a**3 + a**2*(1-2*b) + b**2*(1+b) - 2*a*b*(2+b))
        g2 /= a*b*(a+b+2)*(a+b+3)
        return mn, var, g1, g2
beta = beta_gen(a=0.0, b=1.0, name='beta',shapes='a,b',extradoc="""

Beta distribution

beta.pdf(x, a, b) = gamma(a+b)/(gamma(a)*gamma(b)) * x**(a-1) * (1-x)**(b-1)
for 0 < x < 1, a, b > 0.
""")

## Beta Prime
class betaprime_gen(rv_continuous):
    def _rvs(self, a, b):
        u1 = gamma.rvs(a,size=self._size)
        u2 = gamma.rvs(b,size=self._size)
        return (u1 / u2)
    def _pdf(self, x, a, b):
        return 1.0/special.beta(a,b)*x**(a-1.0)/(1+x)**(a+b)
    def _cdf_skip(self, x, a, b):
        # remove for now: special.hyp2f1 is incorrect for large a
        x = where(x==1.0, 1.0-1e-6,x)
        return pow(x,a)*special.hyp2f1(a+b,a,1+a,-x)/a/special.beta(a,b)
    def _munp(self, n, a, b):
        if (n == 1.0):
            return where(b > 1, a/(b-1.0), inf)
        elif (n == 2.0):
            return where(b > 2, a*(a+1.0)/((b-2.0)*(b-1.0)), inf)
        elif (n == 3.0):
            return where(b > 3, a*(a+1.0)*(a+2.0)/((b-3.0)*(b-2.0)*(b-1.0)),
                         inf)
        elif (n == 4.0):
            return where(b > 4,
                         a*(a+1.0)*(a+2.0)*(a+3.0)/((b-4.0)*(b-3.0) \
                                                    *(b-2.0)*(b-1.0)), inf)
        else:
            raise NotImplementedError
betaprime = betaprime_gen(a=0.0, b=500.0, name='betaprime', shapes='a,b',
                          extradoc="""

Beta prime distribution

betaprime.pdf(x, a, b) = gamma(a+b)/(gamma(a)*gamma(b))
                          * x**(a-1) * (1-x)**(-a-b)
for x > 0, a, b > 0.
""")

## Bradford
##

class bradford_gen(rv_continuous):
    def _pdf(self, x, c):
        return  c / (c*x + 1.0) / log(1.0+c)
    def _cdf(self, x, c):
        return log(1.0+c*x) / log(c+1.0)
    def _ppf(self, q, c):
        return ((1.0+c)**q-1)/c
    def _stats(self, c, moments='mv'):
        k = log(1.0+c)
        mu = (c-k)/(c*k)
        mu2 = ((c+2.0)*k-2.0*c)/(2*c*k*k)
        g1 = None
        g2 = None
        if 's' in moments:
            g1 = sqrt(2)*(12*c*c-9*c*k*(c+2)+2*k*k*(c*(c+3)+3))
            g1 /= sqrt(c*(c*(k-2)+2*k))*(3*c*(k-2)+6*k)
        if 'k' in moments:
            g2 = c**3*(k-3)*(k*(3*k-16)+24)+12*k*c*c*(k-4)*(k-3) \
               + 6*c*k*k*(3*k-14) + 12*k**3
            g2 /= 3*c*(c*(k-2)+2*k)**2
        return mu, mu2, g1, g2
    def _entropy(self, c):
        k = log(1+c)
        return k/2.0 - log(c/k)
bradford = bradford_gen(a=0.0, b=1.0, name='bradford', longname="A Bradford",
                        shapes='c', extradoc="""

Bradford distribution

bradford.pdf(x,c) = c/(k*(1+c*x))
for 0 < x < 1, c > 0 and k = log(1+c).
""")


## Burr

# burr with d=1 is called the fisk distribution
class burr_gen(rv_continuous):
    def _pdf(self, x, c, d):
        return c*d*(x**(-c-1.0))*((1+x**(-c*1.0))**(-d-1.0))
    def _cdf(self, x, c, d):
        return (1+x**(-c*1.0))**(-d**1.0)
    def _ppf(self, q, c, d):
        return (q**(-1.0/d)-1)**(-1.0/c)
    def _stats(self, c, d, moments='mv'):
        g2c, g2cd = gam(1-2.0/c), gam(2.0/c+d)
        g1c, g1cd = gam(1-1.0/c), gam(1.0/c+d)
        gd = gam(d)
        k = gd*g2c*g2cd - g1c**2 * g1cd**2
        mu = g1c*g1cd / gd
        mu2 = k / gd**2.0
        g1, g2 = None, None
        g3c, g3cd = None, None
        if 's' in moments:
            g3c, g3cd = gam(1-3.0/c), gam(3.0/c+d)
            g1 = 2*g1c**3 * g1cd**3 + gd*gd*g3c*g3cd - 3*gd*g2c*g1c*g1cd*g2cd
            g1 /= sqrt(k**3)
        if 'k' in moments:
            if g3c is None:
                g3c = gam(1-3.0/c)
            if g3cd is None:
                g3cd = gam(3.0/c+d)
            g4c, g4cd = gam(1-4.0/c), gam(4.0/c+d)
            g2 = 6*gd*g2c*g2cd * g1c**2 * g1cd**2 + gd**3 * g4c*g4cd
            g2 -= 3*g1c**4 * g1cd**4 -4*gd**2*g3c*g1c*g1cd*g3cd
        return mu, mu2, g1, g2
burr = burr_gen(a=0.0, name='burr', longname="Burr",
                shapes="c,d", extradoc="""

Burr distribution

burr.pdf(x,c,d) = c*d * x**(-c-1) * (1+x**(-c))**(-d-1)
for x > 0.
""")

# Fisk distribution
# burr is a generalization

class fisk_gen(burr_gen):
    def _pdf(self, x, c):
        return burr_gen._pdf(self, x, c, 1.0)
    def _cdf(self, x, c):
        return burr_gen._cdf(self, x, c, 1.0)
    def _ppf(self, x, c):
        return burr_gen._ppf(self, x, c, 1.0)
    def _stats(self, c):
        return burr_gen._stats(self, c, 1.0)
    def _entropy(self, c):
        return 2 - log(c)
fisk = fisk_gen(a=0.0, name='fink', longname="A funk",
                shapes='c', extradoc="""

Fink distribution.

Burr distribution with d=1.
"""
                )

## Cauchy

# median = loc

class cauchy_gen(rv_continuous):
    def _pdf(self, x):
        return 1.0/pi/(1.0+x*x)
    def _cdf(self, x):
        return 0.5 + 1.0/pi*arctan(x)
    def _ppf(self, q):
        return tan(pi*q-pi/2.0)
    def _sf(self, x):
        return 0.5 - 1.0/pi*arctan(x)
    def _isf(self, q):
        return tan(pi/2.0-pi*q)
    def _stats(self):
        return inf, inf, nan, nan
    def _entropy(self):
        return log(4*pi)
cauchy = cauchy_gen(name='cauchy',longname='Cauchy',extradoc="""

Cauchy distribution

cauchy.pdf(x) = 1/(pi*(1+x**2))

This is the t distribution with one degree of freedom.
"""
                    )

## Chi
##   (positive square-root of chi-square)
##   chi(1, loc, scale) = halfnormal
##   chi(2, 0, scale) = Rayleigh
##   chi(3, 0, scale) = MaxWell

class chi_gen(rv_continuous):
    def _rvs(self, df):
        return sqrt(chi2.rvs(df,size=self._size))
    def _pdf(self, x, df):
        return x**(df-1.)*exp(-x*x*0.5)/(2.0)**(df*0.5-1)/gam(df*0.5)
    def _cdf(self, x, df):
        return special.gammainc(df*0.5,0.5*x*x)
    def _ppf(self, q, df):
        return sqrt(2*special.gammaincinv(df*0.5,q))
    def _stats(self, df):
        mu = sqrt(2)*special.gamma(df/2.0+0.5)/special.gamma(df/2.0)
        mu2 = df - mu*mu
        g1 = (2*mu**3.0 + mu*(1-2*df))/arr(mu2**1.5)
        g2 = 2*df*(1.0-df)-6*mu**4 + 4*mu**2 * (2*df-1)
        g2 /= arr(mu2**2.0)
        return mu, mu2, g1, g2
chi = chi_gen(a=0.0,name='chi',shapes='df',extradoc="""

Chi distribution

chi.pdf(x,df) = x**(df-1)*exp(-x**2/2)/(2**(df/2-1)*gamma(df/2))
for x > 0.
"""
              )


## Chi-squared (gamma-distributed with loc=0 and scale=2 and shape=df/2)
class chi2_gen(rv_continuous):
    def _rvs(self, df):
        return mtrand.chisquare(df,self._size)
    def _pdf(self, x, df):
        Px = x**(df/2.0-1)*exp(-x/2.0)
        Px /= special.gamma(df/2.0)* 2**(df/2.0)
        return Px
    def _cdf(self, x, df):
        return special.chdtr(df, x)
    def _sf(self, x, df):
        return special.chdtrc(df, x)
    def _isf(self, p, df):
        return special.chdtri(df, p)
    def _ppf(self, p, df):
        return self._isf(1.0-p, df)
    def _stats(self, df):
        mu = df
        mu2 = 2*df
        g1 = 2*sqrt(2.0/df)
        g2 = 12.0/df
        return mu, mu2, g1, g2
chi2 = chi2_gen(a=0.0,name='chi2',longname='A chi-squared',shapes='df',
                extradoc="""

Chi-squared distribution

chi2.pdf(x,df) = 1/(2*gamma(df/2)) * (x/2)**(df/2-1) * exp(-x/2)
"""
                )

## Cosine (Approximation to the Normal)
class cosine_gen(rv_continuous):
    def _pdf(self, x):
        return 1.0/2/pi*(1+cos(x))
    def _cdf(self, x):
        return 1.0/2/pi*(pi + x + sin(x))
    def _stats(self):
        return 0.0, pi*pi/3.0-2.0, 0.0, -6.0*(pi**4-90)/(5.0*(pi*pi-6)**2)
    def _entropy(self):
        return log(4*pi)-1.0
cosine = cosine_gen(a=-pi,b=pi,name='cosine',extradoc="""

Cosine distribution (approximation to the normal)

cosine.pdf(x) = 1/(2*pi) * (1+cos(x))
for -pi <= x <= pi.
""")

## Double Gamma distribution
class dgamma_gen(rv_continuous):
    def _rvs(self, a):
        u = random(size=self._size)
        return (gamma.rvs(a,size=self._size)*where(u>=0.5,1,-1))
    def _pdf(self, x, a):
        ax = abs(x)
        return 1.0/(2*special.gamma(a))*ax**(a-1.0) * exp(-ax)
    def _cdf(self, x, a):
        fac = 0.5*special.gammainc(a,abs(x))
        return where(x>0,0.5+fac,0.5-fac)
    def _sf(self, x, a):
        fac = 0.5*special.gammainc(a,abs(x))
        #return where(x>0,0.5-0.5*fac,0.5+0.5*fac)
        return where(x>0,0.5-fac,0.5+fac)
    def _ppf(self, q, a):
        fac = special.gammainccinv(a,1-abs(2*q-1))
        return where(q>0.5, fac, -fac)
    def _stats(self, a):
        mu2 = a*(a+1.0)
        return 0.0, mu2, 0.0, (a+2.0)*(a+3.0)/mu2-3.0
dgamma = dgamma_gen(name='dgamma',longname="A double gamma",
                    shapes='a',extradoc="""

Double gamma distribution

dgamma.pdf(x,a) = 1/(2*gamma(a))*abs(x)**(a-1)*exp(-abs(x))
for a > 0.
"""
                    )

## Double Weibull distribution
##
class dweibull_gen(rv_continuous):
    def _rvs(self, c):
        u = random(size=self._size)
        return weibull_min.rvs(c, size=self._size)*(where(u>=0.5,1,-1))
    def _pdf(self, x, c):
        ax = abs(x)
        Px = c/2.0*ax**(c-1.0)*exp(-ax**c)
        return Px
    def _cdf(self, x, c):
        Cx1 = 0.5*exp(-abs(x)**c)
        return where(x > 0, 1-Cx1, Cx1)
    def _ppf_skip(self, q, c):
        fac = where(q<=0.5,2*q,2*q-1)
        fac = pow(arr(log(1.0/fac)),1.0/c)
        return where(q>0.5,fac,-fac)
    def _stats(self, c):
        var = gam(1+2.0/c)
        return 0.0, var, 0.0, gam(1+4.0/c)/var
dweibull = dweibull_gen(name='dweibull',longname="A double Weibull",
                        shapes='c',extradoc="""

Double Weibull distribution

dweibull.pdf(x,c) = c/2*abs(x)**(c-1)*exp(-abs(x)**c)
"""
                        )

## ERLANG
##
## Special case of the Gamma distribution with shape parameter an integer.
##
class erlang_gen(rv_continuous):
    def _rvs(self, n):
        return gamma.rvs(n,size=self._size)
    def _arg_check(self, n):
        return (n > 0) & (floor(n)==n)
    def _pdf(self, x, n):
        Px = (x)**(n-1.0)*exp(-x)/special.gamma(n)
        return Px
    def _cdf(self, x, n):
        return special.gdtr(1.0,n,x)
    def _sf(self, x, n):
        return special.gdtrc(1.0,n,x)
    def _ppf(self, q, n):
        return special.gdtrix(1.0, n, q)
    def _stats(self, n):
        n = n*1.0
        return n, n, 2/sqrt(n), 6/n
    def _entropy(self, n):
        return special.psi(n)*(1-n) + 1 + special.gammaln(n)
erlang = erlang_gen(a=0.0,name='erlang',longname='An Erlang',
                    shapes='n',extradoc="""

Erlang distribution (Gamma with integer shape parameter)
"""
                    )

## Exponential (gamma distributed with a=1.0, loc=loc and scale=scale)
## scale == 1.0 / lambda

class expon_gen(rv_continuous):
    def link(self,x,logSF,phat,ix):
        ''' Link for x,SF and parameters of Exponential distribution

        CALL  phati = expon.link(x,logSF,phat,i)

         phati = parameter i as function of x, logSF and phat(j) where j ~= i
         x     = quantile
         logSF  = logarithm of the survival probability

        LINK is a function connecting the quantile (x) and the survival
        probability (R) with the fixed distribution parameter, i.e.:
        phat(i) = link(x,logSF,phat,i),
        where logSF = log(Prob(X>x;phat)).

        Example % See proflog

        See also profile
        '''
        if ix==1:
            return -(x-phat[0])/logSF
        elif ix==0:
            return x+phat[1]*logSF


    def _rvs(self):
        return mtrand.standard_exponential(self._size)
    def _pdf(self, x):
        return exp(-x)
    def _chf(self,x):
        return x
    def _cdf(self, x):
        return -expm1(-x)
    def _ppf(self, q):
        return -log1p(-q)
    def _stats(self):
        return 1.0, 1.0, 2.0, 6.0
    def _entropy(self):
        return 1.0
expon = expon_gen(a=0.0,name='expon',longname="An exponential",
                  extradoc="""

Exponential distribution

expon.pdf(x) = exp(-x)
for x >= 0.

scale = 1.0 / lambda
"""
                  )


## Exponentiated Weibull
class exponweib_gen(rv_continuous):

    def _pdf(self, x, a, c):
        exc = exp(-x**c)
        return a*c*(1-exc)**arr(a-1) * exc * x**arr(c-1)
    def _cdf(self, x, a, c):
        exm1c = -expm1(-x**c)
        return arr((exm1c)**a)
    def _ppf(self, q, a, c):
        return (-log1p(-q**(1.0/a)))**arr(1.0/c)
exponweib = exponweib_gen(a=0.0,name='exponweib',
                          longname="An exponentiated Weibull",
                          shapes="a,c",extradoc="""

Exponentiated Weibull distribution

exponweib.pdf(x,a,c) = a*c*(1-exp(-x**c))**(a-1)*exp(-x**c)*x**(c-1)
for x > 0, a, c > 0.
"""
                          )

## Exponential Power

class exponpow_gen(rv_continuous):
    def _pdf(self, x, b):
        xbm1 = arr(x**(b-1.0))
        xb = xbm1 * x
        return exp(1)*b*xbm1 * exp(xb - exp(xb))
    def _cdf(self, x, b):
        xb = arr(x**b)
        return -expm1(-expm1(xb))
    def _ppf(self, q, b):
        return pow(log1p(-log1p(-q)), 1.0/b)
exponpow = exponpow_gen(a=0.0,name='exponpow',longname="An exponential power",
                        shapes='b',extradoc="""

Exponential Power distribution

exponpow.pdf(x,b) = b*x**(b-1) * exp(1+x**b - exp(x**b))
for x >= 0, b > 0.
"""
                        )

## Fatigue-Life (Birnbaum-Sanders)
class fatiguelife_gen(rv_continuous):
    def _rvs(self, c):
        z = norm.rvs(size=self._size)
        x = 0.5*c*z
        x2 = x*x
        t = 1.0 + 2*x2 + 2*x*sqrt(1 + x2)
        return t
    def _pdf(self, x, c):
        return (x+1)/arr(2*c*sqrt(2*pi*x**3))*exp(-(x-1)**2/arr((2.0*x*c**2)))
    def _cdf(self, x, c):
        return special.ndtr(1.0/c*(sqrt(x)-1.0/arr(sqrt(x))))
    def _ppf(self, q, c):
        tmp = c*special.ndtri(q)
        return 0.25*(tmp + sqrt(tmp**2 + 4))**2
    def _stats(self, c):
        c2 = c*c
        mu = c2 / 2.0 + 1
        den = 5*c2 + 4
        mu2 = c2*den /4.0
        g1 = 4*c*sqrt(11*c2+6.0)/den**1.5
        g2 = 6*c2*(93*c2+41.0) / den**2.0
        return mu, mu2, g1, g2
fatiguelife = fatiguelife_gen(a=0.0,name='fatiguelife',
                              longname="A fatigue-life (Birnbaum-Sanders)",
                              shapes='c',extradoc="""

Fatigue-life (Birnbaum-Sanders) distribution

fatiguelife.pdf(x,c) = (x+1)/(2*c*sqrt(2*pi*x**3)) * exp(-(x-1)**2/(2*x*c**2))
for x > 0.
"""
                              )

## Folded Cauchy

class foldcauchy_gen(rv_continuous):
    def _rvs(self, c):
        return abs(cauchy.rvs(loc=c,size=self._size))
    def _pdf(self, x, c):
        return 1.0/pi*(1.0/(1+(x-c)**2) + 1.0/(1+(x+c)**2))
    def _cdf(self, x, c):
        return 1.0/pi*(arctan(x-c) + arctan(x+c))
    def _stats(self, c):
        return inf, inf, nan, nan
# setting xb=1000 allows to calculate ppf for up to q=0.9993
foldcauchy = foldcauchy_gen(a=0.0, name='foldcauchy',xb=1000,
                            longname = "A folded Cauchy",
                            shapes='c',extradoc="""

A folded Cauchy distributions

foldcauchy.pdf(x,c) = 1/(pi*(1+(x-c)**2)) + 1/(pi*(1+(x+c)**2))
for x >= 0.
"""
                            )

## F

class f_gen(rv_continuous):
    def _rvs(self, dfn, dfd):
        return mtrand.f(dfn, dfd, self._size)
    def _pdf(self, x, dfn, dfd):
        n = arr(1.0*dfn)
        m = arr(1.0*dfd)
        Px = m**(m/2) * n**(n/2) * x**(n/2-1)
        Px /= (m+n*x)**((n+m)/2)*special.beta(n/2,m/2)
        return Px
    def _cdf(self, x, dfn, dfd):
        return special.fdtr(dfn, dfd, x)
    def _sf(self, x, dfn, dfd):
        return special.fdtrc(dfn, dfd, x)
    def _ppf(self, q, dfn, dfd):
        return special.fdtri(dfn, dfd, q)
    def _stats(self, dfn, dfd):
        v2 = arr(dfd*1.0)
        v1 = arr(dfn*1.0)
        mu = where (v2 > 2, v2 / arr(v2 - 2), inf)
        mu2 = 2*v2*v2*(v2+v1-2)/(v1*(v2-2)**2 * (v2-4))
        mu2 = where(v2 > 4, mu2, inf)
        g1 = 2*(v2+2*v1-2)/(v2-6)*sqrt((2*v2-4)/(v1*(v2+v1-2)))
        g1 = where(v2 > 6, g1, nan)
        g2 = 3/(2*v2-16)*(8+g1*g1*(v2-6))
        g2 = where(v2 > 8, g2, nan)
        return mu, mu2, g1, g2
f = f_gen(a=0.0,name='f',longname='An F',shapes="dfn,dfd",
          extradoc="""

F distribution

                   df2**(df2/2) * df1**(df1/2) * x**(df1/2-1)
F.pdf(x,df1,df2) = --------------------------------------------
                   (df2+df1*x)**((df1+df2)/2) * B(df1/2, df2/2)
for x > 0.
"""
          )

## Folded Normal
##   abs(Z) where (Z is normal with mu=L and std=S so that c=abs(L)/S)
##
##  note: regress docs have scale parameter correct, but first parameter
##    he gives is a shape parameter A = c * scale

##  Half-normal is folded normal with shape-parameter c=0.

class foldnorm_gen(rv_continuous):
    def _rvs(self, c):
        return abs(norm.rvs(loc=c,size=self._size))
    def _pdf(self, x, c):
        return sqrt(2.0/pi)*cosh(c*x)*exp(-(x*x+c*c)/2.0)
    def _cdf(self, x, c,):
        return special.ndtr(x-c) + special.ndtr(x+c) - 1.0
    def _stats(self, c):
        fac = special.erf(c/sqrt(2))
        mu = sqrt(2.0/pi)*exp(-0.5*c*c)+c*fac
        mu2 = c*c + 1 - mu*mu
        c2 = c*c
        g1 = sqrt(2/pi)*exp(-1.5*c2)*(4-pi*exp(c2)*(2*c2+1.0))
        g1 += 2*c*fac*(6*exp(-c2) + 3*sqrt(2*pi)*c*exp(-c2/2.0)*fac + \
                       pi*c*(fac*fac-1))
        g1 /= pi*mu2**1.5

        g2 = c2*c2+6*c2+3+6*(c2+1)*mu*mu - 3*mu**4
        g2 -= 4*exp(-c2/2.0)*mu*(sqrt(2.0/pi)*(c2+2)+c*(c2+3)*exp(c2/2.0)*fac)
        g2 /= mu2**2.0
        return mu, mu2, g1, g2
foldnorm = foldnorm_gen(a=0.0,name='foldnorm',longname='A folded normal',
                        shapes='c',extradoc="""

Folded normal distribution

foldnormal.pdf(x,c) = sqrt(2/pi) * cosh(c*x) * exp(-(x**2+c**2)/2)
for c >= 0.
"""
                        )

## Extreme Value Type II or Frechet
## (defined in Regress+ documentation as Extreme LB) as
##   a limiting value distribution.
##
class frechet_r_gen(rv_continuous):
    def link(self,x,logSF,phat,ix):
        u = phat[1]
        if ix==0:
            phati = (x-phat[1])/(-logSF)**(1./phat[2])
        elif ix==2:
            phati = log(-logSF)/log((x-phat[1])/phat[0])
        elif ix==1:
            phati = x-phat[0]*(-logSF)**(1./phat[2]);
        else:
            raise IndexError('Index to the fixed parameter is out of bounds')
        return phati


    def _pdf(self, x, c):
        return c*pow(x,c-1)*exp(-pow(x,c))
    def _cdf(self, x, c):
        return -expm1(-pow(x,c))
    def _ppf(self, q, c):
        return pow(-log1p(-q),1.0/c)
    def _munp(self, n, c):
        return special.gamma(1.0+n*1.0/c)
    def _entropy(self, c):
        return -_EULER / c - log(c) + _EULER + 1
frechet_r = frechet_r_gen(a=0.0,name='frechet_r',longname="A Frechet right",
                          shapes='c',extradoc="""

A Frechet (right) distribution (also called Weibull minimum)

frechet_r.pdf(x,c) = c*x**(c-1)*exp(-x**c)
for x > 0, c > 0.
"""
                          )
weibull_min = frechet_r_gen(a=0.0,name='weibull_min',
                            longname="A Weibull minimum",
                            shapes='c',extradoc="""

A Weibull minimum distribution (also called a Frechet (right) distribution)

weibull_min.pdf(x,c) = c*x**(c-1)*exp(-x**c)
for x > 0, c > 0.
"""
                            )

class frechet_l_gen(rv_continuous):
    def _pdf(self, x, c):
        return c*pow(-x,c-1)*exp(-pow(-x,c))
    def _cdf(self, x, c):
        return exp(-pow(-x,c))
    def _ppf(self, q, c):
        return -pow(-log(q),1.0/c)
    def _munp(self, n, c):
        val = special.gamma(1.0+n*1.0/c)
        if (int(n) % 2): sgn = -1
        else:            sgn = 1
        return sgn*val
    def _entropy(self, c):
        return -_EULER / c - log(c) + _EULER + 1
frechet_l = frechet_l_gen(b=0.0,name='frechet_l',longname="A Frechet left",
                          shapes='c',extradoc="""

A Frechet (left) distribution (also called Weibull maximum)

frechet_l.pdf(x,c) = c * (-x)**(c-1) * exp(-(-x)**c)
for x < 0, c > 0.
"""
                          )
weibull_max = frechet_l_gen(b=0.0,name='weibull_max',
                            longname="A Weibull maximum",
                            shapes='c',extradoc="""

A Weibull maximum distribution (also called a Frechet (left) distribution)

weibull_max.pdf(x,c) = c * (-x)**(c-1) * exp(-(-x)**c)
for x < 0, c > 0.
"""
                            )


## Generalized Logistic
##
class genlogistic_gen(rv_continuous):
    def _pdf(self, x, c):
        Px = c*exp(-x)/(1+exp(-x))**(c+1.0)
        return Px
    def _cdf(self, x, c):
        Cx = (1+exp(-x))**(-c)
        return Cx
    def _ppf(self, q, c):
        vals = -log(pow(q,-1.0/c)-1)
        return vals
    def _stats(self, c):
        zeta = special.zeta
        mu = _EULER + special.psi(c)
        mu2 = pi*pi/6.0 + zeta(2,c)
        g1 = -2*zeta(3,c) + 2*_ZETA3
        g1 /= mu2**1.5
        g2 = pi**4/15.0 + 6*zeta(4,c)
        g2 /= mu2**2.0
        return mu, mu2, g1, g2
genlogistic = genlogistic_gen(name='genlogistic',
                              longname="A generalized logistic",
                              shapes='c',extradoc="""

Generalized logistic distribution

genlogistic.pdf(x,c) = c*exp(-x) / (1+exp(-x))**(c+1)
for x > 0, c > 0.
"""
                              )

def log1pxdx(x):
    '''Computes Log(1+x)/x
    '''
    y = where(x==0,1.0,log1p(x)/x)
    return where(x==inf,0.0,y)
##    y = ones(shape(x))
##    k = (x!=0.0)
##    y[k] = log1p(x[k])/x[k]
##    y[x==inf] = 0.0
##    return y

## Generalized Pareto
class genpareto_gen(rv_continuous):
    def link(self,x,logSF,phat,ix):
        # Reference
        # Stuart Coles (2004)
        # "An introduction to statistical modelling of extreme values".
        # Springer series in statistics

        u = phat[1]
        if ix==0:
            raise ValueError('link(x,logSF,phat,i) where i=0 is not implemented!')
        elif ix==2:
            # % Reorganizing w.r.t. phat(2) (scale), Eq. 4.13 and 4.14, pp 81 in Coles (2004) gives
            #   link = @(x,logSF,phat,ix) -(x-phat(3)).*phat(1)./expm1(phat(1).*logSF);
            if phat[0]!=0.0:
                phati =  (x-u)*phat[0]/expm1(-phat[0]*logSF)
            else:
                phati =  -(x-u)/logSF
        elif ix==1:
            if phat[0]!=0:
                phati =  x + phat[2]*expm1(phat[0]*logSF)/phat[0]
            else:
                phati = x+phat(2)*logSF
        else:
            raise IndexError('Index to the fixed parameter is out of bounds')
        return phati

    def _argcheck(self, c):
        c = arr(c)
        self.b = where(0<=c,inf, 1.0/abs(c))
        return where(abs(c)==inf, 0, 1)
    def _pdf(self, x, c):
        cx = where((c==0) & (x==inf),0.0,c*x).clip(min=-1.0)
        #putmask(cx,cx<-1,-1.0)
        logpdf = where((cx==inf) | (cx==-1),-inf,-(x+cx)*log1pxdx(cx))
        putmask(logpdf,(c==-1) & (x==1.0),0.0)
        return exp(logpdf)

        #%f = exp(-xn)./s;                   % for  k==0
        #%f = (1+k.*xn).^(-1./k-1)/s;        % for  k~=0
        #%f = exp((-1./k-1).*log1p(kxn))/s  % for  k~=0
        #%f = exp((-xn-kxn).*log1p(kxn)./(kxn))/s  % for any k kxn~=inf
        #Px = pow(1+c*x,arr(-1.0-1.0/c))
        #return Px
    def _chf(self,x,c):
        cx = c*x
        return where((0.0<x) & (-1.0<=cx) & (c!=0),log1p(cx)/c,x)
    def _cdf(self, x, c):
        log_sf = -self._chf(x,c)
        return -expm1(log_sf)
        #return 1.0 - pow(1+c*x,arr(-1.0/c))
    def _sf(self,x,c):
        log_sf = -self._chf(x,c)
        return exp(log_sf)
    def _isf2(self,log_sf,c):
        return where((c!=0) & (-inf<log_sf),expm1(-c*log_sf)/c,-log_sf)
    def _ppf(self, q, c):
        log_sf = log1p(-q)
        return self._isf2(log_sf,c)
    def _isf(self,q,c):
        log_sf = log(q)
        return self._isf2(log_sf,c)

        #vals = 1.0/c * (pow(1-q, -c)-1)
        #return vals
    def hessian_nnlf(self,theta,x,eps=None):
        try:
            loc = theta[-2]
            scale = theta[-1]
            args = tuple(theta[:-2])
        except IndexError:
            raise ValueError, "Not enough input arguments."
        if not self._argcheck(*args) or scale <= 0:
            return inf
        x = arr((x-loc) / scale)
        cond0 = (x <= self.a) | (x >= self.b)
        if any(cond0):
            np = self.numargs+2
            return valarray((np,np),value=nan)
        eps = floatinfo.machar.eps
        c = args[0]
        n = len(x)
        if abs(c) > eps:
            cx = c*x;
            sumlog1pcx = sum(log1p(cx));
            #LL = n*log(scale) + (1-1/k)*sumlog1mkxn
            r = x/(1.0+cx)
            sumix = sum(1.0/(1.0+cx)**2.0)

            sumr = sum(r)
            sumr2 = sum(r**2.0)
            H11 = -2*sumlog1pcx/c**3 + 2*sumr/c**2 + (1.0+1.0/c)*sumr2
            H22 = c*(c+1)*sumix/scale**2.0
            H33 = (n - 2*(c+1)*sumr + c*(c+1)*sumr2)/scale**2.0;
            H12 = -sum((1-x)/((1+cx)**2.0))/scale
            H23 = -(c+1)*sumix/scale**2.0
            H13 = -(sumr - (c+1)*sumr2)/scale;


        else: # c == 0
            sumx = sum(x);
            #LL = n*log(scale) + sumx;

            sumx2 = sum(x**2.0);
            H11 = -(2/3)*sum(x**3.0) + sumx2
            H22 = 0.0
            H12 = -(n-sum(x))/scale
            H23 = -n*1.0/scale**2.0
            H33 = (n - 2*sumx)/scale**2.0
            H13 = -(sumx - sumx2)/scale

        #% Hessian matrix
        H = [[H11,H12, H13],[H12,H22,H23],[H13, H23, H33]]
        return asarray(H)
    def _stats(self,c):
        #return None,None,None,None
        k = -c
        m = where(k<-1.0,inf,1.0/(1+k))
        v = where(k<-0.5,nan,1.0/((1+k)**2.0*(1+2*k)))
        sk = where(k<-1.0/3,nan,2.*(1-k)*sqrt(1+2.0*k)/(1.0 +3.*k))
        #% E(X^r) = s^r*(-k)^-(r+1)*gamma(1+r)*gamma(-1/k-r)/gamma(1-1/k)
        #%  = s^r*gamma(1+r)./( (1+k)*(1+2*k).*....*(1+r*k))
        #% E[(1-k(X-m0)/s)^r] = 1/(1+k*r)

        #%Ex3 = (sk.*sqrt(v)+3*m).*v+m^3
        #%Ex3 = 6.*s.^3/((1+k).*(1+2*k).*(1+3*k))
        r = 4.0;
        Ex4 = gam(1.+r)/((1.+k)*(1.+2.*k)*(1.+3.*k)*(1+4.*k))
        m1 = m
        ku = where(k<-1./4,nan,(Ex4-4.*sk*v**(3./2)*m1-6*m1**2.*v-m1**4.)/v**2.-3.0)
        return m,v,sk,ku
    def _munp(self, n, c):
        k = arange(0,n+1)
        val = (-1.0/c)**n * sum(comb(n,k)*(-1)**k / (1.0-c*k),axis=0)
        return where(c*n < 1, val, inf)
    def _entropy(self, c):
        return 1+c
##        if (c >= 0):
##            return 1+c
##        else:
##            self.b = -1.0 / c
##            return rv_continuous._entropy(self, c)
genpareto = genpareto_gen(a=0.0,name='genpareto',
                          longname="A generalized Pareto",
                          shapes='c',extradoc="""

Generalized Pareto distribution

genpareto.pdf(x,c) = exp(-x) for c==0
genpareto.pdf(x,c) = (1+c*x)**(-1-1/c)
for c != 0, and for x >= 0 for all c, and x < 1/abs(c) for c < 0.
"""
                          )

## Generalized Exponential

class genexpon_gen(rv_continuous):
    def link(self,x,logSF,phat,ix):
        xn = (x-phat[3])/phat[4]
        fact1 = (xn+expm1(-c*xn)/c)
        if ix ==0:
            phati = b*fact1+logSF
        elif ix == 1:
            phati = (phat[0]-logSF)/fact1
        else:
            raise IndexError('Only implemented for ix in [1,2]!')
        return phati

    def _pdf(self, x, a, b, c):
        return (a+b*(-expm1(-c*x)))*exp((-a-b)*x+b*(-expm1(-c*x))/c)
    def _cdf(self, x, a, b, c):
        return -expm1((-a-b)*x + b*(-expm1(-c*x))/c)
genexpon = genexpon_gen(a=0.0,name='genexpon',
                        longname='A generalized exponential',
                        shapes='a,b,c',extradoc="""

Generalized exponential distribution (Ryu 1993)

genexpon.pdf(x,a,b,c) = (a+b*(1-exp(-c*x))) * exp(-a*x-b*x+b/c*(1-exp(-c*x)))
for x >= 0, a,b,c > 0.

a, b, c are the first, second and third shape parameters.

References
----------
"The Exponential Distribution: Theory, Methods and Applications",
N. Balakrishnan, Asit P. Basu
"""
                        )

## Generalized Extreme Value
##  c=0 is just gumbel distribution.
##  This version does now accept c==0
##  Use gumbel_r for c==0

# new version by Per Brodtkorb, see ticket:767
# also works for c==0, special case is gumbel_r
# increased precision for small c

class genextreme_gen(rv_continuous):
    def _argcheck(self, c):
        min = np.minimum
        max = np.maximum
        sml = floatinfo.machar.xmin
        #self.b = where(c > 0, 1.0 / c,inf)
        #self.a = where(c < 0, 1.0 / c, -inf)
        self.b = where(c > 0, 1.0 / max(c, sml),inf)
        self.a = where(c < 0, 1.0 / min(c,-sml), -inf)
        return where(abs(c)==inf, 0, 1) #True #(c!=0)
    def _pdf(self, x, c):
        ##        ex2 = 1-c*x
        ##        pex2 = pow(ex2,1.0/c)
        ##        p2 = exp(-pex2)*pex2/ex2
        ##        return p2
        cx = c*x

        logex2 = where((c==0)*(x==x),0.0,log1p(-cx))
        logpex2 = where((c==0)*(x==x),-x,logex2/c)
        pex2 = exp(logpex2)
        # % Handle special cases
        logpdf = where((cx==1) | (cx==-inf),-inf,-pex2+logpex2-logex2)
        putmask(logpdf,(c==1) & (x==1),0.0) # logpdf(c==1 & x==1) = 0; % 0^0 situation

        return exp(logpdf)


    def _cdf(self, x, c):
        #return exp(-pow(1-c*x,1.0/c))
        loglogcdf = where((c==0)*(x==x),-x,log1p(-c*x)/c)
        return exp(-exp(loglogcdf))

    def _ppf(self, q, c):
        #return 1.0/c*(1.-(-log(q))**c)
        x = -log(-log(q))
        return where((c==0)*(x==x),x,-expm1(-c*x)/c)
    def _stats(self,c):

        g = lambda n : gam(n*c+1)
        g1 = g(1)
        g2 = g(2)
        g3 = g(3);
        g4 = g(4)
        g2mg12 = where(abs(c)<1e-7,(c*pi)**2.0/6.0,g2-g1**2.0)
        gam2k = where(abs(c)<1e-7,pi**2.0/6.0, expm1(gamln(2.0*c+1.0)-2*gamln(c+1.0))/c**2.0);
        eps = 1e-14
        gamk = where(abs(c)<eps,-_EULER,expm1(gamln(c+1))/c)

        m = where(c<-1.0,nan,-gamk)
        v = where(c<-0.5,nan,g1**2.0*gam2k)

        #% skewness
        sk1 = where(c<-1./3,nan,np.sign(c)*(-g3+(g2+2*g2mg12)*g1)/((g2mg12)**(3./2.)));
        sk = where(abs(c)<=eps**0.29,12*sqrt(6)*_ZETA3/pi**3,sk1)

        #% The kurtosis is:
        ku1 = where(c<-1./4,nan,(g4+(-4*g3+3*(g2+g2mg12)*g1)*g1)/((g2mg12)**2))
        ku = where(abs(c)<=(eps)**0.23,12.0/5.0,ku1-3.0)
        return m,v,sk,ku


    def _munp(self, n, c):
        k = arange(0,n+1)
        vals = 1.0/c**n * sum(comb(n,k) * (-1)**k * special.gamma(c*k + 1),axis=0)
        return where(c*n > -1, vals, inf)
genextreme = genextreme_gen(name='genextreme',
                            longname="A generalized extreme value",
                            shapes='c',extradoc="""

Generalized extreme value (see gumbel_r for c=0)

genextreme.pdf(x,c) = exp(-exp(-x))*exp(-x) for c==0
genextreme.pdf(x,c) = exp(-(1-c*x)**(1/c))*(1-c*x)**(1/c-1)
for x <= 1/c, c > 0
"""
                            )

## Gamma (Use MATLAB and MATHEMATICA (b=theta=scale, a=alpha=shape) definition)

## gamma(a, loc, scale)  with a an integer is the Erlang distribution
## gamma(1, loc, scale)  is the Exponential distribution
## gamma(df/2, 0, 2) is the chi2 distribution with df degrees of freedom.

class gamma_gen(rv_continuous):
    def _rvs(self, a):
        return mtrand.standard_gamma(a, self._size)
    def _pdf(self, x, a):
        return x**(a-1)*exp(-x)/special.gamma(a)
    def _cdf(self, x, a):
        return special.gammainc(a, x)
    def _ppf(self, q, a):
        return special.gammaincinv(a,q)
    def _stats(self, a):
        return a, a, 2.0/sqrt(a), 6.0/a
    def _entropy(self, a):
        return special.psi(a)*(1-a) + 1 + special.gammaln(a)
gamma = gamma_gen(a=0.0,name='gamma',longname='A gamma',
                  shapes='a',extradoc="""

Gamma distribution

For a = integer, this is the Erlang distribution, and for a=1 it is the
exponential distribution.

gamma.pdf(x,a) = x**(a-1)*exp(-x)/gamma(a)
for x >= 0, a > 0.
"""
                  )

# Generalized Gamma
class gengamma_gen(rv_continuous):
    def _argcheck(self, a, c):
        return (a > 0) & (c != 0)
    def _pdf(self, x, a, c):
        return abs(c)* exp((c*a-1)*log(x)-x**c- special.gammaln(a))
    def _cdf(self, x, a, c):
        val = special.gammainc(a,x**c)
        cond = c + 0*val
        return where(cond>0,val,1-val)
    def _ppf(self, q, a, c):
        val1 = special.gammaincinv(a,q)
        val2 = special.gammaincinv(a,1.0-q)
        ic = 1.0/c
        cond = c+0*val1
        return where(cond > 0,val1**ic,val2**ic)
    def _stats(self,a,c):

        return _EULER, pi*pi/6.0, \
               12*sqrt(6)/pi**3 * _ZETA3, 12.0/5
    def _munp(self, n, a, c):
        return special.gamma(a+n*1.0/c) / special.gamma(a)
    def _entropy(self, a,c):
        val = special.psi(a)
        return a*(1-val) + 1.0/c*val + special.gammaln(a)-log(abs(c))
gengamma = gengamma_gen(a=0.0, name='gengamma',
                        longname='A generalized gamma',
                        shapes="a,c", extradoc="""

Generalized gamma distribution

gengamma.pdf(x,a,c) = abs(c)*x**(c*a-1)*exp(-x**c)/gamma(a)
for x > 0, a > 0, and c != 0.
"""
                        )

##  Generalized Half-Logistic
##

class genhalflogistic_gen(rv_continuous):
    def _argcheck(self, c):
        self.b = 1.0 / c
        return (c > 0)
    def _pdf(self, x, c):
        limit = 1.0/c
        tmp = arr(1-c*x)
        tmp0 = tmp**(limit-1)
        tmp2 = tmp0*tmp
        return 2*tmp0 / (1+tmp2)**2
    def _cdf(self, x, c):
        limit = 1.0/c
        tmp = arr(1-c*x)
        tmp2 = tmp**(limit)
        return (1.0-tmp2) / (1+tmp2)
    def _ppf(self, q, c):
        return 1.0/c*(1-((1.0-q)/(1.0+q))**c)
    def _entropy(self,c):
        return 2 - (2*c+1)*log(2)
genhalflogistic = genhalflogistic_gen(a=0.0, name='genhalflogistic',
                                      longname="A generalized half-logistic",
                                      shapes='c',extradoc="""

Generalized half-logistic

genhalflogistic.pdf(x,c) = 2*(1-c*x)**(1/c-1) / (1+(1-c*x)**(1/c))**2
for 0 <= x <= 1/c, and c > 0.
"""
                                      )

## Gompertz (Truncated Gumbel)
##  Defined for x>=0

class gompertz_gen(rv_continuous):
    def _pdf(self, x, c):
        ex = exp(x)
        return c*ex*exp(-c*(ex-1))
    def _cdf(self, x, c):
        return 1.0-exp(-c*(exp(x)-1))
    def _ppf(self, q, c):
        return log(1-1.0/c*log(1-q))
    def _entropy(self, c):
        return 1.0 - log(c) - exp(c)*special.expn(1,c)
gompertz = gompertz_gen(a=0.0, name='gompertz',
                        longname="A Gompertz (truncated Gumbel) distribution",
                        shapes='c',extradoc="""

Gompertz (truncated Gumbel) distribution

gompertz.pdf(x,c) = c*exp(x) * exp(-c*(exp(x)-1))
for x >= 0, c > 0.
"""
                        )

## Gumbel, Log-Weibull, Fisher-Tippett, Gompertz
## The left-skewed gumbel distribution.
## and right-skewed are available as gumbel_l  and gumbel_r

class gumbel_r_gen(rv_continuous):
    def _pdf(self, x):
        ex = exp(-x)
        return ex*exp(-ex)
    def _cdf(self, x):
        return exp(-exp(-x))
    def _ppf(self, q):
        return -log(-log(q))
    def _stats(self):
        return _EULER, pi*pi/6.0, \
               12*sqrt(6)/pi**3 * _ZETA3, 12.0/5
    def _entropy(self):
        return 1.0608407169541684911
gumbel_r = gumbel_r_gen(name='gumbel_r',longname="A (right-skewed) Gumbel",
                        extradoc="""

Right-skewed Gumbel (Log-Weibull, Fisher-Tippett, Gompertz) distribution

gumbel_r.pdf(x) = exp(-(x+exp(-x)))
"""
                        )
class gumbel_l_gen(rv_continuous):
    def _pdf(self, x):
        ex = exp(x)
        return ex*exp(-ex)
    def _cdf(self, x):
        return 1.0-exp(-exp(x))
    def _ppf(self, q):
        return log(-log(1-q))
    def _stats(self):
        return _EULER, pi*pi/6.0, \
               12*sqrt(6)/pi**3 * _ZETA3, 12.0/5
    def _entropy(self):
        return 1.0608407169541684911
gumbel_l = gumbel_l_gen(name='gumbel_l',longname="A left-skewed Gumbel",
                        extradoc="""

Left-skewed Gumbel distribution

gumbel_l.pdf(x) = exp(x - exp(x))
"""
                        )

# Half-Cauchy

class halfcauchy_gen(rv_continuous):
    def _pdf(self, x):
        return 2.0/pi/(1.0+x*x)
    def _cdf(self, x):
        return 2.0/pi*arctan(x)
    def _ppf(self, q):
        return tan(pi/2*q)
    def _stats(self):
        return inf, inf, nan, nan
    def _entropy(self):
        return log(2*pi)
halfcauchy = halfcauchy_gen(a=0.0,name='halfcauchy',
                            longname="A Half-Cauchy",extradoc="""

Half-Cauchy distribution

halfcauchy.pdf(x) = 2/(pi*(1+x**2))
for x >= 0.
"""
                            )


## Half-Logistic
##

class halflogistic_gen(rv_continuous):
    def _pdf(self, x):
        return 0.5/(cosh(x/2.0))**2.0
    def _cdf(self, x):
        return tanh(x/2.0)
    def _ppf(self, q):
        return 2*arctanh(q)
    def _munp(self, n):
        if n==1: return 2*log(2)
        if n==2: return pi*pi/3.0
        if n==3: return 9*_ZETA3
        if n==4: return 7*pi**4 / 15.0
        return 2*(1-pow(2.0,1-n))*special.gamma(n+1)*special.zeta(n,1)
    def _entropy(self):
        return 2-log(2)
halflogistic = halflogistic_gen(a=0.0, name='halflogistic',
                                longname="A half-logistic",
                                extradoc="""

Half-logistic distribution

halflogistic.pdf(x) = 2*exp(-x)/(1+exp(-x))**2 = 1/2*sech(x/2)**2
for x >= 0.
"""
                                )


## Half-normal = chi(1, loc, scale)

class halfnorm_gen(rv_continuous):
    def _rvs(self):
        return abs(norm.rvs(size=self._size))
    def _pdf(self, x):
        return sqrt(2.0/pi)*exp(-x*x/2.0)
    def _cdf(self, x):
        return special.ndtr(x)*2-1.0
    def _ppf(self, q):
        return special.ndtri((1+q)/2.0)
    def _stats(self):
        return sqrt(2.0/pi), 1-2.0/pi, sqrt(2)*(4-pi)/(pi-2)**1.5, \
               8*(pi-3)/(pi-2)**2
    def _entropy(self):
        return 0.5*log(pi/2.0)+0.5
halfnorm = halfnorm_gen(a=0.0, name='halfnorm',
                        longname="A half-normal",
                        extradoc="""

Half-normal distribution

halfnorm.pdf(x) = sqrt(2/pi) * exp(-x**2/2)
for x > 0.
"""
                        )

## Hyperbolic Secant

class hypsecant_gen(rv_continuous):
    def _pdf(self, x):
        return 1.0/(pi*cosh(x))
    def _cdf(self, x):
        return 2.0/pi*arctan(exp(x))
    def _ppf(self, q):
        return log(tan(pi*q/2.0))
    def _stats(self):
        return 0, pi*pi/4, 0, 2
    def _entropy(self):
        return log(2*pi)
hypsecant = hypsecant_gen(name='hypsecant',longname="A hyperbolic secant",
                          extradoc="""

Hyperbolic secant distribution

hypsecant.pdf(x) = 1/pi * sech(x)
"""
                          )

## Gauss Hypergeometric

class gausshyper_gen(rv_continuous):
    def _argcheck(self, a, b, c, z):
        return (a > 0) & (b > 0) & (c==c) & (z==z)
    def _pdf(self, x, a, b, c, z):
        Cinv = gam(a)*gam(b)/gam(a+b)*special.hyp2f1(c,a,a+b,-z)
        return 1.0/Cinv * x**(a-1.0) * (1.0-x)**(b-1.0) / (1.0+z*x)**c
    def _munp(self, n, a, b, c, z):
        fac = special.beta(n+a,b) / special.beta(a,b)
        num = special.hyp2f1(c,a+n,a+b+n,-z)
        den = special.hyp2f1(c,a,a+b,-z)
        return fac*num / den
gausshyper = gausshyper_gen(a=0.0, b=1.0, name='gausshyper',
                            longname="A Gauss hypergeometric",
                            shapes="a,b,c,z",
                            extradoc="""

Gauss hypergeometric distribution

gausshyper.pdf(x,a,b,c,z) = C * x**(a-1) * (1-x)**(b-1) * (1+z*x)**(-c)
for 0 <= x <= 1, a > 0, b > 0, and
C = 1/(B(a,b)F[2,1](c,a;a+b;-z))
"""
                            )

##  Inverted Gamma
#     special case of generalized gamma with c=-1
#

class invgamma_gen(rv_continuous):
    def _pdf(self, x, a):
        return exp(-(a+1)*log(x)-special.gammaln(a) - 1.0/x)
    def _cdf(self, x, a):
        return 1.0-special.gammainc(a, 1.0/x)
    def _ppf(self, q, a):
        return 1.0/special.gammaincinv(a,1-q)
    def _munp(self, n, a):
        return exp(special.gammaln(a-n) - special.gammaln(a))
    def _entropy(self, a):
        return a - (a+1.0)*special.psi(a) + special.gammaln(a)
invgamma = invgamma_gen(a=0.0, name='invgamma',longname="An inverted gamma",
                        shapes='a',extradoc="""

Inverted gamma distribution

invgamma.pdf(x,a) = x**(-a-1)/gamma(a) * exp(-1/x)
for x > 0, a > 0.
"""
                        )


## Inverse Normal Distribution
# scale is gamma from DATAPLOT and B from Regress

class invnorm_gen(rv_continuous):
    def _rvs(self, mu):
        return mtrand.wald(mu, 1.0, size=self._size)
    def _pdf(self, x, mu):
        return 1.0/sqrt(2*pi*x**3.0)*exp(-1.0/(2*x)*((x-mu)/mu)**2)
    def _cdf(self, x, mu):
        fac = sqrt(1.0/x)
        C1 = norm.cdf(fac*(x-mu)/mu)
        C1 += exp(2.0/mu)*norm.cdf(-fac*(x+mu)/mu)
        return C1
    def _stats(self, mu):
        return mu, mu**3.0, 3*sqrt(mu), 15*mu
invnorm = invnorm_gen(a=0.0, name='invnorm', longname="An inverse normal",
                      shapes="mu",extradoc="""

Inverse normal distribution

invnorm.pdf(x,mu) = 1/sqrt(2*pi*x**3) * exp(-(x-mu)**2/(2*x*mu**2))
for x > 0.
"""
                      )

## Inverted Weibull

class invweibull_gen(rv_continuous):
    def _pdf(self, x, c):
        xc1 = x**(-c-1.0)
        #xc2 = xc1*x
        xc2 = x**(-c)
        xc2 = exp(-xc2)
        return c*xc1*xc2
    def _cdf(self, x, c):
        xc1 = x**(-c)
        return exp(-xc1)
    def _ppf(self, q, c):
        return pow(-log(q),arr(-1.0/c))
    def _entropy(self, c):
        return 1+_EULER + _EULER / c - log(c)
invweibull = invweibull_gen(a=0,name='invweibull',
                            longname="An inverted Weibull",
                            shapes='c',extradoc="""

Inverted Weibull distribution

invweibull.pdf(x,c) = c*x**(-c-1)*exp(-x**(-c))
for x > 0, c > 0.
"""
                            )

## Johnson SB

class johnsonsb_gen(rv_continuous):
    def _argcheck(self, a, b):
        return (b > 0) & (a==a)
    def _pdf(self, x, a, b):
        trm = norm.pdf(a+b*log(x/(1.0-x)))
        return b*1.0/(x*(1-x))*trm
    def _cdf(self, x, a, b):
        return norm.cdf(a+b*log(x/(1.0-x)))
    def _ppf(self, q, a, b):
        return 1.0/(1+exp(-1.0/b*(norm.ppf(q)-a)))
johnsonsb = johnsonsb_gen(a=0.0,b=1.0,name='johnsonb',
                          longname="A Johnson SB",
                          shapes="a,b",extradoc="""

Johnson SB distribution

johnsonsb.pdf(x,a,b) = b/(x*(1-x)) * phi(a + b*log(x/(1-x)))
for 0 < x < 1 and a,b > 0, and phi is the normal pdf.
"""
                          )

## Johnson SU
class johnsonsu_gen(rv_continuous):
    def _argcheck(self, a, b):
        return (b > 0) & (a==a)
    def _pdf(self, x, a, b):
        x2 = x*x
        trm = norm.pdf(a+b*log(x+sqrt(x2+1)))
        return b*1.0/sqrt(x2+1.0)*trm
    def _cdf(self, x, a, b):
        return norm.cdf(a+b*log(x+sqrt(x*x+1)))
    def _ppf(self, q, a, b):
        return sinh((norm.ppf(q)-a)/b)
johnsonsu = johnsonsu_gen(name='johnsonsu',longname="A Johnson SU",
                          shapes="a,b", extradoc="""

Johnson SU distribution

johnsonsu.pdf(x,a,b) = b/sqrt(x**2+1) * phi(a + b*log(x+sqrt(x**2+1)))
for all x, a,b > 0, and phi is the normal pdf.
"""
                          )


## Laplace Distribution

class laplace_gen(rv_continuous):
    def _rvs(self):
        return mtrand.laplace(0, 1, size=self._size)
    def _pdf(self, x):
        return 0.5*exp(-abs(x))
    def _cdf(self, x):
        return where(x > 0, 1.0-0.5*exp(-x), 0.5*exp(x))
    def _ppf(self, q):
        return where(q > 0.5, -log(2*(1-q)), log(2*q))
    def _stats(self):
        return 0, 2, 0, 3
    def _entropy(self):
        return log(2)+1
laplace = laplace_gen(name='laplace', longname="A Laplace",
                      extradoc="""

Laplacian distribution

laplace.pdf(x) = 1/2*exp(-abs(x))
"""
                      )


## Levy Distribution

class levy_gen(rv_continuous):
    def _pdf(self, x):
        return 1/sqrt(2*pi*x)/x*exp(-1/(2*x))
    def _cdf(self, x):
        return 2*(1-norm._cdf(1/sqrt(x)))
    def _ppf(self, q):
        val = norm._ppf(1-q/2.0)
        return 1.0/(val*val)
    def _stats(self):
        return inf, inf, nan, nan
levy = levy_gen(a=0.0,name="levy", longname = "A Levy", extradoc="""

Levy distribution

levy.pdf(x) = 1/(x*sqrt(2*pi*x)) * exp(-1/(2*x))
for x > 0.

This is the same as the Levy-stable distribution with a=1/2 and b=1.
"""
                )

## Left-skewed Levy Distribution

class levy_l_gen(rv_continuous):
    def _pdf(self, x):
        ax = abs(x)
        return 1/sqrt(2*pi*ax)/ax*exp(-1/(2*ax))
    def _cdf(self, x):
        ax = abs(x)
        return 2*norm._cdf(1/sqrt(ax))-1
    def _ppf(self, q):
        val = norm._ppf((q+1.0)/2)
        return -1.0/(val*val)
    def _stats(self):
        return inf, inf, nan, nan
levy_l = levy_l_gen(b=0.0,name="levy_l", longname = "A left-skewed Levy", extradoc="""

Left-skewed Levy distribution

levy_l.pdf(x) = 1/(abs(x)*sqrt(2*pi*abs(x))) * exp(-1/(2*abs(x)))
for x < 0.

This is the same as the Levy-stable distribution with a=1/2 and b=-1.
"""
                    )

## Levy-stable Distribution (only random variates)

class levy_stable_gen(rv_continuous):
    def _rvs(self, alpha, beta):
        sz = self._size
        TH = uniform.rvs(loc=-pi/2.0,scale=pi,size=sz)
        W = expon.rvs(size=sz)
        if alpha==1:
            return 2/pi*(pi/2+beta*TH)*tan(TH)-beta*log((pi/2*W*cos(TH))/(pi/2+beta*TH))
        # else
        ialpha = 1.0/alpha
        aTH = alpha*TH
        if beta==0:
            return W/(cos(TH)/tan(aTH)+sin(TH))*((cos(aTH)+sin(aTH)*tan(TH))/W)**ialpha
        # else
        val0 = beta*tan(pi*alpha/2)
        th0 = arctan(val0)/alpha
        val3 = W/(cos(TH)/tan(alpha*(th0+TH))+sin(TH))
        res3 = val3*((cos(aTH)+sin(aTH)*tan(TH)-val0*(sin(aTH)-cos(aTH)*tan(TH)))/W)**ialpha
        return res3

    def _argcheck(self, alpha, beta):
        if beta == -1:
            self.b = 0.0
        elif beta == 1:
            self.a = 0.0
        return (alpha > 0) & (alpha <= 2) & (beta <= 1) & (beta >= -1)

    def _pdf(self, x, alpha, beta):
        raise NotImplementedError

levy_stable = levy_stable_gen(name='levy_stable', longname="A Levy-stable",
                    shapes="alpha, beta", extradoc="""

Levy-stable distribution (only random variates available -- ignore other docs)
"""
                    )


## Logistic (special case of generalized logistic with c=1)
## Sech-squared

class logistic_gen(rv_continuous):
    def _rvs(self):
        return mtrand.logistic(size=self._size)
    def _pdf(self, x):
        ex = exp(-x)
        return ex / (1+ex)**2.0
    def _cdf(self, x):
        return 1.0/(1+exp(-x))
    def _ppf(self, q):
        return -log(1.0/q-1)
    def _stats(self):
        return 0, pi*pi/3.0, 0, 6.0/5.0
    def _entropy(self):
        return 1.0
logistic = logistic_gen(name='logistic', longname="A logistic",
                        extradoc="""

Logistic distribution

logistic.pdf(x) = exp(-x)/(1+exp(-x))**2
"""
                        )


## Log Gamma
#
class loggamma_gen(rv_continuous):
    def _rvs(self, c):
        return log(mtrand.gamma(c, size=self._size))
    def _pdf(self, x, c):
        return exp(c*x-exp(x)-special.gammaln(c))
    def _cdf(self, x, c):
        return special.gammainc(c, exp(x))
    def _ppf(self, q, c):
        return log(special.gammaincinv(c,q))
    def _munp(self,n,*args):
        # use generic moment calculation using ppf
        return self._mom0_sc(n,*args)
loggamma = loggamma_gen(name='loggamma', longname="A log gamma",
                        extradoc="""

Log gamma distribution

loggamma.pdf(x,c) = exp(c*x-exp(x)) / gamma(c)
for all x, c > 0.
"""
                        )

## Log-Laplace  (Log Double Exponential)
##
class loglaplace_gen(rv_continuous):
    def _pdf(self, x, c):
        cd2 = c/2.0
        c = where(x < 1, c, -c)
        return cd2*x**(c-1)
    def _cdf(self, x, c):
        return where(x < 1, 0.5*x**c, 1-0.5*x**(-c))
    def _ppf(self, q, c):
        return where(q < 0.5, (2.0*q)**(1.0/c), (2*(1.0-q))**(-1.0/c))
    def _entropy(self, c):
        return log(2.0/c) + 1.0
loglaplace = loglaplace_gen(a=0.0, name='loglaplace',
                            longname="A log-Laplace",shapes='c',
                            extradoc="""

Log-Laplace distribution (Log Double Exponential)

loglaplace.pdf(x,c) = c/2*x**(c-1) for 0 < x < 1
                    = c/2*x**(-c-1) for x >= 1
for c > 0.
"""
                            )

## Lognormal (Cobb-Douglass)
## std is a shape parameter and is the variance of the underlying
##    distribution.
## the mean of the underlying distribution is log(scale)

class lognorm_gen(rv_continuous):
    def _rvs(self, s):
        return exp(s * norm.rvs(size=self._size))
    def _pdf(self, x, s):
        Px = exp(-log(x)**2 / (2*s**2))
        return Px / (s*x*sqrt(2*pi))
    def _cdf(self, x, s):
        return norm.cdf(log(x)/s)
    def _ppf(self, q, s):
        return exp(s*norm._ppf(q))
    def _stats(self, s):
        p = exp(s*s)
        mu = sqrt(p)
        mu2 = p*(p-1)
        g1 = sqrt((p-1))*(2+p)
        g2 = numpy.polyval([1,2,3,0,-6.0],p)
        return mu, mu2, g1, g2
    def _entropy(self, s):
        return 0.5*(1+log(2*pi)+2*log(s))
lognorm = lognorm_gen(a=0.0, name='lognorm',
                      longname='A lognormal', shapes='s',
                      extradoc="""

Lognormal distribution

lognorm.pdf(x,s) = 1/(s*x*sqrt(2*pi)) * exp(-1/2*(log(x)/s)**2)
for x > 0, s > 0.

If log x is normally distributed with mean mu and variance sigma**2,
then x is log-normally distributed with shape paramter sigma and scale
parameter exp(mu).
"""
                      )

# Gibrat's distribution is just lognormal with s=1

class gilbrat_gen(lognorm_gen):
    def _rvs(self):
        return lognorm_gen._rvs(self, 1.0)
    def _pdf(self, x):
        return lognorm_gen._pdf(self, x, 1.0)
    def _cdf(self, x):
        return lognorm_gen._cdf(self, x, 1.0)
    def _ppf(self, q):
        return lognorm_gen._ppf(self, q, 1.0)
    def _stats(self):
        return lognorm_gen._stats(self, 1.0)
    def _entropy(self):
        return 0.5*log(2*pi) + 0.5
gilbrat = gilbrat_gen(a=0.0, name='gilbrat', longname='A Gilbrat',
                      extradoc="""

Gilbrat distribution

gilbrat.pdf(x) = 1/(x*sqrt(2*pi)) * exp(-1/2*(log(x))**2)
"""
                      )


# MAXWELL
#  a special case of chi with df = 3, loc=0.0, and given scale = 1.0/sqrt(a)
#    where a is the parameter used in mathworld description

class maxwell_gen(rv_continuous):
    def _rvs(self):
        return chi.rvs(3.0,size=self._size)
    def _pdf(self, x):
        return sqrt(2.0/pi)*x*x*exp(-x*x/2.0)
    def _cdf(self, x):
        return special.gammainc(1.5,x*x/2.0)
    def _ppf(self, q):
        return sqrt(2*special.gammaincinv(1.5,q))
    def _stats(self):
        val = 3*pi-8
        return 2*sqrt(2.0/pi), 3-8/pi, sqrt(2)*(32-10*pi)/val**1.5, \
               (-12*pi*pi + 160*pi - 384) / val**2.0
    def _entropy(self):
        return _EULER + 0.5*log(2*pi)-0.5
maxwell = maxwell_gen(a=0.0, name='maxwell', longname="A Maxwell",
                      extradoc="""

Maxwell distribution

maxwell.pdf(x) = sqrt(2/pi) * x**2 * exp(-x**2/2)
for x > 0.
"""
                      )

# Mielke's Beta-Kappa

class mielke_gen(rv_continuous):
    def _pdf(self, x, k, s):
        return k*x**(k-1.0) / (1.0+x**s)**(1.0+k*1.0/s)
    def _cdf(self, x, k, s):
        return x**k / (1.0+x**s)**(k*1.0/s)
    def _ppf(self, q, k, s):
        qsk = pow(q,s*1.0/k)
        return pow(qsk/(1.0-qsk),1.0/s)
mielke = mielke_gen(a=0.0, name='mielke', longname="A Mielke's Beta-Kappa",
                    shapes="k,s", extradoc="""

Mielke's Beta-Kappa distribution

mielke.pdf(x,k,s) = k*x**(k-1) / (1+x**s)**(1+k/s)
for x > 0.
"""
                    )

# Nakagami (cf Chi)

class nakagami_gen(rv_continuous):
    def _pdf(self, x, nu):
        return 2*nu**nu/gam(nu)*(x**(2*nu-1.0))*exp(-nu*x*x)
    def _cdf(self, x, nu):
        return special.gammainc(nu,nu*x*x)
    def _ppf(self, q, nu):
        return sqrt(1.0/nu*special.gammaincinv(nu,q))
    def _stats(self, nu):
        mu = gam(nu+0.5)/gam(nu)/sqrt(nu)
        mu2 = 1.0-mu*mu
        g1 = mu*(1-4*nu*mu2)/2.0/nu/mu2**1.5
        g2 = -6*mu**4*nu + (8*nu-2)*mu**2-2*nu + 1
        g2 /= nu*mu2**2.0
        return mu, mu2, g1, g2
nakagami = nakagami_gen(a=0.0, name="nakagami", longname="A Nakagami",
                        shapes='nu', extradoc="""

Nakagami distribution

nakagami.pdf(x,nu) = 2*nu**nu/gamma(nu) * x**(2*nu-1) * exp(-nu*x**2)
for x > 0, nu > 0.
"""
                        )


# Non-central chi-squared
# nc is lambda of definition, df is nu

class ncx2_gen(rv_continuous):
    def _rvs(self, df, nc):
        return mtrand.noncentral_chisquare(df,nc,self._size)
    def _pdf(self, x, df, nc):
        a = arr(df/2.0)
        Px = exp(-nc/2.0)*special.hyp0f1(a,nc*x/4.0)
        Px *= exp(-x/2.0)*x**(a-1) / arr(2**a * special.gamma(a))
        return Px
    def _cdf(self, x, df, nc):
        return special.chndtr(x,df,nc)
    def _ppf(self, q, df, nc):
        return special.chndtrix(q,df,nc)
    def _stats(self, df, nc):
        val = df + 2.0*nc
        return df + nc, 2*val, sqrt(8)*(val+nc)/val**1.5, \
               12.0*(val+2*nc)/val**2.0
ncx2 = ncx2_gen(a=0.0, name='ncx2', longname="A non-central chi-squared",
                shapes="df,nc", extradoc="""

Non-central chi-squared distribution

ncx2.pdf(x,df,nc) = exp(-(nc+df)/2)*1/2*(x/nc)**((df-2)/4)
                        * I[(df-2)/2](sqrt(nc*x))
for x > 0.
"""
                )

# Non-central F

class ncf_gen(rv_continuous):
    def _rvs(self, dfn, dfd, nc):
        return mtrand.noncentral_f(dfn,dfd,nc,self._size)
    def _pdf_skip(self, x, dfn, dfd, nc):
        n1,n2 = dfn, dfd
        term = -nc/2+nc*n1*x/(2*(n2+n1*x)) + gamln(n1/2.)+gamln(1+n2/2.)
        term -= gamln((n1+n2)/2.0)
        Px = exp(term)
        Px *= n1**(n1/2) * n2**(n2/2) * x**(n1/2-1)
        Px *= (n2+n1*x)**(-(n1+n2)/2)
        Px *= special.assoc_laguerre(-nc*n1*x/(2.0*(n2+n1*x)),n2/2,n1/2-1)
        Px /= special.beta(n1/2,n2/2)
         #this function does not have a return
         #   drop it for now, the generic function seems to work ok
    def _cdf(self, x, dfn, dfd, nc):
        return special.ncfdtr(dfn,dfd,nc,x)
    def _ppf(self, q, dfn, dfd, nc):
        return special.ncfdtri(dfn, dfd, nc, q)
    def _munp(self, n, dfn, dfd, nc):
        val = (dfn *1.0/dfd)**n
        term = gamln(n+0.5*dfn) + gamln(0.5*dfd-n) - gamln(dfd*0.5)
        val *= exp(-nc / 2.0+term)
        val *= special.hyp1f1(n+0.5*dfn, 0.5*dfn, 0.5*nc)
        return val
    def _stats(self, dfn, dfd, nc):
        mu = where(dfd <= 2, inf, dfd / (dfd-2.0)*(1+nc*1.0/dfn))
        mu2 = where(dfd <=4, inf, 2*(dfd*1.0/dfn)**2.0 * \
                    ((dfn+nc/2.0)**2.0 + (dfn+nc)*(dfd-2.0)) / \
                    ((dfd-2.0)**2.0 * (dfd-4.0)))
        return mu, mu2, None, None
ncf = ncf_gen(a=0.0, name='ncf', longname="A non-central F distribution",
              shapes="dfn,dfd,nc", extradoc="""

Non-central F distribution

ncf.pdf(x,df1,df2,nc) = exp(nc/2 + nc*df1*x/(2*(df1*x+df2)))
                * df1**(df1/2) * df2**(df2/2) * x**(df1/2-1)
                * (df2+df1*x)**(-(df1+df2)/2)
                * gamma(df1/2)*gamma(1+df2/2)
                * L^{v1/2-1}^{v2/2}(-nc*v1*x/(2*(v1*x+v2)))
                / (B(v1/2, v2/2) * gamma((v1+v2)/2))
for df1, df2, nc > 0.
"""
              )

## Student t distribution

class t_gen(rv_continuous):
    def _rvs(self, df):
        return mtrand.standard_t(df, size=self._size)
        #Y = f.rvs(df, df, size=self._size)
        #sY = sqrt(Y)
        #return 0.5*sqrt(df)*(sY-1.0/sY)
    def _pdf(self, x, df):
        r = arr(df*1.0)
        Px = exp(special.gammaln((r+1)/2)-special.gammaln(r/2))
        Px /= sqrt(r*pi)*(1+(x**2)/r)**((r+1)/2)
        return Px
    def _cdf(self, x, df):
        return special.stdtr(df, x)
    def _ppf(self, q, df):
        return special.stdtrit(df, q)
    def _stats(self, df):
        mu2 = where(df > 2, df / (df-2.0), inf)
        g1 = where(df > 3, 0.0, nan)
        g2 = where(df > 4, 6.0/(df-4.0), nan)
        return 0, mu2, g1, g2
t = t_gen(name='t',longname="Student's T",
          shapes="df", extradoc="""

Student's T distribution

                            gamma((df+1)/2)
t.pdf(x,df) = -----------------------------------------------
              sqrt(pi*df)*gamma(df/2)*(1+x**2/df)**((df+1)/2)
for df > 0.
"""
          )

## Non-central T distribution

class nct_gen(rv_continuous):
    def _rvs(self, df, nc):
        return norm.rvs(loc=nc,size=self._size)*sqrt(df) / sqrt(chi2.rvs(df,size=self._size))
    def _pdf(self, x, df, nc):
        n = df*1.0
        nc = nc*1.0
        x2 = x*x
        ncx2 = nc*nc*x2
        fac1 = n + x2
        trm1 = n/2.*log(n) + gamln(n+1)
        trm1 -= n*log(2)+nc*nc/2.+(n/2.)*log(fac1)+gamln(n/2.)
        Px = exp(trm1)
        valF = ncx2 / (2*fac1)
        trm1 = sqrt(2)*nc*x*special.hyp1f1(n/2+1,1.5,valF)
        trm1 /= arr(fac1*special.gamma((n+1)/2))
        trm2 = special.hyp1f1((n+1)/2,0.5,valF)
        trm2 /= arr(sqrt(fac1)*special.gamma(n/2+1))
        Px *= trm1+trm2
        return Px
    def _cdf(self, x, df, nc):
        return special.nctdtr(df, nc, x)
    def _ppf(self, q, df, nc):
        return special.nctdtrit(df, nc, q)
    def _stats(self, df, nc, moments='mv'):
        mu, mu2, g1, g2 = None, None, None, None
        val1 = gam((df-1.0)/2.0)
        val2 = gam(df/2.0)
        if 'm' in moments:
            mu = nc*sqrt(df/2.0)*val1/val2
        if 'v' in moments:
            var = (nc*nc+1.0)*df/(df-2.0)
            var -= nc*nc*df* val1**2 / 2.0 / val2**2
            mu2 = var
        if 's' in moments:
            g1n = 2*nc*sqrt(df)*val1*((nc*nc*(2*df-7)-3)*val2**2 \
                                      -nc*nc*(df-2)*(df-3)*val1**2)
            g1d = (df-3)*sqrt(2*df*(nc*nc+1)/(df-2) - \
                              nc*nc*df*(val1/val2)**2) * val2 * \
                              (nc*nc*(df-2)*val1**2 - \
                               2*(nc*nc+1)*val2**2)
            g1 = g1n/g1d
        if 'k' in moments:
            g2n = 2*(-3*nc**4*(df-2)**2 *(df-3) *(df-4)*val1**4 + \
                     2**(6-2*df) * nc*nc*(df-2)*(df-4)* \
                     (nc*nc*(2*df-7)-3)*pi* gam(df+1)**2 - \
                     4*(nc**4*(df-5)-6*nc*nc-3)*(df-3)*val2**4)
            g2d = (df-3)*(df-4)*(nc*nc*(df-2)*val1**2 - \
                                 2*(nc*nc+1)*val2)**2
            g2 = g2n / g2d
        return mu, mu2, g1, g2
nct = nct_gen(name="nct", longname="A Noncentral T",
              shapes="df,nc", extradoc="""

Non-central Student T distribution

                                 df**(df/2) * gamma(df+1)
nct.pdf(x,df,nc) = --------------------------------------------------
                   2**df*exp(nc**2/2)*(df+x**2)**(df/2) * gamma(df/2)
for df > 0, nc > 0.
"""
              )

# Pareto

class pareto_gen(rv_continuous):
    def _pdf(self, x, b):
        return b * x**(-b-1)
    def _cdf(self, x, b):
        return 1 -  x**(-b)
    def _ppf(self, q, b):
        return pow(1-q, -1.0/b)
    def _stats(self, b, moments='mv'):
        mu, mu2, g1, g2 = None, None, None, None
        if 'm' in moments:
            mask = b > 1
            bt = extract(mask,b)
            mu = valarray(shape(b),value=inf)
            place(mu, mask, bt / (bt-1.0))
        if 'v' in moments:
            mask = b > 2
            bt = extract( mask,b)
            mu2 = valarray(shape(b), value=inf)
            place(mu2, mask, bt / (bt-2.0) / (bt-1.0)**2)
        if 's' in moments:
            mask = b > 3
            bt = extract( mask,b)
            g1 = valarray(shape(b), value=nan)
            vals = 2*(bt+1.0)*sqrt(b-2.0)/((b-3.0)*sqrt(b))
            place(g1, mask, vals)
        if 'k' in moments:
            mask = b > 4
            bt = extract( mask,b)
            g2 = valarray(shape(b), value=nan)
            vals = 6.0*polyval([1.0,1.0,-6,-2],bt)/ \
                   polyval([1.0,-7.0,12.0,0.0],bt)
            place(g2, mask, vals)
        return mu, mu2, g1, g2
    def _entropy(self, c):
        return 1 + 1.0/c - log(c)
pareto = pareto_gen(a=1.0, name="pareto", longname="A Pareto",
                    shapes="b", extradoc="""

Pareto distribution

pareto.pdf(x,b) = b/x**(b+1)
for x >= 1, b > 0.
"""
                    )

# LOMAX (Pareto of the second kind.)
#  Special case of Pareto of the first kind (location=-1.0)

class lomax_gen(rv_continuous):
    def _pdf(self, x, c):
        return c*1.0/(1.0+x)**(c+1.0)
    def _cdf(self, x, c):
        return 1.0-1.0/(1.0+x)**c
    def _ppf(self, q, c):
        return pow(1.0-q,-1.0/c)-1
    def _stats(self, c):
        mu, mu2, g1, g2 = pareto.stats(c, loc=-1.0, moments='mvsk')
        return mu, mu2, g1, g2
    def _entropy(self, c):
        return 1+1.0/c-log(c)
lomax = lomax_gen(a=0.0, name="lomax",
                  longname="A Lomax (Pareto of the second kind)",
                  shapes="c", extradoc="""

Lomax (Pareto of the second kind) distribution

lomax.pdf(x,c) = c / (1+x)**(c+1)
for x >= 0, c > 0.
"""
                  )
## Power-function distribution
##   Special case of beta dist. with d =1.0

class powerlaw_gen(rv_continuous):
    def _pdf(self, x, a):
        return a*x**(a-1.0)
    def _cdf(self, x, a):
        return x**(a*1.0)
    def _ppf(self, q, a):
        return pow(q, 1.0/a)
    def _stats(self, a):
        return a/(a+1.0), a*(a+2.0)/(a+1.0)**2, \
               2*(1.0-a)*sqrt((a+2.0)/(a*(a+3.0))), \
               6*polyval([1,-1,-6,2],a)/(a*(a+3.0)*(a+4))
    def _entropy(self, a):
        return 1 - 1.0/a - log(a)
powerlaw = powerlaw_gen(a=0.0, b=1.0, name="powerlaw",
                        longname="A power-function",
                        shapes="a", extradoc="""

Power-function distribution

powerlaw.pdf(x,a) = a**x**(a-1)
for 0 <= x <= 1, a > 0.
"""
                        )

# Power log normal

class powerlognorm_gen(rv_continuous):
    def _pdf(self, x, c, s):
        return c/(x*s)*norm.pdf(log(x)/s)*pow(norm.cdf(-log(x)/s),c*1.0-1.0)

    def _cdf(self, x, c, s):
        return 1.0 - pow(norm.cdf(-log(x)/s),c*1.0)
    def _ppf(self, q, c, s):
        return exp(-s*norm.ppf(pow(1.0-q,1.0/c)))
powerlognorm = powerlognorm_gen(a=0.0, name="powerlognorm",
                                longname="A power log-normal",
                                shapes="c,s", extradoc="""

Power log-normal distribution

powerlognorm.pdf(x,c,s) = c/(x*s) * phi(log(x)/s) * (Phi(-log(x)/s))**(c-1)
where phi is the normal pdf, and Phi is the normal cdf, and x > 0, s,c > 0.
"""
                                )

# Power Normal

class powernorm_gen(rv_continuous):
    def _pdf(self, x, c):
        return c*norm.pdf(x)* \
               (norm.cdf(-x)**(c-1.0))
    def _cdf(self, x, c):
        return 1.0-norm.cdf(-x)**(c*1.0)
    def _ppf(self, q, c):
        return -norm.ppf(pow(1.0-q,1.0/c))
powernorm = powernorm_gen(name='powernorm', longname="A power normal",
                          shapes="c", extradoc="""

Power normal distribution

powernorm.pdf(x,c) = c * phi(x)*(Phi(-x))**(c-1)
where phi is the normal pdf, and Phi is the normal cdf, and x > 0, c > 0.
"""
                          )

# R-distribution ( a general-purpose distribution with a
#  variety of shapes.

# FIXME: PPF does not work.
class rdist_gen(rv_continuous):
    def _pdf(self, x, c):
        return pow((1.0-x*x),c/2.0-1) / special.beta(0.5,c/2.0)
    def _cdf_skip(self, x, c):
        #error inspecial.hyp2f1 for some values see tickets 758, 759
        return 0.5 + x/special.beta(0.5,c/2.0)* \
               special.hyp2f1(0.5,1.0-c/2.0,1.5,x*x)
    def _munp(self, n, c):
        return (1-(n % 2))*special.beta((n+1.0)/2,c/2.0)
rdist = rdist_gen(a=-1.0,b=1.0, name="rdist", longname="An R-distributed",
                  shapes="c", extradoc="""

R-distribution

rdist.pdf(x,c) = (1-x**2)**(c/2-1) / B(1/2, c/2)
for -1 <= x <= 1, c > 0.
"""
                  )

# Rayleigh distribution (this is chi with df=2 and loc=0.0)
# scale is the mode.

class rayleigh_gen(rv_continuous):
    #rayleigh_gen.link.__doc__ = rv_continuous.link.__doc__

    def link(self,x,logSF,phat,ix):
        rv_continuous.link.__doc__
        if ix==1:
            return x-phat[0]/sqrt(-2.0*logSF)
        else:
            return x-phat[1]*sqrt(-2.0*logSF)

    def _rvs(self):
        return chi.rvs(2,size=self._size)
    def _pdf(self, r):
        return r*exp(-r*r/2.0)
    def _cdf(self, r):
        return 1.0-exp(-r*r/2.0)
    def _ppf(self, q):
        return sqrt(-2*log(1-q))
    def _stats(self):
        val = 4-pi
        return pi/2, val/2, 2*(pi-3)*sqrt(pi)/val**1.5, \
               6*pi/val-16/val**2
    def _entropy(self):
        return _EULER/2.0 + 1 - 0.5*log(2)
rayleigh = rayleigh_gen(a=0.0, name="rayleigh",
                        longname="A Rayleigh",
                        extradoc="""

Rayleigh distribution

rayleigh.pdf(r) = r * exp(-r**2/2)
for x >= 0.
"""
                        )

# Reciprocal Distribution
class reciprocal_gen(rv_continuous):
    def _argcheck(self, a, b):
        self.a = a
        self.b = b
        self.d = log(b*1.0 / a)
        return (a > 0) & (b > 0) & (b > a)
    def _pdf(self, x, a, b):
        # argcheck should be called before _pdf
        return 1.0/(x*self.d)
    def _cdf(self, x, a, b):
        return (log(x)-log(a)) / self.d
    def _ppf(self, q, a, b):
        return a*pow(b*1.0/a,q)
    def _munp(self, n, a, b):
        return 1.0/self.d / n * (pow(b*1.0,n) - pow(a*1.0,n))
    def _entropy(self,a,b):
        return 0.5*log(a*b)+log(log(b/a))
reciprocal = reciprocal_gen(name="reciprocal",
                            longname="A reciprocal",
                            shapes="a,b", extradoc="""

Reciprocal distribution

reciprocal.pdf(x,a,b) = 1/(x*log(b/a))
for a <= x <= b, a,b > 0.
"""
                            )

# Rice distribution

# FIXME: PPF does not work.
class rice_gen(rv_continuous):
    def _pdf(self, x, b):
        return x*exp(-(x*x+b*b)/2.0)*special.i0(x*b)
    def _munp(self, n, b):
        nd2 = n/2.0
        n1 = 1+nd2
        b2 = b*b/2.0
        return 2.0**(nd2)*exp(-b2)*special.gamma(n1) * \
               special.hyp1f1(n1,1,b2)
rice = rice_gen(a=0.0, name="rice", longname="A Rice",
                shapes="b", extradoc="""

Rician distribution

rice.pdf(x,b) = x * exp(-(x**2+b**2)/2) * I[0](x*b)
for x > 0, b > 0.
"""
                )

# Reciprocal Inverse Gaussian

# FIXME: PPF does not work.
class recipinvgauss_gen(rv_continuous):
    def _rvs(self, mu): #added, taken from invnorm
        return 1.0/mtrand.wald(mu, 1.0, size=self._size)
    def _pdf(self, x, mu):
        return 1.0/sqrt(2*pi*x)*exp(-(1-mu*x)**2.0 / (2*x*mu**2.0))
    def _cdf(self, x, mu):
        trm1 = 1.0/mu - x
        trm2 = 1.0/mu + x
        isqx = 1.0/sqrt(x)
        return 1.0-norm.cdf(isqx*trm1)-exp(2.0/mu)*norm.cdf(-isqx*trm2)
    # xb=50 or something large is necessary for stats to converge without exception
recipinvgauss = recipinvgauss_gen(a=0.0, xb=50, name='recipinvgauss',
                                  longname="A reciprocal inverse Gaussian",
                                  shapes="mu", extradoc="""

Reciprocal inverse Gaussian

recipinvgauss.pdf(x, mu) = 1/sqrt(2*pi*x) * exp(-(1-mu*x)**2/(2*x*mu**2))
for x >= 0.
"""
                                  )

# Semicircular

class semicircular_gen(rv_continuous):
    def _pdf(self, x):
        return 2.0/pi*sqrt(1-x*x)
    def _cdf(self, x):
        return 0.5+1.0/pi*(x*sqrt(1-x*x) + arcsin(x))
    def _stats(self):
        return 0, 0.25, 0, -1.0
    def _entropy(self):
        return 0.64472988584940017414
semicircular = semicircular_gen(a=-1.0,b=1.0, name="semicircular",
                                longname="A semicircular",
                                extradoc="""

Semicircular distribution

semicircular.pdf(x) = 2/pi * sqrt(1-x**2)
for -1 <= x <= 1.
"""
                                )

# Triangular
# up-sloping line from loc to (loc + c*scale) and then downsloping line from
#    loc + c*scale to loc + scale

# _trstr = "Left must be <= mode which must be <= right with left < right"
class triang_gen(rv_continuous):
    def _rvs(self, c):
        return mtrand.triangular(0, c, 1, self._size)
    def _argcheck(self, c):
        return (c >= 0) & (c <= 1)
    def _pdf(self, x, c):
        return where(x < c, 2*x/c, 2*(1-x)/(1-c))
    def _cdf(self, x, c):
        return where(x < c, x*x/c, (x*x-2*x+c)/(c-1))
    def _ppf(self, q, c):
        return where(q < c, sqrt(c*q), 1-sqrt((1-c)*(1-q)))
    def _stats(self, c):
        return (c+1.0)/3.0, (1.0-c+c*c)/18, sqrt(2)*(2*c-1)*(c+1)*(c-2) / \
               (5*(1.0-c+c*c)**1.5), -3.0/5.0
    def _entropy(self,c):
        return 0.5-log(2)
triang = triang_gen(a=0.0, b=1.0, name="triang", longname="A Triangular",
                    shapes="c", extradoc="""

Triangular distribution

    up-sloping line from loc to (loc + c*scale) and then downsloping
    for (loc + c*scale) to (loc+scale).

    - standard form is in the range [0,1] with c the mode.
    - location parameter shifts the start to loc
    - scale changes the width from 1 to scale
"""
                    )

# Truncated Exponential

class truncexpon_gen(rv_continuous):
    def _argcheck(self, b):
        self.b = b
        return (b > 0)
    def _pdf(self, x, b):
        return exp(-x)/(1-exp(-b))
    def _cdf(self, x, b):
        return (1.0-exp(-x))/(1-exp(-b))
    def _ppf(self, q, b):
        return -log(1-q+q*exp(-b))
    def _munp(self, n, b):
        return gam(n+1)-special.gammainc(1+n,b)
    def _entropy(self, b):
        eB = exp(b)
        return log(eB-1)+(1+eB*(b-1.0))/(1.0-eB)
truncexpon = truncexpon_gen(a=0.0, name='truncexpon',
                            longname="A truncated exponential",
                            shapes="b", extradoc="""

Truncated exponential distribution

truncexpon.pdf(x,b) = exp(-x)/(1-exp(-b))
for 0 < x < b.
"""
                            )

# Truncated Normal

class truncnorm_gen(rv_continuous):
    def _argcheck(self, a, b):
        self.a = a
        self.b = b
        self.nb = norm._cdf(b)
        self.na = norm._cdf(a)
        return (a != b)
    def _pdf(self, x, a, b):
        return norm._pdf(x) / (self.nb - self.na)
    def _cdf(self, x, a, b):
        return (norm._cdf(x) - self.na) / (self.nb - self.na)
    def _ppf(self, q, a, b):
        return norm._ppf(q*self.nb + self.na*(1.0-q))
    def _stats(self, a, b):
        nA, nB = self.na, self.nb
        d = nB - nA
        pA, pB = norm._pdf(a), norm._pdf(b)
        mu = (pB - pA) / d
        mu2 = 1 + (a*pA - b*pB) / d - mu*mu
        return mu, mu2, None, None
truncnorm = truncnorm_gen(name='truncnorm', longname="A truncated normal",
                          shapes="a,b", extradoc="""

Truncated Normal distribution.

  The standard form of this distribution is a standard normal truncated to the
  range [a,b] --- notice that a and b are defined over the domain
  of the standard normal.  To convert clip values for a specific mean and
  standard deviation use a,b = (myclip_a-my_mean)/my_std, (myclip_b-my_mean)/my_std
"""
                          )

# Tukey-Lambda
# A flexible distribution ranging from Cauchy (lam=-1)
#   to logistic (lam=0.0)
#   to approx Normal (lam=0.14)
#   to u-shape (lam = 0.5)
#   to Uniform from -1 to 1 (lam = 1)

# FIXME: RVS does not work.
class tukeylambda_gen(rv_continuous):
    def _pdf(self, x, lam):
        Fx = arr(special.tklmbda(x,lam))
        Px = Fx**(lam-1.0) + (arr(1-Fx))**(lam-1.0)
        Px = 1.0/arr(Px)
        return where((lam > 0) & (abs(x) < 1.0/lam), Px, 0.0)
    def _cdf(self, x, lam):
        return special.tklmbda(x, lam)
    def _ppf(self, q, lam):
        q = q*1.0
        vals1 = (q**lam - (1-q)**lam)/lam
        vals2 = log(q/(1-q))
        return where((lam == 0)&(q==q), vals2, vals1)
    def _stats(self, lam):
        mu2 = 2*gam(lam+1.5)-lam*pow(4,-lam)*sqrt(pi)*gam(lam)*(1-2*lam)
        mu2 /= lam*lam*(1+2*lam)*gam(1+1.5)
        mu4 = 3*gam(lam)*gam(lam+0.5)*pow(2,-2*lam) / lam**3 / gam(2*lam+1.5)
        mu4 += 2.0/lam**4 / (1+4*lam)
        mu4 -= 2*sqrt(3)*gam(lam)*pow(2,-6*lam)*pow(3,3*lam) * \
            gam(lam+1.0/3)*gam(lam+2.0/3) / (lam**3.0 * gam(2*lam+1.5) * \
                                             gam(lam+0.5))
        g2 = mu4 / mu2 / mu2 - 3.0

        return 0, mu2, 0, g2
    def _entropy(self, lam):
        def integ(p):
            return log(pow(p,lam-1)+pow(1-p,lam-1))
        return quad(integ,0,1)[0]
        #return scipy.integrate.quad(integ,0,1)[0]
tukeylambda = tukeylambda_gen(name='tukeylambda', longname="A Tukey-Lambda",
                              shapes="lam", extradoc="""

Tukey-Lambda distribution

   A flexible distribution ranging from Cauchy (lam=-1)
   to logistic (lam=0.0)
   to approx Normal (lam=0.14)
   to u-shape (lam = 0.5)
   to Uniform from -1 to 1 (lam = 1)
"""
                              )

# Uniform
# loc to loc + scale

class uniform_gen(rv_continuous):
    def _rvs(self):
        return mtrand.uniform(0.0,1.0,self._size)
    def _pdf(self, x):
        return 1.0*(x==x)
    def _cdf(self, x):
        return x
    def _ppf(self, q):
        return q
    def _stats(self):
        return 0.5, 1.0/12, 0, -1.2
    def _entropy(self):
        return 0.0
uniform = uniform_gen(a=0.0,b=1.0, name='uniform', longname="A uniform",
                      extradoc="""

Uniform distribution

   constant between loc and loc+scale
"""
                      )

# Von-Mises

# if x is not in range or loc is not in range it assumes they are angles
#   and converts them to [-pi, pi] equivalents.

eps = numpy.finfo(float).eps

class vonmises_gen(rv_continuous):
    def _rvs(self, b):
        return mtrand.vonmises(0.0, b, size=self._size)
    def _pdf(self, x, b):
        return exp(b*cos(x)) / (2*pi*special.i0(b))
    def _cdf(self, x, b):
        return vonmises_cython.von_mises_cdf(b,x)
    def _stats_skip(self, b):
        return 0, None, 0, None
vonmises = vonmises_gen(name='vonmises', longname="A Von Mises",
                        shapes="b", extradoc="""

Von Mises distribution

  if x is not in range or loc is not in range it assumes they are angles
     and converts them to [-pi, pi] equivalents.

  vonmises.pdf(x,b) = exp(b*cos(x)) / (2*pi*I[0](b))
  for -pi <= x <= pi, b > 0.

"""
                        )


## Wald distribution (Inverse Normal with shape parameter mu=1.0)

class wald_gen(invnorm_gen):
    def _rvs(self):
        return invnorm_gen._rvs(self, 1.0)
    def _pdf(self, x):
        return invnorm.pdf(x,1.0)
    def _cdf(self, x):
        return invnorm.cdf(x,1,0)
    def _stats(self):
        return 1.0, 1.0, 3.0, 15.0
wald = wald_gen(a=0.0, name="wald", longname="A Wald",
                extradoc="""

Wald distribution

wald.pdf(x) = 1/sqrt(2*pi*x**3) * exp(-(x-1)**2/(2*x))
for x > 0.
"""
                )

## Weibull
## See Frechet

# Wrapped Cauchy

class wrapcauchy_gen(rv_continuous):
    def _argcheck(self, c):
        return (c > 0) & (c < 1)
    def _pdf(self, x, c):
        return (1.0-c*c)/(2*pi*(1+c*c-2*c*cos(x)))
    def _cdf(self, x, c):
        output = 0.0*x
        val = (1.0+c)/(1.0-c)
        c1 = x<pi
        c2 = 1-c1
        xp = extract( c1,x)
        valp = extract(c1,val)
        xn = extract( c2,x)
        valn = extract(c2,val)
        if (any(xn)):
            xn = 2*pi - xn
            yn = tan(xn/2.0)
            on = 1.0-1.0/pi*arctan(valn*yn)
            place(output, c2, on)
        if (any(xp)):
            yp = tan(xp/2.0)
            op = 1.0/pi*arctan(valp*yp)
            place(output, c1, op)
        return output
    def _ppf(self, q, c):
        val = (1.0-c)/(1.0+c)
        rcq = 2*arctan(val*tan(pi*q))
        rcmq = 2*pi-2*arctan(val*tan(pi*(1-q)))
        return where(q < 1.0/2, rcq, rcmq)
    def _entropy(self, c):
        return log(2*pi*(1-c*c))
wrapcauchy = wrapcauchy_gen(a=0.0,b=2*pi, name='wrapcauchy',
                            longname="A wrapped Cauchy",
                            shapes="c", extradoc="""

Wrapped Cauchy distribution

wrapcauchy.pdf(x,c) = (1-c**2) / (2*pi*(1+c**2-2*c*cos(x)))
for 0 <= x <= 2*pi, 0 < c < 1.
"""
                            )

### DISCRETE DISTRIBUTIONS
###

def entropy(pk,qk=None):
    """S = entropy(pk,qk=None)

    calculate the entropy of a distribution given the p_k values
    S = -sum(pk * log(pk), axis=0)

    If qk is not None, then compute a relative entropy
    S = sum(pk * log(pk / qk), axis=0)

    Routine will normalize pk and qk if they don't sum to 1
    """
    pk = arr(pk)
    pk = 1.0* pk / sum(pk,axis=0)
    if qk is None:
        vec = where(pk == 0, 0.0, pk*log(pk))
    else:
        qk = arr(qk)
        if len(qk) != len(pk):
            raise ValueError, "qk and pk must have same length."
        qk = 1.0*qk / sum(qk,axis=0)
        # If qk is zero anywhere, then unless pk is zero at those places
        #   too, the relative entropy is infinite.
        if any(take(pk,nonzero(qk==0.0),axis=0)!=0.0, 0):
            return inf
        vec = where (pk == 0, 0.0, -pk*log(pk / qk))
    return -sum(vec,axis=0)


## Handlers for generic case where xk and pk are given



def _drv_pmf(self, xk, *args):
    try:
        return self.P[xk]
    except KeyError:
        return 0.0

def _drv_cdf(self, xk, *args):
    indx = argmax((self.xk>xk),axis=-1)-1
    return self.F[self.xk[indx]]

def _drv_ppf(self, q, *args):
    indx = argmax((self.qvals>=q),axis=-1)
    return self.Finv[self.qvals[indx]]

def _drv_nonzero(self, k, *args):
    return 1

def _drv_moment(self, n, *args):
    n = arr(n)
    return sum(self.xk**n[newaxis,...] * self.pk, axis=0)

def _drv_moment_gen(self, t, *args):
    t = arr(t)
    return sum(exp(self.xk * t[newaxis,...]) * self.pk, axis=0)

def _drv2_moment(self, n, *args):
    '''non-central moment of discrete distribution'''
    #many changes, originally not even a return
    tot = 0.0
    diff = 1e100
    #pos = self.a
    pos = max(0, self.a)
    count = 0
    #handle cases with infinite support
    ulimit = max(1000, (min(self.b,1000) + max(self.a,-1000))/2.0 )
    llimit = min(-1000, (min(self.b,1000) + max(self.a,-1000))/2.0 )

    while (pos <= self.b) and ((pos <= ulimit) or \
                               (diff > self.moment_tol)):
        diff = pos**n * self.pmf(pos,*args)
        # use pmf because _pmf does not check support in randint
        #     and there might be problems ? with correct self.a, self.b at this stage
        tot += diff
        pos += self.inc
        count += 1

    if self.a < 0: #handle case when self.a = -inf
        diff = 1e100
        pos = -self.inc
        while (pos >= self.a) and ((pos >= llimit) or \
                                   (diff > self.moment_tol)):
            diff = pos**n * self.pmf(pos,*args)  #using pmf instead of _pmf
            tot += diff
            pos -= self.inc
            count += 1
    return tot

def _drv2_ppfsingle(self, q, *args):  # Use basic bisection algorithm
    b = self.invcdf_b
    a = self.invcdf_a
    if isinf(b):            # Be sure ending point is > q
        b = max(100*q,10)
        while 1:
            if b >= self.b: qb = 1.0; break
            qb = self._cdf(b,*args)
            if (qb < q): b += 10
            else: break
    else:
        qb = 1.0
    if isinf(a):    # be sure starting point < q
        a = min(-100*q,-10)
        while 1:
            if a <= self.a: qb = 0.0; break
            qa = self._cdf(a,*args)
            if (qa > q): a -= 10
            else: break
    else:
        qa = self._cdf(a, *args)

    while 1:
        if (qa == q):
            return a
        if (qb == q):
            return b
        if b == a+1:
    #testcase: return wrong number at lower index
    #python -c "from scipy.stats import zipf;print zipf.ppf(0.01,2)" wrong
    #python -c "from scipy.stats import zipf;print zipf.ppf([0.01,0.61,0.77,0.83],2)"
    #python -c "from scipy.stats import logser;print logser.ppf([0.1,0.66, 0.86,0.93],0.6)"
            if qa > q:
                return a
            else:
                return b
        c = int((a+b)/2.0)
        qc = self._cdf(c, *args)
        if (qc < q):
            a = c
            qa = qc
        elif (qc > q):
            b = c
            qb = qc
        else:
            return c

def reverse_dict(dict):
    newdict = {}
    sorted_keys = copy(dict.keys())
    sorted_keys.sort()
    for key in sorted_keys[::-1]:
        newdict[dict[key]] = key
    return newdict

def make_dict(keys, values):
    d = {}
    for key, value in zip(keys, values):
        d[key] = value
    return d

# Must over-ride one of _pmf or _cdf or pass in
#  x_k, p(x_k) lists in initialization

class rv_discrete(rv_generic):
    """A generic discrete random variable.

    Discrete random variables are defined from a standard form.
    The standard form may require some other parameters to complete
    its specification.  The distribution methods also take an optional location
    parameter using loc= keyword.  The default is loc=0.  The calling form
    of the methods follow:

    generic.rvs(<shape(s)>,loc=0)
        - random variates

    generic.pmf(x,<shape(s)>,loc=0)
        - probability mass function

    generic.cdf(x,<shape(s)>,loc=0)
        - cumulative density function

    generic.sf(x,<shape(s)>,loc=0)
        - survival function (1-cdf --- sometimes more accurate)

    generic.ppf(q,<shape(s)>,loc=0)
        - percent point function (inverse of cdf --- percentiles)

    generic.isf(q,<shape(s)>,loc=0)
        - inverse survival function (inverse of sf)

    generic.stats(<shape(s)>,loc=0,moments='mv')
        - mean('m',axis=0), variance('v'), skew('s'), and/or kurtosis('k')

    generic.entropy(<shape(s)>,loc=0)
        - entropy of the RV

    Alternatively, the object may be called (as a function) to fix
       the shape and location parameters returning a
       "frozen" discrete RV object:

    myrv = generic(<shape(s)>,loc=0)
        - frozen RV object with the same methods but holding the
            given shape and location fixed.

    You can construct an aribtrary discrete rv where P{X=xk} = pk
    by passing to the rv_discrete initialization method (through the values=
    keyword) a tuple of sequences (xk,pk) which describes only those values of
    X (xk) that occur with nonzero probability (pk).
    """
    def __init__(self, a=0, b=inf, name=None, badvalue=None,
                 moment_tol=1e-8,values=None,inc=1,longname=None,
                 shapes=None, extradoc=None):

        rv_generic.__init__(self)

        if badvalue is None:
            badvalue = nan
        self.badvalue = badvalue
        self.a = a
        self.b = b
        self.invcdf_a = a   # what's the difference to self.a, .b
        self.invcdf_b = b
        self.name = name
        self.moment_tol = moment_tol
        self.inc = inc
        self._cdfvec = sgf(self._cdfsingle,otypes='d')
        self.return_integers = 1
        self.vecentropy = vectorize(self._entropy)
        self.shapes = shapes
        self.extradoc = extradoc

        if values is not None:
            self.xk, self.pk = values
            self.return_integers = 0
            indx = argsort(ravel(self.xk))
            self.xk = take(ravel(self.xk),indx, 0)
            self.pk = take(ravel(self.pk),indx, 0)
            self.a = self.xk[0]
            self.b = self.xk[-1]
            self.P = make_dict(self.xk, self.pk)
            self.qvals = numpy.cumsum(self.pk,axis=0)
            self.F = make_dict(self.xk, self.qvals)
            self.Finv = reverse_dict(self.F)
            self._ppf = new.instancemethod(sgf(_drv_ppf,otypes='d'),
                                           self, rv_discrete)
            self._pmf = new.instancemethod(sgf(_drv_pmf,otypes='d'),
                                           self, rv_discrete)
            self._cdf = new.instancemethod(sgf(_drv_cdf,otypes='d'),
                                           self, rv_discrete)
            self._nonzero = new.instancemethod(_drv_nonzero, self, rv_discrete)
            self.generic_moment = new.instancemethod(_drv_moment,
                                                     self, rv_discrete)
            self.moment_gen = new.instancemethod(_drv_moment_gen,
                                                 self, rv_discrete)
            self.numargs=0
        else:
            cdf_signature = inspect.getargspec(self._cdf.im_func)
            numargs1 = len(cdf_signature[0]) - 2
            pmf_signature = inspect.getargspec(self._pmf.im_func)
            numargs2 = len(pmf_signature[0]) - 2
            self.numargs = max(numargs1, numargs2)

            #nin correction needs to be after we know numargs
            #correct nin for generic moment vectorization
            self.vec_generic_moment = sgf(_drv2_moment, otypes='d')
            self.vec_generic_moment.nin = self.numargs + 2
            self.generic_moment = new.instancemethod(self.vec_generic_moment,
                                                     self, rv_discrete)

            #correct nin for ppf vectorization
            _vppf = sgf(_drv2_ppfsingle,otypes='d')
            _vppf.nin = self.numargs + 2 # +1 is for self
            self._vecppf = new.instancemethod(_vppf,
                                              self, rv_discrete)



        #now that self.numargs is defined, we can adjust nin
        self._cdfvec.nin = self.numargs + 1

        if longname is None:
            if name[0] in ['aeiouAEIOU']: hstr = "An "
            else: hstr = "A "
            longname = hstr + name
        if self.__doc__ is None:
            self.__doc__ = rv_discrete.__doc__
        if self.__doc__ is not None:
            self.__doc__ = self.__doc__.replace("A Generic",longname)
            if name is not None:
                self.__doc__ = self.__doc__.replace("generic",name)
            if shapes is None:
                self.__doc__ = self.__doc__.replace("<shape(s)>,","")
            else:
                self.__doc__ = self.__doc__.replace("<shape(s)>",shapes)
            ind = self.__doc__.find("You can construct an arbitrary")
            self.__doc__ = self.__doc__[:ind].strip()
            if extradoc is not None:
                self.__doc__ = self.__doc__ + extradoc

    def _rvs(self, *args):
        return self._ppf(mtrand.random_sample(self._size),*args)

    def _nonzero(self, k, *args):
        return floor(k)==k

    def _argcheck(self, *args):
        cond = 1
        for arg in args:
            cond &= (arg > 0)
        return cond

    def _pmf(self, k, *args):
        return self.cdf(k,*args) - self.cdf(k-1,*args)

    def _cdfsingle(self, k, *args):
        m = arange(int(self.a),k+1)
        return sum(self._pmf(m,*args),axis=0)

    def _cdf(self, x, *args):
        k = floor(x)
        return self._cdfvec(k,*args)

    def _sf(self, x, *args):
        return 1.0-self._cdf(x,*args)

    def _ppf(self, q, *args):
        return self._vecppf(q, *args)

    def _isf(self, q, *args):
        return self._ppf(1-q,*args)

    def _stats(self, *args):
        return None, None, None, None

    def _munp(self, n, *args):
        return self.generic_moment(n, *args)


    def rvs(self, *args, **kwargs):
        kwargs['discrete'] = True
        return super(rv_discrete,self).rvs(*args, **kwargs)
        #rv_generic.rvs(self, *args, **kwargs)

    def pmf(self, k,*args, **kwds):
        """Probability mass function at k of the given RV.

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        """
        loc = kwds.get('loc')
        args, loc = self.fix_loc(args, loc)
        k,loc = map(arr,(k,loc))
        args = tuple(map(arr,args))
        k = arr((k-loc))
        cond0 = self._argcheck(*args)
        cond1 = (k >= self.a) & (k <= self.b) & self._nonzero(k,*args)
        cond = cond0 & cond1
        output = zeros(shape(cond),'d')
        place(output,(1-cond0)*(cond1==cond1),self.badvalue)
        goodargs = argsreduce(cond, *((k,)+args))
        place(output,cond,self._pmf(*goodargs))
        if output.ndim == 0:
            return output[()]
        return output

    def cdf(self, k, *args, **kwds):
        """Cumulative distribution function at k of the given RV

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        """
        loc = kwds.get('loc')
        args, loc = self.fix_loc(args, loc)
        k,loc = map(arr,(k,loc))
        args = tuple(map(arr,args))
        k = arr((k-loc))
        cond0 = self._argcheck(*args)
        cond1 = (k >= self.a) & (k < self.b)
        cond2 = (k >= self.b)
        cond = cond0 & cond1
        output = zeros(shape(cond),'d')
        place(output,(1-cond0)*(cond1==cond1),self.badvalue)
        place(output,cond2*(cond0==cond0), 1.0)

        if any(cond):
            goodargs = argsreduce(cond, *((k,)+args))
            place(output,cond,self._cdf(*goodargs))
        if output.ndim == 0:
            return output[()]
        return output

    def sf(self,k,*args,**kwds):
        """Survival function (1-cdf) at k of the given RV

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        """
        loc= kwds.get('loc')
        args, loc = self.fix_loc(args, loc)
        k,loc = map(arr,(k,loc))
        args = tuple(map(arr,args))
        k = arr(k-loc)
        cond0 = self._argcheck(*args)
        cond1 = (k >= self.a) & (k <= self.b)
        cond2 = (k < self.a) & cond0
        cond = cond0 & cond1
        output = zeros(shape(cond),'d')
        place(output,(1-cond0)*(cond1==cond1),self.badvalue)
        place(output,cond2,1.0)
        goodargs = argsreduce(cond, *((k,)+args))
        place(output,cond,self._sf(*goodargs))
        if output.ndim == 0:
            return output[()]
        return output

    def ppf(self,q,*args,**kwds):
        """Percent point function (inverse of cdf) at q of the given RV

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        """
        loc = kwds.get('loc')
        args, loc = self.fix_loc(args, loc)
        q,loc  = map(arr,(q,loc))
        args = tuple(map(arr,args))
        cond0 = self._argcheck(*args) & (loc == loc)
        cond1 = (q > 0) & (q < 1)
        cond2 = (q==1) & cond0
        cond = cond0 & cond1
        output = valarray(shape(cond),value=self.badvalue,typecode='d')
        #output type 'd' to handle nin and inf
        place(output,(q==0)*(cond==cond), self.a-1)
        place(output,cond2,self.b)
        if any(cond):
            goodargs = argsreduce(cond, *((q,)+args+(loc,)))
            loc, goodargs = goodargs[-1], goodargs[:-1]
            place(output,cond,self._ppf(*goodargs) + loc)

        if output.ndim == 0:
            return output[()]
        return output

    def isf(self,q,*args,**kwds):
        """Inverse survival function (1-sf) at q of the given RV

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc   - location parameter (default=0)
        """

        loc = kwds.get('loc')
        args, loc = self.fix_loc(args, loc)
        q,loc  = map(arr,(q,loc))
        args = tuple(map(arr,args))
        cond0 = self._argcheck(*args) & (loc == loc)
        cond1 = (q > 0) & (q < 1)
        cond2 = (q==1) & cond0
        cond = cond0 & cond1
        #old:
##        output = valarray(shape(cond),value=self.b,typecode='d')
##        #typecode 'd' to handle nin and inf
##        place(output,(1-cond0)*(cond1==cond1), self.badvalue)
##        place(output,cond2,self.a-1)

        #same problem as with ppf
        # copied from ppf and changed
        output = valarray(shape(cond),value=self.badvalue,typecode='d')
        #output type 'd' to handle nin and inf
        place(output,(q==0)*(cond==cond), self.b)
        place(output,cond2,self.a-1)

        # call place only if at least 1 valid argument
        if any(cond):
            goodargs = argsreduce(cond, *((q,)+args+(loc,)))
            loc, goodargs = goodargs[-1], goodargs[:-1]
            place(output,cond,self._isf(*goodargs) + loc) #PB same as ticket 766

        if output.ndim == 0:
            return output[()]
        return output

    def stats(self, *args, **kwds):
        """Some statistics of the given discrete RV

        *args
        =====
        The shape parameter(s) for the distribution (see docstring of the
           instance object for more information)

        **kwds
        ======
        loc     - location parameter (default=0)
        moments - a string composed of letters ['mvsk'] specifying
                   which moments to compute (default='mv')
                   'm' = mean,
                   'v' = variance,
                   's' = (Fisher's) skew,
                   'k' = (Fisher's) kurtosis.
        """
        loc,moments=map(kwds.get,['loc','moments'])
        N = len(args)
        if N > self.numargs:
            if N == self.numargs + 1 and loc is None:  # loc is given without keyword
                loc = args[-1]
            if N == self.numargs + 2 and moments is None: # loc, scale, and moments
                loc, moments = args[-2:]
            args = args[:self.numargs]
        if loc is None: loc = 0.0
        if moments is None: moments = 'mv'

        loc = arr(loc)
        args = tuple(map(arr,args))
        cond = self._argcheck(*args) & (loc==loc)

        signature = inspect.getargspec(self._stats.im_func)
        if (signature[2] is not None) or ('moments' in signature[0]):
            mu, mu2, g1, g2 = self._stats(*args,**{'moments':moments})
        else:
            mu, mu2, g1, g2 = self._stats(*args)
        if g1 is None:
            mu3 = None
        else:
            mu3 = g1*(mu2**1.5)
        default = valarray(shape(cond), self.badvalue)
        output = []

        # Use only entries that are valid in calculation
        goodargs = argsreduce(cond, *(args+(loc,)))
        loc, goodargs = goodargs[-1], goodargs[:-1]

        if 'm' in moments:
            if mu is None:
                mu = self._munp(1.0,*goodargs)
            out0 = default.copy()
            place(out0,cond,mu+loc)
            output.append(out0)

        if 'v' in moments:
            if mu2 is None:
                mu2p = self._munp(2.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                mu2 = mu2p - mu*mu
            out0 = default.copy()
            place(out0,cond,mu2)
            output.append(out0)

        if 's' in moments:
            if g1 is None:
                mu3p = self._munp(3.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                if mu2 is None:
                    mu2p = self._munp(2.0,*goodargs)
                    mu2 = mu2p - mu*mu
                mu3 = mu3p - 3*mu*mu2 - mu**3
                g1 = mu3 / mu2**1.5
            out0 = default.copy()
            place(out0,cond,g1)
            output.append(out0)

        if 'k' in moments:
            if g2 is None:
                mu4p = self._munp(4.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                if mu2 is None:
                    mu2p = self._munp(2.0,*goodargs)
                    mu2 = mu2p - mu*mu
                if mu3 is None:
                    mu3p = self._munp(3.0,*goodargs)
                    mu3 = mu3p - 3*mu*mu2 - mu**3
                mu4 = mu4p - 4*mu*mu3 - 6*mu*mu*mu2 - mu**4
                g2 = mu4 / mu2**2.0 - 3.0
            out0 = default.copy()
            place(out0,cond,g2)
            output.append(out0)

        if len(output) == 1:
            return output[0]
        else:
            return tuple(output)

    def moment(self, n, *args, **kwds):   # Non-central moments in standard form.
        if (floor(n) != n):
            raise ValueError, "Moment must be an integer."
        if (n < 0): raise ValueError, "Moment must be positive."
        if (n == 0): return 1.0
        if (n > 0) and (n < 5):
            signature = inspect.getargspec(self._stats.im_func)
            if (signature[2] is not None) or ('moments' in signature[0]):
                dict = {'moments':{1:'m',2:'v',3:'vs',4:'vk'}[n]}
            else:
                dict = {}
            mu, mu2, g1, g2 = self._stats(*args,**dict)
            if (n==1):
                if mu is None: return self._munp(1,*args)
                else: return mu
            elif (n==2):
                if mu2 is None or mu is None: return self._munp(2,*args)
                else: return mu2 + mu*mu
            elif (n==3):
                if g1 is None or mu2 is None: return self._munp(3,*args)
                else: return g1*(mu2**1.5)
            else: # (n==4)
                if g2 is None or mu2 is None: return self._munp(4,*args)
                else: return (g2+3.0)*(mu2**2.0)
        else:
            return self._munp(n,*args)

    def freeze(self, *args, **kwds):
        return rv_frozen(self, *args, **kwds)

    def _entropy(self, *args):
        if hasattr(self,'pk'):
            return entropy(self.pk)
        else:
            mu = int(self.stats(*args, **{'moments':'m'}))
            val = self.pmf(mu,*args)
            if (val==0.0): ent = 0.0
            else: ent = -val*log(val)
            k = 1
            term = 1.0
            while (abs(term) > eps):
                val = self.pmf(mu+k,*args)
                if val == 0.0: term = 0.0
                else: term = -val * log(val)
                val = self.pmf(mu-k,*args)
                if val != 0.0: term -= val*log(val)
                k += 1
                ent += term
            return ent

    def entropy(self, *args, **kwds):
        loc= kwds.get('loc')
        args, loc = self.fix_loc(args, loc)
        loc = arr(loc)
        args = map(arr,args)
        cond0 = self._argcheck(*args) & (loc==loc)
        output = zeros(shape(cond0),'d')
        place(output,(1-cond0),self.badvalue)
        goodargs = argsreduce(cond0, *args)
        place(output,cond0,self.vecentropy(*goodargs))
        return output

    def __call__(self, *args, **kwds):
        return self.freeze(*args,**kwds)

# Binomial

class binom_gen(rv_discrete):
    def _rvs(self, n, pr):
        return mtrand.binomial(n,pr,self._size)
    def _argcheck(self, n, pr):
        self.b = n
        return (n>=0) & (pr >= 0) & (pr <= 1)
    def _pmf(self,x,n,pr):
        """ Return PMF

        Reference
        --------------
         Catherine Loader (2000).
         "Fast and Accurate Computation of Binomial Probabilities";
           url = "http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.35.2719" }
        """
        # if (p==0.0) return( (x==0) ? 1.0 : 0.0);
        # if (p==1.0) return( (x==n) ? 1.0 : 0.0);
        # if (x==0) return(exp(n.*log1p(-p)));
        # if (x==n) return(exp(n.*log(p)));
        PI2 = 2.*pi #6.283185307179586476925286;
        yborder = (x==0.)*exp(n*log1p(-pr))+(x==n)*exp(n*log(pr))
        nx = n-x
        nq = n*(1.-pr)
        lc = stirlerr(n) - stirlerr(x) - stirlerr(nx) - bd0(x,n*pr) - bd0(nx,nq)
        inside = (0.<pr) & (pr<1.) & (0.<x) & (x < n)
        return where(inside,exp(lc)*sqrt(n/(PI2*x*nx)),yborder)

    def _cdf(self, x, n, pr):
        k = floor(x)
        vals = special.bdtr(k,n,pr)
        return vals
    def _sf(self, x, n, pr):
        k = floor(x)
        return special.bdtrc(k,n,pr)
    def _ppf(self, q, n, pr):
        vals = ceil(special.bdtrik(q,n,pr))
        vals1 = vals-1
        temp = special.bdtr(vals1,n,pr)
        return where(temp >= q, vals1, vals)
    def _stats(self, n, pr):
        q = 1.0-pr
        mu = n * pr
        var = n * pr * q
        g1 = (q-pr) / sqrt(n*pr*q)
        g2 = (1.0-6*pr*q)/(n*pr*q)
        return mu, var, g1, g2
    def _entropy(self, n, pr):
        k = r_[0:n+1]
        vals = self._pmf(k,n,pr)
        lvals = where(vals==0,0.0,log(vals))
        return -sum(vals*lvals,axis=0)
binom = binom_gen(name='binom',shapes="n,pr",extradoc="""

Binomial distribution

   Counts the number of successes in *n* independent
   trials when the probability of success each time is *pr*.

   binom.pmf(k,n,p) = choose(n,k)*p**k*(1-p)**(n-k)
   for k in {0,1,...,n}
""")

# Bernoulli distribution

class bernoulli_gen(binom_gen):
    def _rvs(self, pr):
        return binom_gen._rvs(self, 1, pr)
    def _argcheck(self, pr):
        return (pr >=0 ) & (pr <= 1)
    def _cdf(self, x, pr):
        return binom_gen._cdf(self, x, 1, pr)
    def _pmf(self,x,pr):
        return binom_gen._pmf(self, x, 1, pr)
    def _sf(self, x, pr):
        return binom_gen._sf(self, x, 1, pr)
    def _ppf(self, q, pr):
        return binom_gen._ppf(self, q, 1, pr)
    def _stats(self, pr):
        return binom_gen._stats(self, 1, pr)
    def _entropy(self, pr):
        return -pr*log(pr)-(1-pr)*log(1-pr)
bernoulli = bernoulli_gen(b=1,name='bernoulli',shapes="pr",extradoc="""

Bernoulli distribution

   1 if binary experiment succeeds, 0 otherwise.  Experiment
   succeeds with probabilty *pr*.

   bernoulli.pmf(k,p) = 1-p  if k = 0
                      = p    if k = 1
   for k = 0,1
"""
)

# Negative binomial
class nbinom_gen(rv_discrete):
    def _rvs(self, n, pr):
        return mtrand.negative_binomial(n, pr, self._size)
    def _argcheck(self, n, pr):
        return (n >= 0) & (pr >= 0) & (pr <= 1)
    def _pmf(self, x, n, pr):
        coeff = exp(special.gammaln(n+x) - special.gammaln(x+1) - special.gammaln(n))
        return coeff * power(pr,n) * power(1-pr,x)
    def _cdf(self, x, n, pr):
        k = floor(x)
        return special.betainc(n, k+1, pr)
    def _sf_skip(self, x, n, pr):
        #skip because special.nbdtrc doesn't work for 0<n<1
        k = floor(x)
        return special.nbdtrc(k,n,pr)
    def _ppf(self, q, n, pr):
        vals = ceil(special.nbdtrik(q,n,pr))
        vals1 = vals-1
        temp = special.nbdtr(vals1,n,pr)
        return where(temp >= q, vals1, vals)
    def _stats(self, n, pr):
        Q = 1.0 / pr
        P = Q - 1.0
        mu = n*P
        var = n*P*Q
        g1 = (Q+P)/sqrt(n*P*Q)
        g2 = (1.0 + 6*P*Q) / (n*P*Q)
        return mu, var, g1, g2
nbinom = nbinom_gen(name='nbinom', longname="A negative binomial",
                    shapes="n,pr", extradoc="""

Negative binomial distribution

nbinom.pmf(k,n,p) = choose(k+n-1,n-1) * p**n * (1-p)**k
for k >= 0.
"""
                    )

## Geometric distribution

class geom_gen(rv_discrete):
    def _rvs(self, pr):
        return mtrand.geometric(pr,size=self._size)
    def _argcheck(self, pr):
        return (pr<=1) & (pr >= 0)
    def _pmf(self, k, pr):
        return (1-pr)**(k-1) * pr
    def _cdf(self, x, pr):
        k = floor(x)
        return (1.0-(1.0-pr)**k)
    def _sf(self, x, pr):
        k = floor(x)
        return (1.0-pr)**k
    def _ppf(self, q, pr):
        vals = ceil(log(1.0-q)/log(1-pr))
        temp = 1.0-(1.0-pr)**(vals-1)
        return where((temp >= q) & (vals > 0), vals-1, vals)
    def _stats(self, pr):
        mu = 1.0/pr
        qr = 1.0-pr
        var = qr / pr / pr
        g1 = (2.0-pr) / sqrt(qr)
        g2 = numpy.polyval([1,-6,6],pr)/(1.0-pr)
        return mu, var, g1, g2
geom = geom_gen(a=1,name='geom', longname="A geometric",
                shapes="pr", extradoc="""

Geometric distribution

geom.pmf(k,p) = (1-p)**(k-1)*p
for k >= 1
"""
                )

## Hypergeometric distribution

class hypergeom_gen(rv_discrete):
    def _rvs(self, M, n, N):
        return mtrand.hypergeometric(n,M-n,N,size=self._size)
    def _argcheck(self, M, n, N):
        cond = rv_discrete._argcheck(self,M,n,N)
        cond &= (n <= M) & (N <= M)
        self.a = N-(M-n)
        self.b = min(n,N)
        return cond
    def _pmf(self, k, M, n, N):
        tot, good = M, n
        bad = tot - good
        return comb(good,k) * comb(bad,N-k) / comb(tot,N)
    def _stats(self, M, n, N):
        tot, good = M, n
        n = good*1.0
        m = (tot-good)*1.0
        N = N*1.0
        tot = m+n
        p = n/tot
        mu = N*p
        var = m*n*N*(tot-N)*1.0/(tot*tot*(tot-1))
        g1 = (m - n)*(tot-2*N) / (tot-2.0)*sqrt((tot-1.0)/(m*n*N*(tot-N)))
        m2, m3, m4, m5 = m**2, m**3, m**4, m**5
        n2, n3, n4, n5 = n**2, n**2, n**4, n**5
        g2 = m3 - m5 + n*(3*m2-6*m3+m4) + 3*m*n2 - 12*m2*n2 + 8*m3*n2 + n3 \
           - 6*m*n3 + 8*m2*n3 + m*n4 - n5 - 6*m3*N + 6*m4*N + 18*m2*n*N \
           - 6*m3*n*N + 18*m*n2*N - 24*m2*n2*N - 6*n3*N - 6*m*n3*N \
           + 6*n4*N + N*N*(6*m2 - 6*m3 - 24*m*n + 12*m2*n + 6*n2 + \
                           12*m*n2 - 6*n3)
        return mu, var, g1, g2
    def _entropy(self, M, n, N):
        k = r_[N-(M-n):min(n,N)+1]
        vals = self.pmf(k,M,n,N)
        lvals = where(vals==0.0,0.0,log(vals))
        return -sum(vals*lvals,axis=0)
hypergeom = hypergeom_gen(name='hypergeom',longname="A hypergeometric",
                          shapes="M,n,N", extradoc="""

Hypergeometric distribution

   Models drawing objects from a bin.
   M is total number of objects, n is total number of Type I objects.
   RV counts number of Type I objects in N drawn without replacement from
   population.

   hypergeom.pmf(k, M, n, N) = choose(n,k)*choose(M-n,N-k)/choose(M,N)
   for N - (M-n) <= k <= min(m,N)
"""
                          )

## Logarithmic (Log-Series), (Series) distribution
# FIXME: Fails _cdfvec
class logser_gen(rv_discrete):
    def _rvs(self, pr):
        # looks wrong for pr>0.5, too few k=1
        # trying to use generic is worse, no k=1 at all
        return mtrand.logseries(pr,size=self._size)
    def _argcheck(self, pr):
        return (pr > 0) & (pr < 1)
    def _pmf(self, k, pr):
        return -pr**k * 1.0 / k / log(1-pr)
    def _stats(self, pr):
        r = log(1-pr)
        mu = pr / (pr - 1.0) / r
        mu2p = -pr / r / (pr-1.0)**2
        var = mu2p - mu*mu
        mu3p = -pr / r * (1.0+pr) / (1.0-pr)**3
        mu3 = mu3p - 3*mu*mu2p + 2*mu**3
        g1 = mu3 / var**1.5

        mu4p = -pr / r * (1.0/(pr-1)**2 - 6*pr/(pr-1)**3 + \
                          6*pr*pr / (pr-1)**4)
        mu4 = mu4p - 4*mu3p*mu + 6*mu2p*mu*mu - 3*mu**4
        g2 = mu4 / var**2 - 3.0
        return mu, var, g1, g2
logser = logser_gen(a=1,name='logser', longname='A logarithmic',
                    shapes='pr', extradoc="""

Logarithmic (Log-Series, Series) distribution

logser.pmf(k,p) = - p**k / (k*log(1-p))
for k >= 1
"""
                    )

## Poisson distribution

class poisson_gen(rv_discrete):
    def _rvs(self, mu):
        return mtrand.poisson(mu, self._size)
    def _pmf(self, k, mu):
        Pk = k*log(mu)-special.gammaln(k+1) - mu
        return exp(Pk)
    def _cdf(self, x, mu):
        k = floor(x)
        return special.pdtr(k,mu)
    def _sf(self, x, mu):
        k = floor(x)
        return special.pdtrc(k,mu)
    def _ppf(self, q, mu):
        vals = ceil(special.pdtrik(q,mu))
        vals1 = vals-1
        temp = special.pdtr(vals1,mu)
        return where((temp >= q), vals1, vals)
    def _stats(self, mu):
        var = mu
        g1 = 1.0/arr(sqrt(mu))
        g2 = 1.0 / arr(mu)
        return mu, var, g1, g2
poisson = poisson_gen(name="poisson", longname='A Poisson',
                      shapes="mu", extradoc="""

Poisson distribution

poisson.pmf(k, mu) = exp(-mu) * mu**k / k!
for k >= 0
"""
                      )

## (Planck) Discrete Exponential

class planck_gen(rv_discrete):
    def _argcheck(self, lambda_):
        if (lambda_ > 0):
            self.a = 0
            self.b = inf
            return 1
        elif (lambda_ < 0):
            self.a = -inf
            self.b = 0
            return 1
        return 0  # lambda_ = 0
    def _pmf(self, k, lambda_):
        fact = (1-exp(-lambda_))
        return fact*exp(-lambda_*k)
    def _cdf(self, x, lambda_):
        k = floor(x)
        return 1-exp(-lambda_*(k+1))
    def _ppf(self, q, lambda_):
        val = ceil(-1.0/lambda_ * log1p(-q)-1)
        return val
    def _stats(self, lambda_):
        mu = 1/(exp(lambda_)-1)
        var = exp(-lambda_)/(expm1(-lambda_))**2
        g1 = 2*cosh(lambda_/2.0)
        g2 = 4+2*cosh(lambda_)
        return mu, var, g1, g2
    def _entropy(self, lambda_):
        l = lambda_
        C = (1-exp(-l))
        return l*exp(-l)/C - log(C)
planck = planck_gen(name='planck',longname='A discrete exponential ',
                    shapes="lambda_",
                    extradoc="""

Planck (Discrete Exponential)

planck.pmf(k,b) = (1-exp(-b))*exp(-b*k)
for k*b >= 0
"""
                      )

class boltzmann_gen(rv_discrete):
    def _pmf(self, k, lambda_, N):
        fact = (1-exp(-lambda_))/(1-exp(-lambda_*N))
        return fact*exp(-lambda_*k)
    def _cdf(self, x, lambda_, N):
        k = floor(x)
        return (1-exp(-lambda_*(k+1)))/(1-exp(-lambda_*N))
    def _ppf(self, q, lambda_, N):
        qnew = q*(1-exp(-lambda_*N))
        val = ceil(-1.0/lambda_ * log(1-qnew)-1)
        return val
    def _stats(self, lambda_, N):
        z = exp(-lambda_)
        zN = exp(-lambda_*N)
        mu = z/(1.0-z)-N*zN/(1-zN)
        var = z/(1.0-z)**2 - N*N*zN/(1-zN)**2
        trm = (1-zN)/(1-z)
        trm2 = (z*trm**2 - N*N*zN)
        g1 = z*(1+z)*trm**3 - N**3*zN*(1+zN)
        g1 = g1 / trm2**(1.5)
        g2 = z*(1+4*z+z*z)*trm**4 - N**4 * zN*(1+4*zN+zN*zN)
        g2 = g2 / trm2 / trm2
        return mu, var, g1, g2

boltzmann = boltzmann_gen(name='boltzmann',longname='A truncated discrete exponential ',
                    shapes="lambda_,N",
                    extradoc="""

Boltzmann (Truncated Discrete Exponential)

boltzmann.pmf(k,b,N) = (1-exp(-b))*exp(-b*k)/(1-exp(-b*N))
for k=0,..,N-1
"""
                      )




## Discrete Uniform

class randint_gen(rv_discrete):
    def _argcheck(self, min, max):
        self.a = min
        self.b = max-1
        return (max > min)
    def _pmf(self, k, min, max):
        fact = 1.0 / (max - min)
        return fact
    def _cdf(self, x, min, max):
        k = floor(x)
        return (k-min+1)*1.0/(max-min)
    def _ppf(self, q, min, max):
        val = ceil(q*(max-min)+min)-1
        return val
    def _stats(self, min, max):
        m2, m1 = arr(max), arr(min)
        mu = (m2 + m1 - 1.0) / 2
        d = m2 - m1
        var = (d-1)*(d+1.0)/12.0
        g1 = 0.0
        g2 = -6.0/5.0*(d*d+1.0)/(d-1.0)*(d+1.0)
        return mu, var, g1, g2
    def _rvs(self, min, max=None):
        """An array of *size* random integers >= min and < max.

        If max is None, then range is >=0  and < min
        """
        return mtrand.randint(min, max, self._size)

    def _entropy(self, min, max):
        return log(max-min)
randint = randint_gen(name='randint',longname='A discrete uniform '\
                      '(random integer)', shapes="min,max",
                      extradoc="""

Discrete Uniform

    Random integers >=min and <max.

    randint.pmf(k,min, max) = 1/(max-min)
    for min <= k < max.
"""
                      )


# Zipf distribution

# FIXME: problems sampling.
class zipf_gen(rv_discrete):
    def _rvs(self, a):
        return mtrand.zipf(a, size=self._size)
    def _argcheck(self, a):
        return a > 1
    def _pmf(self, k, a):
        Pk = 1.0 / arr(special.zeta(a,1) * k**a)
        return Pk
    def _munp(self, n, a):
        return special.zeta(a-n,1) / special.zeta(a,1)
    def _stats(self, a):
        sv = errp(0)
        fac = arr(special.zeta(a,1))
        mu = special.zeta(a-1.0,1)/fac
        mu2p = special.zeta(a-2.0,1)/fac
        var = mu2p - mu*mu
        mu3p = special.zeta(a-3.0,1)/fac
        mu3 = mu3p - 3*mu*mu2p + 2*mu**3
        g1 = mu3 / arr(var**1.5)

        mu4p = special.zeta(a-4.0,1)/fac
        sv = errp(sv)
        mu4 = mu4p - 4*mu3p*mu + 6*mu2p*mu*mu - 3*mu**4
        g2 = mu4 / arr(var**2) - 3.0
        return mu, var, g1, g2
zipf = zipf_gen(a=1,name='zipf', longname='A Zipf',
                shapes="a", extradoc="""

Zipf distribution

zipf.pmf(k,a) = 1/(zeta(a)*k**a)
for k >= 1
"""
                )


# Discrete Laplacian

class dlaplace_gen(rv_discrete):
    def _pmf(self, k, a):
        return tanh(a/2.0)*exp(-a*abs(k))
    def _cdf(self, x, a):
        k = floor(x)
        ind = (k >= 0)
        const = exp(a)+1
        return where(ind, 1.0-exp(-a*k)/const, exp(a*(k+1))/const)
    def _ppf(self, q, a):
        const = 1.0/(1+exp(-a))
        cons2 = 1+exp(a)
        ind = q < const
        return ceil(where(ind, log(q*cons2)/a-1, -log((1-q)*cons2)/a))

    def _stats_skip(self, a):
        # variance mu2 does not aggree with sample variance,
        #   nor with direct calculation using pmf
        # remove for now because generic calculation works
        #   except it does not show nice zeros for mean and skew(?)
        ea = exp(-a)
        e2a = exp(-2*a)
        e3a = exp(-3*a)
        e4a = exp(-4*a)
        mu2 = 2* (e2a + ea) / (1-ea)**3.0
        mu4 = 2* (e4a + 11*e3a + 11*e2a + ea) / (1-ea)**5.0
        return 0.0, mu2, 0.0, mu4 / mu2**2.0 - 3
    def _entropy(self, a):
        return a / sinh(a) - log(tanh(a/2.0))
dlaplace = dlaplace_gen(a=-inf,
                        name='dlaplace', longname='A discrete Laplacian',
                        shapes="a", extradoc="""

Discrete Laplacian distribution.

dlapacle.pmf(k,a) = tanh(a/2) * exp(-a*abs(k))
for a > 0.
"""
                        )

if __name__=='__main__':
    #nbinom(10, 0.75).rvs(3)
    bernoulli(0.75).rvs(3)
    x = np.r_[5,10]
    npr = np.r_[9,9]
    bd0(x,npr)
    #Examples   MLE and better CI for phat.par[0]
    R = weibull_min.rvs(1, size=100);
    phat = weibull_min.fit(R,1,1,par_fix=[nan,0,nan])
    Lp = phat.profile(i=0)
    Lp.plot()
    Lp.get_CI(alpha=0.1)
    R = 1./990
    x = phat.isf(R)

    # CI for x
    Lx = phat.profile(i=0,x=x)
    Lx.plot()
    Lx.get_CI(alpha=0.2)

    # CI for logSF=log(SF)
    Lpr = phat.profile(i=1,logSF=log(R),link = phat.dist.link)
    Lpr.plot()
    Lpr.get_CI(alpha=0.075)

    dlaplace.stats(0.8,loc=0)
#    pass
    t = planck(0.51000000000000001)
    t.ppf(0.5)
    t = zipf(2)
    t.ppf(0.5)
    import pylab as plb
    rice.rvs(1)
    x = plb.linspace(-5,5)
    y = genpareto.cdf(x,0)
    #plb.plot(x,y)
    #plb.show()


    on = ones((2,3))
    r = genpareto.rvs(0,size=100)
    pht = genpareto.fit(r,1,par_fix=[0,0,nan])
    lp = pht.profile()
