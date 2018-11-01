from copy import deepcopy

class DynamicProgrammingMatrix:
    '''
    Dynamic Programming Matrix that automatically does wrapping modulo N
    '''
    def __init__( self, N ):
        self.N = N
        self.DPmatrix = []
        for i in range( N ):
            self.DPmatrix.append( [] )
            for j in range( N ):
                self.DPmatrix[i].append( DynamicProgrammingData() )

    def __getitem__( self, idx ):
        return self.DPmatrix[ idx ]

    def __len__( self ): return len( self.DPmatrix )

class DynamicProgrammingData:
    '''
    Dynamic programming object, with derivs and contribution accumulation.
     Q   = value
     dQ  = derivative (later will generalize to gradient w.r.t. all parameters)
     contrib = contributions
    '''
    def __init__( self ):
        self.Q = 0.0
        self.dQ = 0.0
        self.contrib = []
        self.info = []

    def __iadd__(self, other):
        self.Q += other.Q
        self.contrib.append( [other.Q, [other.info]] )
        return self

    def __mul__(self, other):
        prod = DynamicProgrammingData()
        if type( self ) == type( other ):
            prod.Q       = self.Q * other.Q
            prod.contrib = other.contrib
        else:
            prod.Q = self.Q * other
            for contrib in self.contrib:
                prod.contrib.append( [contrib[0]*other, contrib[1] ] )
        prod.info = self.info
        return prod

    def __truediv__( self, other ):
        quot = deepcopy( self )
        quot.Q /= other
        return quot

    __rmul__ = __mul__
    __floordiv__ = __truediv__
    __div__ = __truediv__


def set_ids( D ):
    for i in range( len( D ) ):
        for j in range( len( D ) ):
            D.DPmatrix[i][j].info = [id( D ),i,j]

