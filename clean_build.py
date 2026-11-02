"""
clean_build.py

Clean the Vivado proj/ directory, then (re)create and/or build the project,
and optionally export the .xsa and a release archive.
Reuses git_vivado.do_checkout(), so the checkout.tcl code path is unchanged.

Note: Python 3 is required.

Sections: constants, console output, job context, Vivado discovery,
project helpers, build steps, variant builds, command line.
"""

import argparse
import concurrent.futures
import glob
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time

import git_vivado


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Lines echoed during a parallel build; the log file always gets every line.
# Problems are always included, --verbose echoes everything.
MILESTONE_RE = re.compile(
    r'(ERROR|CRITICAL WARNING|FATAL|Failure|failed)'
    r'|^\s*INFO: (Creating new project|Rebuilding block design|Build complete'
    r'|Project created|Writing hardware platform|Wrote out|Archiving project'
    r'|Opening project|Using IP cache)'
    r'|^\s*(Starting|Finished|Phase)\s'
    r'|\[Vivado 12-\d+\]'
)


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------

# Guard stdout so concurrent workers emit whole lines.
_print_lock = threading.Lock()


def emit(text):
    """Write text to stdout as one indivisible unit."""
    with _print_lock:
        sys.stdout.write(text)
        sys.stdout.flush()


def shorten(text, width):
    """Shorten text to width characters, eliding the middle.

    Vivado progress lines end with a file name, so the tail is worth keeping.
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
    """Return the usable output width; a redirected stdout gets the default."""
    try:
        if not sys.stdout.isatty():
            return default
        cols = shutil.get_terminal_size().columns
    except Exception:
        return default
    return cols if cols > 40 else default


# ---------------------------------------------------------------------------
# Job context and logging runner
# ---------------------------------------------------------------------------

# Concurrent variants (--jobs > 1) must not share these, so each one gets:
#   - its own IP cache (checkout.tcl -ip-cache)
#   - its own vivado.jou/vivado.log (vivado -journal/-log)
#   - its own archive scratch directory (archive_project.tcl -t)
#   - its own per-user Xilinx directory (tclapp manifest race, see private_user_env)
# Output is captured per variant to proj/logs/<variant>/<step>.log.

class BuildError(Exception):
    """A build step failed.

    Raised instead of sys.exit() so a worker thread can report the failure
    to the dispatcher, since SystemExit in a thread loses the exit code.
    """


class JobContext(object):
    """Per-project execution settings.

    Sequential mode leaves everything unset, so os.system is used as before.
    """

    def __init__(self, name='', log_dir=None, ip_cache=None, temp_dir=None, verbose=False):
        self.name = name          # variant name, tags console output
        self.log_dir = log_dir    # captured output dir, None means sequential
        self.ip_cache = ip_cache  # private IP cache, None means the shared one
        self.temp_dir = temp_dir  # private archive scratch, None means default
        self.verbose = verbose    # echo every captured line
        self.journal_dir = None   # journal/log dir of a sequential run
        self.env = None           # process environment, None means inherited
        self.status = 'pending'
        self.last_line = ''
        self.started = None

    @property
    def parallel(self):
        """Return True when sharing the machine with other projects."""
        return self.log_dir is not None

    def opts(self, step):
        """Return the extra vivado options for one step.

        The step is part of the name so a later xsa/archive run does not
        overwrite the build journal. Sequential runs use the same files in
        journal_dir, which keeps vivado.jou/.log out of the working directory.
        """
        directory = self.log_dir or self.journal_dir
        if not directory:
            return ''
        os.makedirs(directory, exist_ok=True)
        base = os.path.join(directory, step).replace('\\', '/')
        return '-journal %s.jou -log %s.log' % (base, base)

    def runner_for(self, step):
        """Return the runner for one step, None selects os.system."""
        if not self.parallel:
            return None
        return make_logging_runner(self, step, self.verbose)

    def say(self, text):
        """Print a progress message, tagged when running concurrently."""
        if self.parallel:
            emit('[%s] %s\n' % (self.name, text))
        else:
            print(text)


def private_user_env(user_dir):
    """Return an environment with a private per-user Xilinx directory.

    Vivado, and every synth run it spawns, rewrites tclapp/manifest.tcl in the
    per-user directory on each start. Concurrent starts truncate it, which
    fails runs with "tclapp::load_apps failed". Pointing each job to its own
    copy removes the shared file. Licenses are copied over.
    """
    if platform.system() == 'Windows':
        var, home = 'APPDATA', os.environ.get('APPDATA', '')
        xilinx_name = 'Xilinx'
    else:
        var, home = 'HOME', os.path.expanduser('~')
        xilinx_name = '.Xilinx'

    private_xilinx = os.path.join(user_dir, xilinx_name)
    os.makedirs(private_xilinx, exist_ok=True)
    for lic in glob.glob(os.path.join(home, xilinx_name, '*.lic')):
        shutil.copy(lic, private_xilinx)

    env = dict(os.environ)
    env[var] = user_dir
    return env


def make_logging_runner(ctx, step, verbose):
    """Return a runner(cmd) like os.system that logs and tags its output."""
    log_path = os.path.join(ctx.log_dir, '%s.log' % step)

    def run(cmd):
        ctx.status = step
        with open(log_path, 'w', encoding='utf-8', errors='replace') as log:
            log.write('$ %s\n\n' % cmd)
            log.flush()
            proc = subprocess.Popen(
                cmd, shell=True, env=ctx.env,
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


def start_heartbeat(contexts, interval=60):
    """Print a periodic status per unfinished project; return the stop event.

    Synthesis and implementation log to .runs/, so a long build is otherwise
    silent and looks hung.
    """
    stop = threading.Event()

    def loop():
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

    threading.Thread(target=loop, daemon=True).start()
    return stop


# ---------------------------------------------------------------------------
# Vivado discovery and environment checks
# ---------------------------------------------------------------------------

def tclapp_manifest_path():
    """Return the per-user vivado tclapp manifest path."""
    if platform.system() == 'Windows':
        base = os.path.join(os.environ.get('APPDATA', ''), 'Xilinx', 'Vivado')
    else:
        base = os.path.join(os.path.expanduser('~'), '.Xilinx', 'Vivado')
    return os.path.join(base, 'tclapp', 'manifest.tcl')


def check_tclapp_manifest(fix):
    """Warn about a truncated tclapp manifest, which breaks every vivado start.

    The file is removed when fix is set; vivado regenerates it.
    """
    path = tclapp_manifest_path()
    if not os.path.isfile(path):
        return
    with open(path, 'r', errors='replace') as f:
        apps = [line for line in f if line.lstrip().startswith('::tclapp::load_app')]
    if len(apps) > 1:
        return
    print('WARNING: %s has only %d app entries (truncated by concurrent vivado starts?).'
          % (path, len(apps)))
    if fix:
        os.remove(path)
        print('INFO: Removed %s, vivado regenerates it on the next start.' % path)
    else:
        print('         Use --fix-tclapp to remove it, or delete it manually.')


def resolve_vivado(script_dir, args):
    """Locate vivado, save the settings and check the environment.

    Return (vivado_cmd, version).
    """
    vivado_cmd, version = git_vivado.locate_vivado(script_dir, args.version, args.install_path)
    print('INFO: Using Vivado at %s' % vivado_cmd)
    check_tclapp_manifest(args.fix_tclapp)
    return vivado_cmd, version


# ---------------------------------------------------------------------------
# Project helpers
# ---------------------------------------------------------------------------

def clean_proj_dir(proj_dir, force):
    """Delete all contents of proj_dir except .keep, creating it if missing."""
    if not force and not git_vivado.accept_warning(
            'All contents of %s will be permanently deleted.' % proj_dir):
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


def variant_xpr_path(base_xpr_path, variant_value):
    """Return the project path of a variant: <proj dir>/<variant>/<xpr name>.

    Each variant gets a fully separate project directory under proj/.
    """
    proj_dir = os.path.dirname(base_xpr_path)
    basename = os.path.basename(base_xpr_path)
    return os.path.join(proj_dir, variant_value, basename)


def find_bitstream(xpr_path):
    """Return the bitstreams produced by impl_1.

    A failed run still exits 0 in batch mode, so a .bit is the direct proof
    that the build succeeded.
    """
    runs_dir = os.path.join('%s.runs' % os.path.splitext(xpr_path)[0], 'impl_1')
    return sorted(glob.glob(os.path.join(runs_dir, '*.bit')))


# ---------------------------------------------------------------------------
# Build steps
# ---------------------------------------------------------------------------

def check_path_length(xpr_path):
    """Warn when the project path risks the Windows 260 character limit.

    Vivado generates paths about 100 characters deeper than the .xpr.
    """
    if platform.system() == 'Windows' and len(os.path.abspath(xpr_path)) > 140:
        print('WARNING: %s is %d characters long. Vivado can fail on Windows paths above 260 '
              'characters; use a shorter repository path.' % (xpr_path, len(xpr_path)))


def run_vivado_tcl(vivado_cmd, script_dir, tcl_name, xpr_path, repo_path, extra_args='',
                   vivado_opts='', runner=None):
    """Run a batch-mode Tcl script (export_xsa.tcl/archive_project.tcl) on xpr_path."""
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


def do_one_project(args, script_dir, vivado_cmd, repo_path, xpr_path, extra_tclargs='',
                   output_name=None, ctx=None):
    """Run the requested --checkout/--build/--xsa/--archive steps for one project.

    Raise BuildError on failure, so concurrent callers can attribute it and
    still collect the other results.
    """
    ctx = ctx or JobContext()
    ctx.started = time.time()
    if not ctx.parallel:
        ctx.journal_dir = os.path.join(os.path.dirname(xpr_path), 'logs')
    check_path_length(xpr_path)

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
            # The prompt is answered up front, input() cannot be served from a worker.
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
        # Batch vivado can exit 0 after a failed script, so check the result
        if not os.path.isfile(xpr_path):
            raise BuildError('checkout did not create %s' % xpr_path)

        if args.build and not find_bitstream(xpr_path):
            raise BuildError('build produced no bitstream in %s.runs/impl_1 '
                             '(synthesis or implementation failed)'
                             % os.path.splitext(xpr_path)[0])

    # --xsa and --archive need an existing project, from above or a prior run
    if args.xsa or args.archive:
        if not os.path.isfile(xpr_path):
            raise BuildError('%s does not exist; run with --checkout or --build first'
                             % xpr_path)

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


# ---------------------------------------------------------------------------
# Variant builds
# ---------------------------------------------------------------------------

def make_variant_specs(args, variant_values, repo_path, xpr_path, jobs):
    """Return a (value, xpr path, JobContext) tuple per variant."""
    proj_dir = os.path.dirname(xpr_path)
    specs = []
    for variant_value in variant_values:
        variant_xpr = variant_xpr_path(xpr_path, variant_value)
        ctx = JobContext(name=variant_value)
        if jobs > 1:
            # Beside the project dirs, so create_project gets an empty dir
            # and --clean still removes them.
            ctx.log_dir = os.path.join(proj_dir, 'logs', variant_value)
            os.makedirs(ctx.log_dir, exist_ok=True)
            ctx.ip_cache = os.path.join(proj_dir, 'cache-%s' % variant_value)
            ctx.temp_dir = os.path.join(repo_path, 'temp', variant_value)
            ctx.env = private_user_env(os.path.join(proj_dir, 'user-%s' % variant_value))
            ctx.verbose = args.verbose
        specs.append((variant_value, variant_xpr, ctx))
    return specs


def run_sequential(args, specs, run_variant):
    """Run the variants one by one, stopping at the first failure."""
    for spec in specs:
        variant_value, variant_xpr, _ = spec
        print('INFO: ===== %s=%s (%s) =====' % (args.variant_tclvar, variant_value, variant_xpr))
        try:
            run_variant(spec)
        except BuildError as exc:
            print('Error: %s' % exc)
            sys.exit(1)


def run_parallel(args, specs, jobs, run_variant):
    """Run the variants concurrently, then print a summary and exit 1 on failure."""
    print('INFO: ===== building %d variants, %d at a time =====' % (len(specs), jobs))
    for variant_value, variant_xpr, ctx in specs:
        print('INFO:   %s=%s -> %s (logs in %s)'
              % (args.variant_tclvar, variant_value, variant_xpr, ctx.log_dir))

    failures = []
    started_at = time.time()
    heartbeat = start_heartbeat([c for _, _, c in specs])
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(run_variant, spec): spec for spec in specs}
            for future in concurrent.futures.as_completed(futures):
                variant_value, _, ctx = futures[future]
                try:
                    future.result()
                    emit('[%s] OK (%.1f min)\n'
                         % (variant_value, (time.time() - ctx.started) / 60.0))
                except BaseException as exc:
                    ctx.status = 'failed'
                    failures.append((variant_value, exc))
                    emit('[%s] FAILED: %s\n' % (variant_value, exc))
    finally:
        heartbeat.set()

    print('\nINFO: ===== summary (%.1f min wall clock) =====' % ((time.time() - started_at) / 60.0))
    for variant_value, _, ctx in specs:
        print('  %-12s %s' % (variant_value, 'FAILED' if ctx.status == 'failed' else 'ok'))
    if failures:
        for variant_value, exc in failures:
            print('Error: %s: %s' % (variant_value, exc))
        sys.exit(1)


def run_variants(args, script_dir, vivado_cmd, repo_path, xpr_path):
    """Run the requested steps once per --variant-values entry."""
    variant_values = [v.strip() for v in args.variant_values.split(',') if v.strip()]
    base_proj_name = os.path.splitext(os.path.basename(xpr_path))[0]
    jobs = len(variant_values) if args.jobs == 0 else min(args.jobs, len(variant_values))

    if jobs > 1 and (args.checkout or args.build) and not args.force:
        # Ask once here, do_checkout would prompt from inside a worker thread.
        targets = ', '.join(os.path.dirname(variant_xpr_path(xpr_path, v))
                            for v in variant_values)
        if not git_vivado.accept_warning(
                'Files and directories contained in %s may be overwritten. '
                'Do you wish to continue?' % targets):
            sys.exit()

    specs = make_variant_specs(args, variant_values, repo_path, xpr_path, jobs)

    # One unit of work for both modes, so they cannot drift apart.
    def run_variant(spec):
        variant_value, variant_xpr, ctx = spec
        do_one_project(
            args, script_dir, vivado_cmd, repo_path, variant_xpr,
            extra_tclargs='-D %s %s' % (args.variant_tclvar, variant_value),
            output_name='%s-%s' % (base_proj_name, variant_value),
            ctx=ctx,
        )

    if jobs <= 1:
        run_sequential(args, specs, run_variant)
    else:
        run_parallel(args, specs, jobs, run_variant)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def parse_args(script_dir):
    """Parse and validate the command line."""
    project_name = os.path.basename(os.path.abspath(os.path.join(script_dir, '..')))
    default_repo_path = os.path.abspath(os.path.join(script_dir, '..'))
    default_xpr_path = os.path.abspath(
        os.path.join(script_dir, '..', 'proj', '%s.xpr' % project_name))
    default_version = git_vivado.load_config(script_dir)['version'] or 'newest installed'

    parser = argparse.ArgumentParser(
        description='Cleans the proj/ directory and, optionally, '
                    '(re)creates and/or builds the Vivado project',
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Paths and version
    parser.add_argument('-f', dest='force', default=False, action='store_true',
                        help='Skip confirmation prompts')
    parser.add_argument('-r', dest='repo_path', type=str, default=default_repo_path,
                        help='Path to target repository\nDefault = %s' % default_repo_path)
    parser.add_argument('-x', dest='xpr_path', type=str, default=default_xpr_path,
                        help='Path to XPR file\nDefault = %s' % default_xpr_path)
    parser.add_argument('-v', dest='version', type=str, default=None,
                        help='Vivado version number 20##.#\nDefault = %s' % default_version)
    parser.add_argument('-i', dest='install_path', type=str, default=None,
                        help='Vivado install root, e.g. <drive>/AMDDesignTools\n'
                             'Saved with -v to <repo>/config.ini for later runs')

    # Actions
    parser.add_argument('--clean', dest='clean', default=False, action='store_true',
                        help='Delete the contents of proj/ first')
    parser.add_argument('--checkout', dest='checkout', default=False, action='store_true',
                        help='(Re)create the project only, no build')
    parser.add_argument('--build', dest='build', default=False, action='store_true',
                        help='Create (if needed) and build: synth, impl, write_bitstream\n'
                             'Takes precedence over --checkout')
    parser.add_argument('--xsa', dest='xsa', default=False, action='store_true',
                        help='Export the fixed .xsa with bitstream to <repo>/hw_handoff\n'
                             'Needs a built project')
    parser.add_argument('--archive', dest='archive', default=False, action='store_true',
                        help='Create the release ZIP under <repo>/release')

    # Variants
    parser.add_argument('--variant-tclvar', dest='variant_tclvar', type=str, default='',
                        help='Global Tcl variable (checkout.tcl -D) set once per variant\n'
                             'Requires --variant-values')
    parser.add_argument('--variant-values', dest='variant_values', type=str, default='',
                        help='Comma-separated variant values, one project each\n'
                             'proj/foo.xpr with a,b gives proj/a/foo.xpr, proj/b/foo.xpr')
    parser.add_argument('-j', '--jobs', dest='jobs', type=int, default=1,
                        help='Variants built concurrently, 0 is one per variant\n'
                             'Default = 1 (sequential). Needs ~8 GB RAM per job\n'
                             'Logs go to proj/logs/<variant>/<step>.log')
    parser.add_argument('--verbose', dest='verbose', default=False, action='store_true',
                        help='With --jobs > 1, echo every output line')

    # Environment
    parser.add_argument('--fix-tclapp', dest='fix_tclapp', default=False, action='store_true',
                        help='Delete a truncated per-user vivado tclapp/manifest.tcl')

    args = parser.parse_args()

    if not (args.clean or args.checkout or args.build or args.xsa or args.archive):
        parser.error('Nothing to do: specify at least one of '
                     '--clean, --checkout, --build, --xsa, --archive')
    if bool(args.variant_tclvar) != bool(args.variant_values):
        parser.error('--variant-tclvar and --variant-values must be used together')
    if args.jobs < 0:
        parser.error('--jobs must be 0 (one per variant) or a positive number')
    return args


def main():
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    args = parse_args(script_dir)

    repo_path = os.path.abspath(os.path.join(os.getcwd(), args.repo_path))
    xpr_path = os.path.abspath(os.path.join(os.getcwd(), args.xpr_path))

    if args.clean:
        clean_proj_dir(os.path.dirname(xpr_path), args.force)

    vivado_cmd = None
    if args.checkout or args.build or args.xsa or args.archive:
        vivado_cmd, args.version = resolve_vivado(script_dir, args)

    if args.variant_values:
        run_variants(args, script_dir, vivado_cmd, repo_path, xpr_path)
        return

    try:
        do_one_project(args, script_dir, vivado_cmd, repo_path, xpr_path)
    except BuildError as exc:
        print('Error: %s' % exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
