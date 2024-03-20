import numpy as np
import numpy as py




class mcc128:

    def __init__(self):
        self._npts: int = 1000

    @property
    def npts(self):
        return self._npts

    @npts.setter
    def npts(self, npt: int):
        if not isinstance(npt, int):
            raise TypeError("")
        elif npt < 1:
            raise ValueError("")
        self._npts = npt

    def get_x_axis(self, nbre_point, freq_echatillonage ):
        te = np.linspace(0, (nbre_point - 1) / freq_echatillonage, nbre_point)
        return te

    def generateur(self, duree: float):
        freq = self.npts / duree
        ts = self.get_x_axis(self.npts, freq)
        return np.sin(2 * np.pi * ts), ts



