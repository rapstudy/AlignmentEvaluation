"""
Created on Oct 10, 2017

@author: joro
"""


import sys
import os
import glob
import numpy as np


EXTENSION_RECO = '.final.txt'
# Mauch
# EXTENSION_RECO = '_align.txt'
# Jamendo
# EXTENSION_RECO = '_align.csv'

# EXTENSION_RECO ='.mp3_align.txt'

projDir = os.path.join(os.path.dirname(__file__), os.path.pardir)

if projDir not in sys.path:
    sys.path.append(projDir)

from align_eval.Utilz import load_labeled_intervals, load_delimited_variants,\
    remove_dot_tokens
from align_eval.Utilz import getMeanAndStDevError
from align_eval.Utilz import writeCsv
from parse.TextGrid_Parsing import tierAliases
from align_eval.ErrorEvaluator import _eval_alignment_error
from align_eval.PercentageCorrectEvaluator import _eval_percentage_correct
from align_eval.ErrorEvaluator import _eval_percentage_tolerance


def eval_all_metrics_lab(refs_URI, detected_URI, tolerance=0.3):
    """
    run all eval metrics on one file
    """
    ref_intervals, ref_labels, has_ends = load_labeled_intervals(refs_URI)
    
    detected_intervals, use_end_ts = load_detected_intervals(detected_URI)
    
    # metric 1: alignment error
    alignmentErrors = _eval_alignment_error(ref_intervals, detected_intervals, ref_labels, use_end_ts)
    
    mean, stDev, median = getMeanAndStDevError(alignmentErrors)

    # metric 2: percentage correct
    if has_ends:
        initialTimeOffset_refs = ref_intervals[0][0]
        finalts_refs = ref_intervals[-1][1]
        durationCorrect, totalLength  = _eval_percentage_correct(reference_token_list=ref_intervals,
                                                                 detected_token_List=detected_intervals,
                                                                 final_ts_anno=finalts_refs,
                                                                 initial_time_offset_refs=initialTimeOffset_refs,
                                                                 reference_labels=ref_labels)
        percentage_correct = durationCorrect / totalLength
    else:
        percentage_correct = None

    # metric 3: percentage tolerance
    percentage_tolerance = _eval_percentage_tolerance(ref_intervals=ref_intervals,
                                                      detected_intervals=detected_intervals,
                                                      reference_labels=ref_labels,
                                                      tolerance=tolerance)
    return mean, median, percentage_correct, percentage_tolerance


def load_detected_intervals(detected_URI):
    detected_starts, detected_ends, labels = load_delimited_variants(detected_URI)
    
    use_end_ts = False #  do not use end_ts even if they have been detected
    if detected_ends is None:
        detected_ends = detected_starts # to keep format
    
    detected_starts, detected_ends, labels = remove_dot_tokens(detected_starts, detected_ends,  labels)
    
    detected_intervals = np.array([detected_starts, detected_ends]).T
    return detected_intervals, use_end_ts

def main_eval_one_file(argv):
    if len(argv) != 4:
        sys.exit('usage: {} <path to reference word boundaries> <path to detected word boundaries>  <tolerance>'.format(sys.argv[0]))
    refs_URI = argv[1]
    detected_URI = argv[2]
    tolerance = float(argv[3])
    print('evaluating on {}'.format(refs_URI))
    meanError, median_error, percentage_correct, percentage_tolerance = eval_all_metrics_lab(refs_URI, detected_URI, tolerance )
    
    print ( "Metric 1: average error {}, median error {}".format(meanError, median_error) )
    if percentage_correct:
        print ( "Metric 2: percentage correct segments {}".format(percentage_correct) )
    print ( "Metric 3: percentage estimates {0:0.2f} with tolerance {1}".format(percentage_tolerance, tolerance) )

    return meanError, median_error, percentage_correct, percentage_tolerance


def main_eval_all_files(argv):
    if len(argv) != 5:
        sys.exit('usage: {} <path dir with to reference word boundaries> <path to dir with detected word boundaries> <tolerance (s)> <path_output>'.format(sys.argv[0]))
    refs_dir_URI = argv[1]
    detected_dir_URI = argv[2]
    a = os.path.join(detected_dir_URI, "*{}".format(EXTENSION_RECO))
    lab_files = glob.glob(a)
    print('Found {} alignment files'.format(len(lab_files)))
    
    results = [['Track', 'Average absolute error', 'Median absolute error', 'Percentage of correct segments', 'Percentage of correct onsets with tolerance']]
    for lab_file in lab_files:
        base_name = os.path.basename(lab_file)
        extension_length = len(EXTENSION_RECO)
        ref_file = os.path.join(refs_dir_URI, base_name[:-extension_length] + '.wordonset.tsv')
        mean, median, percentage_correct, percentage_tolerance = main_eval_one_file(["dummy",  ref_file, lab_file, argv[3]])
        if percentage_correct:
            perc_correct = '{:.3f}'.format(percentage_correct)
        else:
            perc_correct = 'NaN'
        results.append([base_name[:-extension_length], '{:.3f}'.format(mean),
                        '{:.3f}'.format(median),
                         perc_correct,
                        '{:.3f}'.format(percentage_tolerance)])
            
    output_URI = argv[4]
    writeCsv(os.path.join(output_URI, 'results.csv'), results)


if __name__ == '__main__':
#     main_eval_one_file(sys.argv)
    main_eval_all_files(sys.argv)