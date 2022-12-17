#!/usr/bin/env python3

import argparse
import hashlib
import json
import os

import pyfastx


def md5(file_path):
    """
    """
    with open(file_path, 'rb') as f:
        file_contents = f.read()
        md5 = hashlib.md5(file_contents).hexdigest()

    return md5


def main(args):
    filename = os.path.basename(args.fastq)
    md5_checksum = md5(args.fastq)
    total_reads = 0
    total_bases = 0
    num_bases_greater_or_equal_to_q30 = 0
    min_read_length = None
    max_read_length = 0
    file_stats = os.stat(args.fastq)
    file_size_bytes = file_stats.st_size
    fq = pyfastx.Fastx(args.fastq)
    
    for name, seq, qual, comment in fq:
        read_length = len(seq)
        if min_read_length is None or read_length < min_read_length:
            min_read_length = read_length
        if read_length > max_read_length:
            max_read_length = read_length
        total_reads += 1
        total_bases += read_length
        for q in qual:
            phred = ord(q) - 33
            if phred >= 30:
                num_bases_greater_or_equal_to_q30 += 1

    stats = {
        'filename': filename,
        'md5_checksum': md5_checksum,
        'size_bytes': file_size_bytes,
        'total_reads': total_reads,
        'total_bases': total_bases,
        'num_bases_greater_or_equal_to_q30': num_bases_greater_or_equal_to_q30,
        'mean_read_length': total_bases / total_reads,
        'max_read_length': max_read_length,
        'min_read_length': min_read_length,
    }

    print(json.dumps(stats, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fastq')
    args = parser.parse_args()
    main(args)
