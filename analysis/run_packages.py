#!/usr/bin/python
import argparse, os
from zetafold.data.training_examples import *
from zetafold.training import *
from multiprocessing import Pool
import __builtin__

parser = argparse.ArgumentParser( description = "Test nearest neighbor model partitition function for RNA sequence" )
parser.add_argument("-params","--parameters", type=str, help='Parameter file to use [default: use latest zetafold version]')
parser.add_argument("--data", type=str, help="Data to use. Give none to get list.")
parser.add_argument("-f","--force", action='store_true', help="Overwrite prior output.")
parser.add_argument("--jobs","-j", type=int, default=4, help='Number of jobs to run in parallel')
args     = parser.parse_args()

examples = initialize_training_examples( all_training_examples, training_sets, training_set_names, args.data )

dirname = os.path.basename(args.parameters).replace( '.params', '' )
if not os.path.exists(dirname):
    print 'Creating directory: ', dirname
    os.mkdir( dirname )

def run_package( example ):
    subdirname = dirname+'/'+example.name
    if not os.path.exists( subdirname ):
        print 'Creating directory: ', subdirname
        os.mkdir( subdirname )

    if dirname == 'contrafold' or dirname == 'contrafold-nc':
        fasta = '%s/%s.fasta' % (subdirname,example.name)
        fid = open( fasta, 'w' )
        fid.write( '>%s\n' % example.name )
        fid.write( '%s\n' % example.sequence )
        fid.close()
        noncomplementaryflag = '--noncomplementary' if dirname == 'contrafold-nc' else ''
        cmdline = 'contrafold predict %s %s --parens %s/secstruct.txt --posteriors 0.00001 %s/posteriors.txt > %s/contrafold.out 2> %s/contrafold.err' % (fasta,noncomplementaryflag,subdirname,subdirname,subdirname,subdirname)
        outfile = '%s/contrafold.out' % subdirname
        if not args.force and os.path.exists( '%s/posteriors.txt' % subdirname ): return
    else:
        cmdline = 'zetafold.py -s %s -params %s --bpp --stochastic 100 --mfe --calc_gap_structure "%s" --allow_extra_base_pairs --bpp_file  %s/bpp.txt > %s/zetafold.out 2> %s/zetafold.err' % (example.sequence,args.parameters,example.structure,subdirname,subdirname,subdirname)
        outfile = '%s/zetafold.out' % subdirname
        if not args.force and os.path.exists( '%s/bpp.txt' % subdirname ): return

    print cmdline
    os.system( cmdline )
    os.system( 'cat %s' % outfile  )

pool = __builtin__
if args.jobs > 1: pool = Pool( args.jobs )

pool.map( run_package, examples )
