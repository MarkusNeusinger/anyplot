/*
 * libexecdeny.so: the exec filter of the renderer's exec-mode rows (R, later Julia),
 * loaded with LD_PRELOAD into the language's own binary.
 *
 * The plot, data and conversion modes install the filter in the harness's process
 * (agents/anyplot/render/harness.py, install_exec_deny). Exec mode cannot: the filter
 * would also refuse the start of the language's program. This library's constructor
 * installs it in that program instead, after ld.so loaded it and before its main runs,
 * so before any user code (agentic/specs/261024-agent-all-libraries.md, step 2b).
 *
 * Differences from the in-process program, each from the second opinion of 2026-10-28:
 * - execve and execveat end the calling process (SECCOMP_RET_KILL_PROCESS) instead of
 *   failing with EPERM. R's utils package runs Sys.which("uname") when it loads, and its
 *   popen reports a child's EPERM as an error, so under EPERM neither utils nor stats
 *   (nor ggplot2) loads. Killed, the posix_spawn child dies before it runs anything and
 *   R sees a dead child: system("true") returns 159 and every package loads.
 * - SECCOMP_FILTER_FLAG_TSYNC puts the filter on the threads a linked library's
 *   constructor (which runs before a preload's) may have started already.
 * - The process is made non-dumpable first (PR_SET_DUMPABLE 0): a killed vfork child that
 *   dumped core would take its parent with it on kernels before 5.16 (see install).
 * - The probe forks: an execve of a path that cannot exist exits the child with ENOENT
 *   before the filter and kills it with SIGSYS after it, so no probe starts a program.
 *
 * ANYPLOT_DENY_EXEC unset or empty: nothing happens. Any other value installs the
 * filter; "required" ends the process with exit code 3 (the plot mode's
 * EXEC_DENY_EXIT) when it is not in place. The state (on, unavailable, unsupported) is
 * written to the file descriptor ANYPLOT_EXEC_DENY_FD names, which is then closed and
 * dropped from the environment, so user code can neither forge nor reuse it. The
 * harness refuses the run unless it read "on".
 */
#define _GNU_SOURCE
#include <errno.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <signal.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

#define PROBE_PATH "/nonexistent/anyplot-exec-probe"
#define REQUIRED_EXIT 3
#define PROBE_ENOENT_EXIT 10

#if defined(__x86_64__)
#define AUDIT_ARCH_THIS AUDIT_ARCH_X86_64
#elif defined(__aarch64__)
#define AUDIT_ARCH_THIS AUDIT_ARCH_AARCH64
#endif

enum probe { PROBE_ENOENT, PROBE_KILLED, PROBE_OTHER };

/* Fork a child that execs PROBE_PATH, and say how it ended. */
static enum probe probe(void) {
    pid_t pid = fork();
    if (pid < 0) return PROBE_OTHER;
    if (pid == 0) {
        char *const argv[] = {PROBE_PATH, NULL};
        char *const envp[] = {NULL};
        execve(PROBE_PATH, argv, envp);
        _exit(errno == ENOENT ? PROBE_ENOENT_EXIT : PROBE_ENOENT_EXIT + 1);
    }
    int status;
    while (waitpid(pid, &status, 0) < 0) {
        if (errno != EINTR) return PROBE_OTHER;
    }
    if (WIFEXITED(status) && WEXITSTATUS(status) == PROBE_ENOENT_EXIT) return PROBE_ENOENT;
    if (WIFSIGNALED(status) && WTERMSIG(status) == SIGSYS) return PROBE_KILLED;
    return PROBE_OTHER;
}

static const char *install(void) {
#ifndef AUDIT_ARCH_THIS
    return "unsupported";
#else
    /* A sandbox that refuses execve already would make the probe after the install prove nothing. */
    if (probe() != PROBE_ENOENT) return "unavailable";
    struct sock_filter program[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
#if defined(__x86_64__)
        /* Another architecture (a 32-bit int 0x80) and the x32 ABI carry other numbers for the same calls. */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_THIS, 0, 5),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000, 3, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_execve, 2, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_execveat, 1, 0),
#else
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_THIS, 0, 4),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_execve, 2, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_execveat, 1, 0),
#endif
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
    };
    struct sock_fprog fprog = {
        .len = (unsigned short)(sizeof(program) / sizeof(program[0])),
        .filter = program,
    };
    /* Not dumpable, so a killed child never dumps core. A popen or system() child is a vfork (CLONE_VM) child of
     * R, and before Linux 5.16 a core dump kills every process that shares the dumping one's memory: the
     * child's SIGSYS took R down with it (the first Cloud Build of the toolchain, 2026-10-29), where newer
     * kernels kill the child alone. Without a dump the child dies alone on every kernel. */
    if (prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != 0) return "unavailable";
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) return "unavailable";
    /* TSYNC answers a positive thread id when a thread cannot take the filter; only 0 installed it everywhere. */
    if (syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, SECCOMP_FILTER_FLAG_TSYNC, &fprog) != 0) {
        return "unavailable";
    }
    return probe() == PROBE_KILLED ? "on" : "unavailable";
#endif
}

/* Write the state to the harness's pipe, then close it and drop its name. */
static void report(const char *state) {
    const char *name = getenv("ANYPLOT_EXEC_DENY_FD");
    if (name == NULL) return;
    char *end = NULL;
    long fd = strtol(name, &end, 10);
    if (end != name && *end == '\0' && fd > 2 && fd < 1024) {
        ssize_t ignored = write((int)fd, state, strlen(state));
        (void)ignored;
        close((int)fd);
    }
    unsetenv("ANYPLOT_EXEC_DENY_FD");
}

__attribute__((constructor)) static void anyplot_exec_deny(void) {
    const char *mode = getenv("ANYPLOT_DENY_EXEC");
    if (mode == NULL || mode[0] == '\0') return;
    const char *state = install();
    int required = strcmp(mode, "required") == 0;
    report(state);
    if (required && strcmp(state, "on") != 0) _exit(REQUIRED_EXIT);
}
