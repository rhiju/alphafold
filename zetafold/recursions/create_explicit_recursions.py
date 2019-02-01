#!/usr/bin/python
'''
This is a pretty awful 'compiler' script to convert recursions.py to explicit_recursions.py
'''

# a bunch of unfortunate edge cases!
not_data_objects = ['self.Z_BPq','sequence','self.params.C_eff_stack', 'motif_type.strands',
                    'match_base_pair_type_sets','motif_type.base_pair_type_sets','possible_motif_types']
not_2D_dynamic_programming_objects = ['all_ligated','ligated','self.Z_BPq','sequence','self.allow_base_pair',
                                      'self.in_forced_base_pair','motif_type.strands',
                                      'match_base_pair_type_sets','motif_type.base_pair_type_sets',
                                      'self.possible_base_pair_types','self.possible_motif_types' ]
dynamic_programming_lists = ['Z_final']
dynamic_programming_data = ['Z_seg1','Z_seg2']


def find_substring(substring, string):
    """
    From stackoverflow...
    Returns list of indices where substring begins in string

    >>> find_substring('me', "The cat says meow, meow")
    [13, 19]
    """
    indices = []
    index = -1  # Begin at -1 so index + 1 is 0
    while True:
        # Find next index of substring, by starting search from index + 1
        index = string.find(substring, index + 1)
        if index == -1:
            break  # All occurrences have been found
        indices.append(index)
    return indices

lines_new = []

lines_backtrack_info = []
lines_sum_at_end = []
lines_comment_block = []
in_comment_block = False

with open('recursions.py') as f:  lines = f.readlines()

for n,line in enumerate(lines):
    line_new = ''

    # add blocks of contrib lines that may be accumulating.
    if len( line ) > 1 and line[0] != ' ' or n == len(lines)-1:
        if len( lines_sum_at_end ) and len( lines_backtrack_info ) > 0:
            if len(lines_comment_block) > 0:
                lines_new += lines_comment_block
                lines_new += ' '*4 + "'''\n"
            lines_new.append( ' '*4 + 'contribs = [] # AUTOGENERATED SUM_AT_END BLOCK\n\n' )
            if len(lines_comment_block) == 0: lines_new.append( lines_sum_at_end[0] )
            lines_new += lines_sum_at_end[1:]
            lines_new.append( ' '*4 + Z +' = sum( contribs )\n' )
            lines_new += '\n'
            lines_sum_at_end    = []
            lines_comment_block = []

        if len( lines_backtrack_info ) > 0:
            lines_new.append('    if self.options.calc_backtrack_info: # AUTOGENERATED CONTRIBS BLOCK\n')
            lines_new += lines_backtrack_info
            lines_backtrack_info = []
            lines_new += '\n'

    if line.count( '.Q') :
        # if explicitly defining Q already, special case!!!
        line_new = line.replace( '[i][j].Q', '.Q[i][j]' )

        assign_pos = line_new.find('+= ')
        Z = line_new[:assign_pos].split()[-1]  # needed to know where to put sum(contribs) at end of code block
        line_sum_at_end = ''
        line_sum_at_end += line_new[:line_new.index(Z)]
        line_sum_at_end += 'contribs.append( '
        line_sum_at_end += line_new[assign_pos+3:-1]
        line_sum_at_end += ')\n'
        print line_sum_at_end,
        lines_sum_at_end.append( line_sum_at_end )
        continue

    if line.count( "'''" ): in_comment_block = not in_comment_block

    # most important thing -- need to look for get/set of Z_BP[i][j] (DynamicProgrammingMatrix)
    in_bracket = False
    in_second_bracket = False
    just_finished_first_bracket = False
    all_args = []
    args = []
    words = []
    word = ''
    bracket_word = ''
    at_beginning = True
    num_indent = 0
    first_char = ''
    for char in line:
        if (char == ' ' or char == '\n') and not in_bracket:
            if at_beginning: num_indent += 1
            if word in dynamic_programming_data:
                line_new += '.Q'
            line_new += char
            if len( word ) > 0:
                words.append( word )
                word = ''
            continue
        else:
            if at_beginning: first_char = char
            at_beginning = False
        if in_bracket:
            bracket_word += char
            arg += char
        if char == '[':
            if not (word in not_2D_dynamic_programming_objects+not_data_objects ) and not just_finished_first_bracket: line_new += '.Q'
            bracket_word += char
            arg = ''
            in_bracket = True
            if just_finished_first_bracket:
                in_second_bracket = True
            else:
                args = []
                if len( word ) > 0:
                    words.append( word )
                    word = ''
        elif char == ']':
            if not words[-1].replace('(','') in not_data_objects:
                if len(arg[:-1]) == 1:
                    line_new += '['+arg[:-1]+'%N]'
                else:
                    line_new += '[('+arg[:-1]+')%N]'
            else:
                line_new += bracket_word
            args.append( arg[:-1] )
            if in_second_bracket:
                assert( len( args ) == 2 )
                if not words[-1].replace('(','') in not_data_objects:
                    all_args.append( (len(line_new),words[-1],args[0],args[1]) )
                args = []
            else:
                just_finished_first_bracket = True
            in_bracket = False
            in_second_bracket = False
            bracket_word = ''
        else:
            if not in_bracket: line_new += char
            word += char
            just_finished_first_bracket = False

    if (line_new.count( 'def' ) or num_indent < 4) and len(line_new)!=1:
        lines_new.append( line_new )

    # is this an assignment? then need to create contribution lines
    assign_pos = line_new.find('+= ')
    if ( assign_pos < 0 ): assign_pos = line_new.find(' = ' )
    is_assignment_line =  assign_pos >= 0 and line_new.count('.Q') > 0

    if first_char != '#' and line_new.count( 'def' ) == 0 and not is_assignment_line and \
       not in_comment_block and not line.count( "'''" ) and first_char != '' and num_indent >= 4:
        lines_backtrack_info.append( ' '*4 + line_new )

    if line_new.count( 'def' ) == 0 and not is_assignment_line and \
       ( num_indent >= 4 or first_char == '' ) :
        if in_comment_block:
            lines_comment_block.append( line_new )
        else:
            lines_sum_at_end.append( line_new )

    if line == line_new: continue

    if assign_pos > -1:
        Qpos = find_substring( '.Q', line_new )
        if len( Qpos ) > 0 and Qpos[0] < assign_pos:
            assert( len( Qpos ) > 1 )

            Z = line_new[:assign_pos].split()[-1]  # needed to know where to put sum(contribs) at end of code block
            line_sum_at_end = ''
            line_sum_at_end += line_new[:line_new.index(Z)]
            line_sum_at_end += 'contribs.append( '
            line_sum_at_end += line_new[assign_pos+3:-1]
            line_sum_at_end += ' )\n'
            #print line_sum_at_end,
            lines_sum_at_end.append( line_sum_at_end)


            line_backtrack_info = ' '*num_indent
            line_backtrack_info += ' '*4
            line_backtrack_info += 'if %s > 0:\n' % line_new[assign_pos+3:-1]
            line_backtrack_info += ' '*8
            line_backtrack_info += line_new[:Qpos[0]] +  '.backtrack_info'  # extra indent
            line_backtrack_info += line_new[Qpos[0]+2 : assign_pos+3]
            line_backtrack_info +=' [ ('
            line_backtrack_info += line_new[assign_pos+3:-1] + ', ['
            for (n,info) in enumerate(all_args):
                if info[ 0 ] <= assign_pos: continue
                line_backtrack_info += '(%s,' % info[1]
                if len(info[2])> 1:  line_backtrack_info += '(%s)%%N' % info[2]
                else: line_backtrack_info += '%s%%N' % info[2]
                line_backtrack_info+=','
                if len(info[3])>1:   line_backtrack_info += '(%s)%%N' % info[3]
                else: line_backtrack_info += '%s%%N' % info[3]
                line_backtrack_info+=')'
                if n < len( all_args )-1: line_backtrack_info += ', '
            line_backtrack_info += '] ) ]\n'
            lines_backtrack_info.append( line_backtrack_info )


with open('explicit_recursions.py','w') as f:
    f.writelines( lines_new )

