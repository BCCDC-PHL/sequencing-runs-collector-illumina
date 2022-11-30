import pyfastx

def collect_fastq_stats(fastq_path):
    """
    Collect a set of statistics from a fastq file.

    :param fastq_path:
    :type fastq_path: str
    :return:
    :rtype: dict[str, object]
    """
    total_reads = 0
    total_bases = 0
    num_bases_greater_or_equal_to_q30 = 0
    min_read_length = None
    max_read_length = 0

    fq = pyfastx.Fastx(fastq_path)
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
        'total_reads': total_reads,
        'total_bases': total_bases,
        'num_bases_greater_or_equal_to_q30': num_bases_greater_or_equal_to_q30,
        'mean_read_length': total_bases / total_reads,
        'max_read_length': max_read_length,
        'min_read_length': min_read_length,
    }

    return stats
