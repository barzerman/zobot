import sys
import re
import argparse

# TODO: move this into a generic ile
class FileProcessor(object):
    def __init__(
        self,
        files,
        use_stdin=False,
        output=None,
        progress=None
    ):
        """
        Arguments:
            files (list(string)) - list of file names to read from
            use_stdin (bool) - when true reads from `stdin` when file list is blank. defaults to `False`
            output (dict) - file output parameters. defaults to `stdout`
                stdout (bool) - when set all output is streamed to `stdout`
                ext (str) - output file extension. if not `stdout` this defaults to `.out`
                dir (str) - output file directory
        """
        if not files:
            if not use_stdin:
                raise Exception('must specify `use_stdin` or pass a list of valid file names')
            else:
                self.files = [None]
        else:

            self.files = files

        self.output = output
        self.fp = None  # this is used by `__exit__` for cleaning state

    def __exit__(self, *args):
        self._close_files()

    def _close_files(self):
        if self.fp:
            for x in self.fp:
                x.close()

    def generate_output_file_name(self, fn):
        return fn + self.outext

    def _open_files(self, fn):
        if fn:
            fp = open(fn)
            self.fp = [fp]
            outfp = self.generate_output_file_name(fn)
            self.fp.append(outfp)
        else:
            fp = sys.stdin
            outfp = sys.stdout
        return fp, outfp

    def process_file(self, infp, outfp):
        count = 0
        for l in infp:
            result = self.process_line(l.strip())
            if result is not None:
                outfp.write(result)

            count += 1

        return count

    def process_all_files(self):
        stats= dict()
        for fn in self.files:
            infp, outfp = self._open_files(fn)
            stats[fn] = self.process_file(infp, outfp)
        return stats

    def process_line(self, l):
        return l

class ArgsFilesProcessor(FileProcessor):
    def __init__(self, args, use_stdin=False):
        self.args = args
        super(ArgsFilesProcessor, self).__init__(args.file, use_stdin=use_stdin)

class EntityNamesProcessor(ArgsFilesProcessor):
    split_re = re.compile(r'[^0-9a-zA-Z]+')

    def __enter__(self, *args):
        return self

    def __init__(self, args):
        super(EntityNamesProcessor, self).__init__(
            args, use_stdin=True
        )

    def mk_id_from_name(self, name):
        return '-'.join([x.lower()[:12] for x in self.split_re.split(name) if
                         len(x) > 2][:4])

    def process_line(self, line):
        id = self.mk_id_from_name(line)
        return id + '|' + line + '|' + line +'\n'


def main(args):
    with EntityNamesProcessor(args) as proc:
        stats = proc.process_all_files()
        for key, val in stats.iteritems():
            print >> sys.stderr, key, ":", val

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--noid", action="store_true", help="autogenerate ids")
    parser.add_argument("--outext", default=".out", help="outputfile extension")
    parser.add_argument('file',nargs='*')

    args = parser.parse_args()
    main(args)
