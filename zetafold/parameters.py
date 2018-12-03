from __future__ import print_function
import math
from .base_pair_types import BasePairType, setup_base_pair_type, get_base_pair_types_for_tag, get_base_pair_type_for_tag
from .util.constants import KT_IN_KCAL
import os.path

class AlphaFoldParams:
    '''
    Parameters that define the statistical mechanical model for RNA folding
    '''
    def __init__( self ):
        self.C_std  = 1.0      # 1 M. drops out in end (up to overall scale factor).
        self.allow_strained_3WJ = False

    def get_variables( self ):
        if self.C_init == 0.0 and self.name == 'empty': print('WARNING! C_init not defined, and params appear empty. Look at get_minimal_params() or get_latest_params() for examples')
        return ( self.C_init, self.l, self.l_BP, self.K_coax, self.l_coax, self.C_std, self.min_loop_length, self.allow_strained_3WJ )

    def check_C_eff_stack( self ): _check_C_eff_stack( self )

def get_params( params = None, suppress_all_output = False ):
    params_object = None
    if isinstance(params,AlphaFoldParams): return params
    elif params == None or params =='': params_object = get_latest_params()
    elif params == 'minimal':         params_object = get_params_from_file( 'minimal' )
    elif params == 'v0.1':  params_object = get_params_from_file( 'zetafold_v0.1' )
    elif params == 'v0.15': params_object = get_params_v0_15( AlphaFoldParams() )
    elif params == 'v0.16': params_object = get_params_v0_16( AlphaFoldParams() )
    elif params == 'v0.17': params_object = get_params_v0_17( AlphaFoldParams() )
    elif params == 'v0.171': params_object = get_params_from_file( 'zetafold_v0.171' )
    else: print('unrecognized params requested: ', params)
    if not suppress_all_output: print('Parameters: ', params_object.name, ' version', params_object.version)
    return params_object

def get_latest_params():
    # TODO check all params files and pick latest version
    return get_params_from_file( 'zetafold_v0.171' )

def update_C_eff_stack( params, val = None ):
    if not hasattr( params, 'C_eff_stack' ): params.C_eff_stack = {}
    for bpt1 in params.base_pair_types:
        if not params.C_eff_stack.has_key( bpt1 ):  params.C_eff_stack[ bpt1 ] = {}
        for bpt2 in params.base_pair_types:
            params.C_eff_stack[ bpt1 ][ bpt2 ] = val

def _check_C_eff_stack( params ):
    for bpt1 in params.base_pair_types:
        for bpt2 in params.base_pair_types:
            if ( params.C_eff_stack[ bpt1 ][ bpt2 ] != params.C_eff_stack[ bpt2.flipped ][ bpt1.flipped ] ):
                print("PROBLEM with C_eff_stacked pair!!!", bpt1.nt1, bpt1.nt2, " to ", bpt2.nt1, bpt2.nt2, params.C_eff_stack[ bpt1 ][ bpt2 ],
                    ' does not match ' , \
                    bpt2.flipped.nt1, bpt2.flipped.nt2, " to ", bpt1.flipped.nt1, bpt1.flipped.nt2, params.C_eff_stack[ bpt2.flipped ][ bpt1.flipped ] )
            assert( params.C_eff_stack[ bpt1 ][ bpt2 ] == params.C_eff_stack[ bpt2.flipped ][ bpt1.flipped ] )

def setup_base_pair_type_by_tag( params, Kd_tag, val ):
    tag = Kd_tag[3:]
    if get_base_pair_type_for_tag( params, tag ) != None: return
    if tag == 'matchlowercase':
        setup_base_pair_type( params, '*', '*', val, match_lowercase = True )
    else:
        setup_base_pair_type( params, tag[0], tag[1], val, match_lowercase = False )

def set_parameter( params, tag, val ):
    if tag == 'name': params.name = val
    elif tag == 'version': params.version = val
    elif tag == 'min_loop_length':    params.min_loop_length = int( val )
    elif tag == 'allow_strained_3WJ': params.allow_strained_3WJ = (val == 'True')
    elif len( tag )>=2 and tag[:2] == 'Kd':
        setup_base_pair_type_by_tag( params, tag, float(val) )
        update_C_eff_stack( params )
    elif len( tag )>=11 and tag[:11] == 'C_eff_stack':
        if tag == 'C_eff_stacked_pair':
            for bpt1 in params.base_pair_types:
                for bpt2 in params.base_pair_types:
                    params.C_eff_stack[bpt1][bpt2] = float(val)
        else:
            assert( len(tag) > 11 )
            tags = tag[12:].split('_')
            assert( len( tags ) == 2 )
            bpts1 = get_base_pair_types_for_tag( params, tags[0] )
            bpts2 = get_base_pair_types_for_tag( params, tags[1] )
            for bpt1 in bpts1:
                for bpt2 in bpts2:
                    params.C_eff_stack[ bpt1 ][ bpt2 ] = float(val)
                    params.C_eff_stack[ bpt2.flipped ][ bpt1.flipped ] = float(val)
    else:
        setattr( params, tag, float( val ) )

def read_params_fields( params_file ):
    assert( os.path.isfile( params_file ) )
    lines = open( params_file, 'r' ).readlines()
    tags = []
    vals = []
    for line in lines:
        if len( line.replace( ' ','' ) ) == 1: continue # blank line
        elif line[0] == '#': continue # comment line
        else:
            cols = line.split()
            tags.append( cols[0] )
            vals.append( cols[1] )
            if len( cols ) > 2: assert( cols[2][0] == '#' ) # better be a comment
    return zip( tags, vals )

def get_params_from_file( params_file_tag ):
    params = AlphaFoldParams()
    params_file = os.path.dirname( os.path.abspath(__file__) ) + '/parameters/'+params_file_tag +'.params'
    params_fields = read_params_fields( params_file );
    for param_tag,param_val in params_fields:  set_parameter( params, param_tag, param_val )
    return params

#######################################
def get_params_v0_17( params ):
    # Starting to make use of train_zetafold.py on tRNA and P4-P6.
    params.name     = 'zetafold'
    params.version  = '0.17'

    params.min_loop_length = 3

    # Seven parameter model
    dG_init = +4.09 # Turner 1999, kcal/mol
    Kd_CG = 1.0 * math.exp( dG_init/ KT_IN_KCAL) # 762 M
    Kd_AU = 10.0**5.0 # 100000 M
    Kd_GU = 10.0**5.0 # 100000 M

    dG_terminal_AU = 0.5 # Turner 1999, kcal/mol -- NUPACK

    dG_CG_CG = -3.30 # Turner 1999 5'-CC-3'/5'-GG-3', kcal/mol
    params.C_eff_stacked_pair = 10**5.425 # about 10^5

    # From nupack rna1999.params
    #>Multiloop terms: ALPHA_1, ALPHA_2, ALPHA_3
    #>ML penalty = ALPHA_1 + s * ALPHA_2 + u *ALPHA_3
    #>s = # stems adjacent to ML, u = unpaired bases in ML
    # 340   40    0
    #>AT_PENALTY:
    #>Penalty for non GC pairs that terminate a helix
    #  50
    dG_bulge = 3.4 # bulge cost is roughly 3-4 kcal/mol
    dG_multiloop_stems = 0.40 # in kcal/mol
    dG_multiloop_unpaired = 0.0 #0.40 # in kcal/mol -- ZERO in NUPACK -- fudging here.
    # oops, should have been:
    #params.C_init = 1.0 * math.exp( -(dG_bulge + dG_CG_CG)/ KT_IN_KCAL )
    params.C_init = 10**1.0 #

    params.l = math.exp( dG_multiloop_unpaired / KT_IN_KCAL )
    params.l_BP = math.exp( dG_multiloop_stems/KT_IN_KCAL ) / params.l

    setup_base_pair_type(params, 'C', 'G', Kd_CG )
    setup_base_pair_type(params, 'A', 'U', Kd_AU )
    setup_base_pair_type(params, 'G', 'U', Kd_GU )

    # turn off coax
    params.K_coax = 5.0
    params.l_coax = 1.0

    update_C_eff_stack( params, params.C_eff_stacked_pair )
    bpts_WC = params.base_pair_types[0:4]
    bpt_GU  = params.base_pair_types[4]
    bpt_UG  = params.base_pair_types[5]
    for bpt in bpts_WC:
        params.C_eff_stack[bpt   ][bpt_GU] = 10.0**4.8
        params.C_eff_stack[bpt_UG][bpt   ] = 10.0**4.8
        params.C_eff_stack[bpt   ][bpt_UG] = 10.0**3.0
        params.C_eff_stack[bpt_GU][bpt   ] = 10.0**3.0
    params.C_eff_stack[bpt_GU][bpt_GU] = 10.0**4.0
    params.C_eff_stack[bpt_UG][bpt_UG] = 10.0**4.0 # must be same as above!
    params.C_eff_stack[bpt_UG][bpt_GU] = 10.0**4.0
    params.C_eff_stack[bpt_GU][bpt_UG] = 10.0**4.0

    return params

def get_params_v0_16( params ):
    # Starting to make use of train_zetafold.py on tRNA and P4-P6.
    params.name     = 'zetafold'
    params.version  = '0.16'

    params.min_loop_length = 3

    # Seven parameter model
    dG_init = +4.09 # Turner 1999, kcal/mol
    Kd_CG = 1.0 * math.exp( dG_init/ KT_IN_KCAL) # 762 M
    Kd_AU = 10.0**5.0 # 100000 M
    Kd_GU = 10.0**5.0 # 100000 M

    dG_terminal_AU = 0.5 # Turner 1999, kcal/mol -- NUPACK

    dG_CG_CG = -3.30 # Turner 1999 5'-CC-3'/5'-GG-3', kcal/mol
    params.C_eff_stacked_pair = 10**5.425 # about 10^5

    # From nupack rna1999.params
    #>Multiloop terms: ALPHA_1, ALPHA_2, ALPHA_3
    #>ML penalty = ALPHA_1 + s * ALPHA_2 + u *ALPHA_3
    #>s = # stems adjacent to ML, u = unpaired bases in ML
    # 340   40    0
    #>AT_PENALTY:
    #>Penalty for non GC pairs that terminate a helix
    #  50
    dG_bulge = 3.4 # bulge cost is roughly 3-4 kcal/mol
    dG_multiloop_stems = 0.40 # in kcal/mol
    dG_multiloop_unpaired = 0.0 #0.40 # in kcal/mol -- ZERO in NUPACK -- fudging here.
    # oops, should have been:
    #params.C_init = 1.0 * math.exp( -(dG_bulge + dG_CG_CG)/ KT_IN_KCAL )
    params.C_init = 10** 1.55034499 # radically different

    params.l = math.exp( dG_multiloop_unpaired / KT_IN_KCAL )
    params.l_BP = math.exp( dG_multiloop_stems/KT_IN_KCAL ) / params.l

    setup_base_pair_type(params, 'C', 'G', Kd_CG )
    setup_base_pair_type(params, 'A', 'U', Kd_AU )
    setup_base_pair_type(params, 'G', 'U', Kd_GU )

    # turn off coax!?
    params.K_coax = 0.0
    params.l_coax = 1.0

    update_C_eff_stack( params, params.C_eff_stacked_pair )

    return params


# Parameters developed before extensive optimization
def get_params_v0_15( params ):
    # Starting to make use of train_zetafold.py on P4-P6.
    params.name     = 'zetafold'
    params.version  = '0.15'

    params.min_loop_length = 3

    # Seven parameter model
    dG_init = +4.09 # Turner 1999, kcal/mol
    Kd_CG = 1.0 * math.exp( dG_init/ KT_IN_KCAL)
    dG_terminal_AU = 0.5 # Turner 1999, kcal/mol -- NUPACK
    #Kd_AU = 10.0**5.40731537 # 255000
    Kd_GU = 10.0**3.5863221 # 4000
    Kd_AU = 10.0**5.40731537 # 255000
    Kd_GU = 10.0**3.5863221 # 4000

    dG_CG_CG = -3.30 # Turner 1999 5'-CC-3'/5'-GG-3', kcal/mol
    params.C_eff_stacked_pair = math.exp( -dG_CG_CG / KT_IN_KCAL ) * Kd_CG # about 10^5

    # From nupack rna1999.params
    #>Multiloop terms: ALPHA_1, ALPHA_2, ALPHA_3
    #>ML penalty = ALPHA_1 + s * ALPHA_2 + u *ALPHA_3
    #>s = # stems adjacent to ML, u = unpaired bases in ML
    # 340   40    0
    #>AT_PENALTY:
    #>Penalty for non GC pairs that terminate a helix
    #  50
    dG_bulge = 3.4 # bulge cost is roughly 3-4 kcal/mol
    dG_multiloop_stems = 0.40 # in kcal/mol
    dG_multiloop_unpaired = 0.0 #0.40 # in kcal/mol -- ZERO in NUPACK -- fudging here.
    #params.C_init = 1.0 * math.exp( -dG_bulge / KT_IN_KCAL )
    params.C_init = 10** 1.55034499 # radically different

    params.l = math.exp( dG_multiloop_unpaired / KT_IN_KCAL )
    params.l_BP = math.exp( dG_multiloop_stems/KT_IN_KCAL ) / params.l

    setup_base_pair_type(params, 'C', 'G', Kd_CG )
    setup_base_pair_type(params, 'A', 'U', Kd_AU )
    setup_base_pair_type(params, 'G', 'U', Kd_GU )

    #Kd_GA = Kd_AU*100000  # fudge factor to make GA weaker.
    #base_pair_types.append( BasePairType( 'G', 'A', Kd_GA ) ) # totally made up
    #Kd_AA = Kd_AU * 40 # fudge factor to make GU weaker.
    #base_pair_types.append( BasePairType( 'A', 'A', Kd_AA ) ) # totally made up

    # turn off coax!?
    params.K_coax = 0.0
    params.l_coax = 1.0

    update_C_eff_stack( params, params.C_eff_stacked_pair )

    return params