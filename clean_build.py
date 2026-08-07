# PYTHON 3.X.X REQUIRED!!!
"""
clean_build.py

Cleans the Vivado 'proj' working directory and, optionally, (re)creates the
project from the repo/ sources and/or builds it (synth -> impl -> bitstream).

This script is additive: it does not change or remove any existing
functionality in git_vivado.py (checkin/checkout/release keep working as
before). It reuses git_vivado.do_checkout() so the checkout.tcl code path
stays identical.

Vivado install auto-discovery
------------------------------
Starting with Vivado 2025.1, AMD renamed the default installation root from
"Xilinx" to "AMDDesignTools". Additionally, in some versions the on-disk
layout itself changed from "<root>/Vivado/<version>/bin" (older) to
"<root>/<version>/Vivado/bin" (2025.1+). The tools may also be installed on
any drive/partition letter, not just C:. Resolution order:
  1. config.ini's VivadoInstallPath + <version> (existing/unchanged behavior),
     tried against both known layouts.
  2. Auto-scan: on Windows, every available drive letter is checked for both
     root directory names ("AMDDesignTools", "Xilinx") and both layouts;
     on Linux, a handful of common install locations are checked the same way.

Parallel variant builds (--jobs)
--------------------------------
With --variant-values, each variant is an independent project and can be
built concurrently. This is opt-in via --jobs N (default 1 = the original
sequential behavior, byte-for-byte unchanged).

Running vivado processes concurrently requires separating three things they
would otherwise share, all of which are handled automatically when --jobs > 1:

  * the out-of-context IP cache (proj/cache), shared by every project checked
    out from this repo -- passed per variant via checkout.tcl's -ip-cache
  * vivado.jou / vivado.log, written to the working directory under fixed
    names -- passed per variant via vivado's own -journal/-log
  * the archive scratch directory (<repo>/temp); because variants of one
    design share a project name they would stage to the identical path --
    passed per variant via archive_project.tcl's -t

Console output is also serialized: os.system lets every child write straight
to the shared console, so concurrent builds interleave mid-line. Under
--jobs > 1 each variant's output is captured to proj/logs/<variant>/ in full,
while the console shows milestone lines tagged with the variant name (or
every line, with --verbose).
"""

import argparse
import concurrent.futures
import ctypes
import glob
import os
import platform
import re
import shutil
import string
import subprocess
import sys
import threading
import time

import git_vivado

# Root directory names Vivado has been installed under, in search priority order.
# Vivado 2025.1+ uses "AMDDesignTools"; earlier versions use "Xilinx".
VIVADO_ROOT_DIR_NAMES = ['AMDDesignTools', 'Xilinx']

# Lines echoed to the console during a parallel build. Everything is always
# written to the per-variant log file regardless; this only decides what is
# worth showing while several builds are talking at once. Anything that
# reports a problem is included, so nothing is hidden that would explain a
# failure -- use --verbose to see every line instead.
MILESTONE_RE = re.compile(
    r'(ERROR|CRITICAL WARNING|FATAL|Failure|failed)'
    r'|^\s*INFO: (Creating new project|Rebuilding block design|Build complete'
    r'|Project created|Writing hardware platform|Wrote out|Archiving project'
    r'|Opening project|Using IP cache)'
    r'|^\s*(Starting|Finished|Phase)\s'
    r'|\[Vivado 12-\d+\]'
)

# Guards stdout so concurrent workers emit whole lines instead of interleaving.
_print_lock = threading.Lock()


def emit(text):
    """Writes text to stdout as one indivisible unit.

    Concurrent workers would otherwise interleave partial lines, since each
    print() is several underlying writes.
    """
    with _print_lock:
        sys.stdout.write(text)
        sys.stdout.flush()


class BuildError(Exception):
    """A build step failed. Raised instead of sys.exit() so that a worker
    thread reports the failure to the dispatcher rather than trying to
    terminate the interpreter from a thread (where SystemExit only unwinds
    that one thread and the exit code is lost)."""


class JobContext(object):
    """Per-project execution settings.

    In sequential mode nothing is configured, opts() returns no extra vivado
    options and runner_for() returns None, so do_one_project falls back to the
    original os.system code path unchanged.
    """

    def __init__(self, name='', log_dir=None, ip_cache=None, temp_dir=None, verbose=False):
        """Creates a context for one project.

        name     -- variant name, used to tag console output
        log_dir  -- where captured output goes; None selects sequential mode
        ip_cache -- private IP cache directory, or None to use the shared one
        temp_dir -- private archive scratch directory, or None for the default
        verbose  -- echo every captured line rather than only milestones
        """
        self.name = name
        self.log_dir = log_dir
        self.ip_cache = ip_cache
        self.temp_dir = temp_dir
        self.verbose = verbose
        self.status = 'pending'
        self.last_line = ''
        self.started = None

    @property
    def parallel(self):
        """True when this project shares the machine with others.

        Having a log directory is what distinguishes the two modes: it is set
        only by the concurrent dispatcher, and everything else that must
        differ under concurrency keys off it.
        """
        return self.log_dir is not None

    def opts(self, step):
        """Extra vivado command-line options for one step.

        vivado writes vivado.jou/vivado.log into the working directory under
        fixed names, so concurrent processes fight over them (the repo already
        contains vivado_<pid>.backup.jou files from exactly that). The names
        include the step because a variant runs several vivado invocations in
        turn, and the build's journal must not be overwritten by the later
        xsa/archive ones.
        """
        if not self.parallel:
            return ''
        base = os.path.join(self.log_dir, step).replace('\\', '/')
        return '-journal %s.jou -log %s.log' % (base, base)

    def runner_for(self, step):
        """Returns the runner for one step, or None to use os.system.

        None is returned in sequential mode so that the original, uncaptured
        console behaviour is preserved exactly.
        """
        if not self.parallel:
            return None
        return make_logging_runner(self, step, self.verbose)

    def say(self, text):
        """Progress message, tagged and serialized when running concurrently."""
        if self.parallel:
            emit('[%s] %s\n' % (self.name, text))
        else:
            print(text)


def make_logging_runner(ctx, step, verbose):
    """Returns a runner(cmd) that behaves like os.system but captures the
    child's output to a log file and echoes selected lines with the variant
    name prefixed, so concurrent builds stay readable."""
    log_path = os.path.join(ctx.log_dir, '%s.log' % step)

    def run(cmd):
        """Runs cmd, logging all output and echoing the interesting lines."""
        ctx.status = step
        with open(log_path, 'w', encoding='utf-8', errors='replace') as log:
            log.write('$ %s\n\n' % cmd)
            log.flush()
            proc = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', bufsize=1,
            )
            for line in proc.stdout:
                log.write(line)
                stripped = line.rstrip()
                if not stripped:
                    continue
                ctx.last_line = stripped
                if verbose or MILESTONE_RE.search(stripped):
                    emit('[%s] %s\n' % (ctx.name, stripped))
            proc.stdout.close()
            rc = proc.wait()
        if rc != 0:
            emit('[%s] step "%s" exited %s -- see %s\n' % (ctx.name, step, rc, log_path))
        return rc

    return run


def shorten(text, width):
    """Shortens text to width characters, eliding the MIDDLE, not the tail.

    Vivado's progress lines are dominated by long absolute paths whose useful
    part -- the file name -- sits at the very end, e.g.

        output Verilog Output written to : D:/.../Zuca.gen/sources_1/bd/.../top.v

    Cutting the tail off therefore discards exactly the information worth
    showing and leaves a line that stops mid-path. Eliding the middle keeps
    both the "what happened" prefix and the "to which file" suffix.
    """
    if width <= 0:
        return ''
    if len(text) <= width:
        return text
    if width <= 5:
        return text[:width]
    keep = width - 3
    head = keep // 3
    return text[:head] + '...' + text[-(keep - head):]


def console_width(default=120):
    """Returns the usable output width in characters.

    When stdout is not a terminal (redirected to a file, or piped into a CI
    log) there is no width limit worth honouring, so the roomier default is
    used -- get_terminal_size() would otherwise report a misleading 80.
    """
    try:
        if not sys.stdout.isatty():
            return default
        cols = shutil.get_terminal_size().columns
    except Exception:
        return default
    return cols if cols > 40 else default


def start_heartbeat(contexts, interval=60):
    """Prints a periodic one-line-per-variant status while builds run.

    A full ZU build produces long silent stretches (synthesis and
    implementation run in their own processes and log to .runs/, not to the
    parent's stdout), so without this there is no way to tell a working build
    from a hung one.
    """
    stop = threading.Event()

    def loop():
        """Reports on every unfinished project until asked to stop."""
        while not stop.wait(interval):
            active = [c for c in contexts if c.started and c.status not in ('done', 'failed')]
            if not active:
                continue
            lines = ['--- still running ---']
            for c in active:
                mins = (time.time() - c.started) / 60.0
                prefix = '    [%s] %-10s %5.1f min | ' % (c.name, c.status, mins)
                lines.append(prefix + shorten(c.last_line, console_width() - len(prefix) - 1))
            emit('\n'.join(lines) + '\n')

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return stop



def list_windows_drives():
    """Returns available drive roots on Windows, e.g. ['C:\\\\', 'D:\\\\', 'E:\\\\']."""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drives.append('%s:\\' % letter)
    return drives


def vivado_layout_candidates(root_base, version, exe_name):
    """
    Returns both known on-disk install layouts under an install root, e.g. for
    root_base="E:\\AMDDesignTools" and version="2025.2":
      - E:\\AMDDesignTools\\Vivado\\2025.2\\bin\\vivado.bat  (older layout)
      - E:\\AMDDesignTools\\2025.2\\Vivado\\bin\\vivado.bat  (2025.1+ layout)
    """
    return [
        os.path.join(root_base, 'Vivado', version, 'bin', exe_name),
        os.path.join(root_base, version, 'Vivado', 'bin', exe_name),
    ]


def find_vivado_cmd(version, configured_install_path=None):
    """
    Locates the vivado executable for `version`.

    Search order:
      1. Both known layouts under configured_install_path (config.ini,
         unchanged behavior) and, in case config.ini already points at a
         ".../Vivado" style path (older convention), under its parent too.
      2. Both known layouts under "<root>/<root_dir_name>" for every root
         name in VIVADO_ROOT_DIR_NAMES, where <root> is every drive letter
         on Windows, or a common install base on Linux.

    Returns the path to the vivado command if found, otherwise None.
    """
    exe_name = 'vivado.bat' if platform.system() == 'Windows' else 'vivado'
    candidates = []

    if configured_install_path:
        configured_install_path = os.path.abspath(configured_install_path)
        candidates += vivado_layout_candidates(configured_install_path, version, exe_name)
        candidates += vivado_layout_candidates(os.path.dirname(configured_install_path), version, exe_name)

    if platform.system() == 'Windows':
        root_bases = [os.path.join(drive, root_dir_name)
                      for drive in list_windows_drives()
                      for root_dir_name in VIVADO_ROOT_DIR_NAMES]
    else:
        root_bases = [os.path.join(base, root_dir_name)
                      for base in ('/opt', '/tools', os.path.expanduser('~'))
                      for root_dir_name in VIVADO_ROOT_DIR_NAMES]

    for root_base in root_bases:
        candidates += vivado_layout_candidates(root_base, version, exe_name)

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def clean_proj_dir(proj_dir, force):
    """Deletes all contents of proj_dir except .keep (recreates proj_dir if missing)."""
    if not force and not git_vivado.accept_warning('All contents of %s will be permanently deleted.' % proj_dir):
        sys.exit()

    if not os.path.isdir(proj_dir):
        os.makedirs(proj_dir)
        print('INFO: Created empty %s' % proj_dir)
        return

    for entry in os.listdir(proj_dir):
        if entry == '.keep':
            continue
        entry_path = os.path.join(proj_dir, entry)
        if os.path.islink(entry_path):
            os.unlink(entry_path)
        elif os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.remove(entry_path)
    print('INFO: Cleaned %s' % proj_dir)


def run_vivado_tcl(vivado_cmd, script_dir, tcl_name, xpr_path, repo_path, extra_args='',
                   vivado_opts='', runner=None):
    """Runs a batch-mode vivado tcl script (export_xsa.tcl / archive_project.tcl) against xpr_path."""
    vivado_cmd = vivado_cmd.replace('\\', '/')
    script_path = os.path.join(script_dir, tcl_name).replace('\\', '/')
    xpr_path = xpr_path.replace('\\', '/')
    repo_path = repo_path.replace('\\', '/')
    cmd = "%s%s -mode batch -source %s -notrace -tclargs -x %s -r %s%s" % (
        vivado_cmd,
        ' %s' % vivado_opts if vivado_opts else '',
        script_path, xpr_path, repo_path,
        ' %s' % extra_args if extra_args else ''
    )
    return (runner or os.system)(cmd)


def variant_xpr_path(base_xpr_path, variant_value):
    """
    Places this variant's project in its own subdirectory (named after
    variant_value) under base_xpr_path's directory, so each variant gets a
    fully separate project directory (all its .runs/.srcs/.cache/etc.) under
    proj/, instead of sharing one proj/ directory with differently-prefixed
    files.
    """
    proj_dir = os.path.dirname(base_xpr_path)
    basename = os.path.basename(base_xpr_path)
    return os.path.join(proj_dir, variant_value, basename)


def find_bitstream(xpr_path):
    """Returns the bitstreams produced by impl_1, if any.

    checkout.tcl's build path calls wait_on_run without inspecting the run's
    result, and a vivado batch session whose runs failed still exits 0, so a
    non-zero exit status alone does not prove the build succeeded. The
    presence of a .bit is the cheap, direct evidence -- and it matters most
    under --jobs, where nobody is watching the console.
    """
    runs_dir = os.path.join('%s.runs' % os.path.splitext(xpr_path)[0], 'impl_1')
    return sorted(glob.glob(os.path.join(runs_dir, '*.bit')))


def do_one_project(args, script_dir, vivado_cmd, repo_path, xpr_path, extra_tclargs='',
                   output_name=None, ctx=None):
    """Runs the requested --checkout/--build/--xsa/--archive steps for a single project (xpr_path).

    Raises BuildError on failure rather than exiting, so that a caller running
    several projects concurrently can attribute the failure and still collect
    the other results.
    """
    ctx = ctx or JobContext()
    ctx.started = time.time()

    if args.checkout or args.build:
        if os.path.isfile(xpr_path):
            raise BuildError('cannot check out repo when project exists; '
                             're-run with --clean to remove %s first' % os.path.dirname(xpr_path))

        tclargs = extra_tclargs
        if ctx.ip_cache:
            tclargs = ('%s -ip-cache %s' % (tclargs, ctx.ip_cache.replace('\\', '/'))).strip()

        step = 'build' if args.build else 'checkout'
        funcargs = {
            'script_dir': script_dir,
            # The confirmation prompt is answered once up front by the caller;
            # input() cannot be served from a worker thread.
            'force': args.force or ctx.parallel,
            'repo_path': repo_path,
            'xpr_path': xpr_path,
            'version': args.version,
            'vivado_cmd': vivado_cmd,
            'build': args.build,
            'extra_tclargs': tclargs,
            'vivado_opts': ctx.opts(step),
            'runner': ctx.runner_for(step),
            'DEBUG_NO_VIVADO': False,
            'DEBUG_VIVADO_TCL_TRACE': False,
        }
        if git_vivado.do_checkout(funcargs) != 0:
            raise BuildError('%s failed' % step)

        if args.build and not find_bitstream(xpr_path):
            raise BuildError('build produced no bitstream in %s.runs/impl_1 '
                             '(synthesis or implementation failed)'
                             % os.path.splitext(xpr_path)[0])

    # --xsa and --archive operate on an existing project (just checked out/built above,
    # or already present from a prior run) and can be combined freely with each other.
    if args.xsa or args.archive:
        if not os.path.isfile(xpr_path):
            raise BuildError('%s does not exist; run with --checkout or --build first' % xpr_path)

    output_extra = '-o %s' % output_name if output_name else ''

    if args.xsa:
        ctx.say('INFO: Exporting hardware platform (.xsa)')
        if run_vivado_tcl(vivado_cmd, script_dir, 'export_xsa.tcl', xpr_path, repo_path,
                          output_extra, ctx.opts('xsa'), ctx.runner_for('xsa')) != 0:
            raise BuildError('xsa export failed')

    if args.archive:
        ctx.say('INFO: Creating project release archive')
        archive_extra = output_extra
        if ctx.temp_dir:
            os.makedirs(ctx.temp_dir, exist_ok=True)
            archive_extra = ('%s -t %s' % (archive_extra, ctx.temp_dir.replace('\\', '/'))).strip()
        if run_vivado_tcl(vivado_cmd, script_dir, 'archive_project.tcl', xpr_path, repo_path,
                          archive_extra, ctx.opts('archive'), ctx.runner_for('archive')) != 0:
            raise BuildError('project archive failed')

    ctx.status = 'done'


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    project_name = os.path.basename(os.path.abspath(os.path.join(script_dir, '..')))

    config = git_vivado.configparser.ConfigParser()
    config.read(os.path.join(script_dir, "config.ini"))
    operating_system = platform.system()
    config_settings = config[operating_system]

    default_repo_path = os.path.abspath(os.path.join(script_dir, '..'))
    default_xpr_path = os.path.abspath(os.path.join(script_dir, '..', 'proj', '%s.xpr' % project_name))
    default_version = config_settings['VivadoVersion']

    parser = argparse.ArgumentParser(
        description='Cleans the proj/ directory and, optionally, (re)creates and/or builds the Vivado project',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-f', dest='force', default=False, action='store_true',
                         help='Skip confirmation prompts')
    parser.add_argument('-r', dest='repo_path', type=str, default=default_repo_path,
                         help='Path to target repository\nDefault = %s' % default_repo_path)
    parser.add_argument('-x', dest='xpr_path', type=str, default=default_xpr_path,
                         help='Path to XPR file\nDefault = %s' % default_xpr_path)
    parser.add_argument('-v', dest='version', type=str, default=default_version,
                         help='Vivado version number 20##.#\nDefault = %s' % default_version)
    parser.add_argument('--clean', dest='clean', default=False, action='store_true',
                         help='Delete all contents of the proj/ directory before doing anything else')
    parser.add_argument('--checkout', dest='checkout', default=False, action='store_true',
                         help='(Re)create the Vivado project only (no build)')
    parser.add_argument('--build', dest='build', default=False, action='store_true',
                         help='Create (if needed) and build the whole project: synth -> impl -> write_bitstream.\n'
                              'Takes precedence over --checkout if both are given.')
    parser.add_argument('--xsa', dest='xsa', default=False, action='store_true',
                         help='Export a fixed, bitstream-included hardware platform (.xsa) to <repo>/hw_handoff.\n'
                              'Requires a built project (use with --build, or run separately after one).')
    parser.add_argument('--archive', dest='archive', default=False, action='store_true',
                         help='Create a project release ZIP archive under <repo>/release.\n'
                              'Can be used with or without --build (only needs project sources).')
    parser.add_argument('--variant-tclvar', dest='variant_tclvar', type=str, default='',
                         help='Name of a global Tcl variable to set (via checkout.tcl\'s -D) to one of\n'
                              '--variant-values, once per value, so a project\'s own BD script can read\n'
                              'it to switch build-time options -- this script has no built-in knowledge\n'
                              'of what the variable means. Requires --variant-values. Example: a project\n'
                              'whose BD script reads a "CODEC_VARIANT" global would pass\n'
                              '--variant-tclvar CODEC_VARIANT --variant-values foo,bar.')
    parser.add_argument('--variant-values', dest='variant_values', type=str, default='',
                         help='Comma-separated values for --variant-tclvar. --checkout/--build/--xsa/\n'
                              '--archive are applied once per value, as independent projects, each in\n'
                              'its own subdirectory (named after the value) under the same parent\n'
                              '(proj/) directory as -x/--xpr-path -- e.g. -x proj/foo.xpr with\n'
                              '--variant-values a,b produces proj/a/foo.xpr and proj/b/foo.xpr.\n'
                              '--clean (if given) still only cleans proj/ once, up front.')
    parser.add_argument('-j', '--jobs', dest='jobs', type=int, default=1,
                         help='Build this many --variant-values concurrently. Default = 1\n'
                              '(sequential, the original behaviour). Use 0 for one job per\n'
                              'variant. Only has an effect with --variant-values, since a single\n'
                              'project has nothing to run alongside.\n'
                              'Each variant gets its own IP cache, vivado journal/log and archive\n'
                              'scratch directory, because those are otherwise shared and would be\n'
                              'written by both processes at once. Full per-variant output is\n'
                              'captured to proj/logs/<variant>/<step>.log; the console shows\n'
                              'milestone and error lines tagged with the variant name.\n'
                              'A full build needs roughly 8 GB of RAM per concurrent job, so\n'
                              'raising this past what the machine can hold makes builds slower,\n'
                              'not faster.')
    parser.add_argument('--verbose', dest='verbose', default=False, action='store_true',
                         help='With --jobs > 1, echo every line of each variant\'s output instead of\n'
                              'just milestones and errors. Logs always contain everything either way.')
    args = parser.parse_args()

    if not (args.clean or args.checkout or args.build or args.xsa or args.archive):
        parser.error('Nothing to do: specify at least one of --clean, --checkout, --build, --xsa, --archive')

    if bool(args.variant_tclvar) != bool(args.variant_values):
        parser.error('--variant-tclvar and --variant-values must be used together')

    if args.jobs < 0:
        parser.error('--jobs must be 0 (one per variant) or a positive number')

    repo_path = os.path.abspath(os.path.join(os.getcwd(), args.repo_path))
    xpr_path = os.path.abspath(os.path.join(os.getcwd(), args.xpr_path))
    proj_dir = os.path.dirname(xpr_path)

    if args.clean:
        clean_proj_dir(proj_dir, args.force)

    vivado_cmd = None
    if args.checkout or args.build or args.xsa or args.archive:
        vivado_cmd = find_vivado_cmd(args.version, config_settings.get('VivadoInstallPath'))
        if not vivado_cmd:
            print('Error: Could not locate Vivado %s.' % args.version)
            print('       Checked config.ini path: %s' % config_settings.get('VivadoInstallPath'))
            print('       Checked root directories %s across all available drives/locations.' % VIVADO_ROOT_DIR_NAMES)
            sys.exit(1)
        print('INFO: Using Vivado at %s' % vivado_cmd)

    if args.variant_values:
        variant_values = [v.strip() for v in args.variant_values.split(',') if v.strip()]
        base_proj_name = os.path.splitext(os.path.basename(xpr_path))[0]
        jobs = len(variant_values) if args.jobs == 0 else min(args.jobs, len(variant_values))

        if jobs > 1 and (args.checkout or args.build) and not args.force:
            # do_checkout would otherwise prompt from inside a worker thread,
            # where input() competes with the other workers for stdin. Ask the
            # one question that applies to every variant here instead.
            targets = ', '.join(os.path.dirname(variant_xpr_path(xpr_path, v)) for v in variant_values)
            if not git_vivado.accept_warning('Files and directories contained in %s may be overwritten. '
                                             'Do you wish to continue?' % targets):
                sys.exit()

        jobspecs = []
        for variant_value in variant_values:
            variant_xpr = variant_xpr_path(xpr_path, variant_value)
            ctx = JobContext(name=variant_value)
            if jobs > 1:
                # Kept beside the project directories rather than inside them,
                # so nothing extra is present in the directory create_project
                # is about to populate, and so --clean still removes them.
                ctx.log_dir = os.path.join(proj_dir, 'logs', variant_value)
                os.makedirs(ctx.log_dir, exist_ok=True)
                # Private copies of the three things concurrent vivado
                # processes would otherwise share (see module docstring).
                ctx.ip_cache = os.path.join(proj_dir, 'cache-%s' % variant_value)
                ctx.temp_dir = os.path.join(repo_path, 'temp', variant_value)
                ctx.verbose = args.verbose
            jobspecs.append((variant_value, variant_xpr, ctx))

        def run_variant(spec):
            """Runs every requested step for one variant.

            Used as the unit of work by both the sequential loop and the
            thread pool, so the two paths cannot drift apart.
            """
            variant_value, variant_xpr, ctx = spec
            do_one_project(
                args, script_dir, vivado_cmd, repo_path, variant_xpr,
                extra_tclargs='-D %s %s' % (args.variant_tclvar, variant_value),
                output_name='%s-%s' % (base_proj_name, variant_value),
                ctx=ctx,
            )

        failures = []
        if jobs <= 1:
            for spec in jobspecs:
                variant_value, variant_xpr, ctx = spec
                print('INFO: ===== %s=%s (%s) =====' % (args.variant_tclvar, variant_value, variant_xpr))
                try:
                    run_variant(spec)
                except BuildError as exc:
                    # Sequential runs stop at the first failure, as before.
                    print('Error: %s' % exc)
                    sys.exit(1)
        else:
            print('INFO: ===== building %d variants, %d at a time =====' % (len(jobspecs), jobs))
            for variant_value, variant_xpr, ctx in jobspecs:
                print('INFO:   %s=%s -> %s (logs in %s)'
                      % (args.variant_tclvar, variant_value, variant_xpr, ctx.log_dir))
            started_at = time.time()
            heartbeat = start_heartbeat([c for _, _, c in jobspecs])
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
                    futures = {pool.submit(run_variant, spec): spec for spec in jobspecs}
                    for future in concurrent.futures.as_completed(futures):
                        variant_value, _, ctx = futures[future]
                        try:
                            future.result()
                            emit('[%s] OK (%.1f min)\n' % (variant_value, (time.time() - ctx.started) / 60.0))
                        except BaseException as exc:
                            ctx.status = 'failed'
                            failures.append((variant_value, exc))
                            emit('[%s] FAILED: %s\n' % (variant_value, exc))
            finally:
                heartbeat.set()

            print('\nINFO: ===== summary (%.1f min wall clock) =====' % ((time.time() - started_at) / 60.0))
            for variant_value, _, ctx in jobspecs:
                print('  %-12s %s' % (variant_value, 'FAILED' if ctx.status == 'failed' else 'ok'))
            if failures:
                for variant_value, exc in failures:
                    print('Error: %s: %s' % (variant_value, exc))
                sys.exit(1)
    else:
        try:
            do_one_project(args, script_dir, vivado_cmd, repo_path, xpr_path)
        except BuildError as exc:
            print('Error: %s' % exc)
            sys.exit(1)


