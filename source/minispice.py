"""
minispice.py - A tiny transient circuit simulator (modified nodal analysis,
backward-Euler companion models, Newton-Raphson for diodes).

It is deliberately small but general: any network of R, C, L, independent
voltage/current sources (arbitrary functions of time), time-controlled
switches and diodes (with optional reverse breakdown = zener) can be
simulated. Used by the Diode circuit lab.

    ckt = Circuit()
    ckt.V("Vs", "in", "0", lambda t: 10 * sin(2*pi*50*t))
    ckt.R("R1", "in", "out", 1e3)
    ckt.D("D1", "out", "0", DiodeModel.silicon())
    res = ckt.tran(0.04, 2000)
    res.v("out"), res.i("D1"), res.t
"""
import math
import numpy as np

VT = 0.025852  # thermal voltage at 300 K


class DiodeModel:
    def __init__(self, Is=2.5e-9, n=1.9, bv=None, ibv=1e-3, nbv=1.0, rs=0.0, name=""):
        self.Is, self.n, self.bv, self.ibv, self.nbv, self.rs, self.name = Is, n, bv, ibv, nbv, rs, name

    @staticmethod
    def silicon():            # 1N4148 / 1N4001-like
        return DiodeModel(Is=2.5e-9, n=1.9, name="Si")

    @staticmethod
    def schottky():
        return DiodeModel(Is=1e-6, n=1.05, name="Schottky")

    @staticmethod
    def germanium():
        return DiodeModel(Is=2e-6, n=1.3, name="Ge")

    @staticmethod
    def led(vf=2.0, i_ref=0.02):
        n = 2.0
        Is = i_ref / math.exp(vf / (n * VT))
        return DiodeModel(Is=Is, n=n, name="LED")

    @staticmethod
    def zener(vz):
        return DiodeModel(Is=2.5e-9, n=1.9, bv=vz, ibv=1e-3, nbv=1.0 + 0.2 * max(0, 6 - vz), name="Zener")

    def iv(self, v):
        """Current and conductance at junction voltage v (a->k)."""
        nvt = self.n * VT
        vcrit = nvt * math.log(20.0 / self.Is)       # beyond ~20 A continue linearly
        if v > vcrit:
            e = math.exp(vcrit / nvt)
            i0 = self.Is * (e - 1)
            g = self.Is * e / nvt
            i, gd = i0 + g * (v - vcrit), g
        elif v > -30 * nvt:
            e = math.exp(v / nvt)
            i, gd = self.Is * (e - 1), self.Is * e / nvt
        else:
            i, gd = -self.Is, 0.0
        if self.bv is not None:
            nb = self.nbv * VT
            x = (-v - self.bv) / nb
            xcrit = math.log(20.0 / self.ibv)
            if x > xcrit:
                e = math.exp(xcrit)
                ib = self.ibv * (e + e * (x - xcrit))
                gb = self.ibv * e / nb
            elif x > -40:
                e = math.exp(x)
                ib, gb = self.ibv * e, self.ibv * e / nb
            else:
                ib, gb = 0.0, 0.0
            i -= ib
            gd += gb
        return i, gd + 1e-12


def _pnjlim(vnew, vold, vt, vcrit):
    """SPICE junction-voltage limiting (keeps Newton from overshooting the exponential)."""
    if vnew > vcrit and abs(vnew - vold) > 2 * vt:
        if vold > 0:
            arg = 1 + (vnew - vold) / vt
            vnew = vold + vt * math.log(arg) if arg > 0 else vcrit
        else:
            vnew = vt * math.log(vnew / vt)
    return vnew


def _limit(model, vnew, vold):
    nvt = model.n * VT
    vcrit = nvt * math.log(nvt / (math.sqrt(2) * model.Is))
    vnew = _pnjlim(vnew, vold, nvt, vcrit)
    if model.bv is not None:
        nb = model.nbv * VT
        ucrit = nb * math.log(nb / (math.sqrt(2) * model.ibv * math.exp(-40)))
        # breakdown in terms of u = -v - bv (+ a margin so the exp is near 1e-17 A)
        off = 40 * nb
        un, uo = -vnew - model.bv + off, -vold - model.bv + off
        un = _pnjlim(un, uo, nb, ucrit)
        vnew = -(un - off) - model.bv
    return vnew


class Result:
    def __init__(self, t, nodes, volts, currents):
        self.t = t
        self._nodes = nodes
        self._v = volts
        self._i = currents

    def v(self, node):
        if node in ("0", "gnd"):
            return np.zeros_like(self.t)
        return self._v[:, self._nodes[node]]

    def i(self, name):
        return self._i[name]


class Circuit:
    def __init__(self):
        self.nodes = {}
        self.res, self.caps, self.inds, self.vs, self.isrc, self.diodes, self.sws = [], [], [], [], [], [], []

    def _n(self, name):
        if name in ("0", "gnd"):
            return -1
        if name not in self.nodes:
            self.nodes[name] = len(self.nodes)
        return self.nodes[name]

    # ---- elements --------------------------------------------------------
    def R(self, name, a, b, r):
        self.res.append((name, self._n(a), self._n(b), max(float(r), 1e-6)))

    def C(self, name, a, b, c, ic=0.0):
        self.caps.append([name, self._n(a), self._n(b), float(c), float(ic)])

    def L(self, name, a, b, l, ic=0.0):
        self.inds.append([name, self._n(a), self._n(b), float(l), float(ic)])

    def V(self, name, a, b, fn):
        self.vs.append((name, self._n(a), self._n(b), fn))

    def I(self, name, a, b, fn):
        """Current fn(t) flowing from a, through the source, into b."""
        self.isrc.append((name, self._n(a), self._n(b), fn))

    def D(self, name, a, k, model):
        self.diodes.append((name, self._n(a), self._n(k), model))

    def SW(self, name, a, b, fn_on, ron=0.05, roff=1e7):
        self.sws.append((name, self._n(a), self._n(b), fn_on, ron, roff))

    # ---- analysis --------------------------------------------------------
    def tran(self, tstop, steps=2000, max_iter=150):
        n = len(self.nodes)
        m = len(self.vs)
        N = n + m
        dt = tstop / steps
        t = np.linspace(0, tstop, steps + 1)

        def stamp_g(A, a, b, g):
            if a >= 0:
                A[a, a] += g
            if b >= 0:
                A[b, b] += g
            if a >= 0 and b >= 0:
                A[a, b] -= g
                A[b, a] -= g

        def stamp_i(z, a, b, i):   # current i flowing a -> b through element (leaves a)
            if a >= 0:
                z[a] -= i
            if b >= 0:
                z[b] += i

        G0 = np.zeros((N, N))
        for _, a, b, r in self.res:
            stamp_g(G0, a, b, 1.0 / r)
        for _, a, b, c, _ in self.caps:
            stamp_g(G0, a, b, c / dt)
        for _, a, b, l, _ in self.inds:
            stamp_g(G0, a, b, dt / l)
        for k, (_, a, b, _) in enumerate(self.vs):
            row = n + k
            if a >= 0:
                G0[a, row] += 1
                G0[row, a] += 1
            if b >= 0:
                G0[b, row] -= 1
                G0[row, b] -= 1
        # tiny conductance to ground on every node (keeps floating nodes solvable)
        for i in range(n):
            G0[i, i] += 1e-9

        x = np.zeros(N)
        vc = [c[4] for c in self.caps]
        il = [l[4] for l in self.inds]
        vd_prev = [0.0] * len(self.diodes)
        V = np.zeros((steps + 1, n))
        cur = {name: np.zeros(steps + 1) for name, *_ in self.diodes}
        for name, *_ in self.vs:
            cur[name] = np.zeros(steps + 1)
        for name, *_ in self.inds:
            cur[name] = np.zeros(steps + 1)
        for name, *_ in self.caps:
            cur[name] = np.zeros(steps + 1)
        for name, *_ in self.res:
            cur[name] = np.zeros(steps + 1)
        for name, *_ in self.sws:
            cur[name] = np.zeros(steps + 1)

        def vnode(xv, a):
            return xv[a] if a >= 0 else 0.0

        # initial point: caps as voltage sources are approximated by solving
        # the first step with the given initial conditions
        for step in range(steps + 1):
            tt = t[step]
            base_z = np.zeros(N)
            for k, (_, a, b, c, _) in enumerate(self.caps):
                stamp_i(base_z, a, b, -c / dt * vc[k])      # BE companion: i = C/dt (v - vprev)
            for k, (_, a, b, l, _) in enumerate(self.inds):
                stamp_i(base_z, a, b, il[k])
            for _, a, b, fn in self.isrc:
                stamp_i(base_z, a, b, fn(tt))
            for k, (_, a, b, fn) in enumerate(self.vs):
                base_z[n + k] = fn(tt)
            Gs = G0.copy()
            for _, a, b, fn_on, ron, roff in self.sws:
                stamp_g(Gs, a, b, 1.0 / (ron if fn_on(tt) else roff))
            vd = list(vd_prev)
            for it in range(max_iter):
                A = Gs.copy()
                z = base_z.copy()
                for k, (_, a, kk, model) in enumerate(self.diodes):
                    i0, gd = model.iv(vd[k])
                    stamp_g(A, a, kk, gd)
                    stamp_i(z, a, kk, i0 - gd * vd[k])
                try:
                    xn = np.linalg.solve(A, z)
                except np.linalg.LinAlgError:
                    xn = np.linalg.lstsq(A, z, rcond=None)[0]
                conv = True
                for k, (_, a, kk, model) in enumerate(self.diodes):
                    vnew = vnode(xn, a) - vnode(xn, kk)
                    if abs(vnew - vd[k]) > 1e-6 * max(1.0, abs(vnew)):
                        conv = False
                    vd[k] = _limit(model, vnew, vd[k])
                x = xn
                if conv and it > 0:
                    break
            vd_prev = vd
            V[step, :] = x[:n]
            for k, (name, a, b, c, _) in enumerate(self.caps):
                v = vnode(x, a) - vnode(x, b)
                cur[name][step] = c / dt * (v - vc[k]) if step > 0 else 0.0
                vc[k] = v
            for k, (name, a, b, l, _) in enumerate(self.inds):
                v = vnode(x, a) - vnode(x, b)
                il[k] = il[k] + dt / l * v
                cur[name][step] = il[k]
            for k, (name, a, kk, model) in enumerate(self.diodes):
                cur[name][step] = model.iv(vnode(x, a) - vnode(x, kk))[0]
            for k, (name, *_r) in enumerate(self.vs):
                cur[name][step] = -x[n + k]      # current delivered out of the + terminal
            for name, a, b, r in self.res:
                cur[name][step] = (vnode(x, a) - vnode(x, b)) / r
            for name, a, b, fn_on, ron, roff in self.sws:
                cur[name][step] = (vnode(x, a) - vnode(x, b)) / (ron if fn_on(tt) else roff)
        return Result(t, dict(self.nodes), V, cur)
