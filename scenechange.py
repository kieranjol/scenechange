#!/usr/bin/env python
'''
Remuxes video files to matrosa and inserts chapter markers at scene changes.
Scene changes are detected by using the YDIFF filter in ffmpeg/signalstats.
YDIFF plots time based difference in luminance values, so a larger value most
likely means a scene change.

Written by Kieran O'Leary.
'''
import sys
import subprocess
import argparse
import json
import ififuncs


def parse_args(args_):
    '''
    Parse command line arguments.
    '''
    parser = argparse.ArgumentParser(
        description='Remux video file to Matroska and insert chapter points at'
        'scene changes'
        ' Written by Kieran O\'Leary.'
    )
    parser.add_argument(
        '-i',
        help='full path of input directory', required=True
    )
    parser.add_argument(
        '-o', '-output',
        help='full path of output directory', required=True
    )
    parsed_args = parser.parse_args(args_)
    return parsed_args


def remux(input_file):
    '''
    Launches ffmpeg in order to remux video file to Matroska.
    '''
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-c', 'copy', '-map', '0:v', '-map', '0:a?',
        input_file + '.mkv',
    ]
    print cmd
    subprocess.call(
        cmd
    )
    return input_file + '.mkv'

def get_scene_changes(input_file):
    '''
    Creates a list of timestamps that will hopefully correspond to scene changes.
    '''
    cmd = [
        'ffprobe',
        '-f', 'lavfi',
        '-i', "movie='%s',signalstats" % input_file,
        '-show_entries',
        'frame=pkt_pts_time:frame_tags=lavfi.signalstats.YDIF',
        '-of', 'json'
    ]
    ydiff_list = []
    ydiff_json = subprocess.check_output(cmd)
    json_object = json.loads(ydiff_json)
    for i in json_object:
        for x in json_object[i]:
            # currently hard coded to detect 8-bit values.
            if float(x['tags']['lavfi.signalstats.YDIF']) > 25:
                ydiff_list.append(float(x["pkt_pts_time"]) * 1000)
    return ydiff_list


def make_chapters(ydiff_list):
    '''
    Use mkvpropedit to insert chapter markers for each source video.
    Each chapter's name will reflect the source filename of each clip.
    '''
    chapter_list = [['00:00:00.000', 'bla']]
    for video in ydiff_list:
        timestamp = ififuncs.convert_millis(int(video))
        chapter_list.append([timestamp, 'blsss'])
    chapter_counter = 1
    # uh use a real path/filename.
    with open('chapters.txt', 'wb') as fo:
        for i in chapter_list:
            fo.write(
                'CHAPTER%s=%s\nCHAPTER%sNAME=%s\n' % (
                    str(chapter_counter).zfill(2), i[0], str(chapter_counter).zfill(2), i[1]
                    )
                )
            chapter_counter += 1


def main(args_):
    '''
    Launches the functions that prepare and execute the concatenation.
    '''
    args = parse_args(args_)
    remuxed_file = remux(args.i)
    ydiff_list = get_scene_changes(remuxed_file)
    make_chapters(ydiff_list)
    subprocess.call([
        'mkvpropedit', remuxed_file, '-c', 'chapters.txt'
    ])

if __name__ == '__main__':
    main(sys.argv[1:])
