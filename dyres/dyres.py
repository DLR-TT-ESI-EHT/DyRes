# main file
import json
import h5py
import scipy.io as sio
import numpy as np
import pandas as pd
from functools import singledispatchmethod
import re

class DyRes:

    '''
    https://www.claytex.com/tech-blog/trajectory-file-what-is-it-dissecting-a-dymola-result-file/
    '''
    
    def __init__(self, file):
        self.file = file
        if self.file.endswith('.json'):
            self.from_json()
        if self.file.endswith('.mat'):
            self.__mat = sio.loadmat(self.file, chars_as_strings=False, appendmat=False)
            if 'DyRes' in self.__mat.keys():
                self.from_mat()
            else:
                self.from_dymola()
        if self.file.endswith('.h5'):
            self.from_hdf5()
        
        self.__mat['data_1']= self.__mat['data_1'].astype(float)
        self.__mat['data_2']= self.__mat['data_2'].astype(float)

        self.Time = self.__mat['data_2'][0].astype(float)

    @singledispatchmethod
    def __getitem__(self, key):
        raise NotImplementedError(f"Cannot index {type(key)}")

    def _baseGetRes(self, key:str):
        """base method for getting result from a str key. 
        This method is expanded by the __getitem__ method which is called conveniently by self[key]

        further explanations for how to access dymola result files: https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/technical_details.html

        Args:
            key (str): full variable path in dymola

        Returns:
            result (np.array | float): array or float of the values of the variable being accessed
        """        
        
        if key=='Time':
            return self.__mat['data_2'][0]
        else:
            idxKey = self.names.index(key)
            data = self.__mat['dataInfo'][0, idxKey]
            idxData = self.__mat['dataInfo'][1, idxKey] 
            if idxData <0:
                return -self.__mat[f'data_{data}'][-idxData-1]
            else:
                return self.__mat[f'data_{data}'][idxData-1]

    def _timeSlice(self, t):
        """Create a slice object from time values

        Args:
            t {3-tuple[float, float, int]}: (start)time, stoptime(optional), skip(optional)
                (start)time:    time at which you want the value
                stoptime:       time at which to end slice
                skip:           skip every other _ index

        Returns:
            _type_: Slice Object indicating which indices to slice
        """        

        # taken from simres can be better
        try:
            t1, t2, skip = t
        except ValueError:
            skip = None
            try:
                t1, t2 = t
            except ValueError:
                t1 = None
                t2, = t
        assert t1 is None or t2 is None or t1 <= t2, (
            "The lower time limit must be less than or equal to the upper "
            "time limit.")
        # find idx of closest point in time - may change this to use interpolated time val
        i1 = None if t1 is None else np.searchsorted(self.Time, t1, side='left')
        i2 = None if t2 is None else np.searchsorted(self.Time, t2, side='left') 
        return slice(i1, i2, skip)

    @__getitem__.register
    def _(self, key:str):
        """_summary_

        Args:
            key (str): _description_

        Returns:
            _type_: _description_
        """        
        return self._baseGetRes(key)

    @__getitem__.register
    def _(self, key:tuple):
        """Get dymola results for a given time or multiple times

        Args:
            key (tuple[k, t1, t2(optional), skip(optional)]): tuple containing the full variable path and times you want to access
                k (str):    full variable path in dymola
                t1:         time at which you want the value
                t2:         time at which to end slice
                skip:       skip every other _ index
        Returns:
            result (np.array | float): array or float of the values of the variable being accessed
        """        

        fullRes = self._baseGetRes(key[0])
        sli = self._timeSlice(key[1:])
        if sli.start == None:
            dat = np.interp(key[1], self.Time, fullRes)
        else:
            dat_t1 = np.interp(key[1], self.Time, fullRes) # keeping here in case its needed in the future
            dat_t2 = np.interp(key[2], self.Time, fullRes) # keeping here in case its needed in the future
            dat = fullRes[sli]

        return dat

    @__getitem__.register
    def _(self, key:list):
        """Give a list of str and get a array of results corresponding to the variable strings

        Args:
            key (list[str]): full variable paths in dymola of multiple variables

        Returns:
            result (np.Array[np.array | float]): list of results for the multiple variables being accessed
        """        

        dat = np.zeros((len(key), self.Time.size), dtype=float)
        for k,v in enumerate(key):
            dat[k] = self._baseGetRes(v)

        return dat

    def out_Dict(self):
        d = {
            'name': self.names,
            'data_1': self.__mat['data_1'].tolist(),
            'data_2': self.__mat['data_2'].tolist(),
            'dataInfo': self.__mat['dataInfo'][:2,:].tolist(),
            'DyRes': [1,1]
        }
        return d

    # I/O
    def from_dymola(self):
        # Name Sorter
        self.names = [''.join(self.__mat['name'].T[i]).rstrip(' \0') for i in range(self.__mat['name'].shape[1])]
        # Param Cutter
        self.__mat['data_1'] = self.__mat['data_1'][:,0]

    def to_json(self, file):
        with open(self.file, 'w', ) as out_file:
            json.dump(self.out_Dict(), out_file)
            out_file.close()

    def from_json(self):
        with open(self.file, 'r') as in_file:
            d = json.load(in_file)
            in_file.close()

            self.__mat = {
                'name' : d['name'],
                'data_1': np.array(d['data_1'] ),
                'data_2': np.array(d['data_2']),
                'dataInfo': np.array(d['dataInfo'])
            }
            self.names = self.__mat['name']

    def to_mat(self, file) -> None:
        sio.savemat(file, self.out_Dict(), do_compression=True)

    def from_mat(self):
        # Name Sorter
        #self.__mat['name'][self.__mat['name']==' ']=''
        self.names=[v.rstrip(" \0").encode('latin-1').decode('utf-8') for v in chars_to_strings(self.__mat['name'])] # 
        # Param Sorter
        self.__mat['data_1'] = self.__mat['data_1'][0]

    def to_hdf5(self, file) -> None:

        with h5py.File(file, 'a') as h5file:

            for key,val in self.out_Dict().items():
                h5file.create_dataset(
                key,
                data=val,
                compression='gzip',
                compression_opts = 9
            )

    def from_hdf5(self):
        
        with h5py.File(self.file, 'r') as hf:
            self.__mat = {
                'data_1' : np.array(hf.get('data_1')),
                'data_2' : np.array(hf.get('data_2')),
                'name' : np.array(hf.get('name'), dtype=str),
                'dataInfo' : np.array(hf.get('dataInfo')),
                'data_dyres' : np.array(hf.get('DyRes'))
            }
        self.names = list(self.__mat['name'])

    def find_variable(self, var_name):
        """
        Find all instances of parameters matching a pattern

        example: 
        to find all instances of the discretised variable of pattern j[*] use:
        res = DyRes('res.mat')
        j_matches = self.find_variable('j'') # output: ['j[1]', j[2]', 'j[3]']
        """
        pattern_str = rf"^{var_name}\[\d+\]$"
        pattern = re.compile(pattern_str)
        return [n for n in self.names if pattern.match(n)]


# DyRes class that manages more than one result file at the same time
class DyResMulti(DyRes):
    def __init__(self, files, DyResTyp=DyRes):
        self.files=files
        self.DyResTyp = DyResTyp
        self.res = []
        for i in files:
            self.res += [self.DyResTyp(i)]
        

    def __getitem__(self, key):
        return [v[key] for v in self.res]           