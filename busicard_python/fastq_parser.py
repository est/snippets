# http://www.reddit.com/r/Python/comments/1pmrvb/how_much_python_can_you_fit_on_the_back_of_a/

def parse_fastq(filename):
    file = open(filename)
    result = {}
    cn = None
    for i,line in enumerate(file):
        if i % 4 == 0:
            cn = line.rstrip('\n')
        if i % 4 == 1:
            result[cn] = line.rstrip('\n')
    return result


def parse_fastq1(filename):
    l=map(str.rstrip, open(filename))
    return dict(zip(l[0::4], l[1::4]))

if '__main__' == __name__:
    print parse_fastq('1.fastq')