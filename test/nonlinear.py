# Copyright Qiqi Wang (qiqi@mit.edu) 2013

import sys
from pylab import *
from numpy import *
from scipy.interpolate import interp1d


#set_printoptions(threshold=nan)

sys.path.append('..')

from lssode import *
from numpad import *

def outputVector1d(vec,size,filename):
    ufile=open(filename,'w')
    for i in range(size[0]):
      ufile.write('%.40f \n' %(vec[i]))
    ufile.close()
    print('File written: ' +filename)

def outputVector2d(vec,size,filename):
    ufile=open(filename,'w')
    for i in range(size[0]):
      ufile.write('%.40f %.40f \n' %(vec[i,0],vec[i,1]))
    ufile.close()
    print('File written: ' +filename)

def outputVector3d(vec,size,filename):
    ufile=open(filename,'w')
    for i in range(size[0]):
      ufile.write('%.40f %.40f %.40f\n' %(vec[i,0],vec[i,1],vec[i,2]))
    ufile.close()
    print('File written: ' +filename)


import struct
def outputBinary(vec,size,filename):
    binfile=open(filename,'wb')
    for i in range(size):
      data=struct.pack('d',vec[i])
      binfile.write(data)
    binfile.close()
    print('File written: ' +filename)


import resource
def using(point=""):
    usage=resource.getrusage(resource.RUSAGE_SELF)
    return '''%s: usertime=%s systime=%s mem=%s mb
           '''%(point,usage[0],usage[1],
                (usage[2]*resource.getpagesize())/1000000.0 )


def lorenz(u, rho):
    shp = u.shape
    x, y, z = u.reshape([-1, 3]).T
    sigma, beta = 10, 8./3
    dxdt, dydt, dzdt = sigma*(y-x), x*(rho-z)-y, x*y - beta*z
    return transpose([dxdt, dydt, dzdt]).reshape(shp)

def vanderpol(u, mu):
    shp = u.shape
    u = u.reshape([-1,2])
    dudt = zeros(u.shape, u.dtype)
    dudt[:,0] = u[:,1]
    dudt[:,1] = -u[:,0] + mu * (1 - u[:,0]**2) * u[:,1]

    return dudt.reshape(shp)

def costfunction(u,target,mu):
    J=(u[:,1]**8).mean(0)
    J=J**(1./8)
    J=1./2*(J-target)**2
    return J

CASE = 'vanderpol'

#open files for output
blackboxfile=open('blackbox.dat','w')
redgradfile=open('piggyback.dat','w')
adjupdatefile=open('adj_update.dat','w')
adjnextfile=open('adj_next.dat','w')




if CASE == 'vanderpol':
#    mus = linspace(0.2, 2.0, 10)
    mus = linspace(0.2,1.0,2)
    # x0 = random.rand(2)
    x0 = array([0.5, 0.5])
    dt, T = 0.01, 100
    tmp=int(T / dt)
    t = 30 + dt * arange(tmp)

    tfix=t.copy()

    u_adj=array([0.0, 0.0])
    dt_adj=0.0
    

    solver = lssSolver(vanderpol, x0, mus[0], t, dt, u_adj,dt_adj)
    u, t = [solver.u.copy()], [solver.t.copy()]


    for mu in mus[1:]:
        print('mu = ', mu)
        
        for iNewton in range(10):

            #if iNewton==2:
            #  outputVector2d(solver.u,solver.u.shape,'u'+str(iNewton)+'.dat')
        
            ubase = array(base(solver.u))
            dtbase = array(base(solver.dt))
            mubase = array(base(mu))
            

            #compute primal update
            solver = lssSolver(vanderpol, ubase, mubase, base(tfix), \
                        dtbase, base(solver.u_adj), base(solver.dt_adj))
            G1 = solver.lss(mubase, maxIter=1,disp=True, counter=iNewton)


            #evaluate costfunction
            solver.J = costfunction(ubase,solver.target,mubase)
            print('J %.40f' %solver.J) 


            ##compute adjoint update
            #J_u = array((solver.J).diff(ubase).todense()).reshape(solver.u_adj.shape)
            #G1_u = array((G1 * solver.u_adj).sum().diff(ubase)).reshape(solver.u_adj.shape)
            #G2_u = array((G2 * solver.dt_adj).sum().diff(ubase)).reshape(solver.u_adj.shape)
            #G1_dt = array((G1 * solver.u_adj).sum().diff(dtbase)).reshape(solver.dt_adj.shape)
            #G2_dt = array((G2 * solver.dt_adj).sum().diff(dtbase)).reshape(solver.dt_adj.shape)
            #
            #u_adj_next =  J_u \
            #            + G1_u 
            #            + G2_u
            #dt_adj_next = + G1_dt \
            #            + G2_dt

            ##normnext = (ravel(u_adj_next)**2).sum() \
            ##     + (ravel(dt_adj_next)**2).sum()
            #normdiff = (ravel(u_adj_next - solver.u_adj)**2).sum() 
            #         + (ravel(dt_adj_next - solver.dt_adj)**2).sum()
            ##print('Norm adj_next %.40f' %normnext)
            #print('Norm adj_update %.40f' %normdiff)
            #adjupdatefile.write('%.40f \n' %normdiff)

    

            #compute reduced gradient
            #G1_s = array((G1 * solver.u_adj).sum().diff(mubase))
            #G2_s = array((G2 * solver.dt_adj).sum().diff(mubase))
            #solver.redgrad = G1_s # + G2_s 
            #print('reduced gradient %.40f ' %solver.redgrad)
            #redgradfile.write('%.40f  %.40f  %.40f\n'%(solver.redgrad,G1_s,G2_s))

            
            #update primal
            solver.u = G1
            #solver.dt = G2


            ##update adjoint
            #solver.u_adj =  u_adj_next
            #solver.dt_adj = dt_adj_next


            #print('Jdiffmu %.40f ' %solver.J.diff(mu))
            #blackboxfile.write('%.40f \n' %solver.J.diff(mu))

            print(using('newton'+str(iNewton)))
        
        
        u.append(base(solver.u).copy())
        t.append(base(solver.tfix).copy())


    outputVector2d(solver.u,solver.u.shape,'u.dat')
    outputVector1d(solver.tfix,solver.tfix.shape, 'tfix.dat')

    u, t = array(u), array(t)
   
#    figure(figsize=(5,10))
#    contourf(mus[:,newaxis] + t * 0, t, u[:,:,0], 501)
#    ylim([base(t).min(1).max(), base(t).max(1).min()])
#    xlabel(r'$\mu$')
#    ylabel(r'$t$')
#    title(r'$x$')
#    colorbar()
#    show(block=True)

elif CASE == 'lorenz':
    rhos = linspace(28, 33, 21)
    x0 = random.rand(3)
    dt, T = 0.01, 30
    t = 30 + dt * arange(int(T / dt))
    
    solver = lssSolver(lorenz, x0, rhos[0], t)
    u, t = [solver.u.copy()], [solver.t.copy()]
    
    for rho in rhos[1:]:
        print('rho = ', rho)
        solver.lss(rho)
        u.append(solver.u.copy())
        t.append(solver.t.copy())
    
    u, t = array(u), array(t)
    
    figure(figsize=(5,10))
    contourf(rhos[:,newaxis] + t * 0, t, u[:,:,2], 501)
    ylim([t.min(1).max(), t.max(1).min()])
    xlabel(r'$\rho$')
    ylabel(r'$t$')
    title(r'$z$')
    colorbar()
    show()


#close output files
blackboxfile.close()
redgradfile.close()
adjupdatefile.close()
adjnextfile.close()

